"""
Pydantic schemas for lounge management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.db.models.lounge import AccessType, MembershipRole


class LoungeCreate(BaseModel):
    """Schema for creating lounge"""
    title: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    category_id: int
    access_type: AccessType = AccessType.FREE
    plan_id: Optional[int] = None
    max_members: Optional[int] = Field(None, ge=1, le=10000)
    is_public_listing: bool = True
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('plan_id')
    def validate_plan(cls, v, values):
        if values.get('access_type') == AccessType.PAID and not v:
            raise ValueError('plan_id is required for paid lounges')
        return v


class LoungeUpdate(BaseModel):
    """Schema for updating lounge"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    access_type: Optional[AccessType] = None
    plan_id: Optional[int] = None
    max_members: Optional[int] = Field(None, ge=1, le=10000)
    is_public_listing: Optional[bool] = None


class LoungeResponse(BaseModel):
    """Schema for lounge response"""
    id: int
    mentor_id: int
    title: str
    slug: str
    description: Optional[str]
    category_id: int
    access_type: AccessType
    plan_id: Optional[int]
    max_members: Optional[int]
    is_public_listing: bool
    created_at: datetime
    
    # Nested data
    mentor_name: Optional[str]
    mentor_avatar: Optional[str]
    category_name: Optional[str]
    
    # Stats
    member_count: int = 0
    is_full: bool = False
    is_member: bool = False
    
    class Config:
        from_attributes = True


class LoungeListResponse(BaseModel):
    """Schema for lounge list item"""
    id: int
    mentor_id: int
    title: str
    slug: str
    description: Optional[str]
    category_id: int
    access_type: AccessType
    created_at: datetime
    
    mentor_name: Optional[str]
    mentor_avatar: Optional[str]
    category_name: Optional[str]
    member_count: int = 0
    is_full: bool = False
    
    class Config:
        from_attributes = True


class LoungeMemberResponse(BaseModel):
    """Schema for lounge member"""
    id: int
    lounge_id: int
    user_id: int
    role: MembershipRole
    joined_at: datetime
    left_at: Optional[datetime]
    
    # User info
    user_name: str
    user_avatar: Optional[str]
    user_email: Optional[str]
    
    class Config:
        from_attributes = True


class JoinLoungeRequest(BaseModel):
    """Schema for joining lounge"""
    pass  # Can be extended with invite codes, payment info, etc.


class UpdateMemberRole(BaseModel):
    """Schema for updating member role"""
    role: MembershipRole
