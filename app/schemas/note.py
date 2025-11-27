"""
Pydantic schemas for notes and time capsules
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class NoteCreate(BaseModel):
    """Schema for creating note"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=50000)
    is_pinned: bool = False
    is_included_in_rag: bool = True
    tags: List[str] = []
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]


class NoteUpdate(BaseModel):
    """Schema for updating note"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    is_pinned: Optional[bool] = None
    is_included_in_rag: Optional[bool] = None
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Schema for note response"""
    id: int
    user_id: int
    title: str
    content: str
    is_pinned: bool
    is_included_in_rag: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    word_count: int = 0
    
    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for note list item"""
    id: int
    user_id: int
    title: str
    is_pinned: bool
    is_included_in_rag: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    # Preview
    content_preview: str = ""
    word_count: int = 0
    
    class Config:
        from_attributes = True


class TimeCapsuleCreate(BaseModel):
    """Schema for creating time capsule"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    unlock_at: datetime
    
    @validator('unlock_at')
    def validate_unlock_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Unlock date must be in the future')
        return v


class TimeCapsuleUpdate(BaseModel):
    """Schema for updating time capsule"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    unlock_at: Optional[datetime] = None


class TimeCapsuleResponse(BaseModel):
    """Schema for time capsule response"""
    id: int
    user_id: int
    title: str
    content: Optional[str]  # Only shown if unlocked
    unlock_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_unlocked: bool = False
    days_until_unlock: Optional[int] = None
    can_view_content: bool = False
    
    class Config:
        from_attributes = True


class NoteSearchRequest(BaseModel):
    """Schema for note search"""
    query: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None
    include_content: bool = True
    limit: int = Field(20, ge=1, le=100)
