"""
Admin API endpoints
Handles admin dashboard, user management, and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import psutil
import time

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.jwt import get_current_admin
from app.db.models.user import User, UserRole
from app.db.models.mentor import Mentor
from app.db.models.lounge import Lounge, LoungeMembership, AccessType
from app.db.models.mentor import Category
from app.db.models.billing import Subscription, Payment, SubscriptionStatus, LoungeSubscription, PaymentStatus, LoungePlanType
from app.db.models.note import Note
from app.db.models.lounge_resource import LoungeResource
from app.db.models.newsletter import NewsletterSubscriber, SubscriberStatus
from app.db.models.misc import ContactMessage, ContactMessageStatus
from app.db.models.file import File as FileModel
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
    UpdateMentorRequest,
    LoungeInfo,
    UserSubscriptionResponse,
    PaginatedSubscriptionsResponse,
    ContactMessageResponse,
    PaginatedContactMessagesResponse,
    UpdateContactMessageStatusRequest
)
from app.core.security import hash_password
from app.services.file_service import file_service
from app.services.billing_service import billing_service
from app.services.email_service import send_user_credentials_email_sync, send_mentor_welcome_email_sync
from app.services.lounge_resource_service import lounge_resource_service
from app.schemas.lounge_resource import (
    LoungeResourceResponse,
    LoungeResourceListResponse,
    LoungeResourcesListResponse
)
import logging

logger = logging.getLogger(__name__)

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
    
    # Revenue from payments
    payment_revenue = db.query(func.sum(Payment.amount_cents)).filter(
        Payment.status == PaymentStatus.SUCCEEDED
    ).scalar() or 0

    # Revenue from active lounge subscriptions
    # Count by plan type and multiply by fixed prices: monthly = $25 (2500 cents), yearly = $240 (24000 cents)
    monthly_sub_count = db.query(func.count(LoungeSubscription.id)).filter(
        LoungeSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        LoungeSubscription.plan_type == LoungePlanType.MONTHLY
    ).scalar() or 0

    yearly_sub_count = db.query(func.count(LoungeSubscription.id)).filter(
        LoungeSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        LoungeSubscription.plan_type == LoungePlanType.YEARLY
    ).scalar() or 0

    lounge_subscription_revenue = (monthly_sub_count * 2500) + (yearly_sub_count * 24000)

    total_revenue = payment_revenue + lounge_subscription_revenue
    
    # Active users (last 30 days)
    thirty_days_ago = now_naive() - timedelta(days=30)
    active_users = db.query(func.count(func.distinct(ChatMessage.user_id))).filter(
        ChatMessage.created_at >= thirty_days_ago
    ).scalar()
    
    # New users (last 7 days)
    seven_days_ago = now_naive() - timedelta(days=7)
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
    since_date = now_naive() - timedelta(days=days)
    
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
        end_date = now_naive() - timedelta(days=i*30)
        start_date = end_date - timedelta(days=30)
        
        # Revenue
        revenue = db.query(func.sum(Payment.amount_cents)).filter(
            Payment.created_at >= start_date,
            Payment.created_at < end_date,
            Payment.status == PaymentStatus.SUCCEEDED
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
        "filename": f"users_export_{now_naive().strftime('%Y%m%d')}.csv",
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
            "about": lounge.about,
            "brand_color": lounge.brand_color,
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
        "about": lounge.about,
        "brand_color": lounge.brand_color,
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
    about: Optional[str] = None,
    brand_color: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create lounge as admin

    - Requires admin role
    - Can assign to any mentor
    - Automatically creates Stripe product/prices for paid lounges
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

    # Create lounge first (without Stripe IDs)
    lounge = Lounge(
        mentor_id=mentor_id,
        title=title,
        slug=slug,
        description=description,
        category_id=category_id,
        access_type=access_type_enum,
        max_members=max_members,
        is_public_listing=is_public_listing,
        about=about,
        brand_color=brand_color or "#9ECCF2"
    )

    db.add(lounge)
    db.commit()
    db.refresh(lounge)

    # If paid lounge, create Stripe product and prices
    stripe_error = None
    if access_type_enum == AccessType.PAID:
        try:
            stripe_data = await billing_service.create_lounge_stripe_product(
                lounge_id=lounge.id,
                lounge_title=title,
                lounge_slug=slug,
                db=db
            )

            # Update lounge with Stripe IDs
            lounge.stripe_product_id = stripe_data['stripe_product_id']
            lounge.stripe_monthly_price_id = stripe_data['stripe_monthly_price_id']
            lounge.stripe_yearly_price_id = stripe_data['stripe_yearly_price_id']

            db.commit()
            db.refresh(lounge)

            logger.info(f"Created Stripe product for lounge {lounge.id}: {stripe_data['stripe_product_id']}")

        except Exception as e:
            # Log the error but don't fail lounge creation
            logger.error(f"Failed to create Stripe product for lounge {lounge.id}: {str(e)}")
            stripe_error = str(e)

    response = {
        "id": lounge.id,
        "title": lounge.title,
        "slug": lounge.slug,
        "description": lounge.description,
        "category_id": lounge.category_id,
        "access_type": lounge.access_type.value,
        "mentor_id": lounge.mentor_id,
        "created_at": lounge.created_at,
        "stripe_product_id": lounge.stripe_product_id,
        "stripe_monthly_price_id": lounge.stripe_monthly_price_id,
        "stripe_yearly_price_id": lounge.stripe_yearly_price_id
    }

    if stripe_error:
        response["stripe_setup_warning"] = f"Lounge created but Stripe setup failed: {stripe_error}. You can retry via /admin/lounges/{lounge.id}/setup-stripe"

    return response


@router.post("/lounges/{lounge_id}/setup-stripe", status_code=status.HTTP_200_OK)
async def admin_setup_lounge_stripe(
    lounge_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Setup or retry Stripe product/prices for a lounge

    - Requires admin role
    - Creates Stripe product if not exists
    - Useful for retrying failed setups or setting up existing lounges
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    if lounge.access_type != AccessType.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only paid lounges can have Stripe products"
        )

    if lounge.stripe_product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lounge already has Stripe product configured"
        )

    try:
        stripe_data = await billing_service.create_lounge_stripe_product(
            lounge_id=lounge.id,
            lounge_title=lounge.title,
            lounge_slug=lounge.slug,
            db=db
        )

        lounge.stripe_product_id = stripe_data['stripe_product_id']
        lounge.stripe_monthly_price_id = stripe_data['stripe_monthly_price_id']
        lounge.stripe_yearly_price_id = stripe_data['stripe_yearly_price_id']

        db.commit()
        db.refresh(lounge)

        logger.info(f"Setup Stripe product for lounge {lounge.id}: {stripe_data['stripe_product_id']}")

        return {
            "message": "Stripe product created successfully",
            "lounge_id": lounge.id,
            "stripe_product_id": lounge.stripe_product_id,
            "stripe_monthly_price_id": lounge.stripe_monthly_price_id,
            "stripe_yearly_price_id": lounge.stripe_yearly_price_id,
            "monthly_price": "$25/month",
            "yearly_price": "$240/year"
        }

    except Exception as e:
        logger.error(f"Failed to create Stripe product for lounge {lounge.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Stripe product: {str(e)}"
        )


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
    about: Optional[str] = None,
    brand_color: Optional[str] = None,
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

    if about is not None:
        lounge.about = about

    if brand_color is not None:
        lounge.brand_color = brand_color

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
        "about": lounge.about,
        "brand_color": lounge.brand_color,
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create a new user (admin only)

    - Creates user account
    - Sends credentials email to user
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
        email_verified_at=now_naive() if user_data.email_verified else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send credentials email to user in background (only for non-mentor roles)
    if role != UserRole.MENTOR:
        background_tasks.add_task(
            send_user_credentials_email_sync,
            user.email,
            user.name,
            user_data.password  # Send the original password before hashing
        )

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
        user.email_verified_at = now_naive() if user_data.email_verified else None

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


@router.post("/users/{user_id}/avatar")
async def upload_user_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Upload avatar for a user (admin only)

    - Accepts image files (jpg, jpeg, png, gif, webp)
    - Max file size: 5MB
    - Returns updated user with new avatar_url
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = '.' + file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Upload file to storage
        file_record = await file_service.upload_file(
            file=file,
            user_id=user.id,
            db=db,
            folder="avatars"
        )

        # Generate URL for the uploaded file
        avatar_url = await file_service.get_file_url(file_record.id, db)

        # Update user's avatar_url
        user.avatar_url = avatar_url
        user.updated_at = now_naive()

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

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to upload avatar for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


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
        "lounge_count": lounge_count,
        # Mentor profile fields for "More from Mentor" modal
        "mentor_title": mentor.mentor_title,
        "philosophy": mentor.philosophy,
        "hobbies": mentor.hobbies,
        "social_instagram": mentor.social_instagram,
        "social_tiktok": mentor.social_tiktok,
        "social_linkedin": mentor.social_linkedin,
        "social_youtube": mentor.social_youtube,
        "book_title": mentor.book_title,
        "book_description": mentor.book_description,
        "podcast_rec_title": mentor.podcast_rec_title,
        "podcast_name": mentor.podcast_name,
        "podcast_youtube": mentor.podcast_youtube,
        "podcast_spotify": mentor.podcast_spotify,
        "podcast_apple": mentor.podcast_apple,
        "quick_prompts": mentor.quick_prompts
    }


@router.post("/mentors", status_code=status.HTTP_201_CREATED)
async def create_mentor(
    mentor_data: CreateMentorRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create a mentor profile (admin only)

    - Creates mentor profile for existing user
    - Sends mentor welcome email (no credentials since there's no mentor portal)
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
        status=status_enum,
        # Mentor profile fields for "More from Mentor" modal
        mentor_title=mentor_data.mentor_title,
        philosophy=mentor_data.philosophy,
        hobbies=mentor_data.hobbies,
        # Social links
        social_instagram=mentor_data.social_instagram,
        social_tiktok=mentor_data.social_tiktok,
        social_linkedin=mentor_data.social_linkedin,
        social_youtube=mentor_data.social_youtube,
        # Book recommendation
        book_title=mentor_data.book_title,
        book_description=mentor_data.book_description,
        # Podcast recommendation
        podcast_rec_title=mentor_data.podcast_rec_title,
        # Podcast links
        podcast_name=mentor_data.podcast_name,
        podcast_youtube=mentor_data.podcast_youtube,
        podcast_spotify=mentor_data.podcast_spotify,
        podcast_apple=mentor_data.podcast_apple,
        # Quick prompts
        quick_prompts=mentor_data.quick_prompts
    )

    db.add(mentor)
    db.commit()
    db.refresh(mentor)

    # Send mentor welcome email in background
    background_tasks.add_task(
        send_mentor_welcome_email_sync,
        user.email,
        user.name
    )

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
        "created_at": mentor.created_at,
        # Mentor profile fields
        "mentor_title": mentor.mentor_title,
        "philosophy": mentor.philosophy,
        "hobbies": mentor.hobbies,
        "social_instagram": mentor.social_instagram,
        "social_tiktok": mentor.social_tiktok,
        "social_linkedin": mentor.social_linkedin,
        "social_youtube": mentor.social_youtube,
        "book_title": mentor.book_title,
        "book_description": mentor.book_description,
        "podcast_rec_title": mentor.podcast_rec_title,
        "podcast_name": mentor.podcast_name,
        "podcast_youtube": mentor.podcast_youtube,
        "podcast_spotify": mentor.podcast_spotify,
        "podcast_apple": mentor.podcast_apple,
        "quick_prompts": mentor.quick_prompts
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

    # Update mentor profile fields for "More from Mentor" modal
    if mentor_data.mentor_title is not None:
        mentor.mentor_title = mentor_data.mentor_title
    if mentor_data.philosophy is not None:
        mentor.philosophy = mentor_data.philosophy
    if mentor_data.hobbies is not None:
        mentor.hobbies = mentor_data.hobbies
    # Social links
    if mentor_data.social_instagram is not None:
        mentor.social_instagram = mentor_data.social_instagram
    if mentor_data.social_tiktok is not None:
        mentor.social_tiktok = mentor_data.social_tiktok
    if mentor_data.social_linkedin is not None:
        mentor.social_linkedin = mentor_data.social_linkedin
    if mentor_data.social_youtube is not None:
        mentor.social_youtube = mentor_data.social_youtube
    # Book recommendation
    if mentor_data.book_title is not None:
        mentor.book_title = mentor_data.book_title
    if mentor_data.book_description is not None:
        mentor.book_description = mentor_data.book_description
    # Podcast recommendation
    if mentor_data.podcast_rec_title is not None:
        mentor.podcast_rec_title = mentor_data.podcast_rec_title
    # Podcast links
    if mentor_data.podcast_name is not None:
        mentor.podcast_name = mentor_data.podcast_name
    if mentor_data.podcast_youtube is not None:
        mentor.podcast_youtube = mentor_data.podcast_youtube
    if mentor_data.podcast_spotify is not None:
        mentor.podcast_spotify = mentor_data.podcast_spotify
    if mentor_data.podcast_apple is not None:
        mentor.podcast_apple = mentor_data.podcast_apple
    # Quick prompts
    if mentor_data.quick_prompts is not None:
        mentor.quick_prompts = mentor_data.quick_prompts

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
        "updated_at": mentor.updated_at,
        # Mentor profile fields
        "mentor_title": mentor.mentor_title,
        "philosophy": mentor.philosophy,
        "hobbies": mentor.hobbies,
        "social_instagram": mentor.social_instagram,
        "social_tiktok": mentor.social_tiktok,
        "social_linkedin": mentor.social_linkedin,
        "social_youtube": mentor.social_youtube,
        "book_title": mentor.book_title,
        "book_description": mentor.book_description,
        "podcast_rec_title": mentor.podcast_rec_title,
        "podcast_name": mentor.podcast_name,
        "podcast_youtube": mentor.podcast_youtube,
        "podcast_spotify": mentor.podcast_spotify,
        "podcast_apple": mentor.podcast_apple,
        "quick_prompts": mentor.quick_prompts
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


# =============================================================================
# Admin Subscription Management
# =============================================================================

@router.get("/subscriptions", response_model=PaginatedSubscriptionsResponse)
async def get_user_subscriptions(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None
):
    """
    Get all lounge subscriptions

    - Requires admin role
    - Shows which users have subscribed to which lounges
    - Supports filtering by status and search by user name/email
    """
    query = db.query(LoungeSubscription).join(
        User, LoungeSubscription.user_id == User.id
    ).join(
        Lounge, LoungeSubscription.lounge_id == Lounge.id
    )

    # Filter by status
    if status_filter:
        try:
            status_enum = SubscriptionStatus(status_filter)
            query = query.filter(LoungeSubscription.status == status_enum)
        except ValueError:
            pass  # Ignore invalid status

    # Search by user name/email
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.name.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Calculate offset from page
    skip = (page - 1) * limit

    # Get subscriptions with ordering
    subscriptions = query.order_by(
        LoungeSubscription.started_at.desc()
    ).offset(skip).limit(limit).all()

    items = []
    for sub in subscriptions:
        lounge = sub.lounge
        profile_image_url = await get_lounge_profile_image_url(lounge, db)

        # Determine price and billing interval based on plan type
        price_cents = 2500 if sub.plan_type.value == 'monthly' else 24000  # $25/mo or $240/yr
        billing_interval = 'month' if sub.plan_type.value == 'monthly' else 'year'
        plan_name = f"{lounge.title} - {'Monthly' if sub.plan_type.value == 'monthly' else 'Yearly'}"

        # Build lounge info for frontend compatibility
        lounge_info = LoungeInfo(
            id=lounge.id,
            title=lounge.title,
            slug=lounge.slug,
            access_type=lounge.access_type.value,
            mentor_name=lounge.mentor.user.name if lounge.mentor else None,
            profile_image_url=profile_image_url
        )

        items.append(UserSubscriptionResponse(
            subscription_id=sub.id,
            user_id=sub.user_id,
            user_name=sub.user.name,
            user_email=sub.user.email,
            user_avatar=sub.user.avatar_url,
            plan_name=plan_name,
            plan_price_cents=price_cents,
            billing_interval=billing_interval,
            lounge_id=lounge.id,
            lounge_title=lounge.title,
            lounge_slug=lounge.slug,
            lounges=[lounge_info],
            plan_type=sub.plan_type.value,
            status=sub.status.value,
            stripe_subscription_id=sub.stripe_subscription_id,
            started_at=sub.started_at,
            renews_at=sub.renews_at,
            canceled_at=sub.canceled_at
        ))

    # Calculate total pages
    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedSubscriptionsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/subscriptions/{subscription_id}")
async def get_subscription_detail(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get detailed lounge subscription information (admin only)
    """
    subscription = db.query(LoungeSubscription).filter(
        LoungeSubscription.id == subscription_id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    lounge = subscription.lounge
    profile_image_url = await get_lounge_profile_image_url(lounge, db)
    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge.id,
        LoungeMembership.left_at.is_(None)
    ).scalar()

    is_member = db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge.id,
        LoungeMembership.user_id == subscription.user_id,
        LoungeMembership.left_at.is_(None)
    ).first() is not None

    # Get payment history for this user
    payments = db.query(Payment).filter(
        Payment.user_id == subscription.user_id
    ).order_by(Payment.created_at.desc()).limit(10).all()

    payment_history = []
    for payment in payments:
        payment_history.append({
            "id": payment.id,
            "amount_cents": payment.amount_cents,
            "currency": payment.currency,
            "status": payment.status.value,
            "provider": payment.provider.value,
            "created_at": payment.created_at
        })

    price_cents = 2500 if subscription.plan_type.value == 'monthly' else 24000

    return {
        "subscription_id": subscription.id,
        "user_id": subscription.user_id,
        "user_name": subscription.user.name,
        "user_email": subscription.user.email,
        "user_avatar": subscription.user.avatar_url,
        "lounge_id": lounge.id,
        "lounge_title": lounge.title,
        "lounge_slug": lounge.slug,
        "lounge_mentor_name": lounge.mentor.user.name if lounge.mentor else None,
        "lounge_profile_image_url": profile_image_url,
        "lounge_member_count": member_count,
        "user_is_lounge_member": is_member,
        "plan_type": subscription.plan_type.value,
        "plan_price_cents": price_cents,
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "status": subscription.status.value,
        "started_at": subscription.started_at,
        "renews_at": subscription.renews_at,
        "canceled_at": subscription.canceled_at,
        "payment_history": payment_history
    }


# =============================================================================
# Admin Lounge Resource Management
# =============================================================================

@router.get("/lounge-resources", response_model=LoungeResourcesListResponse)
async def get_all_lounge_resources(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID")
):
    """
    Get all lounge resources (admin only)

    - Requires admin role
    - Supports filtering by lounge_id
    - Returns paginated results
    """
    resources, total = await lounge_resource_service.get_all_lounges_resources(
        db=db,
        page=page,
        page_size=page_size,
        lounge_id=lounge_id
    )

    # Build response with file info
    items = []
    for resource in resources:
        file_url = await lounge_resource_service.get_resource_file_url(resource.id, db)
        file_record = db.query(FileModel).filter(FileModel.id == resource.file_id).first()

        items.append(LoungeResourceListResponse(
            id=resource.id,
            lounge_id=resource.lounge_id,
            title=resource.title,
            description=resource.description,
            file_url=file_url,
            file_type=file_record.mime_type if file_record else None,
            file_size=file_record.size_bytes if file_record else 0,
            file_name=file_record.storage_path.split('/')[-1] if file_record and file_record.storage_path else None,
            created_at=resource.created_at
        ))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return LoungeResourcesListResponse(
        resources=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/lounge-resources/{resource_id}", response_model=LoungeResourceResponse)
async def get_lounge_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get single lounge resource details (admin only)
    """
    resource = await lounge_resource_service.get_resource(resource_id, db)

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    file_url = await lounge_resource_service.get_resource_file_url(resource.id, db)
    file_record = db.query(FileModel).filter(FileModel.id == resource.file_id).first()

    # Get uploader name
    uploader = db.query(User).filter(User.id == resource.uploaded_by_user_id).first()

    return LoungeResourceResponse(
        id=resource.id,
        lounge_id=resource.lounge_id,
        title=resource.title,
        description=resource.description,
        file_url=file_url,
        file_type=file_record.mime_type if file_record else None,
        file_size=file_record.size_bytes if file_record else 0,
        uploaded_by_user_id=resource.uploaded_by_user_id,
        uploaded_by_name=uploader.name if uploader else None,
        created_at=resource.created_at,
        updated_at=resource.updated_at
    )


@router.post("/lounge-resources", status_code=status.HTTP_201_CREATED, response_model=LoungeResourceResponse)
async def create_lounge_resource(
    lounge_id: int,
    title: str,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Upload a new lounge resource (admin only)

    - Requires admin role
    - Uploads file and creates resource record
    - Accepts any file type (pdf, docx, etc.)
    """
    try:
        resource = await lounge_resource_service.create_resource(
            lounge_id=lounge_id,
            title=title,
            file=file,
            uploaded_by_user_id=admin_user.id,
            db=db,
            description=description
        )

        file_url = await lounge_resource_service.get_resource_file_url(resource.id, db)
        file_record = db.query(FileModel).filter(FileModel.id == resource.file_id).first()

        return LoungeResourceResponse(
            id=resource.id,
            lounge_id=resource.lounge_id,
            title=resource.title,
            description=resource.description,
            file_url=file_url,
            file_type=file_record.mime_type if file_record else None,
            file_size=file_record.size_bytes if file_record else 0,
            uploaded_by_user_id=resource.uploaded_by_user_id,
            uploaded_by_name=admin_user.name,
            created_at=resource.created_at,
            updated_at=resource.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create lounge resource: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resource"
        )


@router.put("/lounge-resources/{resource_id}", response_model=LoungeResourceResponse)
async def update_lounge_resource(
    resource_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update lounge resource metadata (admin only)

    - Requires admin role
    - Updates title and/or description
    - Does not replace the file
    """
    try:
        resource = await lounge_resource_service.update_resource(
            resource_id=resource_id,
            db=db,
            title=title,
            description=description
        )

        file_url = await lounge_resource_service.get_resource_file_url(resource.id, db)
        file_record = db.query(FileModel).filter(FileModel.id == resource.file_id).first()
        uploader = db.query(User).filter(User.id == resource.uploaded_by_user_id).first()

        return LoungeResourceResponse(
            id=resource.id,
            lounge_id=resource.lounge_id,
            title=resource.title,
            description=resource.description,
            file_url=file_url,
            file_type=file_record.mime_type if file_record else None,
            file_size=file_record.size_bytes if file_record else 0,
            uploaded_by_user_id=resource.uploaded_by_user_id,
            uploaded_by_name=uploader.name if uploader else None,
            created_at=resource.created_at,
            updated_at=resource.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update lounge resource {resource_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource"
        )


@router.delete("/lounge-resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lounge_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete lounge resource (admin only)

    - Requires admin role
    - Deletes resource record and associated file
    """
    try:
        await lounge_resource_service.delete_resource(resource_id, db)
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete lounge resource {resource_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resource"
        )


# =============================================================================
# Public Chatbot Configuration
# =============================================================================

from app.services.public_chatbot_service import public_chatbot_service
from app.db.models.public_chatbot import PublicChatbotConfig
from pydantic import BaseModel as PydanticBaseModel


class ChatbotConfigUpdate(PydanticBaseModel):
    """Schema for updating chatbot config"""
    name: Optional[str] = None
    welcome_message: Optional[str] = None
    system_prompt: Optional[str] = None
    input_placeholder: Optional[str] = None
    header_subtitle: Optional[str] = None
    is_enabled: Optional[bool] = None
    avatar_url: Optional[str] = None


class ChatbotConfigResponse(PydanticBaseModel):
    """Schema for chatbot config response"""
    id: int
    name: str
    welcome_message: str
    system_prompt: Optional[str]
    input_placeholder: str
    header_subtitle: Optional[str]
    is_enabled: bool
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/chatbot/config", response_model=ChatbotConfigResponse)
async def get_chatbot_config(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get public chatbot configuration (admin only)
    """
    config = await public_chatbot_service.get_config(db)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot configuration not found"
        )

    return config


@router.put("/chatbot/config", response_model=ChatbotConfigResponse)
async def update_chatbot_config(
    config_data: ChatbotConfigUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update public chatbot configuration (admin only)

    - Updates the system prompt, welcome message, and other settings
    - Creates default config if none exists
    """
    try:
        config = await public_chatbot_service.update_config(
            db=db,
            data=config_data.model_dump(exclude_none=True)
        )
        return config

    except Exception as e:
        logger.error(f"Failed to update chatbot config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chatbot configuration"
        )


# ============================================================================
# Newsletter Management Endpoints
# ============================================================================

@router.get("/newsletter/subscribers")
async def get_newsletter_subscribers(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, unsubscribed"),
    search: Optional[str] = Query(None, description="Search by email")
):
    """
    Get all newsletter subscribers (admin only)

    - Supports pagination
    - Supports filtering by status
    - Supports search by email
    """
    query = db.query(NewsletterSubscriber)

    # Apply status filter
    if status_filter:
        if status_filter == "active":
            query = query.filter(NewsletterSubscriber.status == SubscriberStatus.ACTIVE)
        elif status_filter == "unsubscribed":
            query = query.filter(NewsletterSubscriber.status == SubscriberStatus.UNSUBSCRIBED)

    # Apply search filter
    if search:
        query = query.filter(NewsletterSubscriber.email.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination
    subscribers = query.order_by(NewsletterSubscriber.subscribed_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "items": [
            {
                "id": sub.id,
                "email": sub.email,
                "status": sub.status.value,
                "subscribed_at": sub.subscribed_at,
                "unsubscribed_at": sub.unsubscribed_at,
                "source": sub.source,
                "ip_address": sub.ip_address
            }
            for sub in subscribers
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.get("/newsletter/stats")
async def get_newsletter_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Get newsletter statistics (admin only)
    """
    total = db.query(func.count(NewsletterSubscriber.id)).scalar()
    active = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.status == SubscriberStatus.ACTIVE
    ).scalar()
    unsubscribed = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.status == SubscriberStatus.UNSUBSCRIBED
    ).scalar()

    # Get subscriptions in last 7 days
    seven_days_ago = now_naive() - timedelta(days=7)
    new_this_week = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.subscribed_at >= seven_days_ago
    ).scalar()

    # Get subscriptions in last 30 days
    thirty_days_ago = now_naive() - timedelta(days=30)
    new_this_month = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.subscribed_at >= thirty_days_ago
    ).scalar()

    return {
        "total": total,
        "active": active,
        "unsubscribed": unsubscribed,
        "new_this_week": new_this_week,
        "new_this_month": new_this_month
    }


@router.delete("/newsletter/subscribers/{subscriber_id}")
async def delete_newsletter_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete a newsletter subscriber (admin only)
    """
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )

    db.delete(subscriber)
    db.commit()

    return {"success": True, "message": "Subscriber deleted successfully"}


@router.post("/newsletter/export")
async def export_newsletter_subscribers(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, unsubscribed")
):
    """
    Export newsletter subscribers as CSV (admin only)
    """
    import csv
    import io

    query = db.query(NewsletterSubscriber)

    if status_filter:
        if status_filter == "active":
            query = query.filter(NewsletterSubscriber.status == SubscriberStatus.ACTIVE)
        elif status_filter == "unsubscribed":
            query = query.filter(NewsletterSubscriber.status == SubscriberStatus.UNSUBSCRIBED)

    subscribers = query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Status", "Subscribed At", "Unsubscribed At", "Source"])

    for sub in subscribers:
        writer.writerow([
            sub.email,
            sub.status.value,
            sub.subscribed_at.isoformat() if sub.subscribed_at else "",
            sub.unsubscribed_at.isoformat() if sub.unsubscribed_at else "",
            sub.source
        ])

    csv_content = output.getvalue()
    output.close()

    # Upload to S3
    from app.services.file_service import file_service
    filename = f"newsletter_export_{now_naive().strftime('%Y%m%d_%H%M%S')}.csv"

    file_url = await file_service.upload_export_file(
        content=csv_content.encode('utf-8'),
        filename=filename,
        content_type="text/csv"
    )

    return {"success": True, "download_url": file_url}


# =============================================================================
# Contact Message Management Endpoints
# =============================================================================

@router.get("/contacts", response_model=PaginatedContactMessagesResponse)
async def list_contact_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status: new, read, replied, archived"),
    search: Optional[str] = Query(None, description="Search by name, email, or subject"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    List all contact messages with pagination and filtering.
    Admin only endpoint.
    """
    query = db.query(ContactMessage)

    # Apply status filter
    if status_filter:
        try:
            status_enum = ContactMessageStatus(status_filter)
            query = query.filter(ContactMessage.status == status_enum)
        except ValueError:
            pass

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ContactMessage.name.ilike(search_term)) |
            (ContactMessage.email.ilike(search_term)) |
            (ContactMessage.subject.ilike(search_term))
        )

    # Get total count
    total = query.count()
    pages = (total + limit - 1) // limit

    # Get paginated results
    messages = query.order_by(ContactMessage.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedContactMessagesResponse(
        items=[ContactMessageResponse(
            id=msg.id,
            name=msg.name,
            email=msg.email,
            subject=msg.subject,
            message=msg.message,
            status=msg.status.value,
            ip_address=msg.ip_address,
            user_agent=msg.user_agent,
            created_at=msg.created_at,
            read_at=msg.read_at,
            replied_at=msg.replied_at
        ) for msg in messages],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/contacts/{contact_id}", response_model=ContactMessageResponse)
async def get_contact_message(
    contact_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get a single contact message by ID.
    Admin only endpoint.
    """
    message = db.query(ContactMessage).filter(ContactMessage.id == contact_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    # Mark as read if new
    if message.status == ContactMessageStatus.NEW:
        message.status = ContactMessageStatus.READ
        message.read_at = now_naive()
        db.commit()
        db.refresh(message)

    return ContactMessageResponse(
        id=message.id,
        name=message.name,
        email=message.email,
        subject=message.subject,
        message=message.message,
        status=message.status.value,
        ip_address=message.ip_address,
        user_agent=message.user_agent,
        created_at=message.created_at,
        read_at=message.read_at,
        replied_at=message.replied_at
    )


@router.patch("/contacts/{contact_id}/status")
async def update_contact_message_status(
    contact_id: int,
    request: UpdateContactMessageStatusRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update contact message status.
    Admin only endpoint.
    """
    message = db.query(ContactMessage).filter(ContactMessage.id == contact_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    try:
        new_status = ContactMessageStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: new, read, replied, archived"
        )

    message.status = new_status

    # Update timestamps based on status
    if new_status == ContactMessageStatus.READ and not message.read_at:
        message.read_at = now_naive()
    elif new_status == ContactMessageStatus.REPLIED and not message.replied_at:
        message.replied_at = now_naive()
        if not message.read_at:
            message.read_at = now_naive()

    db.commit()

    return {"success": True, "message": f"Status updated to {new_status.value}"}


@router.delete("/contacts/{contact_id}")
async def delete_contact_message(
    contact_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a contact message.
    Admin only endpoint.
    """
    message = db.query(ContactMessage).filter(ContactMessage.id == contact_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    db.delete(message)
    db.commit()

    return {"success": True, "message": "Contact message deleted"}
