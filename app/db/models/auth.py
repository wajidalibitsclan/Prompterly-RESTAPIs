"""
OAuth and Session models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from enum import Enum
from app.db.session import Base
from app.core.timezone import now_naive


class OAuthProvider(str, Enum):
    """OAuth provider enumeration"""
    GOOGLE = "google"


class OAuthAccount(Base):
    """OAuth account model for social authentication"""
    
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(SQLEnum(OAuthProvider, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(
        DateTime,
        default=now_naive,
        onupdate=now_naive,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    def __repr__(self):
        return f"<OAuthAccount(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class UserSession(Base):
    """User session model for tracking active sessions"""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now_naive, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        if self.revoked_at:
            return False
        return now_naive() < self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class EmailOTP(Base):
    """Email OTP model for verification codes"""

    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    purpose = Column(String(50), nullable=False, default="registration")  # registration, password_reset, etc.
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now_naive, nullable=False)

    @property
    def is_valid(self) -> bool:
        """Check if OTP is still valid"""
        if self.verified_at:
            return False
        return now_naive() < self.expires_at

    def __repr__(self):
        return f"<EmailOTP(id={self.id}, email={self.email}, valid={self.is_valid})>"
