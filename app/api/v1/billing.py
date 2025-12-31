"""
Billing API endpoints
Handles subscriptions, payments, and Stripe webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import stripe
import logging

from app.db.session import get_db
from app.core.jwt import get_current_active_user
from app.core.config import settings
from app.db.models.user import User
from app.db.models.billing import SubscriptionPlan, Subscription, Payment, LoungeSubscription, SubscriptionStatus
from app.schemas.billing import (
    SubscriptionPlanResponse,
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    SubscriptionResponse,
    PaymentResponse,
    PortalSessionResponse,
    CancelSubscriptionRequest,
    WebhookEvent,
    LoungeCheckoutCreate,
    LoungeSubscriptionResponse,
    CancelLoungeSubscriptionRequest,
    LoungePricing
)
from app.services.billing_service import billing_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    db: Session = Depends(get_db)
):
    """
    List subscription plans
    
    - Public endpoint
    - Returns active plans with pricing
    """
    plans = await billing_service.get_active_plans(db)
    
    result = []
    for plan in plans:
        price_display = f"${plan.price_cents / 100:.2f}/{plan.billing_interval}"
        features = plan.features if isinstance(plan.features, list) else []
        
        result.append(SubscriptionPlanResponse(
            id=plan.id,
            name=plan.name,
            slug=plan.slug,
            stripe_price_id=plan.stripe_price_id,
            price_cents=plan.price_cents,
            billing_interval=plan.billing_interval,
            features=features,
            is_active=plan.is_active,
            price_display=price_display
        ))
    
    return result


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    checkout_data: CheckoutSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create Stripe checkout session

    - Requires authentication
    - Creates checkout for subscription
    - Redirects to Stripe hosted page
    """
    try:
        session_data = await billing_service.create_checkout_session(
            user_id=current_user.id,
            plan_id=checkout_data.plan_id,
            lounge_id=checkout_data.lounge_id,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
            db=db
        )
        
        return CheckoutSessionResponse(**session_data)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout: {str(e)}"
        )


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current subscription
    
    - Returns active subscription details
    - Returns null if no active subscription
    """
    subscription = await billing_service.get_user_subscription(
        user_id=current_user.id,
        db=db
    )
    
    if not subscription:
        return None
    
    plan = subscription.plan
    
    is_active = subscription.status in ['active', 'trialing']
    days_until = None
    if subscription.renews_at:
        delta = subscription.renews_at - datetime.utcnow()
        days_until = max(0, delta.days)
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_id=subscription.plan_id,
        stripe_subscription_id=subscription.stripe_subscription_id,
        status=subscription.status.value,
        started_at=subscription.started_at,
        renews_at=subscription.renews_at,
        canceled_at=subscription.canceled_at,
        plan_name=plan.name,
        plan_price_cents=plan.price_cents,
        billing_interval=plan.billing_interval,
        is_active=is_active,
        days_until_renewal=days_until
    )


@router.post("/subscription/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    cancel_data: CancelSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    immediate: bool = False
):
    """
    Cancel subscription
    
    - By default, cancels at period end
    - Set immediate=true to cancel immediately
    """
    try:
        subscription = await billing_service.cancel_subscription(
            user_id=current_user.id,
            db=db,
            immediate=immediate
        )
        
        plan = subscription.plan
        
        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_id=subscription.plan_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            status=subscription.status.value,
            started_at=subscription.started_at,
            renews_at=subscription.renews_at,
            canceled_at=subscription.canceled_at,
            plan_name=plan.name,
            plan_price_cents=plan.price_cents,
            billing_interval=plan.billing_interval,
            is_active=False
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling subscription: {str(e)}"
        )


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    return_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create billing portal session
    
    - Opens Stripe customer portal
    - Manage payment methods, invoices, etc.
    """
    try:
        portal_url = await billing_service.create_portal_session(
            user_id=current_user.id,
            return_url=return_url,
            db=db
        )
        
        return PortalSessionResponse(url=portal_url)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating portal session: {str(e)}"
        )


@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = 50
):
    """
    List payment history
    
    - Returns user's payment transactions
    - Sorted by most recent
    """
    payments = await billing_service.get_payment_history(
        user_id=current_user.id,
        db=db,
        limit=limit
    )
    
    result = []
    for payment in payments:
        amount_display = f"${payment.amount_cents / 100:.2f} {payment.currency}"
        
        result.append(PaymentResponse(
            id=payment.id,
            user_id=payment.user_id,
            provider=payment.provider.value,
            provider_payment_id=payment.provider_payment_id,
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            status=payment.status.value,
            created_at=payment.created_at,
            amount_display=amount_display
        ))

    return result


# =============================================================================
# Lounge-Specific Subscription Endpoints
# =============================================================================

@router.get("/lounge/pricing", response_model=LoungePricing)
async def get_lounge_pricing():
    """
    Get lounge subscription pricing information

    - Public endpoint
    - Returns fixed pricing for all lounges
    """
    return LoungePricing()


@router.post("/lounge/checkout", response_model=CheckoutSessionResponse)
async def create_lounge_checkout(
    checkout_data: LoungeCheckoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create Stripe checkout session for lounge subscription

    - Requires authentication
    - Creates checkout for lounge-specific subscription
    - Plan type: 'monthly' ($25/month) or 'yearly' ($240/year)
    """
    try:
        session_data = await billing_service.create_lounge_checkout_session(
            user_id=current_user.id,
            lounge_id=checkout_data.lounge_id,
            plan_type=checkout_data.plan_type,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
            db=db
        )

        return CheckoutSessionResponse(**session_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout: {str(e)}"
        )


@router.post("/lounge/verify-session")
async def verify_lounge_checkout_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify a lounge checkout session and ensure membership is created.

    This is a fallback for when webhooks don't fire properly.
    Called after user returns from successful Stripe checkout.
    """
    from app.db.models.lounge import LoungeMembership, MembershipRole
    from app.db.models.billing import SubscriptionStatus, LoungePlanType

    try:
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != 'paid':
            return {"success": False, "message": "Payment not completed"}

        # Check if this is a lounge subscription
        metadata = session.get('metadata', {})
        if metadata.get('subscription_type') != 'lounge':
            return {"success": False, "message": "Not a lounge subscription"}

        user_id = int(metadata.get('user_id', 0))
        lounge_id = int(metadata.get('lounge_id', 0))
        plan_type_str = metadata.get('plan_type', 'monthly')

        # Verify the user matches
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to current user"
            )

        # Check if subscription already exists
        existing_sub = db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id,
            LoungeSubscription.lounge_id == lounge_id,
            LoungeSubscription.stripe_subscription_id == session.subscription
        ).first()

        if not existing_sub and session.subscription:
            # Create subscription record (webhook didn't fire)
            stripe_sub = stripe.Subscription.retrieve(session.subscription)
            price_id = stripe_sub['items']['data'][0]['price']['id']
            plan_type = LoungePlanType.MONTHLY if plan_type_str == 'monthly' else LoungePlanType.YEARLY

            lounge_subscription = LoungeSubscription(
                user_id=user_id,
                lounge_id=lounge_id,
                plan_type=plan_type,
                stripe_subscription_id=session.subscription,
                stripe_price_id=price_id,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.fromtimestamp(stripe_sub['current_period_start']),
                renews_at=datetime.fromtimestamp(stripe_sub['current_period_end'])
            )
            db.add(lounge_subscription)
            db.commit()
            logger.info(f"Created lounge subscription via verify for user {user_id}, lounge {lounge_id}")

        # Check if membership exists
        existing_membership = db.query(LoungeMembership).filter(
            LoungeMembership.user_id == user_id,
            LoungeMembership.lounge_id == lounge_id,
            LoungeMembership.left_at.is_(None)
        ).first()

        if not existing_membership:
            # Create membership
            membership = LoungeMembership(
                user_id=user_id,
                lounge_id=lounge_id,
                role=MembershipRole.MEMBER
            )
            db.add(membership)
            db.commit()
            logger.info(f"Created lounge membership via verify for user {user_id} in lounge {lounge_id}")
            return {"success": True, "message": "Membership created", "lounge_id": lounge_id}

        return {"success": True, "message": "Already a member", "lounge_id": lounge_id}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error verifying checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying session: {str(e)}"
        )


@router.get("/lounge/{lounge_id}/subscription", response_model=Optional[LoungeSubscriptionResponse])
async def get_lounge_subscription(
    lounge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's subscription to a specific lounge

    - Returns active subscription details
    - Returns null if no active subscription
    """
    subscription = await billing_service.get_user_lounge_subscription(
        user_id=current_user.id,
        lounge_id=lounge_id,
        db=db
    )

    if not subscription:
        return None

    lounge = subscription.lounge

    days_until = None
    if subscription.renews_at:
        from datetime import datetime
        delta = subscription.renews_at - datetime.utcnow()
        days_until = max(0, delta.days)

    return LoungeSubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        lounge_id=subscription.lounge_id,
        plan_type=subscription.plan_type.value,
        stripe_subscription_id=subscription.stripe_subscription_id,
        stripe_price_id=subscription.stripe_price_id,
        status=subscription.status.value,
        started_at=subscription.started_at,
        renews_at=subscription.renews_at,
        canceled_at=subscription.canceled_at,
        lounge_title=lounge.title,
        lounge_slug=lounge.slug,
        is_active=subscription.is_active,
        days_until_renewal=days_until
    )


@router.get("/lounge/subscriptions", response_model=List[LoungeSubscriptionResponse])
async def get_lounge_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    include_canceled: bool = False
):
    """
    Get all user's lounge subscriptions

    - Returns list of lounge subscriptions
    - Optionally include canceled subscriptions
    """
    subscriptions = await billing_service.get_user_lounge_subscriptions(
        user_id=current_user.id,
        db=db,
        include_canceled=include_canceled
    )

    result = []
    for subscription in subscriptions:
        lounge = subscription.lounge

        days_until = None
        if subscription.renews_at:
            from datetime import datetime
            delta = subscription.renews_at - datetime.utcnow()
            days_until = max(0, delta.days)

        result.append(LoungeSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            lounge_id=subscription.lounge_id,
            plan_type=subscription.plan_type.value,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_price_id=subscription.stripe_price_id,
            status=subscription.status.value,
            started_at=subscription.started_at,
            renews_at=subscription.renews_at,
            canceled_at=subscription.canceled_at,
            lounge_title=lounge.title,
            lounge_slug=lounge.slug,
            is_active=subscription.is_active,
            days_until_renewal=days_until
        ))

    return result


@router.post("/lounge/{lounge_id}/subscription/cancel", response_model=LoungeSubscriptionResponse)
async def cancel_lounge_subscription(
    lounge_id: int,
    cancel_data: CancelLoungeSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel lounge subscription

    - By default, cancels at period end
    - Set immediate=true to cancel immediately
    """
    try:
        subscription = await billing_service.cancel_lounge_subscription(
            user_id=current_user.id,
            lounge_id=lounge_id,
            db=db,
            immediate=cancel_data.immediate
        )

        lounge = subscription.lounge

        return LoungeSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            lounge_id=subscription.lounge_id,
            plan_type=subscription.plan_type.value,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_price_id=subscription.stripe_price_id,
            status=subscription.status.value,
            started_at=subscription.started_at,
            renews_at=subscription.renews_at,
            canceled_at=subscription.canceled_at,
            lounge_title=lounge.title,
            lounge_slug=lounge.slug,
            is_active=False
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling subscription: {str(e)}"
        )


@router.post("/sync-subscription")
async def sync_subscription_from_stripe(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually sync subscription status from Stripe.

    Use this as a fallback when webhooks aren't working properly.
    Syncs both regular subscriptions and lounge subscriptions.
    """
    synced = {"regular": 0, "lounge": 0, "errors": []}

    # Sync regular subscriptions
    regular_subs = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.stripe_subscription_id.isnot(None)
    ).all()

    for sub in regular_subs:
        try:
            stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
            await billing_service.handle_subscription_updated(stripe_sub, db)
            synced["regular"] += 1
            logger.info(f"Synced regular subscription {sub.id} for user {current_user.id}")
        except stripe.error.InvalidRequestError as e:
            # Subscription doesn't exist in Stripe anymore
            sub.status = SubscriptionStatus.CANCELED
            db.commit()
            synced["errors"].append(f"Regular sub {sub.id}: {str(e)}")
        except Exception as e:
            synced["errors"].append(f"Regular sub {sub.id}: {str(e)}")

    # Sync lounge subscriptions
    lounge_subs = db.query(LoungeSubscription).filter(
        LoungeSubscription.user_id == current_user.id,
        LoungeSubscription.stripe_subscription_id.isnot(None)
    ).all()

    for sub in lounge_subs:
        try:
            stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
            await billing_service.handle_lounge_subscription_updated(stripe_sub, db)
            synced["lounge"] += 1
            logger.info(f"Synced lounge subscription {sub.id} for user {current_user.id}")
        except stripe.error.InvalidRequestError as e:
            # Subscription doesn't exist in Stripe anymore
            sub.status = SubscriptionStatus.CANCELED
            db.commit()
            synced["errors"].append(f"Lounge sub {sub.id}: {str(e)}")
        except Exception as e:
            synced["errors"].append(f"Lounge sub {sub.id}: {str(e)}")

    return {
        "message": "Subscription sync completed",
        "synced_regular": synced["regular"],
        "synced_lounge": synced["lounge"],
        "errors": synced["errors"] if synced["errors"] else None
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None)
):
    """
    Stripe webhook endpoint
    
    - Handles Stripe events
    - Validates webhook signature
    - Updates subscriptions and payments
    """
    try:
        # Get raw body
        payload = await request.body()
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Handle event
        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Received Stripe webhook: {event_type}")

        if event_type == 'checkout.session.completed':
            # Check if this is a lounge subscription by looking at metadata
            metadata = event_data.get('metadata', {})
            if metadata.get('subscription_type') == 'lounge':
                logger.info(f"Processing lounge checkout completion for lounge {metadata.get('lounge_id')}")
                await billing_service.handle_lounge_checkout_completed(event_data, db)
            else:
                await billing_service.handle_checkout_completed(event_data, db)

        elif event_type in ['customer.subscription.updated', 'customer.subscription.deleted']:
            # Determine if this is a lounge subscription by checking the database
            stripe_sub_id = event_data['id']

            # Check if it's a lounge subscription first
            lounge_sub = db.query(LoungeSubscription).filter(
                LoungeSubscription.stripe_subscription_id == stripe_sub_id
            ).first()

            if lounge_sub:
                logger.info(f"Processing lounge subscription update for subscription {stripe_sub_id}")
                await billing_service.handle_lounge_subscription_updated(event_data, db)
            else:
                await billing_service.handle_subscription_updated(event_data, db)

        elif event_type == 'invoice.paid':
            # Handle successful subscription renewal
            subscription_id = event_data.get('subscription')
            if subscription_id:
                logger.info(f"Invoice paid for subscription {subscription_id}")
                # Fetch the updated subscription from Stripe
                try:
                    stripe_sub = stripe.Subscription.retrieve(subscription_id)
                    # Check if it's a lounge subscription
                    lounge_sub = db.query(LoungeSubscription).filter(
                        LoungeSubscription.stripe_subscription_id == subscription_id
                    ).first()
                    if lounge_sub:
                        await billing_service.handle_lounge_subscription_updated(stripe_sub, db)
                    else:
                        await billing_service.handle_subscription_updated(stripe_sub, db)
                except Exception as e:
                    logger.error(f"Error processing invoice.paid: {str(e)}")

        elif event_type == 'invoice.payment_failed':
            # Handle failed subscription renewal payment
            subscription_id = event_data.get('subscription')
            if subscription_id:
                logger.warning(f"Invoice payment failed for subscription {subscription_id}")
                # Fetch the updated subscription from Stripe to get its current status
                try:
                    stripe_sub = stripe.Subscription.retrieve(subscription_id)
                    # Check if it's a lounge subscription
                    lounge_sub = db.query(LoungeSubscription).filter(
                        LoungeSubscription.stripe_subscription_id == subscription_id
                    ).first()
                    if lounge_sub:
                        await billing_service.handle_lounge_subscription_updated(stripe_sub, db)
                    else:
                        await billing_service.handle_subscription_updated(stripe_sub, db)
                except Exception as e:
                    logger.error(f"Error processing invoice.payment_failed: {str(e)}")

        elif event_type == 'payment_intent.succeeded':
            await billing_service.handle_payment_succeeded(event_data, db)

        elif event_type == 'payment_intent.payment_failed':
            logger.warning(f"Payment failed: {event_data.get('id')}")

        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.get("/invoices")
async def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = 20
):
    """
    List invoices

    - Returns Stripe invoices for user
    - Includes download URLs
    """
    try:
        subscription = await billing_service.get_user_subscription(
            user_id=current_user.id,
            db=db
        )

        if not subscription or not subscription.stripe_subscription_id:
            return []

        # Check if the subscription ID looks like a real Stripe subscription ID
        # Real Stripe subscription IDs start with "sub_" followed by alphanumeric characters
        stripe_sub_id = subscription.stripe_subscription_id
        if not stripe_sub_id.startswith("sub_") or len(stripe_sub_id) < 20:
            # This is likely a placeholder/test subscription ID, return empty
            logger.info(f"Subscription ID {stripe_sub_id} appears to be a placeholder, skipping invoice fetch")
            return []

        # Get invoices from Stripe
        invoices = stripe.Invoice.list(
            subscription=stripe_sub_id,
            limit=limit
        )

        result = []
        for invoice in invoices.data:
            result.append({
                'id': invoice.id,
                'number': invoice.number,
                'amount_due': invoice.amount_due,
                'amount_paid': invoice.amount_paid,
                'currency': invoice.currency.upper(),
                'status': invoice.status,
                'created': datetime.fromtimestamp(invoice.created),
                'invoice_pdf': invoice.invoice_pdf,
                'hosted_invoice_url': invoice.hosted_invoice_url
            })

        return result

    except stripe.error.InvalidRequestError as e:
        # Handle invalid subscription ID (not found in Stripe)
        logger.warning(f"Invalid Stripe subscription ID: {str(e)}")
        return []

    except Exception as e:
        logger.error(f"Error fetching invoices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching invoices: {str(e)}"
        )
