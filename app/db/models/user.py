"""
User model - Core user entity
"""
import uuid as uuid_lib
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum
from app.db.session import Base
from app.core.timezone import now_naive


class UserRole(str, Enum):
    """User role enumeration"""
    MEMBER = "member"
    MENTOR = "mentor"
    ADMIN = "admin"


class User(Base):
    """User model representing platform users"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_uuid = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)  # Stripe customer ID for billing
    role = Column(
        SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.MEMBER,
        nullable=False
    )
    email_verified_at = Column(DateTime, nullable=True)
    # 2FA / MFA
    totp_secret = Column(String(32), nullable=True)  # Base32 TOTP secret (totp method)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    # Which 2FA method the user picked: 'totp' or 'email'. NULL when 2FA is disabled.
    two_factor_method = Column(String(16), nullable=True)
    # Transient storage for emailed one-time codes (email method).
    # Code is stored hashed (SHA-256 hex) so the DB never holds plaintext OTPs.
    email_2fa_code_hash = Column(String(64), nullable=True)
    email_2fa_expires_at = Column(DateTime, nullable=True)
    email_2fa_purpose = Column(String(16), nullable=True)  # 'setup' or 'login'
    # Settings & Preferences
    language = Column(String(10), default="en", nullable=False)  # ISO 639-1
    timezone = Column(String(50), default="Australia/Sydney", nullable=False)  # IANA timezone
    # Tone mode for AI coaching replies ('motivational' | 'analytical' | 'empathetic').
    # NULL means "fall through to the global default". See app/core/support_style.py.
    support_style = Column(String(24), nullable=True)
    notify_email_enabled = Column(Boolean, default=True, nullable=False)
    notify_in_app_enabled = Column(Boolean, default=True, nullable=False)
    notify_capsule_unlock = Column(Boolean, default=True, nullable=False)
    notify_new_message = Column(Boolean, default=True, nullable=False)
    notify_subscription_updates = Column(Boolean, default=True, nullable=False)
    notify_mentor_approved = Column(Boolean, default=True, nullable=False)
    # Privacy / Legal
    privacy_accepted_at = Column(DateTime, nullable=True)
    tos_accepted_at = Column(DateTime, nullable=True)
    age_confirmed = Column(Boolean, default=False, nullable=False)  # 18+ confirmation
    # Account lifecycle
    account_paused_at = Column(DateTime, nullable=True)  # When account was paused (payment failure Day 7)
    data_deletion_scheduled_at = Column(DateTime, nullable=True)  # When data will be permanently deleted
    payment_failure_count = Column(Integer, default=0, nullable=False)  # Tracks retry attempts (0, 1, 2, 3)
    # Legal hold — prevents account/data deletion when active
    legal_hold = Column(Boolean, default=False, nullable=False)
    legal_hold_reason = Column(String(500), nullable=True)
    legal_hold_set_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(
        DateTime,
        default=now_naive,
        onupdate=now_naive,
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
    lounge_subscriptions = relationship(
        "LoungeSubscription",
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
