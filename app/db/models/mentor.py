"""
Mentor and Category models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import relationship
from enum import Enum
from app.db.session import Base
from app.core.timezone import now_naive


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
    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(
        DateTime,
        default=now_naive,
        onupdate=now_naive,
        nullable=False
    )

    # Mentor profile fields for "More from Mentor" modal
    mentor_title = Column(String(255), nullable=True)  # e.g., "Mindset mentor"
    philosophy = Column(Text, nullable=True)  # Mentor's philosophy/bio
    hobbies = Column(Text, nullable=True)  # JSON array of hobbies/interests

    # Social links
    social_instagram = Column(String(500), nullable=True)
    social_tiktok = Column(String(500), nullable=True)
    social_linkedin = Column(String(500), nullable=True)
    social_youtube = Column(String(500), nullable=True)

    # Book recommendation
    book_title = Column(String(500), nullable=True)
    book_description = Column(Text, nullable=True)

    # Podcast recommendation
    podcast_rec_title = Column(String(500), nullable=True)

    # Podcast links (More from me section)
    podcast_name = Column(String(255), nullable=True)
    podcast_youtube = Column(String(500), nullable=True)
    podcast_spotify = Column(String(500), nullable=True)
    podcast_apple = Column(String(500), nullable=True)

    # Quick prompts - JSON array of prompt strings
    quick_prompts = Column(Text, nullable=True)
    
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
