"""
Lounge and LoungeMembership models
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey, 
    Enum as SQLEnum, Text, Boolean, DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.session import Base


class AccessType(str, Enum):
    """Lounge access type enumeration"""
    FREE = "free"
    PAID = "paid"
    INVITE_ONLY = "invite_only"


class MembershipRole(str, Enum):
    """Lounge membership role enumeration"""
    MEMBER = "member"
    CO_MENTOR = "co_mentor"


class Lounge(Base):
    """Lounge model - coaching spaces created by mentors"""

    __tablename__ = "lounges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    access_type = Column(
        SQLEnum(AccessType, values_callable=lambda obj: [e.value for e in obj]),
        default=AccessType.FREE,
        nullable=False
    )
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    max_members = Column(Integer, nullable=True)
    is_public_listing = Column(Boolean, default=True, nullable=False)
    profile_image_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    mentor = relationship("Mentor", back_populates="lounges")
    category = relationship("Category", back_populates="lounges")
    plan = relationship("SubscriptionPlan", back_populates="lounges")
    profile_image = relationship("File", foreign_keys=[profile_image_id])
    memberships = relationship(
        "LoungeMembership",
        back_populates="lounge",
        cascade="all, delete-orphan"
    )
    chat_threads = relationship(
        "ChatThread",
        back_populates="lounge",
        cascade="all, delete-orphan"
    )
    
    @property
    def member_count(self) -> int:
        """Get count of active members"""
        return len([m for m in self.memberships if m.left_at is None])
    
    @property
    def is_full(self) -> bool:
        """Check if lounge has reached max capacity"""
        if self.max_members is None:
            return False
        return self.member_count >= self.max_members
    
    def __repr__(self):
        return f"<Lounge(id={self.id}, title={self.title}, mentor_id={self.mentor_id})>"


class LoungeMembership(Base):
    """Lounge membership model - tracks user participation in lounges"""
    
    __tablename__ = "lounge_memberships"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lounge_id = Column(Integer, ForeignKey("lounges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(
        SQLEnum(MembershipRole, values_callable=lambda obj: [e.value for e in obj]),
        default=MembershipRole.MEMBER,
        nullable=False
    )
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    left_at = Column(DateTime, nullable=True)
    
    # Relationships
    lounge = relationship("Lounge", back_populates="memberships")
    user = relationship("User", back_populates="lounge_memberships")
    
    @property
    def is_active(self) -> bool:
        """Check if membership is active"""
        return self.left_at is None
    
    def __repr__(self):
        return (
            f"<LoungeMembership(id={self.id}, "
            f"lounge_id={self.lounge_id}, "
            f"user_id={self.user_id}, "
            f"active={self.is_active})>"
        )
