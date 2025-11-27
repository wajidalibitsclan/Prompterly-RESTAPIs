"""
Notification, CMS, and compliance related models.
"""
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Enum, JSON, Boolean
)
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel."""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"


class NotificationStatus(str, enum.Enum):
    """Notification status."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(BaseModel):
    """User notifications."""
    
    __tablename__ = "notifications"
    
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional contextual data
    channel = Column(
        Enum(NotificationChannel),
        default=NotificationChannel.IN_APP,
        nullable=False
    )
    status = Column(
        Enum(NotificationStatus),
        default=NotificationStatus.QUEUED,
        nullable=False,
        index=True
    )
    priority = Column(Integer, default=0)  # Higher = more important
    
    # Action link
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Timestamps
    scheduled_for = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    @property
    def is_read(self) -> bool:
        """Check if notification is read."""
        return self.read_at is not None
    
    @property
    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self.sent_at is not None


class StaticPage(BaseModel):
    """Static CMS pages."""
    
    __tablename__ = "static_pages"
    
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    @property
    def is_live(self) -> bool:
        """Check if page is published."""
        return self.is_published


class FAQ(BaseModel):
    """Frequently Asked Questions."""
    
    __tablename__ = "faqs"
    
    category = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True, nullable=False)
    views_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)


class ComplianceRequestType(str, enum.Enum):
    """Type of compliance request."""
    EXPORT = "export"
    DELETE = "delete"


class ComplianceRequestStatus(str, enum.Enum):
    """Status of compliance request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ComplianceRequest(BaseModel):
    """GDPR/CCPA compliance requests."""
    
    __tablename__ = "compliance_requests"
    
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    request_type = Column(
        Enum(ComplianceRequestType),
        nullable=False,
        index=True
    )
    status = Column(
        Enum(ComplianceRequestStatus),
        default=ComplianceRequestStatus.PENDING,
        nullable=False,
        index=True
    )
    reason = Column(Text, nullable=True)
    
    # For export requests
    export_file_path = Column(String(500), nullable=True)
    download_url = Column(String(500), nullable=True)
    download_expires_at = Column(DateTime, nullable=True)
    
    # Processing info
    processed_at = Column(DateTime, nullable=True)
    processed_by_user_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    @property
    def is_export(self) -> bool:
        """Check if this is an export request."""
        return self.request_type == ComplianceRequestType.EXPORT
    
    @property
    def is_delete(self) -> bool:
        """Check if this is a deletion request."""
        return self.request_type == ComplianceRequestType.DELETE
    
    @property
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == ComplianceRequestStatus.COMPLETED


class AuditLog(BaseModel):
    """Audit log for tracking important actions."""
    
    __tablename__ = "audit_logs"
    
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after values
    metadata = Column(JSON, nullable=True)
    
    @property
    def has_changes(self) -> bool:
        """Check if there are tracked changes."""
        return self.changes is not None and len(self.changes) > 0


class SystemSetting(BaseModel):
    """System-wide settings."""
    
    __tablename__ = "system_settings"
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, int, bool, json
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  # Can be accessed by frontend
    
    def get_typed_value(self):
        """Get value with proper type casting."""
        if self.value is None:
            return None
        
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ["true", "1", "yes"]
        elif self.value_type == "json":
            import json
            return json.loads(self.value)
        return self.value
