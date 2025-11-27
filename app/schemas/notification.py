"""
Pydantic schemas for notifications and CMS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int
    type: str
    data: Dict
    channel: str
    status: str
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
    
    # Computed
    is_read: bool = False
    is_sent: bool = False
    
    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    """Schema for creating notification"""
    type: str = Field(..., min_length=1, max_length=100)
    data: Dict = {}
    channel: str = "in_app"


class MarkAsReadRequest(BaseModel):
    """Schema for marking notifications as read"""
    notification_ids: List[int]


class StaticPageResponse(BaseModel):
    """Schema for static page response"""
    id: int
    slug: str
    title: str
    content: str
    is_published: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StaticPageCreate(BaseModel):
    """Schema for creating static page"""
    slug: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    is_published: bool = True
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class StaticPageUpdate(BaseModel):
    """Schema for updating static page"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    is_published: Optional[bool] = None


class FAQResponse(BaseModel):
    """Schema for FAQ response"""
    id: int
    category: str
    question: str
    answer: str
    sort_order: int
    
    class Config:
        from_attributes = True


class FAQCreate(BaseModel):
    """Schema for creating FAQ"""
    category: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=5000)
    sort_order: int = Field(0, ge=0)


class FAQUpdate(BaseModel):
    """Schema for updating FAQ"""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1, max_length=5000)
    sort_order: Optional[int] = Field(None, ge=0)


class NotificationPreferences(BaseModel):
    """Schema for notification preferences"""
    email_enabled: bool = True
    in_app_enabled: bool = True
    capsule_unlock: bool = True
    new_message: bool = True
    subscription_expiring: bool = True
    mentor_approved: bool = True
