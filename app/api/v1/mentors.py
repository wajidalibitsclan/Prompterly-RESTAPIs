"""
Mentor API endpoints
Handles mentor applications, profiles, and discovery
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.jwt import (
    get_current_user,
    get_current_active_user,
    get_current_admin
)
from app.db.models.user import User, UserRole
from app.db.models.mentor import Mentor, MentorStatus, Category
from app.db.models.lounge import Lounge, LoungeMembership
from app.schemas.mentor import (
    MentorApplication,
    MentorUpdate,
    MentorResponse,
    MentorListResponse,
    MentorApproval,
    CategoryResponse,
    CategoryCreate
)

router = APIRouter()


@router.get("/", response_model=List[MentorListResponse])
async def list_mentors(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[MentorStatus] = None,
    search: Optional[str] = None,
    min_experience: Optional[int] = None
):
    """
    List all mentors
    
    - Public endpoint
    - Supports filtering by status, search, experience
    - Returns paginated results
    """
    query = db.query(Mentor).join(User)
    
    # Filter by status (default to approved for public listing)
    if status:
        query = query.filter(Mentor.status == status)
    else:
        query = query.filter(Mentor.status == MentorStatus.APPROVED)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Mentor.headline.ilike(search_term),
                Mentor.bio.ilike(search_term),
                User.name.ilike(search_term)
            )
        )
    
    # Experience filter
    if min_experience is not None:
        query = query.filter(Mentor.experience_years >= min_experience)
    
    mentors = query.offset(skip).limit(limit).all()
    
    # Build response with stats
    result = []
    for mentor in mentors:
        lounge_count = db.query(func.count(Lounge.id)).filter(
            Lounge.mentor_id == mentor.id
        ).scalar()
        
        result.append(MentorListResponse(
            id=mentor.id,
            user_id=mentor.user_id,
            headline=mentor.headline,
            experience_years=mentor.experience_years,
            status=mentor.status,
            user_name=mentor.user.name,
            user_avatar=mentor.user.avatar_url,
            total_lounges=lounge_count
        ))
    
    return result


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor(
    mentor_id: int,
    db: Session = Depends(get_db)
):
    """
    Get mentor details
    
    - Public endpoint
    - Returns detailed mentor profile
    """
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )
    
    # Get stats
    lounge_count = db.query(func.count(Lounge.id)).filter(
        Lounge.mentor_id == mentor.id
    ).scalar()
    
    member_count = db.query(func.count(LoungeMembership.id)).join(
        Lounge
    ).filter(
        Lounge.mentor_id == mentor.id,
        LoungeMembership.left_at.is_(None)
    ).scalar()
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        headline=mentor.headline,
        bio=mentor.bio,
        intro_video_url=mentor.intro_video_url,
        experience_years=mentor.experience_years,
        status=mentor.status,
        created_at=mentor.created_at,
        updated_at=mentor.updated_at,
        user_name=mentor.user.name,
        user_email=mentor.user.email if mentor.status == MentorStatus.APPROVED else None,
        user_avatar=mentor.user.avatar_url,
        total_lounges=lounge_count,
        total_members=member_count
    )


@router.post("/apply", response_model=MentorResponse, status_code=status.HTTP_201_CREATED)
async def apply_as_mentor(
    application: MentorApplication,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Apply to become a mentor
    
    - Requires authenticated user
    - Creates mentor profile with pending status
    - User can only have one mentor profile
    """
    # Check if user already has mentor profile
    existing_mentor = db.query(Mentor).filter(
        Mentor.user_id == current_user.id
    ).first()
    
    if existing_mentor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a mentor profile"
        )
    
    # Create mentor profile
    mentor = Mentor(
        user_id=current_user.id,
        headline=application.headline,
        bio=application.bio,
        intro_video_url=application.intro_video_url,
        experience_years=application.experience_years,
        status=MentorStatus.PENDING
    )
    
    db.add(mentor)
    db.commit()
    db.refresh(mentor)
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        headline=mentor.headline,
        bio=mentor.bio,
        intro_video_url=mentor.intro_video_url,
        experience_years=mentor.experience_years,
        status=mentor.status,
        created_at=mentor.created_at,
        updated_at=mentor.updated_at,
        user_name=current_user.name,
        user_email=current_user.email,
        user_avatar=current_user.avatar_url,
        total_lounges=0,
        total_members=0
    )


@router.put("/me", response_model=MentorResponse)
async def update_mentor_profile(
    update_data: MentorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update own mentor profile
    
    - Requires mentor role
    - Updates mentor information
    """
    mentor = db.query(Mentor).filter(
        Mentor.user_id == current_user.id
    ).first()
    
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found. Apply first."
        )
    
    # Update fields
    if update_data.headline is not None:
        mentor.headline = update_data.headline
    
    if update_data.bio is not None:
        mentor.bio = update_data.bio
    
    if update_data.intro_video_url is not None:
        mentor.intro_video_url = update_data.intro_video_url
    
    if update_data.experience_years is not None:
        mentor.experience_years = update_data.experience_years
    
    mentor.updated_at = now_naive()
    
    db.commit()
    db.refresh(mentor)
    
    # Get stats
    lounge_count = db.query(func.count(Lounge.id)).filter(
        Lounge.mentor_id == mentor.id
    ).scalar()
    
    member_count = db.query(func.count(LoungeMembership.id)).join(
        Lounge
    ).filter(
        Lounge.mentor_id == mentor.id,
        LoungeMembership.left_at.is_(None)
    ).scalar()
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        headline=mentor.headline,
        bio=mentor.bio,
        intro_video_url=mentor.intro_video_url,
        experience_years=mentor.experience_years,
        status=mentor.status,
        created_at=mentor.created_at,
        updated_at=mentor.updated_at,
        user_name=current_user.name,
        user_email=current_user.email,
        user_avatar=current_user.avatar_url,
        total_lounges=lounge_count,
        total_members=member_count
    )


@router.get("/{mentor_id}/lounges")
async def get_mentor_lounges(
    mentor_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get lounges by mentor
    
    - Public endpoint
    - Returns list of mentor's lounges
    """
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )
    
    lounges = db.query(Lounge).filter(
        Lounge.mentor_id == mentor_id,
        Lounge.is_public_listing == True
    ).offset(skip).limit(limit).all()
    
    return lounges


@router.patch("/{mentor_id}/approve", response_model=MentorResponse)
async def approve_mentor(
    mentor_id: int,
    approval: MentorApproval,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Approve or reject mentor application
    
    - Requires admin role
    - Updates mentor status
    - Upgrades user role if approved
    """
    mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
    
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )
    
    if mentor.status != MentorStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mentor is not pending (current status: {mentor.status})"
        )
    
    # Update mentor status
    if approval.approved:
        mentor.status = MentorStatus.APPROVED
        
        # Upgrade user role to mentor
        user = db.query(User).filter(User.id == mentor.user_id).first()
        user.role = UserRole.MENTOR
        
        # TODO: Send approval email
    else:
        mentor.status = MentorStatus.DISABLED
        # TODO: Send rejection email with feedback
    
    mentor.updated_at = now_naive()
    
    db.commit()
    db.refresh(mentor)
    
    user = mentor.user
    
    return MentorResponse(
        id=mentor.id,
        user_id=mentor.user_id,
        headline=mentor.headline,
        bio=mentor.bio,
        intro_video_url=mentor.intro_video_url,
        experience_years=mentor.experience_years,
        status=mentor.status,
        created_at=mentor.created_at,
        updated_at=mentor.updated_at,
        user_name=user.name,
        user_email=user.email,
        user_avatar=user.avatar_url,
        total_lounges=0,
        total_members=0
    )


# Category endpoints
@router.get("/categories/list", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """
    List all categories
    
    - Public endpoint
    - Returns all available categories
    """
    categories = db.query(Category).all()
    return categories


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create new category
    
    - Requires admin role
    - Creates category for lounge organization
    """
    # Check if slug already exists
    existing = db.query(Category).filter(
        Category.slug == category_data.slug
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists"
        )
    
    category = Category(
        name=category_data.name,
        slug=category_data.slug
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category
