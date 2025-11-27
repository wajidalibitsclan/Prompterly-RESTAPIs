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
