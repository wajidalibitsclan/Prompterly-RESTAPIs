"""
File and MessageAttachment models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class File(Base):
    """File model - stores uploaded file metadata"""
    
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    storage_path = Column(String(500), nullable=False)  # S3 key or path
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship(
        "User",
        back_populates="files",
        foreign_keys=[owner_user_id]
    )
    message_attachments = relationship(
        "MessageAttachment",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image"""
        return self.mime_type.startswith("image/")
    
    @property
    def is_video(self) -> bool:
        """Check if file is a video"""
        return self.mime_type.startswith("video/")
    
    @property
    def is_audio(self) -> bool:
        """Check if file is audio"""
        return self.mime_type.startswith("audio/")
    
    @property
    def is_document(self) -> bool:
        """Check if file is a document"""
        doc_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]
        return self.mime_type in doc_types
    
    def __repr__(self):
        return (
            f"<File(id={self.id}, "
            f"owner_id={self.owner_user_id}, "
            f"mime_type={self.mime_type})>"
        )


class MessageAttachment(Base):
    """MessageAttachment model - links files to messages"""
    
    __tablename__ = "message_attachments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")
    file = relationship("File", back_populates="message_attachments")
    
    def __repr__(self):
        return (
            f"<MessageAttachment(id={self.id}, "
            f"message_id={self.message_id}, "
            f"file_id={self.file_id})>"
        )
