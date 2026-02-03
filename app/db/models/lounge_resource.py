"""
LoungeResource model - stores documents/resources for lounges
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.core.timezone import now_naive


class LoungeResource(Base):
    """LoungeResource model - documents uploaded by admin for lounges"""

    __tablename__ = "lounge_resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lounge_id = Column(Integer, ForeignKey("lounges.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(DateTime, default=now_naive, onupdate=now_naive, nullable=False)

    # Relationships
    lounge = relationship("Lounge", back_populates="resources")
    file = relationship("File", foreign_keys=[file_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])

    @property
    def file_url(self) -> str:
        """Get file URL from related file"""
        if self.file:
            return self.file.storage_path
        return None

    @property
    def file_type(self) -> str:
        """Get file MIME type"""
        if self.file:
            return self.file.mime_type
        return None

    @property
    def file_size(self) -> int:
        """Get file size in bytes"""
        if self.file:
            return self.file.size_bytes
        return 0

    def __repr__(self):
        return (
            f"<LoungeResource(id={self.id}, "
            f"lounge_id={self.lounge_id}, "
            f"title={self.title})>"
        )
