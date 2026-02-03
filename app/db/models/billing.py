"""
Subscription and Payment models
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Enum as SQLEnum, DateTime, Boolean, JSON
)
from sqlalchemy.orm import relationship
from enum import Enum
from app.db.session import Base
from app.core.timezone import now_naive


class BillingInterval(str, Enum):
    """Billing interval enumeration"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class LoungePlanType(str, Enum):
    """Lounge subscription plan type enumeration"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class PaymentProvider(str, Enum):
    """Payment provider enumeration"""
    STRIPE = "stripe"
    KLARNA = "klarna"
    AFTERPAY = "afterpay"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SubscriptionPlan(Base):
    """Subscription plan model - defines pricing tiers"""
    
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    price_cents = Column(Integer, nullable=False)
    billing_interval = Column(SQLEnum(BillingInterval, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    features = Column(JSON, nullable=True)  # Array of feature strings
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
        cascade="all, delete-orphan"
    )
    lounges = relationship("Lounge", back_populates="plan")
    
    @property
    def price_dollars(self) -> float:
        """Get price in dollars"""
        return self.price_cents / 100
    
    @property
    def feature_list(self) -> list:
        """Get features as list"""
        return self.features if self.features else []
    
    def __repr__(self):
        return (
            f"<SubscriptionPlan(id={self.id}, "
            f"name={self.name}, "
            f"price=${self.price_dollars})>"
        )


class Subscription(Base):
    """Subscription model - user subscription to plans"""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    stripe_subscription_id = Column(String(255), nullable=False, unique=True)
    status = Column(
        SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=SubscriptionStatus.TRIALING,
        nullable=False
    )
    started_at = Column(DateTime, default=now_naive, nullable=False)
    renews_at = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.ACTIVE
        ]
    
    @property
    def days_until_renewal(self) -> int:
        """Get days until renewal"""
        if not self.is_active:
            return 0
        delta = self.renews_at - now_naive()
        return max(0, delta.days)
    
    def __repr__(self):
        return (
            f"<Subscription(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status})>"
        )


class Payment(Base):
    """Payment model - tracks payment transactions"""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(SQLEnum(PaymentProvider, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    provider_payment_id = Column(String(255), nullable=False, unique=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(
        SQLEnum(PaymentStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    created_at = Column(DateTime, default=now_naive, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    @property
    def amount_dollars(self) -> float:
        """Get amount in dollars"""
        return self.amount_cents / 100

    def __repr__(self):
        return (
            f"<Payment(id={self.id}, "
            f"user_id={self.user_id}, "
            f"amount=${self.amount_dollars}, "
            f"status={self.status})>"
        )


class LoungeSubscription(Base):
    """
    Lounge subscription model - tracks user subscriptions to specific lounges
    Separate from generic Subscription model for per-lounge billing
    Each lounge has its own Stripe Product with monthly/yearly prices
    """

    __tablename__ = "lounge_subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lounge_id = Column(Integer, ForeignKey("lounges.id"), nullable=False, index=True)
    plan_type = Column(
        SQLEnum(LoungePlanType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    stripe_subscription_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_price_id = Column(String(255), nullable=False)  # The actual Stripe price used
    status = Column(
        SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=SubscriptionStatus.ACTIVE,
        nullable=False
    )
    started_at = Column(DateTime, default=now_naive, nullable=False)
    renews_at = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="lounge_subscriptions")
    lounge = relationship("Lounge", back_populates="subscriptions")

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.ACTIVE
        ]

    @property
    def price_cents(self) -> int:
        """Get price in cents based on plan type"""
        if self.plan_type == LoungePlanType.MONTHLY:
            return 2500  # $25
        return 24000  # $240

    @property
    def days_until_renewal(self) -> int:
        """Get days until renewal"""
        if not self.is_active:
            return 0
        delta = self.renews_at - now_naive()
        return max(0, delta.days)

    def __repr__(self):
        return (
            f"<LoungeSubscription(id={self.id}, "
            f"user_id={self.user_id}, "
            f"lounge_id={self.lounge_id}, "
            f"plan_type={self.plan_type}, "
            f"status={self.status})>"
        )
