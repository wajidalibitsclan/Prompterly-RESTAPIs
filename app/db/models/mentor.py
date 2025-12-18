"""
Mentor and Category models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.session import Base
from sqlalchemy import DateTime


class MentorStatus(str, Enum):
    """Mentor status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    DISABLED = "disabled"


class Mentor(Base):
    """Mentor model - extends user with mentor-specific information"""
    
    __tablename__ = "mentors"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    headline = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    intro_video_url = Column(String(500), nullable=True)
    experience_years = Column(Integer, default=0)
    status = Column(
        SQLEnum(MentorStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=MentorStatus.PENDING,
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
    user = relationship("User", back_populates="mentor_profile")
    lounges = relationship(
        "Lounge",
        back_populates="mentor",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_active(self) -> bool:
        """Check if mentor is active"""
        return self.status == MentorStatus.APPROVED
    
    def __repr__(self):
        return f"<Mentor(id={self.id}, user_id={self.user_id}, status={self.status})>"


class Category(Base):
    """Category model for organizing lounges"""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Relationships
    lounges = relationship("Lounge", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"
