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
