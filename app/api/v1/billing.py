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
from app.db.models.billing import SubscriptionPlan, Subscription, Payment
from app.schemas.billing import (
    SubscriptionPlanResponse,
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    SubscriptionResponse,
    PaymentResponse,
    PortalSessionResponse,
    CancelSubscriptionRequest,
    WebhookEvent
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
            await billing_service.handle_checkout_completed(event_data, db)
        
        elif event_type == 'customer.subscription.updated':
            await billing_service.handle_subscription_updated(event_data, db)
        
        elif event_type == 'customer.subscription.deleted':
            await billing_service.handle_subscription_updated(event_data, db)
        
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
