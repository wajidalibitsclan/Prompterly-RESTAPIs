"""
Newsletter API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.core.timezone import now_naive
from app.db.models.newsletter import NewsletterSubscriber, SubscriberStatus

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


class NewsletterSubscribeRequest(BaseModel):
    """Newsletter subscription request"""
    email: EmailStr
    source: str = "footer"


class NewsletterSubscribeResponse(BaseModel):
    """Newsletter subscription response"""
    success: bool
    message: str


class UnsubscribeRequest(BaseModel):
    """Newsletter unsubscribe request"""
    email: EmailStr


@router.post("/subscribe", response_model=NewsletterSubscribeResponse)
async def subscribe_newsletter(
    request: Request,
    data: NewsletterSubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Subscribe to the newsletter

    - Public endpoint (no auth required)
    - Validates email format
    - Prevents duplicate subscriptions
    """
    # Check if already subscribed
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == data.email.lower()
    ).first()

    if existing:
        if existing.status == SubscriberStatus.ACTIVE:
            return NewsletterSubscribeResponse(
                success=True,
                message="You're already subscribed to our newsletter!"
            )
        else:
            # Resubscribe
            existing.status = SubscriberStatus.ACTIVE
            existing.unsubscribed_at = None
            existing.subscribed_at = now_naive()
            db.commit()
            return NewsletterSubscribeResponse(
                success=True,
                message="Welcome back! You've been resubscribed to our newsletter."
            )

    # Get client IP
    client_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Create new subscriber
    subscriber = NewsletterSubscriber(
        email=data.email.lower(),
        status=SubscriberStatus.ACTIVE,
        ip_address=client_ip,
        source=data.source
    )
    db.add(subscriber)
    db.commit()

    return NewsletterSubscribeResponse(
        success=True,
        message="Thank you for subscribing! You'll be the first to know about new features and updates."
    )


@router.post("/unsubscribe", response_model=NewsletterSubscribeResponse)
async def unsubscribe_newsletter(
    data: UnsubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from the newsletter

    - Public endpoint (no auth required)
    """
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == data.email.lower()
    ).first()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found in our newsletter list"
        )

    if subscriber.status == SubscriberStatus.UNSUBSCRIBED:
        return NewsletterSubscribeResponse(
            success=True,
            message="You've already been unsubscribed from our newsletter."
        )

    subscriber.status = SubscriberStatus.UNSUBSCRIBED
    subscriber.unsubscribed_at = now_naive()
    db.commit()

    return NewsletterSubscribeResponse(
        success=True,
        message="You've been successfully unsubscribed from our newsletter."
    )
