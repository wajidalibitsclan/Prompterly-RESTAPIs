"""
Notification, CMS, and Compliance models
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Enum as SQLEnum, Text, DateTime, Boolean, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base


class NotificationChannel(str, Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification status enumeration"""
    QUEUED = "queued"
    SENT = "sent"
    READ = "read"


class Notification(Base):
    """Notification model - user notifications"""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(100), nullable=False)  # e.g., "capsule_unlocked", "new_message"
    data = Column(JSON, nullable=True)  # Additional notification data
    channel = Column(SQLEnum(NotificationChannel, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    status = Column(
        SQLEnum(NotificationStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=NotificationStatus.QUEUED,
        nullable=False
    )
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    @property
    def is_read(self) -> bool:
        """Check if notification is read"""
        return self.read_at is not None
    
    @property
    def is_sent(self) -> bool:
        """Check if notification is sent"""
        return self.sent_at is not None
    
    def __repr__(self):
        return (
            f"<Notification(id={self.id}, "
            f"user_id={self.user_id}, "
            f"type={self.type}, "
            f"status={self.status})>"
        )


class StaticPage(Base):
    """Static page model - CMS pages"""
    
    __tablename__ = "static_pages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return (
            f"<StaticPage(id={self.id}, "
            f"slug={self.slug}, "
            f"published={self.is_published})>"
        )


class FAQ(Base):
    """FAQ model - Frequently asked questions"""
    
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return (
            f"<FAQ(id={self.id}, "
            f"category={self.category}, "
            f"question={self.question[:50]})>"
        )


class RequestType(str, Enum):
    """Compliance request type enumeration"""
    EXPORT = "export"
    DELETE = "delete"


class RequestStatus(str, Enum):
    """Compliance request status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    REJECTED = "rejected"


class ComplianceRequest(Base):
    """Compliance request model - GDPR data requests"""
    
    __tablename__ = "compliance_requests"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(SQLEnum(RequestType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    status = Column(
        SQLEnum(RequestStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=RequestStatus.PENDING,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="compliance_requests")
    
    @property
    def is_complete(self) -> bool:
        """Check if request is complete"""
        return self.status in [RequestStatus.DONE, RequestStatus.REJECTED]
    
    def __repr__(self):
        return (
            f"<ComplianceRequest(id={self.id}, "
            f"user_id={self.user_id}, "
            f"type={self.request_type}, "
            f"status={self.status})>"
        )
