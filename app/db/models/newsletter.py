"""
Newsletter subscription model
"""
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum

from app.db.session import Base
from app.core.timezone import now_naive


class SubscriberStatus(str, Enum):
    """Newsletter subscriber status"""
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"


class NewsletterSubscriber(Base):
    """Newsletter subscriber model"""

    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(SubscriberStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=SubscriberStatus.ACTIVE,
        nullable=False
    )
    subscribed_at = Column(DateTime, default=now_naive, nullable=False)
    unsubscribed_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    source = Column(String(100), default="footer", nullable=False)  # Where they signed up from

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"
