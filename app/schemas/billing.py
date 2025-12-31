"""
Pydantic schemas for billing and subscriptions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class SubscriptionPlanResponse(BaseModel):
    """Schema for subscription plan response"""
    id: int
    name: str
    slug: str
    stripe_price_id: Optional[str]
    price_cents: int
    billing_interval: str
    features: List[str]
    is_active: bool
    
    # Computed
    price_display: str = ""
    
    class Config:
        from_attributes = True


class CheckoutSessionCreate(BaseModel):
    """Schema for creating checkout session"""
    plan_id: int
    lounge_id: Optional[int] = None
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Schema for checkout session response"""
    session_id: str
    checkout_url: str
    expires_at: datetime


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: int
    user_id: int
    plan_id: int
    stripe_subscription_id: Optional[str]
    status: str
    started_at: datetime
    renews_at: Optional[datetime]
    canceled_at: Optional[datetime]
    
    # Plan details
    plan_name: str
    plan_price_cents: int
    billing_interval: str
    
    # Computed
    is_active: bool = False
    days_until_renewal: Optional[int] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    user_id: int
    provider: str
    provider_payment_id: str
    amount_cents: int
    currency: str
    status: str
    created_at: datetime
    
    # Computed
    amount_display: str = ""
    
    class Config:
        from_attributes = True


class PortalSessionResponse(BaseModel):
    """Schema for billing portal session"""
    url: str


class WebhookEvent(BaseModel):
    """Schema for Stripe webhook event"""
    type: str
    data: Dict


class CancelSubscriptionRequest(BaseModel):
    """Schema for canceling subscription"""
    reason: Optional[str] = None
    feedback: Optional[str] = None


class UpdatePaymentMethodResponse(BaseModel):
    """Schema for payment method update"""
    setup_url: str


class LoungeCheckoutCreate(BaseModel):
    """Schema for creating lounge checkout session"""
    lounge_id: int
    plan_type: str = Field(..., pattern="^(monthly|yearly)$")  # 'monthly' or 'yearly'
    success_url: str
    cancel_url: str


class LoungeSubscriptionResponse(BaseModel):
    """Schema for lounge subscription response"""
    id: int
    user_id: int
    lounge_id: int
    plan_type: str  # 'monthly' or 'yearly'
    stripe_subscription_id: str
    stripe_price_id: str
    status: str
    started_at: datetime
    renews_at: Optional[datetime]
    canceled_at: Optional[datetime]

    # Lounge details
    lounge_title: str
    lounge_slug: str

    # Computed
    is_active: bool = False
    days_until_renewal: Optional[int] = None

    class Config:
        from_attributes = True


class CancelLoungeSubscriptionRequest(BaseModel):
    """Schema for canceling lounge subscription"""
    immediate: bool = False
    reason: Optional[str] = None
    feedback: Optional[str] = None


class LoungePricing(BaseModel):
    """Schema for lounge pricing information"""
    monthly_price_cents: int = 2500   # $25
    yearly_price_cents: int = 24000   # $240
    monthly_price_display: str = "$25/month"
    yearly_price_display: str = "$240/year"
    yearly_savings_percent: int = 20
