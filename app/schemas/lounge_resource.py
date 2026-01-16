"""
Pydantic schemas for lounge resources
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoungeResourceCreate(BaseModel):
    """Schema for creating lounge resource"""
    lounge_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class LoungeResourceUpdate(BaseModel):
    """Schema for updating lounge resource"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class LoungeResourceResponse(BaseModel):
    """Schema for lounge resource response"""
    id: int
    lounge_id: int
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: int = 0
    uploaded_by_user_id: int
    uploaded_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoungeResourceListResponse(BaseModel):
    """Schema for lounge resource list item"""
    id: int
    lounge_id: int
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size: int = 0
    file_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoungeResourcesListResponse(BaseModel):
    """Schema for paginated list of lounge resources"""
    resources: list[LoungeResourceListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
