"""
Chat models - Thread and Message
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Enum as SQLEnum, Text, DateTime, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.session import Base


class ThreadStatus(str, Enum):
    """Chat thread status enumeration"""
    OPEN = "open"
    ARCHIVED = "archived"


class SenderType(str, Enum):
    """Message sender type enumeration"""
    USER = "user"
    AI = "ai"
    MENTOR = "mentor"


class ChatThread(Base):
    """Chat thread model - conversation container"""
    
    __tablename__ = "chat_threads"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lounge_id = Column(Integer, ForeignKey("lounges.id"), nullable=True)
    title = Column(String(255), nullable=True)
    status = Column(
        SQLEnum(ThreadStatus),
        default=ThreadStatus.OPEN,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_threads")
    lounge = relationship("Lounge", back_populates="chat_threads")
    messages = relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    @property
    def message_count(self) -> int:
        """Get count of messages in thread"""
        return len(self.messages)
    
    @property
    def last_message_at(self) -> datetime:
        """Get timestamp of last message"""
        if self.messages:
            return self.messages[-1].created_at
        return self.created_at
    
    def __repr__(self):
        return (
            f"<ChatThread(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status})>"
        )


class ChatMessage(Base):
    """Chat message model - individual messages in threads"""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    sender_type = Column(SQLEnum(SenderType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # For AI model info, tokens, etc. (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship("ChatThread", back_populates="messages")
    sender_user = relationship("User", foreign_keys=[user_id])
    attachments = relationship(
        "MessageAttachment",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    
    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments"""
        return len(self.attachments) > 0
    
    def __repr__(self):
        return (
            f"<ChatMessage(id={self.id}, "
            f"thread_id={self.thread_id}, "
            f"sender_type={self.sender_type})>"
        )
