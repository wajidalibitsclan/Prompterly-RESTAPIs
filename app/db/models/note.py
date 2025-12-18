"""
Note and TimeCapsule models
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Text, Boolean, DateTime, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.session import Base


class Note(Base):
    """Note model - user notes that can be used for RAG"""
    
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_included_in_rag = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, nullable=True)  # Array of tags
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="notes")
    
    @property
    def tag_list(self) -> list:
        """Get tags as list"""
        return self.tags if self.tags else []
    
    @property
    def word_count(self) -> int:
        """Get approximate word count"""
        return len(self.content.split())
    
    def __repr__(self):
        return (
            f"<Note(id={self.id}, "
            f"user_id={self.user_id}, "
            f"title={self.title[:30]})>"
        )


class CapsuleStatus(str, Enum):
    """Time capsule status enumeration"""
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    EXPIRED = "expired"


class TimeCapsule(Base):
    """Time capsule model - locked messages for future"""
    
    __tablename__ = "time_capsules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    unlock_at = Column(DateTime, nullable=False)
    status = Column(
        SQLEnum(CapsuleStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=CapsuleStatus.LOCKED,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="time_capsules")
    
    @property
    def is_unlockable(self) -> bool:
        """Check if capsule can be unlocked"""
        return (
            self.status == CapsuleStatus.LOCKED and
            datetime.utcnow() >= self.unlock_at
        )
    
    @property
    def days_until_unlock(self) -> int:
        """Get days until unlock"""
        if self.status != CapsuleStatus.LOCKED:
            return 0
        delta = self.unlock_at - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return (
            f"<TimeCapsule(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status={self.status})>"
        )
