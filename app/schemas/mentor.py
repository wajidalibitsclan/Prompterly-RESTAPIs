"""
Pydantic schemas for mentor management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.db.models.mentor import MentorStatus


class MentorApplication(BaseModel):
    """Schema for mentor application"""
    headline: str = Field(..., min_length=10, max_length=255)
    bio: str = Field(..., min_length=50, max_length=5000)
    intro_video_url: Optional[str] = None
    experience_years: int = Field(..., ge=0, le=100)
    
    @validator('intro_video_url')
    def validate_video_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Video URL must be a valid HTTP(S) URL')
        return v


class MentorUpdate(BaseModel):
    """Schema for updating mentor profile"""
    headline: Optional[str] = Field(None, min_length=10, max_length=255)
    bio: Optional[str] = Field(None, min_length=50, max_length=5000)
    intro_video_url: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=100)


class MentorResponse(BaseModel):
    """Schema for mentor response"""
    id: int
    user_id: int
    headline: Optional[str]
    bio: Optional[str]
    intro_video_url: Optional[str]
    experience_years: int
    status: MentorStatus
    created_at: datetime
    updated_at: datetime
    
    # Nested user info
    user_name: Optional[str]
    user_email: Optional[str]
    user_avatar: Optional[str]
    
    # Stats
    total_lounges: int = 0
    total_members: int = 0
    
    class Config:
        from_attributes = True


class MentorListResponse(BaseModel):
    """Schema for mentor list item"""
    id: int
    user_id: int
    headline: Optional[str]
    experience_years: int
    status: MentorStatus
    user_name: Optional[str]
    user_avatar: Optional[str]
    total_lounges: int = 0
    
    class Config:
        from_attributes = True


class MentorApproval(BaseModel):
    """Schema for mentor approval/rejection"""
    approved: bool
    feedback: Optional[str] = None


class CategoryResponse(BaseModel):
    """Schema for category response"""
    id: int
    name: str
    slug: str
    
    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    """Schema for creating category"""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)

    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class CategoryUpdate(BaseModel):
    """Schema for updating category"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=255)

    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, hyphens, and underscores')
        return v.lower() if v else v
