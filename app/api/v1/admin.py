"""
Admin API endpoints
Handles admin dashboard, user management, and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import psutil
import time

from app.db.session import get_db
from app.core.jwt import get_current_admin
from app.db.models.user import User, UserRole
from app.db.models.mentor import Mentor
from app.db.models.lounge import Lounge, LoungeMembership
from app.db.models.billing import Subscription, Payment, SubscriptionStatus
from app.db.models.note import Note
from app.db.models.chat import ChatMessage
from app.schemas.admin import (
    UserManagementResponse,
    SystemStatsResponse,
    PlatformHealthResponse,
    UserActivityResponse,
    RevenueReportResponse,
    UpdateUserRoleRequest
)

router = APIRouter()

# Track app start time for uptime
app_start_time = time.time()


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get system statistics
    
    - Requires admin role
    - Returns platform-wide metrics
    """
    # Total counts
    total_users = db.query(func.count(User.id)).scalar()
    
    total_mentors = db.query(func.count(Mentor.id)).scalar()
    
    total_lounges = db.query(func.count(Lounge.id)).scalar()
    
    total_subscriptions = db.query(func.count(Subscription.id)).filter(
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    ).scalar()
    
    # Revenue
    total_revenue = db.query(func.sum(Payment.amount_cents)).filter(
        Payment.status == 'succeeded'
    ).scalar() or 0
    
    # Active users (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(func.distinct(ChatMessage.user_id))).filter(
        ChatMessage.created_at >= thirty_days_ago
    ).scalar()
    
    # New users (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users = db.query(func.count(User.id)).filter(
        User.created_at >= seven_days_ago
    ).scalar()
    
    # Growth rates (simplified)
    user_growth_rate = 0.0
    revenue_growth_rate = 0.0
    
    return SystemStatsResponse(
        total_users=total_users,
        total_mentors=total_mentors,
        total_lounges=total_lounges,
        total_subscriptions=total_subscriptions,
        total_revenue_cents=total_revenue,
        active_users_30d=active_users,
        new_users_7d=new_users,
        user_growth_rate=user_growth_rate,
        revenue_growth_rate=revenue_growth_rate
    )


@router.get("/health", response_model=PlatformHealthResponse)
async def get_platform_health(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get platform health
    
    - Requires admin role
    - Returns system health metrics
    """
    # Calculate uptime
    uptime = int(time.time() - app_start_time)
    
    # Check database
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    # System resources
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # API response time (simplified)
    api_response_time = 50.0  # ms
    
    return PlatformHealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        uptime_seconds=uptime,
        database_status=db_status,
        redis_status="unknown",  # Would check Redis if configured
        s3_status="unknown",  # Would check S3 if configured
        api_response_time_ms=api_response_time,
        cpu_usage_percent=cpu_usage,
        memory_usage_percent=memory_usage
    )


@router.get("/users", response_model=List[UserManagementResponse])
async def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List users for management
    
    - Requires admin role
    - Supports filtering and search
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.name.ilike(search_term))
        )
    
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Get stats
        lounge_count = db.query(func.count(LoungeMembership.id)).filter(
            LoungeMembership.user_id == user.id,
            LoungeMembership.left_at.is_(None)
        ).scalar()
        
        note_count = db.query(func.count(Note.id)).filter(
            Note.user_id == user.id
        ).scalar()
        
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        ).first()
        
        result.append(UserManagementResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            lounge_count=lounge_count,
            note_count=note_count,
            subscription_status=subscription.status.value if subscription else None
        ))
    
    return result


@router.put("/users/{user_id}/role", response_model=UserManagementResponse)
async def update_user_role(
    user_id: int,
    role_update: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update user role
    
    - Requires admin role
    - Changes user's role
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate role
    try:
        new_role = UserRole(role_update.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_update.role}"
        )
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    return UserManagementResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        email_verified_at=user.email_verified_at,
        created_at=user.created_at,
        lounge_count=0,
        note_count=0
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete user (admin)
    
    - Requires admin role
    - Permanently deletes user and data
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return None


@router.get("/activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    days: int = Query(30, ge=1, le=90)
):
    """
    Get user activity report
    
    - Requires admin role
    - Shows most active users
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get users with recent activity
    active_users = db.query(
        User.id,
        User.name,
        User.email,
        func.max(ChatMessage.created_at).label('last_active')
    ).join(
        ChatMessage,
        User.id == ChatMessage.user_id
    ).filter(
        ChatMessage.created_at >= since_date
    ).group_by(
        User.id
    ).order_by(
        func.max(ChatMessage.created_at).desc()
    ).limit(50).all()
    
    result = []
    for user_id, name, email, last_active in active_users:
        # Get stats
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.created_at >= since_date
        ).scalar()
        
        note_count = db.query(func.count(Note.id)).filter(
            Note.user_id == user_id,
            Note.created_at >= since_date
        ).scalar()
        
        lounge_count = db.query(func.count(LoungeMembership.id)).filter(
            LoungeMembership.user_id == user_id,
            LoungeMembership.joined_at >= since_date
        ).scalar()
        
        result.append(UserActivityResponse(
            user_id=user_id,
            user_name=name,
            user_email=email,
            last_active=last_active,
            total_messages=message_count,
            total_notes=note_count,
            total_lounges=lounge_count
        ))
    
    return result


@router.get("/revenue", response_model=List[RevenueReportResponse])
async def get_revenue_report(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    months: int = Query(6, ge=1, le=12)
):
    """
    Get revenue report
    
    - Requires admin role
    - Monthly revenue breakdown
    """
    result = []
    
    for i in range(months):
        # Calculate month start/end
        end_date = datetime.utcnow() - timedelta(days=i*30)
        start_date = end_date - timedelta(days=30)
        
        # Revenue
        revenue = db.query(func.sum(Payment.amount_cents)).filter(
            Payment.created_at >= start_date,
            Payment.created_at < end_date,
            Payment.status == 'succeeded'
        ).scalar() or 0
        
        # Subscriptions
        total_subs = db.query(func.count(Subscription.id)).filter(
            Subscription.started_at < end_date,
            (Subscription.canceled_at.is_(None)) | (Subscription.canceled_at >= end_date)
        ).scalar()
        
        new_subs = db.query(func.count(Subscription.id)).filter(
            Subscription.started_at >= start_date,
            Subscription.started_at < end_date
        ).scalar()
        
        canceled_subs = db.query(func.count(Subscription.id)).filter(
            Subscription.canceled_at >= start_date,
            Subscription.canceled_at < end_date
        ).scalar()
        
        # ARPU
        arpu = revenue // total_subs if total_subs > 0 else 0
        
        result.append(RevenueReportResponse(
            period=start_date.strftime("%Y-%m"),
            total_revenue_cents=revenue,
            total_subscriptions=total_subs,
            new_subscriptions=new_subs,
            canceled_subscriptions=canceled_subs,
            avg_revenue_per_user_cents=arpu
        ))
    
    return list(reversed(result))


@router.get("/mentors/pending")
async def get_pending_mentors(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get pending mentor applications
    
    - Requires admin role
    - Returns mentors awaiting approval
    """
    from app.db.models.mentor import MentorStatus
    
    mentors = db.query(Mentor).filter(
        Mentor.status == MentorStatus.PENDING
    ).order_by(Mentor.created_at.desc()).all()
    
    result = []
    for mentor in mentors:
        result.append({
            'id': mentor.id,
            'user_id': mentor.user_id,
            'user_name': mentor.user.name,
            'user_email': mentor.user.email,
            'headline': mentor.headline,
            'bio': mentor.bio,
            'experience_years': mentor.experience_years,
            'created_at': mentor.created_at
        })
    
    return result


@router.get("/export/users")
async def export_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Export user data (CSV format)
    
    - Requires admin role
    - Returns CSV download
    """
    users = db.query(User).all()
    
    # Build CSV
    csv_data = "id,email,name,role,created_at,email_verified\n"
    for user in users:
        csv_data += f"{user.id},{user.email},{user.name},{user.role.value},{user.created_at},{user.email_verified_at is not None}\n"
    
    return {
        "filename": f"users_export_{datetime.utcnow().strftime('%Y%m%d')}.csv",
        "data": csv_data
    }
