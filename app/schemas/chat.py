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
    """Schema for chat thread response — uses user_uuid for pseudonymisation"""
    id: int
    thread_uuid: str  # Non-enumerable external id. Use this in URLs.
    user_uuid: str  # Pseudonymous identifier (not user_id)
    lounge_id: Optional[int]
    title: Optional[str]
    status: ThreadStatus
    created_at: datetime

    # Stats
    message_count: int = 0
    last_message_at: Optional[datetime] = None

    # Lounge info if applicable
    lounge_title: Optional[str] = None

    # Tone mode for AI coaching replies on this thread ('motivational' |
    # 'analytical' | 'empathetic'). NULL means the user's account default.
    support_style: Optional[str] = None

    class Config:
        from_attributes = True


class SupportStyleUpdate(BaseModel):
    """Schema for changing the tone mode of a single thread or user preference."""
    support_style: Optional[str] = Field(
        None,
        description="Tone slug ('motivational' | 'analytical' | 'empathetic'). "
                    "Null clears any override and falls back to the account default.",
    )


class SupportStyleOption(BaseModel):
    """Single option in the catalogue served by GET /support-styles."""
    slug: str
    name: str
    description: str


class SupportStyleCatalogueResponse(BaseModel):
    """Response for GET /support-styles — the full catalogue + default slug."""
    default: str
    styles: List[SupportStyleOption]


class MessageCreate(BaseModel):
    """Schema for creating message"""
    content: str = Field(..., min_length=1, max_length=10000)
    attachment_ids: List[int] = []
    reply_to_id: Optional[int] = None  # ID of message being replied to


class MessageUpdate(BaseModel):
    """Schema for updating/editing a message"""
    content: str = Field(..., min_length=1, max_length=10000)


class ReplyToInfo(BaseModel):
    """Schema for reply-to message info"""
    id: int
    content: str  # Truncated content for display
    sender_name: Optional[str] = None
    sender_type: SenderType


class MessageResponse(BaseModel):
    """Schema for message response — uses user_uuid for pseudonymisation"""
    id: int
    thread_id: int
    sender_type: SenderType
    user_uuid: Optional[str] = None  # Pseudonymous identifier
    content: str
    metadata: Optional[dict]
    created_at: datetime
    edited_at: Optional[datetime] = None

    # Sender info
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None

    # Reply info
    reply_to_id: Optional[int] = None
    reply_to: Optional[ReplyToInfo] = None

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


class ThreadSearchRequest(BaseModel):
    """Schema for searching within a single chat thread."""
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(50, ge=1, le=200)


class ThreadSearchHit(BaseModel):
    """
    A single match inside a chat thread. Only a short snippet of plaintext
    is returned — clients fetch the full message via the normal thread
    history endpoint when the user clicks the hit.
    """
    message_id: int
    thread_id: int
    sender_type: SenderType
    created_at: datetime
    snippet: str


class ThreadSearchResponse(BaseModel):
    """Schema for thread-level search response."""
    thread_id: int
    query: str
    total_matches: int
    hits: List[ThreadSearchHit]
