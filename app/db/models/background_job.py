"""
Background Job model for tracking async tasks like embedding generation
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    Enum as SQLEnum, JSON
)
from datetime import datetime
from enum import Enum
from app.db.session import Base


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Job type enumeration"""
    PROMPT_EMBEDDING = "prompt_embedding"
    DOCUMENT_PROCESSING = "document_processing"
    FAQ_EMBEDDING = "faq_embedding"
    BULK_EMBEDDING = "bulk_embedding"


class BackgroundJob(Base):
    """Background job model for tracking async tasks"""

    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(
        SQLEnum(JobType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    status = Column(
        SQLEnum(JobStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=JobStatus.PENDING,
        nullable=False
    )

    # Reference to the entity being processed
    entity_type = Column(String(50), nullable=True)  # 'prompt', 'document', 'faq'
    entity_id = Column(Integer, nullable=True)

    # Progress tracking
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    current_step = Column(String(255), nullable=True)
    total_steps = Column(Integer, default=1, nullable=False)
    completed_steps = Column(Integer, default=0, nullable=False)

    # Results and errors
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # User who initiated the job
    created_by_id = Column(Integer, nullable=True)

    def update_progress(self, completed: int, total: int, current_step: str = None):
        """Update job progress"""
        self.completed_steps = completed
        self.total_steps = total
        self.progress = (completed / total * 100) if total > 0 else 0
        if current_step:
            self.current_step = current_step

    def mark_processing(self):
        """Mark job as processing"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: dict = None):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result

    def mark_failed(self, error: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "progress": round(self.progress, 1),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f"<BackgroundJob(id={self.id}, type={self.job_type}, status={self.status}, progress={self.progress}%)>"
