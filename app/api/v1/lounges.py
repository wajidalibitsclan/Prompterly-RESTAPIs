"""
Lounge API endpoints
Handles lounge CRUD, membership, and discovery
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.jwt import (
    get_current_user,
    get_current_active_user,
    get_current_mentor,
    get_current_admin,
    get_optional_current_user
)
from app.db.models.user import User
from app.db.models.mentor import Mentor, Category
from app.db.models.lounge import (
    Lounge,
    LoungeMembership,
    AccessType,
    MembershipRole
)
from app.schemas.lounge import (
    LoungeCreate,
    LoungeUpdate,
    LoungeResponse,
    LoungeListResponse,
    LoungeMemberResponse,
    JoinLoungeRequest,
    UpdateMemberRole
)
from app.services.file_service import file_service
from app.core.config import settings

router = APIRouter()


def normalize_avatar_url(avatar_url: Optional[str]) -> Optional[str]:
    """
    Normalize avatar URL to ensure it's a full URL.

    - If None or empty, returns None
    - If already a full URL (http/https), returns as-is
    - If relative path, prepends BASE_URL
    """
    if not avatar_url:
        return None

    # Already a full URL
    if avatar_url.startswith(('http://', 'https://')):
        return avatar_url

    # Relative path - prepend BASE_URL
    base_url = settings.BASE_URL.rstrip('/')
    if avatar_url.startswith('/'):
        return f"{base_url}{avatar_url}"
    else:
        return f"{base_url}/{avatar_url}"


async def get_profile_image_url(lounge: Lounge, db: Session) -> Optional[str]:
    """Get the profile image URL for a lounge"""
    if lounge.profile_image_id:
        try:
            return await file_service.get_file_url(lounge.profile_image_id, db)
        except Exception:
            return None
    return None


@router.get("/my")
async def get_my_lounges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get lounges the current user is a member of

    - Requires authentication
    - Returns lounges user has joined or subscribed to
    """
    # Get user's memberships
    memberships = db.query(LoungeMembership).filter(
        LoungeMembership.user_id == current_user.id,
        LoungeMembership.left_at.is_(None)
    ).offset(skip).limit(limit).all()

    lounge_ids = [m.lounge_id for m in memberships]

    if not lounge_ids:
        return {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": limit
        }

    lounges = db.query(Lounge).filter(Lounge.id.in_(lounge_ids)).all()

    items = []
    for lounge in lounges:
        member_count = db.query(func.count(LoungeMembership.id)).filter(
            LoungeMembership.lounge_id == lounge.id,
            LoungeMembership.left_at.is_(None)
        ).scalar()

        profile_image_url = await get_profile_image_url(lounge, db)

        items.append({
            "id": lounge.id,
            "mentor_id": lounge.mentor_id,
            "title": lounge.title,
            "slug": lounge.slug,
            "description": lounge.description,
            "category_id": lounge.category_id,
            "access_type": lounge.access_type.value,
            "profile_image_url": profile_image_url,
            "created_at": lounge.created_at,
            "mentor_name": lounge.mentor.user.name if lounge.mentor else None,
            "mentor_avatar": normalize_avatar_url(lounge.mentor.user.avatar_url) if lounge.mentor else None,
            "category_name": lounge.category.name if lounge.category else None,
            "member_count": member_count,
            "is_member": True
        })

    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "limit": limit
    }


@router.get("/")
async def list_lounges(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    category_id: Optional[int] = None,
    access_type: Optional[AccessType] = None,
    search: Optional[str] = None,
    mentor_id: Optional[int] = None
):
    """
    List all lounges

    - Public endpoint (shows only public lounges if not authenticated)
    - Supports filtering by category, access type, search, mentor
    - Returns paginated results
    """
    query = db.query(Lounge).filter(Lounge.is_public_listing == True)

    # Category filter
    if category_id:
        query = query.filter(Lounge.category_id == category_id)

    # Access type filter
    if access_type:
        query = query.filter(Lounge.access_type == access_type)

    # Mentor filter
    if mentor_id:
        query = query.filter(Lounge.mentor_id == mentor_id)

    # Search filter - search in title, description, mentor name, and category name
    if search:
        search_term = f"%{search}%"
        query = query.outerjoin(Mentor, Lounge.mentor_id == Mentor.id)\
                     .outerjoin(User, Mentor.user_id == User.id)\
                     .outerjoin(Category, Lounge.category_id == Category.id)\
                     .filter(
            or_(
                Lounge.title.ilike(search_term),
                Lounge.description.ilike(search_term),
                User.name.ilike(search_term),
                Category.name.ilike(search_term)
            )
        )

    # Get total count before pagination
    total = query.count()

    # Calculate skip from page if page is provided
    if page > 1:
        skip = (page - 1) * limit

    lounges = query.offset(skip).limit(limit).all()

    # Build response with stats
    items = []
    for lounge in lounges:
        member_count = db.query(func.count(LoungeMembership.id)).filter(
            LoungeMembership.lounge_id == lounge.id,
            LoungeMembership.left_at.is_(None)
        ).scalar()

        is_full = (lounge.max_members is not None and
                   member_count >= lounge.max_members)

        profile_image_url = await get_profile_image_url(lounge, db)

        items.append({
            "id": lounge.id,
            "mentor_id": lounge.mentor_id,
            "title": lounge.title,
            "slug": lounge.slug,
            "description": lounge.description,
            "category_id": lounge.category_id,
            "access_type": lounge.access_type.value,
            "profile_image_url": profile_image_url,
            "created_at": lounge.created_at,
            "mentor_name": lounge.mentor.user.name if lounge.mentor else None,
            "mentor_avatar": normalize_avatar_url(lounge.mentor.user.avatar_url) if lounge.mentor else None,
            "category_name": lounge.category.name if lounge.category else None,
            "member_count": member_count,
            "is_full": is_full
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/", response_model=LoungeResponse, status_code=status.HTTP_201_CREATED)
async def create_lounge(
    lounge_data: LoungeCreate,
    current_user: User = Depends(get_current_mentor),
    db: Session = Depends(get_db)
):
    """
    Create new lounge
    
    - Requires mentor role
    - Creates lounge for mentor
    """
    # Get mentor profile
    mentor = db.query(Mentor).filter(
        Mentor.user_id == current_user.id
    ).first()
    
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor profile not found"
        )
    
    # Check if slug already exists
    existing = db.query(Lounge).filter(
        Lounge.slug == lounge_data.slug
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lounge with this slug already exists"
        )
    
    # Verify category exists (if provided)
    if lounge_data.category_id:
        category = db.query(Category).filter(
            Category.id == lounge_data.category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Create lounge
    lounge = Lounge(
        mentor_id=mentor.id,
        title=lounge_data.title,
        slug=lounge_data.slug,
        description=lounge_data.description,
        category_id=lounge_data.category_id,
        access_type=lounge_data.access_type,
        plan_id=lounge_data.plan_id,
        max_members=lounge_data.max_members,
        is_public_listing=lounge_data.is_public_listing
    )
    
    db.add(lounge)
    db.commit()
    db.refresh(lounge)
    
    return LoungeResponse(
        id=lounge.id,
        mentor_id=lounge.mentor_id,
        title=lounge.title,
        slug=lounge.slug,
        description=lounge.description,
        category_id=lounge.category_id,
        access_type=lounge.access_type,
        plan_id=lounge.plan_id,
        max_members=lounge.max_members,
        is_public_listing=lounge.is_public_listing,
        profile_image_url=None,
        created_at=lounge.created_at,
        mentor_name=current_user.name,
        mentor_avatar=normalize_avatar_url(current_user.avatar_url),
        category_name=category.name,
        member_count=0,
        is_full=False,
        is_member=False
    )


@router.get("/{lounge_id}", response_model=LoungeResponse)
async def get_lounge(
    lounge_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Get lounge details
    
    - Public endpoint for public lounges
    - Returns detailed lounge information
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
    
    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )
    
    # Check access (public or member/mentor)
    if not lounge.is_public_listing:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check if user is member or mentor
        is_mentor = (lounge.mentor.user_id == current_user.id)
        is_member = db.query(LoungeMembership).filter(
            LoungeMembership.lounge_id == lounge_id,
            LoungeMembership.user_id == current_user.id,
            LoungeMembership.left_at.is_(None)
        ).first() is not None
        
        if not (is_mentor or is_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private lounge"
            )
    
    # Get stats
    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.left_at.is_(None)
    ).scalar()
    
    is_full = (lounge.max_members is not None and 
               member_count >= lounge.max_members)
    
    is_member = False
    if current_user:
        is_member = db.query(LoungeMembership).filter(
            LoungeMembership.lounge_id == lounge_id,
            LoungeMembership.user_id == current_user.id,
            LoungeMembership.left_at.is_(None)
        ).first() is not None

    profile_image_url = await get_profile_image_url(lounge, db)

    # Get pricing (import constants)
    from app.services.billing_service import LOUNGE_MONTHLY_PRICE_CENTS, LOUNGE_YEARLY_PRICE_CENTS

    return LoungeResponse(
        id=lounge.id,
        mentor_id=lounge.mentor_id,
        title=lounge.title,
        slug=lounge.slug,
        description=lounge.description,
        category_id=lounge.category_id,
        access_type=lounge.access_type,
        plan_id=lounge.plan_id,
        max_members=lounge.max_members,
        is_public_listing=lounge.is_public_listing,
        profile_image_url=profile_image_url,
        created_at=lounge.created_at,
        stripe_product_id=lounge.stripe_product_id,
        stripe_monthly_price_id=lounge.stripe_monthly_price_id,
        stripe_yearly_price_id=lounge.stripe_yearly_price_id,
        monthly_price=LOUNGE_MONTHLY_PRICE_CENTS if lounge.stripe_monthly_price_id else None,
        yearly_price=LOUNGE_YEARLY_PRICE_CENTS if lounge.stripe_yearly_price_id else None,
        mentor_name=lounge.mentor.user.name if lounge.mentor else None,
        mentor_avatar=normalize_avatar_url(lounge.mentor.user.avatar_url) if lounge.mentor else None,
        category_name=lounge.category.name if lounge.category else None,
        member_count=member_count,
        is_full=is_full,
        is_member=is_member
    )


@router.put("/{lounge_id}", response_model=LoungeResponse)
async def update_lounge(
    lounge_id: int,
    update_data: LoungeUpdate,
    current_user: User = Depends(get_current_mentor),
    db: Session = Depends(get_db)
):
    """
    Update lounge
    
    - Requires mentor role
    - Can only update own lounges
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
    
    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )
    
    # Check ownership
    mentor = db.query(Mentor).filter(
        Mentor.user_id == current_user.id
    ).first()
    
    if lounge.mentor_id != mentor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own lounges"
        )
    
    # Update fields
    if update_data.title is not None:
        lounge.title = update_data.title
    
    if update_data.description is not None:
        lounge.description = update_data.description
    
    if update_data.category_id is not None:
        # Verify category exists
        category = db.query(Category).filter(
            Category.id == update_data.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        lounge.category_id = update_data.category_id
    
    if update_data.access_type is not None:
        lounge.access_type = update_data.access_type
    
    if update_data.plan_id is not None:
        lounge.plan_id = update_data.plan_id
    
    if update_data.max_members is not None:
        lounge.max_members = update_data.max_members
    
    if update_data.is_public_listing is not None:
        lounge.is_public_listing = update_data.is_public_listing
    
    db.commit()
    db.refresh(lounge)

    # Get stats
    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.left_at.is_(None)
    ).scalar()

    is_full = (lounge.max_members is not None and
               member_count >= lounge.max_members)

    profile_image_url = await get_profile_image_url(lounge, db)

    return LoungeResponse(
        id=lounge.id,
        mentor_id=lounge.mentor_id,
        title=lounge.title,
        slug=lounge.slug,
        description=lounge.description,
        category_id=lounge.category_id,
        access_type=lounge.access_type,
        plan_id=lounge.plan_id,
        max_members=lounge.max_members,
        is_public_listing=lounge.is_public_listing,
        profile_image_url=profile_image_url,
        created_at=lounge.created_at,
        mentor_name=current_user.name,
        mentor_avatar=normalize_avatar_url(current_user.avatar_url),
        category_name=lounge.category.name if lounge.category else None,
        member_count=member_count,
        is_full=is_full,
        is_member=True
    )


@router.delete("/{lounge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lounge(
    lounge_id: int,
    current_user: User = Depends(get_current_mentor),
    db: Session = Depends(get_db)
):
    """
    Delete lounge
    
    - Requires mentor role
    - Can only delete own lounges
    - Removes all memberships and threads
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
    
    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )
    
    # Check ownership
    mentor = db.query(Mentor).filter(
        Mentor.user_id == current_user.id
    ).first()
    
    if lounge.mentor_id != mentor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own lounges"
        )
    
    db.delete(lounge)
    db.commit()
    
    return None


@router.post("/{lounge_id}/join", response_model=LoungeMemberResponse)
async def join_lounge(
    lounge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    join_request: Optional[JoinLoungeRequest] = None
):
    """
    Join lounge
    
    - Requires authenticated user
    - Checks capacity and access rules
    - Creates membership record
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
    
    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )
    
    # Check if already a member
    existing = db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.user_id == current_user.id,
        LoungeMembership.left_at.is_(None)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this lounge"
        )
    
    # Check capacity
    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.left_at.is_(None)
    ).scalar()
    
    if lounge.max_members and member_count >= lounge.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lounge is full"
        )
    
    # Check access type
    if lounge.access_type == AccessType.PAID:
        # TODO: Verify subscription/payment
        pass
    elif lounge.access_type == AccessType.INVITE_ONLY:
        # TODO: Verify invite code
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This lounge is invite-only"
        )
    
    # Create membership
    membership = LoungeMembership(
        lounge_id=lounge_id,
        user_id=current_user.id,
        role=MembershipRole.MEMBER
    )
    
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return LoungeMemberResponse(
        id=membership.id,
        lounge_id=membership.lounge_id,
        user_id=membership.user_id,
        role=membership.role,
        joined_at=membership.joined_at,
        left_at=membership.left_at,
        user_name=current_user.name,
        user_avatar=normalize_avatar_url(current_user.avatar_url),
        user_email=current_user.email
    )


@router.post("/{lounge_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_lounge(
    lounge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Leave lounge
    
    - Requires authenticated user
    - Marks membership as inactive
    """
    membership = db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.user_id == current_user.id,
        LoungeMembership.left_at.is_(None)
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a member of this lounge"
        )
    
    membership.left_at = datetime.utcnow()
    db.commit()
    
    return None


@router.get("/{lounge_id}/members", response_model=List[LoungeMemberResponse])
async def get_lounge_members(
    lounge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_left: bool = False
):
    """
    Get lounge members
    
    - Requires authentication
    - Must be member or mentor of lounge
    - Returns list of members
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()
    
    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )
    
    # Check if user has access (member or mentor)
    is_mentor = (lounge.mentor.user_id == current_user.id)
    is_member = db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.user_id == current_user.id,
        LoungeMembership.left_at.is_(None)
    ).first() is not None
    
    if not (is_mentor or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get members
    query = db.query(LoungeMembership).filter(
        LoungeMembership.lounge_id == lounge_id
    )
    
    if not include_left:
        query = query.filter(LoungeMembership.left_at.is_(None))
    
    memberships = query.offset(skip).limit(limit).all()
    
    result = []
    for membership in memberships:
        user = membership.user
        result.append(LoungeMemberResponse(
            id=membership.id,
            lounge_id=membership.lounge_id,
            user_id=membership.user_id,
            role=membership.role,
            joined_at=membership.joined_at,
            left_at=membership.left_at,
            user_name=user.name,
            user_avatar=normalize_avatar_url(user.avatar_url),
            user_email=user.email if is_mentor else None
        ))

    return result


@router.post("/{lounge_id}/profile-image", response_model=LoungeResponse)
async def upload_lounge_profile_image(
    lounge_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Upload profile image for a lounge

    - Requires admin role
    - Accepts image files (jpg, png, webp)
    - Returns updated lounge data
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Delete old profile image if exists
    if lounge.profile_image_id:
        try:
            from app.db.models.file import File as FileModel
            old_file = db.query(FileModel).filter(FileModel.id == lounge.profile_image_id).first()
            if old_file:
                await file_service.delete_file_by_path(old_file.storage_path)
                lounge.profile_image_id = None
                db.commit()
                db.delete(old_file)
                db.commit()
        except Exception:
            pass  # Ignore errors when deleting old image

    # Upload new image
    try:
        file_record = await file_service.upload_file(
            file=file,
            user_id=current_user.id,
            db=db,
            folder="lounges/profile_images"
        )

        # Update lounge with new profile image
        lounge.profile_image_id = file_record.id
        db.commit()
        db.refresh(lounge)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

    # Build response
    member_count = db.query(func.count(LoungeMembership.id)).filter(
        LoungeMembership.lounge_id == lounge_id,
        LoungeMembership.left_at.is_(None)
    ).scalar()

    is_full = (lounge.max_members is not None and
               member_count >= lounge.max_members)

    profile_image_url = await get_profile_image_url(lounge, db)

    return LoungeResponse(
        id=lounge.id,
        mentor_id=lounge.mentor_id,
        title=lounge.title,
        slug=lounge.slug,
        description=lounge.description,
        category_id=lounge.category_id,
        access_type=lounge.access_type,
        plan_id=lounge.plan_id,
        max_members=lounge.max_members,
        is_public_listing=lounge.is_public_listing,
        profile_image_url=profile_image_url,
        created_at=lounge.created_at,
        mentor_name=lounge.mentor.user.name if lounge.mentor else None,
        mentor_avatar=normalize_avatar_url(lounge.mentor.user.avatar_url) if lounge.mentor else None,
        category_name=lounge.category.name if lounge.category else None,
        member_count=member_count,
        is_full=is_full,
        is_member=False
    )


@router.delete("/{lounge_id}/profile-image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lounge_profile_image(
    lounge_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete profile image for a lounge

    - Requires admin role
    """
    lounge = db.query(Lounge).filter(Lounge.id == lounge_id).first()

    if not lounge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lounge not found"
        )

    if not lounge.profile_image_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lounge has no profile image"
        )

    # Get file record and delete
    from app.db.models.file import File as FileModel
    file_record = db.query(FileModel).filter(FileModel.id == lounge.profile_image_id).first()

    if file_record:
        try:
            await file_service.delete_file_by_path(file_record.storage_path)
        except Exception:
            pass

        # Remove reference from lounge
        lounge.profile_image_id = None
        db.commit()

        # Delete file record
        db.delete(file_record)
        db.commit()

    return None
