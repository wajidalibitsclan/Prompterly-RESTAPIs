"""
Landing page & dashboard API endpoints.
Handles testimonials, featured lounges, how-it-works, recommended lounges, and search.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List

from app.db.session import get_db
from app.core.jwt import get_current_active_user, get_current_admin, get_optional_current_user
from app.db.models.user import User
from app.db.models.misc import Testimonial, HowItWorksStep
from app.db.models.lounge import Lounge
from app.db.models.mentor import Mentor
from app.db.models.billing import LoungeSubscription, SubscriptionStatus
from app.core.timezone import now_naive

router = APIRouter()


# =============================================================================
# Landing Page — Testimonials
# =============================================================================

@router.get("/testimonials")
async def list_testimonials(db: Session = Depends(get_db)):
    """Get all published testimonials for the landing page."""
    testimonials = db.query(Testimonial).filter(
        Testimonial.is_published == True
    ).order_by(Testimonial.sort_order.asc()).all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "role": t.role,
            "content": t.content,
            "avatar_url": t.avatar_url,
            "rating": t.rating,
        }
        for t in testimonials
    ]


@router.post("/testimonials")
async def create_testimonial(
    name: str,
    content: str,
    role: Optional[str] = None,
    avatar_url: Optional[str] = None,
    rating: int = 5,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Create a testimonial (admin only)."""
    testimonial = Testimonial(
        name=name,
        role=role,
        content=content,
        avatar_url=avatar_url,
        rating=min(max(rating, 1), 5),
        sort_order=sort_order,
    )
    db.add(testimonial)
    db.commit()
    db.refresh(testimonial)
    return {"id": testimonial.id, "message": "Testimonial created"}


@router.delete("/testimonials/{testimonial_id}")
async def delete_testimonial(
    testimonial_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Delete a testimonial (admin only)."""
    t = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
    if not t:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Testimonial not found")
    db.delete(t)
    db.commit()
    return {"message": "Testimonial deleted"}


# =============================================================================
# Landing Page — Featured Lounges
# =============================================================================

@router.get("/featured-lounges")
async def get_featured_lounges(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get featured/highlighted lounges for the landing page."""
    lounges = db.query(Lounge).filter(
        Lounge.is_public_listing == True,
        Lounge.is_featured == True
    ).limit(limit).all()

    return [
        {
            "id": l.id,
            "title": l.title,
            "slug": l.slug,
            "description": l.description,
            "brand_color": l.brand_color,
            "access_type": l.access_type.value if l.access_type else None,
            "member_count": l.member_count,
            "mentor_name": l.mentor.user.name if l.mentor and l.mentor.user else None,
            "category_name": l.category.name if l.category else None,
        }
        for l in lounges
    ]


# =============================================================================
# Landing Page — How It Works
# =============================================================================

@router.get("/how-it-works")
async def get_how_it_works(db: Session = Depends(get_db)):
    """Get 'How it works' steps for the landing page."""
    steps = db.query(HowItWorksStep).filter(
        HowItWorksStep.is_published == True
    ).order_by(HowItWorksStep.step_number.asc()).all()

    return [
        {
            "id": s.id,
            "step_number": s.step_number,
            "title": s.title,
            "description": s.description,
            "icon_url": s.icon_url,
        }
        for s in steps
    ]


@router.post("/how-it-works")
async def create_how_it_works_step(
    step_number: int,
    title: str,
    description: str,
    icon_url: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Create a how-it-works step (admin only)."""
    step = HowItWorksStep(
        step_number=step_number,
        title=title,
        description=description,
        icon_url=icon_url,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return {"id": step.id, "message": "Step created"}


@router.delete("/how-it-works/{step_id}")
async def delete_how_it_works_step(
    step_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Delete a how-it-works step (admin only)."""
    s = db.query(HowItWorksStep).filter(HowItWorksStep.id == step_id).first()
    if not s:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(s)
    db.commit()
    return {"message": "Step deleted"}


# =============================================================================
# Dashboard — Recommended/Suggested Lounges
# =============================================================================

@router.get("/recommended-lounges")
async def get_recommended_lounges(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get suggested lounges for the user dashboard.

    Shows public lounges the user is NOT already subscribed to,
    prioritising featured and popular lounges.
    """
    # Get user's current subscribed lounge IDs
    subscribed_ids = [
        s.lounge_id for s in db.query(LoungeSubscription.lounge_id).filter(
            LoungeSubscription.user_id == current_user.id,
            LoungeSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        ).all()
    ]

    # Get lounges user is NOT subscribed to
    query = db.query(Lounge).filter(
        Lounge.is_public_listing == True,
    )
    if subscribed_ids:
        query = query.filter(~Lounge.id.in_(subscribed_ids))

    # Prioritise featured, then by member count
    lounges = query.order_by(
        Lounge.is_featured.desc(),
        Lounge.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": l.id,
            "title": l.title,
            "slug": l.slug,
            "description": l.description,
            "brand_color": l.brand_color,
            "access_type": l.access_type.value if l.access_type else None,
            "member_count": l.member_count,
            "mentor_name": l.mentor.user.name if l.mentor and l.mentor.user else None,
            "category_name": l.category.name if l.category else None,
        }
        for l in lounges
    ]


# =============================================================================
# Dashboard — Search
# =============================================================================

@router.get("/search")
async def dashboard_search(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Global search bar for the dashboard.
    Searches across lounges (title, description, mentor name, category).
    """
    search_term = f"%{q}%"

    lounges = db.query(Lounge).outerjoin(
        Mentor, Lounge.mentor_id == Mentor.id
    ).outerjoin(
        User, Mentor.user_id == User.id
    ).filter(
        Lounge.is_public_listing == True,
        or_(
            Lounge.title.ilike(search_term),
            Lounge.description.ilike(search_term),
            User.name.ilike(search_term),
        )
    ).limit(20).all()

    return {
        "query": q,
        "results": [
            {
                "id": l.id,
                "title": l.title,
                "slug": l.slug,
                "description": (l.description or "")[:150],
                "mentor_name": l.mentor.user.name if l.mentor and l.mentor.user else None,
                "brand_color": l.brand_color,
            }
            for l in lounges
        ],
        "total": len(lounges)
    }
