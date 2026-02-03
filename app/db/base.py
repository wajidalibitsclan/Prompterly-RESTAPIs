"""
Base database model with common fields and utilities
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app.db.session import Base
from app.core.timezone import now_naive


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""

    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(
        DateTime,
        default=now_naive,
        onupdate=now_naive,
        nullable=False
    )


class BaseModel(Base):
    """Base model with common functionality"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name"""
        return cls.__name__.lower() + "s"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
