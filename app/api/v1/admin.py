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
from app.db.models.lounge import Lounge, LoungeMembership, AccessType
from app.db.models.mentor import Category
from app.db.models.billing import Subscription, Payment, SubscriptionStatus
from app.db.models.note import Note
from app.db.models.chat import ChatMessage
from app.schemas.admin import (
    UserManagementResponse,
    SystemStatsResponse,
    PlatformHealthResponse,
    UserActivityResponse,
    RevenueReportResponse,
    UpdateUserRoleRequest,
    PaginatedUsersResponse,
    CreateUserRequest,
    UpdateUserRequest,
    CreateMentorRequest,
    UpdateMentorRequest
)
from app.core.security import hash_password
from app.services.file_service import file_service

router = APIRouter()


async def get_lounge_profile_image_url(lounge: Lounge, db: Session):
    """Get the profile image URL for a lounge"""
    if lounge.profile_image_id:
        try:
            return await file_service.get_file_url(lounge.profile_image_id, db)
        except Exception:
            return None
    return None

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


@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List users for management

    - Requires admin role
    - Supports filtering and search
    - Returns paginated response
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.name.ilike(search_term))
        )

    # Get total count before pagination
    total = query.count()

    # Calculate offset from page
    skip = (page - 1) * limit

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    items = []
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

        items.append(UserManagementResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            avatar_url=user.avatar_url,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            lounge_count=lounge_count,
            note_count=note_count,
            subscription_status=subscription.status.value if subscription else None
        ))

    # Calculate total pages
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedUsersResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


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


@router.get("/mentors")
async def get_all_mentors(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get all mentors

    - Requires admin role
    - Returns all mentors
    """
    from app.db.models.mentor import MentorStatus

    mentors = db.query(Mentor).filter(
        Mentor.status == MentorStatus.APPROVED
    ).offset(skip).limit(limit).all()

    result = []
    for mentor in mentors:
        result.append({
            'id': mentor.id,
            'user_id': mentor.user_id,
            'user_name': mentor.user.name,
            'user_email': mentor.user.email,
            'headline': mentor.headline,
            'status': mentor.status.value
        })

    return result


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


# =============================================================================
# Admin Lounge Management
# =============================================================================

@router.get("/lounges")
async def get_admin_lounges(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all lounges for admin management

    - Requires admin role
    - Returns all lounges with stats
    """
    lounges = db.query(Lounge).offset(skip).limit(limit).all()

    result = []
    for lounge in lounges:
        member_count = db.query(func.count(LoungeMembership.id)).filter(
            LoungeMembership.lounge_id == lounge.id,
            LoungeMembership.left_at.is_(None)
        ).scalar()

        # Get profile image URL
        profile_image_url = await get_lounge_profile_image_url(lounge, db)

        result.append({
            "id": lounge.id,
            "title": lounge.title,
            "slug": lounge.slug,
            "description": lounge.description,
            "category_id": lounge.category_id,
            "category_name": lounge.category.name if lounge.category else None,
            "access_type": lounge.access_type.value,
            "max_members": lounge.max_members,
            "is_public_listing": lounge.is_public_listing,
            "mentor_id": lounge.mentor_id,
            "mentor_name": lounge.mentor.user.name if lounge.mentor else None,
            "profile_image_url": profile_image_url,
            "member_count": member_count,
            "is_full": lounge.is_full,
            "created_at": lounge.created_at
        })

    return result


@router.get("/lounges/{lounge_id}")
async def get_admin_lounge(
    lounge_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get single lounge details (admin only)
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge.id,
        LoungeMembership.left_at.is_(None)
    ).scalar()

    profile_image_url = await get_lounge_profile_image_url(lounge, db)

    return {
        "id": lounge.id,
        "title": lounge.title,
        "slug": lounge.slug,
        "description": lounge.description,
        "category_id": lounge.category_id,
        "category_name": lounge.category.name if lounge.category else None,
        "access_type": lounge.access_type.value,
        "max_members": lounge.max_members,
        "is_public_listing": lounge.is_public_listing,
        "mentor_id": lounge.mentor_id,
        "mentor_name": lounge.mentor.user.name if lounge.mentor else None,
        "profile_image_url": profile_image_url,
        "member_count": member_count,
        "is_full": lounge.is_full,
        "created_at": lounge.created_at
    }


@router.post("/lounges", status_code=status.HTTP_201_CREATED)
async def admin_create_lounge(
    title: str,
    slug: str,
    mentor_id: int,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    access_type: str = "free",
    max_members: Optional[int] = None,
    is_public_listing: bool = True,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create lounge as admin

    - Requires admin role
    - Can assign to any mentor
    """
    # Verify mentor exists
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )

    # Check slug uniqueness
    existing = db.query(Lounge).filter(Lounge.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lounge with this slug already exists"
        )

    # Verify category if provided
    if category_id:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Map access_type string to enum
    access_type_enum = AccessType.FREE
    if access_type == "paid":
        access_type_enum = AccessType.PAID
    elif access_type == "invite_only":
        access_type_enum = AccessType.INVITE_ONLY

    # Create lounge
    lounge = Lounge(
        mentor_id=mentor_id,
        title=title,
        slug=slug,
        description=description,
        category_id=category_id,
        access_type=access_type_enum,
        max_members=max_members,
        is_public_listing=is_public_listing
    )

    db.add(lounge)
    db.commit()
    db.refresh(lounge)

    return {
        "id": lounge.id,
        "title": lounge.title,
        "slug": lounge.slug,
        "description": lounge.description,
        "category_id": lounge.category_id,
        "access_type": lounge.access_type.value,
        "mentor_id": lounge.mentor_id,
        "created_at": lounge.created_at
    }


@router.put("/lounges/{lounge_id}")
async def admin_update_lounge(
    lounge_id: int,
    title: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    mentor_id: Optional[int] = None,
    access_type: Optional[str] = None,
    max_members: Optional[int] = None,
    is_public_listing: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update lounge details (admin only)
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    # Update fields if provided
    if title is not None:
        lounge.title = title

    if slug is not None:
        # Check slug uniqueness
        existing = db.query(Lounge).filter(
            Lounge.slug == slug,
            Lounge.id != lounge_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lounge with this slug already exists"
            )
        lounge.slug = slug

    if description is not None:
        lounge.description = description

    if category_id is not None:
        if category_id > 0:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            lounge.category_id = category_id
        else:
            lounge.category_id = None

    if mentor_id is not None:
        mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor not found"
            )
        lounge.mentor_id = mentor_id

    if access_type is not None:
        if access_type == "free":
            lounge.access_type = AccessType.FREE
        elif access_type == "paid":
            lounge.access_type = AccessType.PAID
        elif access_type == "invite_only":
            lounge.access_type = AccessType.INVITE_ONLY

    if max_members is not None:
        lounge.max_members = max_members if max_members > 0 else None

    if is_public_listing is not None:
        lounge.is_public_listing = is_public_listing

    db.commit()
    db.refresh(lounge)

    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge.id,
        LoungeMembership.left_at.is_(None)
    ).scalar()

    profile_image_url = await get_lounge_profile_image_url(lounge, db)

    return {
        "id": lounge.id,
        "title": lounge.title,
        "slug": lounge.slug,
        "description": lounge.description,
        "category_id": lounge.category_id,
        "category_name": lounge.category.name if lounge.category else None,
        "access_type": lounge.access_type.value,
        "max_members": lounge.max_members,
        "is_public_listing": lounge.is_public_listing,
        "mentor_id": lounge.mentor_id,
        "mentor_name": lounge.mentor.user.name if lounge.mentor else None,
        "profile_image_url": profile_image_url,
        "member_count": member_count,
        "is_full": lounge.is_full,
        "created_at": lounge.created_at
    }


@router.delete("/lounges/{lounge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_lounge(
    lounge_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete lounge (admin only)
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    # Delete all memberships first
    db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge_id
    ).delete()

    db.delete(lounge)
    db.commit()

    return None


# =============================================================================
# Admin User CRUD Operations
# =============================================================================

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create a new user (admin only)
    """

    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_data.role}"
        )

    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        role=role,
        email_verified_at=datetime.utcnow() if user_data.email_verified else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "email_verified_at": user.email_verified_at,
        "created_at": user.created_at
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get single user details (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

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

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "avatar_url": user.avatar_url,
        "email_verified_at": user.email_verified_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "lounge_count": lounge_count,
        "note_count": note_count,
        "subscription_status": subscription.status.value if subscription else None
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update user details (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    if user_data.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_data.email

    if user_data.name is not None:
        user.name = user_data.name

    if user_data.role is not None:
        try:
            user.role = UserRole(user_data.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {user_data.role}"
            )

    if user_data.email_verified is not None:
        user.email_verified_at = datetime.utcnow() if user_data.email_verified else None

    if user_data.avatar_url is not None:
        user.avatar_url = user_data.avatar_url

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "avatar_url": user.avatar_url,
        "email_verified_at": user.email_verified_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


# =============================================================================
# Admin Mentor CRUD Operations
# =============================================================================

@router.get("/mentors/{mentor_id}")
async def get_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get single mentor details (admin only)
    """
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()

    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )

    lounge_count = db.query(func.count(Lounge.id)).filter(
        Lounge.mentor_id == mentor.id
    ).scalar()

    return {
        "id": mentor.id,
        "user_id": mentor.user_id,
        "user_name": mentor.user.name,
        "user_email": mentor.user.email,
        "user_avatar": mentor.user.avatar_url,
        "headline": mentor.headline,
        "bio": mentor.bio,
        "intro_video_url": mentor.intro_video_url,
        "experience_years": mentor.experience_years,
        "status": mentor.status.value,
        "created_at": mentor.created_at,
        "updated_at": mentor.updated_at,
        "lounge_count": lounge_count
    }


@router.post("/mentors", status_code=status.HTTP_201_CREATED)
async def create_mentor(
    mentor_data: CreateMentorRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create a mentor profile (admin only)
    """
    from app.db.models.mentor import MentorStatus

    # Check if user exists
    user = db.query(User).filter(User.id == mentor_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user already has mentor profile
    existing = db.query(Mentor).filter(Mentor.user_id == mentor_data.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a mentor profile"
        )

    # Validate status
    try:
        status_enum = MentorStatus(mentor_data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {mentor_data.status}"
        )

    # Update user role to mentor
    user.role = UserRole.MENTOR

    # Create mentor profile
    mentor = Mentor(
        user_id=mentor_data.user_id,
        headline=mentor_data.headline,
        bio=mentor_data.bio,
        intro_video_url=mentor_data.intro_video_url,
        experience_years=mentor_data.experience_years,
        status=status_enum
    )

    db.add(mentor)
    db.commit()
    db.refresh(mentor)

    return {
        "id": mentor.id,
        "user_id": mentor.user_id,
        "user_name": user.name,
        "user_email": user.email,
        "headline": mentor.headline,
        "bio": mentor.bio,
        "intro_video_url": mentor.intro_video_url,
        "experience_years": mentor.experience_years,
        "status": mentor.status.value,
        "created_at": mentor.created_at
    }


@router.put("/mentors/{mentor_id}")
async def update_mentor(
    mentor_id: int,
    mentor_data: UpdateMentorRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update mentor details (admin only)
    """
    from app.db.models.mentor import MentorStatus

    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()

    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )

    # Update fields if provided
    if mentor_data.headline is not None:
        mentor.headline = mentor_data.headline

    if mentor_data.bio is not None:
        mentor.bio = mentor_data.bio

    if mentor_data.intro_video_url is not None:
        mentor.intro_video_url = mentor_data.intro_video_url

    if mentor_data.experience_years is not None:
        mentor.experience_years = mentor_data.experience_years

    if mentor_data.status is not None:
        try:
            mentor.status = MentorStatus(mentor_data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {mentor_data.status}"
            )

    db.commit()
    db.refresh(mentor)

    return {
        "id": mentor.id,
        "user_id": mentor.user_id,
        "user_name": mentor.user.name,
        "user_email": mentor.user.email,
        "headline": mentor.headline,
        "bio": mentor.bio,
        "intro_video_url": mentor.intro_video_url,
        "experience_years": mentor.experience_years,
        "status": mentor.status.value,
        "created_at": mentor.created_at,
        "updated_at": mentor.updated_at
    }


@router.delete("/mentors/{mentor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete mentor profile (admin only)
    """
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()

    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )

    # Revert user role to member
    mentor.user.role = UserRole.MEMBER

    db.delete(mentor)
    db.commit()

    return None
