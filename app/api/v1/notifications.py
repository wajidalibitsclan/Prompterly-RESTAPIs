"""
Notifications API endpoints
Handles in-app notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.jwt import get_current_active_user
from app.db.models.user import User
from app.db.models.misc import Notification, NotificationStatus, NotificationChannel
from app.schemas.notification import (
    NotificationResponse,
    NotificationCreate,
    MarkAsReadRequest
)

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
    channel: Optional[str] = None
):
    """
    List user notifications
    
    - Returns notifications for current user
    - Filter by read status and channel
    - Paginated results
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    
    if channel:
        query = query.filter(Notification.channel == channel)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for notif in notifications:
        result.append(NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            type=notif.type,
            data=notif.data or {},
            channel=notif.channel.value,
            status=notif.status.value,
            sent_at=notif.sent_at,
            read_at=notif.read_at,
            created_at=notif.created_at,
            is_read=notif.read_at is not None,
            is_sent=notif.sent_at is not None
        ))
    
    return result


@router.get("/unread/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get unread notification count
    
    - Returns count of unread in-app notifications
    """
    count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.channel == NotificationChannel.IN_APP,
        Notification.read_at.is_(None)
    ).scalar()
    
    return {"unread_count": count}


@router.post("/mark-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    request: MarkAsReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark notifications as read
    
    - Marks specified notifications as read
    - Only user's own notifications
    """
    notifications = db.query(Notification).filter(
        Notification.id.in_(request.notification_ids),
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).all()
    
    now = datetime.utcnow()
    for notif in notifications:
        notif.read_at = now
        notif.status = NotificationStatus.READ
    
    db.commit()
    
    return None


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark all notifications as read
    
    - Marks all unread notifications as read
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).all()
    
    now = datetime.utcnow()
    for notif in notifications:
        notif.read_at = now
        notif.status = NotificationStatus.READ
    
    db.commit()
    
    return None


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete notification
    
    - Deletes notification permanently
    - Only user's own notifications
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return None


@router.post("/test", response_model=NotificationResponse)
async def create_test_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create test notification (development only)
    
    - Creates a test notification for current user
    - Useful for testing notification UI
    """
    notification = Notification(
        user_id=current_user.id,
        type=notification_data.type,
        data=notification_data.data,
        channel=NotificationChannel(notification_data.channel),
        status=NotificationStatus.SENT,
        sent_at=datetime.utcnow()
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        data=notification.data or {},
        channel=notification.channel.value,
        status=notification.status.value,
        sent_at=notification.sent_at,
        read_at=notification.read_at,
        created_at=notification.created_at,
        is_read=False,
        is_sent=True
    )
