"""
Pydantic schemas for chat system
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.db.models.chat import ThreadStatus, SenderType


class ChatThreadCreate(BaseModel):
    """Schema for creating chat thread"""
    lounge_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=255)


class ChatThreadUpdate(BaseModel):
    """Schema for updating chat thread"""
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[ThreadStatus] = None


class ChatThreadResponse(BaseModel):
    """Schema for chat thread response"""
    id: int
    user_id: int
    lounge_id: Optional[int]
    title: Optional[str]
    status: ThreadStatus
    created_at: datetime
    
    # Stats
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    
    # Lounge info if applicable
    lounge_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for creating message"""
    content: str = Field(..., min_length=1, max_length=10000)
    attachment_ids: List[int] = []


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    thread_id: int
    sender_type: SenderType
    user_id: Optional[int]
    content: str
    metadata: Optional[dict]
    created_at: datetime
    
    # Sender info
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    
    # Attachments
    has_attachments: bool = False
    attachment_count: int = 0
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    id: int
    storage_path: str
    mime_type: str
    size_bytes: int
    size_mb: float
    created_at: datetime
    
    # File type flags
    is_image: bool = False
    is_video: bool = False
    is_audio: bool = False
    is_document: bool = False
    
    class Config:
        from_attributes = True


class AIResponseRequest(BaseModel):
    """Schema for requesting AI response"""
    message: str = Field(..., min_length=1, max_length=10000)
    use_rag: bool = True
    use_anthropic: bool = False
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class ChatHistoryResponse(BaseModel):
    """Schema for chat history"""
    thread: ChatThreadResponse
    messages: List[MessageResponse]
    total_messages: int
