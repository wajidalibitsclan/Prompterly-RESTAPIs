"""
Pydantic schemas for admin dashboard
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class UserManagementResponse(BaseModel):
    """Schema for user in admin panel"""
    id: int
    email: str
    name: str
    role: str
    avatar_url: Optional[str] = None
    email_verified_at: Optional[datetime]
    created_at: datetime

    # Stats
    lounge_count: int = 0
    note_count: int = 0
    subscription_status: Optional[str] = None

    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    """Schema for system statistics"""
    total_users: int
    total_mentors: int
    total_lounges: int
    total_subscriptions: int
    total_revenue_cents: int
    active_users_30d: int
    new_users_7d: int
    
    # Growth metrics
    user_growth_rate: float = 0.0
    revenue_growth_rate: float = 0.0


class PlatformHealthResponse(BaseModel):
    """Schema for platform health"""
    status: str
    uptime_seconds: int
    database_status: str
    redis_status: str
    s3_status: str
    api_response_time_ms: float
    
    # Resource usage
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None


class UserActivityResponse(BaseModel):
    """Schema for user activity"""
    user_id: int
    user_name: str
    user_email: str
    last_active: datetime
    total_messages: int
    total_notes: int
    total_lounges: int


class RevenueReportResponse(BaseModel):
    """Schema for revenue report"""
    period: str
    total_revenue_cents: int
    total_subscriptions: int
    new_subscriptions: int
    canceled_subscriptions: int
    avg_revenue_per_user_cents: int


class ContentModerationResponse(BaseModel):
    """Schema for content moderation"""
    id: int
    content_type: str  # note, message, lounge
    content_id: int
    user_id: int
    user_name: str
    content_preview: str
    flagged_at: datetime
    reason: Optional[str]
    status: str  # pending, approved, rejected


class UpdateUserRoleRequest(BaseModel):
    """Schema for updating user role"""
    role: str


class BanUserRequest(BaseModel):
    """Schema for banning user"""
    reason: str
    duration_days: Optional[int] = None


class PaginatedUsersResponse(BaseModel):
    """Paginated response for users list"""
    items: List[UserManagementResponse]
    total: int
    page: int
    limit: int
    pages: int


# =============================================================================
# User CRUD Schemas
# =============================================================================

class CreateUserRequest(BaseModel):
    """Schema for creating a new user"""
    email: str
    password: str
    name: str
    role: str = "member"
    email_verified: bool = False


class UpdateUserRequest(BaseModel):
    """Schema for updating a user"""
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    email_verified: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserDetailResponse(BaseModel):
    """Detailed user response for admin"""
    id: int
    email: str
    name: str
    role: str
    avatar_url: Optional[str]
    email_verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    lounge_count: int = 0
    note_count: int = 0
    subscription_status: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Mentor CRUD Schemas
# =============================================================================

class CreateMentorRequest(BaseModel):
    """Schema for creating a mentor profile"""
    user_id: int
    headline: Optional[str] = None
    bio: Optional[str] = None
    intro_video_url: Optional[str] = None
    experience_years: int = 0
    status: str = "pending"
    # Mentor profile fields for "More from Mentor" modal
    mentor_title: Optional[str] = None
    philosophy: Optional[str] = None
    hobbies: Optional[str] = None
    # Social links
    social_instagram: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_youtube: Optional[str] = None
    # Book recommendation
    book_title: Optional[str] = None
    book_description: Optional[str] = None
    # Podcast recommendation
    podcast_rec_title: Optional[str] = None
    # Podcast links
    podcast_name: Optional[str] = None
    podcast_youtube: Optional[str] = None
    podcast_spotify: Optional[str] = None
    podcast_apple: Optional[str] = None
    # Quick prompts
    quick_prompts: Optional[str] = None


class UpdateMentorRequest(BaseModel):
    """Schema for updating a mentor"""
    headline: Optional[str] = None
    bio: Optional[str] = None
    intro_video_url: Optional[str] = None
    experience_years: Optional[int] = None
    status: Optional[str] = None
    # Mentor profile fields for "More from Mentor" modal
    mentor_title: Optional[str] = None
    philosophy: Optional[str] = None
    hobbies: Optional[str] = None
    # Social links
    social_instagram: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_youtube: Optional[str] = None
    # Book recommendation
    book_title: Optional[str] = None
    book_description: Optional[str] = None
    # Podcast recommendation
    podcast_rec_title: Optional[str] = None
    # Podcast links
    podcast_name: Optional[str] = None
    podcast_youtube: Optional[str] = None
    podcast_spotify: Optional[str] = None
    podcast_apple: Optional[str] = None
    # Quick prompts
    quick_prompts: Optional[str] = None


class MentorDetailResponse(BaseModel):
    """Detailed mentor response for admin"""
    id: int
    user_id: int
    user_name: str
    user_email: str
    user_avatar: Optional[str]
    headline: Optional[str]
    bio: Optional[str]
    intro_video_url: Optional[str]
    experience_years: int
    status: str
    created_at: datetime
    updated_at: datetime
    lounge_count: int = 0
    # Mentor profile fields for "More from Mentor" modal
    mentor_title: Optional[str] = None
    philosophy: Optional[str] = None
    hobbies: Optional[str] = None
    # Social links
    social_instagram: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_youtube: Optional[str] = None
    # Book recommendation
    book_title: Optional[str] = None
    book_description: Optional[str] = None
    # Podcast recommendation
    podcast_rec_title: Optional[str] = None
    # Podcast links
    podcast_name: Optional[str] = None
    podcast_youtube: Optional[str] = None
    podcast_spotify: Optional[str] = None
    podcast_apple: Optional[str] = None
    # Quick prompts
    quick_prompts: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedMentorsResponse(BaseModel):
    """Paginated response for mentors list"""
    items: List[MentorDetailResponse]
    total: int
    page: int
    limit: int
    pages: int


# =============================================================================
# Subscription Management Schemas
# =============================================================================

class LoungeInfo(BaseModel):
    """Schema for lounge info in subscription context"""
    id: int
    title: str
    slug: str
    access_type: str
    mentor_name: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserSubscriptionResponse(BaseModel):
    """Schema for lounge subscription details"""
    subscription_id: int
    user_id: int
    user_name: str
    user_email: str
    user_avatar: Optional[str] = None
    # Plan info for frontend compatibility
    plan_name: str  # e.g. "Leadership Lounge - Monthly"
    plan_price_cents: int
    billing_interval: str  # 'month' or 'year'
    # Lounge details
    lounge_id: int
    lounge_title: str
    lounge_slug: str
    lounges: List[LoungeInfo] = []  # For frontend compatibility
    # Subscription details
    plan_type: str  # 'monthly' or 'yearly'
    status: str
    stripe_subscription_id: str
    started_at: datetime
    renews_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedSubscriptionsResponse(BaseModel):
    """Paginated response for subscriptions list"""
    items: List[UserSubscriptionResponse]
    total: int
    page: int
    limit: int
    pages: int


# =============================================================================
# Contact Message Management Schemas
# =============================================================================

class ContactMessageResponse(BaseModel):
    """Schema for contact message in admin panel"""
    id: int
    name: str
    email: str
    subject: str
    message: str
    status: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedContactMessagesResponse(BaseModel):
    """Paginated response for contact messages list"""
    items: List[ContactMessageResponse]
    total: int
    page: int
    limit: int
    pages: int


class UpdateContactMessageStatusRequest(BaseModel):
    """Request to update contact message status"""
    status: str  # 'new', 'read', 'replied', 'archived'
