"""
Billing service for Stripe integration
Handles subscriptions, payments, and webhooks
"""
import stripe
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.db.models.billing import (
    SubscriptionPlan,
    Subscription,
    LoungeSubscription,
    Payment,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus,
    LoungePlanType
)
from app.db.models.user import User
from app.db.models.lounge import Lounge, LoungeMembership, MembershipRole, AccessType

# Lounge subscription pricing constants
LOUNGE_MONTHLY_PRICE_CENTS = 2500   # $25/month
LOUNGE_YEARLY_PRICE_CENTS = 24000   # $240/year

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class BillingService:
    """Service for managing billing and subscriptions"""
    
    def __init__(self):
        """Initialize billing service"""
        self.stripe = stripe
    
    async def get_active_plans(self, db: Session) -> List[SubscriptionPlan]:
        """
        Get active subscription plans
        
        Args:
            db: Database session
            
        Returns:
            List of active plans
        """
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True
        ).all()
    
    async def create_checkout_session(
        self,
        user_id: int,
        plan_id: int,
        lounge_id: Optional[int],
        success_url: str,
        cancel_url: str,
        db: Session
    ) -> Dict:
        """
        Create Stripe checkout session
        
        Args:
            user_id: User ID
            plan_id: Plan ID
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL
            db: Database session
            
        Returns:
            Checkout session data
            
        Raises:
            ValueError: If plan not found or user already subscribed
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get plan
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        
        if not plan:
            raise ValueError("Plan not found or inactive")
        
        # Check if user already has active subscription
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()
        
        if existing:
            raise ValueError("User already has an active subscription")
        
        try:
            # Create or get Stripe customer
            customer_id = await self._get_or_create_customer(user, db)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'plan_id': str(plan_id),
                    'lounge_id': str(lounge_id) if lounge_id else ''
                }
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            
            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'expires_at': datetime.fromtimestamp(session.expires_at)
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")
    
    async def create_portal_session(
        self,
        user_id: int,
        return_url: str,
        db: Session
    ) -> str:
        """
        Create Stripe customer portal session
        
        Args:
            user_id: User ID
            return_url: Return URL after portal
            db: Database session
            
        Returns:
            Portal URL
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        try:
            customer_id = await self._get_or_create_customer(user, db)
            
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            return session.url
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal: {str(e)}")
            raise Exception(f"Failed to create portal session: {str(e)}")
    
    async def handle_checkout_completed(
        self,
        session: Dict,
        db: Session
    ):
        """
        Handle successful checkout completion

        Args:
            session: Stripe session object
            db: Database session
        """
        try:
            user_id = int(session['metadata']['user_id'])
            plan_id = int(session['metadata']['plan_id'])
            lounge_id_str = session['metadata'].get('lounge_id', '')
            lounge_id = int(lounge_id_str) if lounge_id_str else None

            # Get subscription from Stripe
            subscription_id = session['subscription']
            stripe_sub = stripe.Subscription.retrieve(subscription_id)

            # Create subscription record
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                stripe_subscription_id=subscription_id,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.fromtimestamp(stripe_sub['current_period_start']),
                renews_at=datetime.fromtimestamp(stripe_sub['current_period_end'])
            )

            db.add(subscription)
            db.commit()

            logger.info(f"Created subscription {subscription.id} for user {user_id}")

            # Create lounge membership if lounge_id is provided
            if lounge_id:
                # Check if membership already exists
                existing_membership = db.query(LoungeMembership).filter(
                    LoungeMembership.user_id == user_id,
                    LoungeMembership.lounge_id == lounge_id,
                    LoungeMembership.left_at.is_(None)
                ).first()

                if not existing_membership:
                    membership = LoungeMembership(
                        user_id=user_id,
                        lounge_id=lounge_id,
                        role=MembershipRole.MEMBER
                    )
                    db.add(membership)
                    db.commit()
                    logger.info(f"Created lounge membership for user {user_id} in lounge {lounge_id}")
                else:
                    logger.info(f"User {user_id} already a member of lounge {lounge_id}")

        except Exception as e:
            logger.error(f"Error handling checkout completion: {str(e)}")
            raise
    
    async def handle_subscription_updated(
        self,
        subscription: Dict,
        db: Session
    ):
        """
        Handle subscription update from Stripe

        Args:
            subscription: Stripe subscription object
            db: Database session
        """
        try:
            stripe_sub_id = subscription['id']

            # Find subscription
            sub = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_sub_id
            ).first()

            if not sub:
                logger.warning(f"Subscription {stripe_sub_id} not found in database")
                return

            # Update status
            status_map = {
                'active': SubscriptionStatus.ACTIVE,
                'trialing': SubscriptionStatus.TRIALING,
                'past_due': SubscriptionStatus.PAST_DUE,
                'canceled': SubscriptionStatus.CANCELED,
                'unpaid': SubscriptionStatus.PAST_DUE
            }

            new_status = status_map.get(subscription.get('status'), SubscriptionStatus.CANCELED)
            sub.status = new_status

            # Update renewal date - handle both old and new Stripe API structures
            current_period_end = None
            # Try new structure (current_period object)
            if hasattr(subscription, 'current_period') and subscription.current_period:
                current_period_end = subscription.current_period.get('end')
            # Fallback to old structure
            if not current_period_end:
                current_period_end = subscription.get('current_period_end')

            if current_period_end:
                sub.renews_at = datetime.fromtimestamp(current_period_end)
            
            # Update cancellation date if canceled
            if subscription.get('canceled_at'):
                sub.canceled_at = datetime.fromtimestamp(subscription['canceled_at'])
            
            db.commit()
            
            logger.info(f"Updated subscription {sub.id} to status {new_status}")
        
        except Exception as e:
            logger.error(f"Error handling subscription update: {str(e)}")
            raise
    
    async def handle_payment_succeeded(
        self,
        payment_intent: Dict,
        db: Session
    ):
        """
        Handle successful payment
        
        Args:
            payment_intent: Stripe payment intent object
            db: Database session
        """
        try:
            # Extract customer ID
            customer_id = payment_intent.get('customer')
            if not customer_id:
                return
            
            # Find user by customer ID
            # In production, store customer_id in user table
            # For now, we'll skip user lookup
            
            # Create payment record
            payment = Payment(
                user_id=0,  # TODO: Link to actual user
                provider=PaymentProvider.STRIPE,
                provider_payment_id=payment_intent['id'],
                amount_cents=payment_intent['amount'],
                currency=payment_intent['currency'].upper(),
                status=PaymentStatus.SUCCEEDED
            )
            
            db.add(payment)
            db.commit()
            
            logger.info(f"Recorded payment {payment.id}")
        
        except Exception as e:
            logger.error(f"Error handling payment: {str(e)}")
    
    async def cancel_subscription(
        self,
        user_id: int,
        db: Session,
        immediate: bool = False
    ) -> Subscription:
        """
        Cancel user's subscription
        
        Args:
            user_id: User ID
            db: Database session
            immediate: Cancel immediately vs at period end
            
        Returns:
            Updated subscription
            
        Raises:
            ValueError: If no active subscription found
        """
        # Find active subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        try:
            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=not immediate
                )
                
                if immediate:
                    stripe.Subscription.cancel(subscription.stripe_subscription_id)
            
            # Update database
            if immediate:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.utcnow()
            else:
                # Will cancel at period end
                subscription.canceled_at = subscription.renews_at
            
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Canceled subscription {subscription.id}")
            
            return subscription
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    async def get_user_subscription(
        self,
        user_id: int,
        db: Session
    ) -> Optional[Subscription]:
        """
        Get user's active subscription
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Subscription or None
        """
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()
    
    async def get_payment_history(
        self,
        user_id: int,
        db: Session,
        limit: int = 50
    ) -> List[Payment]:
        """
        Get user's payment history
        
        Args:
            user_id: User ID
            db: Database session
            limit: Maximum records
            
        Returns:
            List of payments
        """
        return db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(
            Payment.created_at.desc()
        ).limit(limit).all()
    
    async def _get_or_create_customer(
        self,
        user: User,
        db: Session
    ) -> str:
        """
        Get or create Stripe customer for user
        
        Args:
            user: User instance
            db: Database session
            
        Returns:
            Stripe customer ID
        """
        # In production, store stripe_customer_id in user table
        # For now, create new customer each time
        
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    'user_id': str(user.id)
                }
            )
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")

            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    # =========================================================================
    # Lounge-Specific Subscription Methods
    # =========================================================================

    async def create_lounge_stripe_product(
        self,
        lounge_id: int,
        lounge_title: str,
        lounge_slug: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Create Stripe product and prices for a lounge

        Args:
            lounge_id: Database ID of the lounge
            lounge_title: Title of the lounge for product name
            lounge_slug: Slug for metadata
            db: Database session

        Returns:
            Dict with stripe_product_id, stripe_monthly_price_id, stripe_yearly_price_id

        Raises:
            Exception: If Stripe API call fails
        """
        try:
            # Create Stripe Product
            product = stripe.Product.create(
                name=f"Lounge: {lounge_title}",
                description=f"Subscription to {lounge_title} lounge",
                metadata={
                    'lounge_id': str(lounge_id),
                    'lounge_slug': lounge_slug,
                    'type': 'lounge_subscription'
                }
            )

            logger.info(f"Created Stripe product {product.id} for lounge {lounge_id}")

            # Create Monthly Price
            monthly_price = stripe.Price.create(
                product=product.id,
                unit_amount=LOUNGE_MONTHLY_PRICE_CENTS,
                currency='usd',
                recurring={
                    'interval': 'month',
                    'interval_count': 1
                },
                metadata={
                    'lounge_id': str(lounge_id),
                    'plan_type': 'monthly'
                }
            )

            logger.info(f"Created monthly price {monthly_price.id} for lounge {lounge_id}")

            # Create Yearly Price
            yearly_price = stripe.Price.create(
                product=product.id,
                unit_amount=LOUNGE_YEARLY_PRICE_CENTS,
                currency='usd',
                recurring={
                    'interval': 'year',
                    'interval_count': 1
                },
                metadata={
                    'lounge_id': str(lounge_id),
                    'plan_type': 'yearly'
                }
            )

            logger.info(f"Created yearly price {yearly_price.id} for lounge {lounge_id}")

            return {
                'stripe_product_id': product.id,
                'stripe_monthly_price_id': monthly_price.id,
                'stripe_yearly_price_id': yearly_price.id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating lounge product: {str(e)}")
            raise Exception(f"Failed to create Stripe product for lounge: {str(e)}")

    async def create_lounge_checkout_session(
        self,
        user_id: int,
        lounge_id: int,
        plan_type: str,  # 'monthly' or 'yearly'
        success_url: str,
        cancel_url: str,
        db: Session
    ) -> Dict:
        """
        Create Stripe checkout session for lounge subscription

        Args:
            user_id: User ID
            lounge_id: Lounge ID
            plan_type: 'monthly' or 'yearly'
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL
            db: Database session

        Returns:
            Checkout session data

        Raises:
            ValueError: If lounge not found, not paid, or user already subscribed
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Get lounge
        lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
        if not lounge:
            raise ValueError("Lounge not found")

        # Verify lounge is paid and has Stripe product
        if lounge.access_type != AccessType.PAID:
            raise ValueError("Lounge is not a paid lounge")

        if not lounge.stripe_product_id:
            raise ValueError("Lounge does not have Stripe product configured")

        # Select correct price ID
        if plan_type == 'monthly':
            price_id = lounge.stripe_monthly_price_id
        elif plan_type == 'yearly':
            price_id = lounge.stripe_yearly_price_id
        else:
            raise ValueError("Invalid plan type. Must be 'monthly' or 'yearly'")

        if not price_id:
            raise ValueError(f"Lounge does not have {plan_type} price configured")

        # Check if user already has active subscription to this lounge
        existing = db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id,
            LoungeSubscription.lounge_id == lounge_id,
            LoungeSubscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()

        if existing:
            raise ValueError("User already has an active subscription to this lounge")

        try:
            # Create or get Stripe customer
            customer_id = await self._get_or_create_customer(user, db)

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'lounge_id': str(lounge_id),
                    'plan_type': plan_type,
                    'subscription_type': 'lounge'  # Distinguish from regular subscriptions
                }
            )

            logger.info(f"Created lounge checkout session {session.id} for user {user_id}, lounge {lounge_id}")

            return {
                'session_id': session.id,
                'checkout_url': session.url,
                'expires_at': datetime.fromtimestamp(session.expires_at)
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating lounge checkout: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")

    async def handle_lounge_checkout_completed(
        self,
        session: Dict,
        db: Session
    ):
        """
        Handle successful lounge subscription checkout

        Args:
            session: Stripe session object
            db: Database session
        """
        try:
            user_id = int(session['metadata']['user_id'])
            lounge_id = int(session['metadata']['lounge_id'])
            plan_type_str = session['metadata']['plan_type']

            logger.info(f"Processing lounge checkout: user={user_id}, lounge={lounge_id}, plan={plan_type_str}")

            # Map plan type string to enum
            plan_type = LoungePlanType.MONTHLY if plan_type_str == 'monthly' else LoungePlanType.YEARLY

            # Get subscription from Stripe
            subscription_id = session['subscription']
            stripe_sub = stripe.Subscription.retrieve(subscription_id)

            logger.info(f"Retrieved Stripe subscription: {subscription_id}")
            logger.info(f"Subscription keys: {list(stripe_sub.keys()) if hasattr(stripe_sub, 'keys') else 'N/A'}")

            # Get the price ID from the subscription - handle new API structure
            try:
                price_id = stripe_sub['items']['data'][0]['price']['id']
            except (KeyError, IndexError) as e:
                logger.warning(f"Could not get price_id from subscription: {e}")
                price_id = None

            # Get period dates - handle both old and new Stripe API structures
            # New API uses 'current_period' object, old API uses direct fields
            current_period_start = None
            current_period_end = None

            # Try new structure first (current_period object)
            if hasattr(stripe_sub, 'current_period') and stripe_sub.current_period:
                current_period_start = stripe_sub.current_period.get('start')
                current_period_end = stripe_sub.current_period.get('end')
                logger.info("Using current_period object structure")

            # Fallback to old structure (direct fields)
            if not current_period_start:
                current_period_start = stripe_sub.get('current_period_start')
                current_period_end = stripe_sub.get('current_period_end')
                logger.info("Using direct field structure")

            # If still not found, use current time as fallback
            if not current_period_start:
                logger.warning("Could not find period dates, using current time")
                current_period_start = datetime.utcnow().timestamp()
                # Default to 1 month or 1 year based on plan
                if plan_type == LoungePlanType.YEARLY:
                    current_period_end = (datetime.utcnow() + timedelta(days=365)).timestamp()
                else:
                    current_period_end = (datetime.utcnow() + timedelta(days=30)).timestamp()

            logger.info(f"Period: start={current_period_start}, end={current_period_end}")

            # Create lounge subscription record
            lounge_subscription = LoungeSubscription(
                user_id=user_id,
                lounge_id=lounge_id,
                plan_type=plan_type,
                stripe_subscription_id=subscription_id,
                stripe_price_id=price_id,
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.fromtimestamp(current_period_start),
                renews_at=datetime.fromtimestamp(current_period_end)
            )

            db.add(lounge_subscription)
            db.commit()

            logger.info(f"Created lounge subscription {lounge_subscription.id} for user {user_id}, lounge {lounge_id}")

            # Create lounge membership if not already a member
            existing_membership = db.query(LoungeMembership).filter(
                LoungeMembership.user_id == user_id,
                LoungeMembership.lounge_id == lounge_id,
                LoungeMembership.left_at.is_(None)
            ).first()

            if not existing_membership:
                membership = LoungeMembership(
                    user_id=user_id,
                    lounge_id=lounge_id,
                    role=MembershipRole.MEMBER
                )
                db.add(membership)
                db.commit()
                logger.info(f"Created lounge membership for user {user_id} in lounge {lounge_id}")
            else:
                logger.info(f"User {user_id} already a member of lounge {lounge_id}")

        except Exception as e:
            logger.error(f"Error handling lounge checkout completion: {str(e)}")
            db.rollback()
            raise

    async def handle_lounge_subscription_updated(
        self,
        subscription: Dict,
        db: Session
    ):
        """
        Handle lounge subscription update from Stripe

        Args:
            subscription: Stripe subscription object
            db: Database session
        """
        try:
            stripe_sub_id = subscription['id']

            # Find lounge subscription
            lounge_sub = db.query(LoungeSubscription).filter(
                LoungeSubscription.stripe_subscription_id == stripe_sub_id
            ).first()

            if not lounge_sub:
                logger.warning(f"Lounge subscription {stripe_sub_id} not found in database")
                return

            # Update status
            status_map = {
                'active': SubscriptionStatus.ACTIVE,
                'trialing': SubscriptionStatus.TRIALING,
                'past_due': SubscriptionStatus.PAST_DUE,
                'canceled': SubscriptionStatus.CANCELED,
                'unpaid': SubscriptionStatus.PAST_DUE
            }

            new_status = status_map.get(subscription.get('status'), SubscriptionStatus.CANCELED)
            old_status = lounge_sub.status
            lounge_sub.status = new_status

            # Update renewal date - handle both old and new Stripe API structures
            current_period_end = None
            # Try new structure (current_period object)
            if hasattr(subscription, 'current_period') and subscription.current_period:
                current_period_end = subscription.current_period.get('end')
            # Fallback to old structure
            if not current_period_end:
                current_period_end = subscription.get('current_period_end')

            if current_period_end:
                lounge_sub.renews_at = datetime.fromtimestamp(current_period_end)

            # Update cancellation date if canceled
            if subscription.get('canceled_at'):
                lounge_sub.canceled_at = datetime.fromtimestamp(subscription['canceled_at'])

            db.commit()

            logger.info(f"Updated lounge subscription {lounge_sub.id} from {old_status} to {new_status}")

            # If subscription was canceled, remove membership
            if new_status == SubscriptionStatus.CANCELED and old_status != SubscriptionStatus.CANCELED:
                membership = db.query(LoungeMembership).filter(
                    LoungeMembership.user_id == lounge_sub.user_id,
                    LoungeMembership.lounge_id == lounge_sub.lounge_id,
                    LoungeMembership.left_at.is_(None)
                ).first()

                if membership:
                    membership.left_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Removed user {lounge_sub.user_id} from lounge {lounge_sub.lounge_id} due to canceled subscription")

        except Exception as e:
            logger.error(f"Error handling lounge subscription update: {str(e)}")
            raise

    async def cancel_lounge_subscription(
        self,
        user_id: int,
        lounge_id: int,
        db: Session,
        immediate: bool = False
    ) -> LoungeSubscription:
        """
        Cancel user's lounge subscription

        Args:
            user_id: User ID
            lounge_id: Lounge ID
            db: Database session
            immediate: Cancel immediately vs at period end

        Returns:
            Updated lounge subscription

        Raises:
            ValueError: If no active subscription found
        """
        # Find active subscription
        subscription = db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id,
            LoungeSubscription.lounge_id == lounge_id,
            LoungeSubscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()

        if not subscription:
            raise ValueError("No active subscription found for this lounge")

        try:
            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=not immediate
                )

                if immediate:
                    stripe.Subscription.cancel(subscription.stripe_subscription_id)

            # Update database
            if immediate:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.utcnow()

                # Remove membership immediately
                membership = db.query(LoungeMembership).filter(
                    LoungeMembership.user_id == user_id,
                    LoungeMembership.lounge_id == lounge_id,
                    LoungeMembership.left_at.is_(None)
                ).first()

                if membership:
                    membership.left_at = datetime.utcnow()
            else:
                # Will cancel at period end
                subscription.canceled_at = subscription.renews_at

            db.commit()
            db.refresh(subscription)

            logger.info(f"Canceled lounge subscription {subscription.id} (immediate={immediate})")

            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling lounge subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")

    async def get_user_lounge_subscription(
        self,
        user_id: int,
        lounge_id: int,
        db: Session
    ) -> Optional[LoungeSubscription]:
        """
        Get user's active subscription to a specific lounge

        Args:
            user_id: User ID
            lounge_id: Lounge ID
            db: Database session

        Returns:
            LoungeSubscription or None
        """
        return db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id,
            LoungeSubscription.lounge_id == lounge_id,
            LoungeSubscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()

    async def get_user_lounge_subscriptions(
        self,
        user_id: int,
        db: Session,
        include_canceled: bool = False
    ) -> List[LoungeSubscription]:
        """
        Get all user's lounge subscriptions

        Args:
            user_id: User ID
            db: Database session
            include_canceled: Include canceled subscriptions

        Returns:
            List of LoungeSubscription
        """
        query = db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id
        )

        if not include_canceled:
            query = query.filter(
                LoungeSubscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING
                ])
            )

        return query.all()

    async def upgrade_lounge_subscription(
        self,
        user_id: int,
        lounge_id: int,
        db: Session,
        prorate: bool = True
    ) -> LoungeSubscription:
        """
        Upgrade lounge subscription from monthly to yearly

        Args:
            user_id: User ID
            lounge_id: Lounge ID
            db: Database session
            prorate: Whether to prorate (charge difference immediately)

        Returns:
            Updated lounge subscription

        Raises:
            ValueError: If no active subscription, not monthly, or lounge not configured
        """
        # Find active subscription
        subscription = db.query(LoungeSubscription).filter(
            LoungeSubscription.user_id == user_id,
            LoungeSubscription.lounge_id == lounge_id,
            LoungeSubscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()

        if not subscription:
            raise ValueError("No active subscription found for this lounge")

        # Check if already yearly
        if subscription.plan_type == LoungePlanType.YEARLY:
            raise ValueError("Subscription is already on yearly plan. Cannot downgrade to monthly.")

        # Get lounge for yearly price ID
        lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
        if not lounge:
            raise ValueError("Lounge not found")

        if not lounge.stripe_yearly_price_id:
            raise ValueError("Lounge does not have yearly price configured")

        try:
            # Get current Stripe subscription to find the subscription item ID
            logger.info(f"Retrieving Stripe subscription: {subscription.stripe_subscription_id}")
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            subscription_item_id = stripe_sub['items']['data'][0]['id']
            current_price_id = stripe_sub['items']['data'][0]['price']['id']
            logger.info(f"Current Stripe subscription item: {subscription_item_id}, current_price: {current_price_id}")

            # Update subscription in Stripe to yearly price
            logger.info(f"Modifying Stripe subscription to yearly price: {lounge.stripe_yearly_price_id}")
            updated_stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': lounge.stripe_yearly_price_id,
                }],
                proration_behavior='create_prorations' if prorate else 'none',
                metadata={
                    'upgraded_from': 'monthly',
                    'upgraded_at': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Stripe subscription modified successfully. New status: {updated_stripe_sub.get('status')}")

            # Update local subscription record
            subscription.plan_type = LoungePlanType.YEARLY
            subscription.stripe_price_id = lounge.stripe_yearly_price_id

            # Update renewal date from Stripe response
            current_period_end = None
            if hasattr(updated_stripe_sub, 'current_period') and updated_stripe_sub.current_period:
                current_period_end = updated_stripe_sub.current_period.get('end')
            if not current_period_end:
                current_period_end = updated_stripe_sub.get('current_period_end')

            if current_period_end:
                subscription.renews_at = datetime.fromtimestamp(current_period_end)

            db.commit()
            db.refresh(subscription)

            logger.info(f"Upgraded lounge subscription {subscription.id} from monthly to yearly (prorate={prorate})")

            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error upgrading subscription: {str(e)}")
            raise Exception(f"Failed to upgrade subscription: {str(e)}")


# Singleton instance
billing_service = BillingService()
