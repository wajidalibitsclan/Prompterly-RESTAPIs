"""
User model - Core user entity
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.session import Base


class UserRole(str, Enum):
    """User role enumeration"""
    MEMBER = "member"
    MENTOR = "mentor"
    ADMIN = "admin"


class User(Base):
    """User model representing platform users"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.MEMBER,
        nullable=False
    )
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    oauth_accounts = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    mentor_profile = relationship(
        "Mentor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    lounge_memberships = relationship(
        "LoungeMembership",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    chat_threads = relationship(
        "ChatThread",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    files = relationship(
        "File",
        back_populates="owner",
        foreign_keys="File.owner_user_id",
        cascade="all, delete-orphan"
    )
    notes = relationship(
        "Note",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    time_capsules = relationship(
        "TimeCapsule",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    compliance_requests = relationship(
        "ComplianceRequest",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active (has verified email)"""
        return self.email_verified_at is not None

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    @property
    def is_mentor(self) -> bool:
        """Check if user has mentor role"""
        return self.role == UserRole.MENTOR

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
