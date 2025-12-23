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
    Payment,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus
)
from app.db.models.user import User
from app.db.models.lounge import LoungeMembership, MembershipRole

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
            
            new_status = status_map.get(subscription['status'], SubscriptionStatus.CANCELED)
            sub.status = new_status
            
            # Update renewal date
            if subscription.get('current_period_end'):
                sub.renews_at = datetime.fromtimestamp(subscription['current_period_end'])
            
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


# Singleton instance
billing_service = BillingService()
