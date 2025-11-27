"""
CMS API endpoints
Handles static pages and FAQs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.jwt import get_current_active_user, get_current_admin
from app.db.models.user import User
from app.db.models.misc import StaticPage, FAQ
from app.schemas.notification import (
    StaticPageResponse,
    StaticPageCreate,
    StaticPageUpdate,
    FAQResponse,
    FAQCreate,
    FAQUpdate
)

router = APIRouter()


# Static Pages
@router.get("/pages", response_model=List[StaticPageResponse])
async def list_pages(
    db: Session = Depends(get_db),
    published_only: bool = True
):
    """
    List static pages
    
    - Public endpoint
    - Returns published pages by default
    """
    query = db.query(StaticPage)
    
    if published_only:
        query = query.filter(StaticPage.is_published == True)
    
    pages = query.order_by(StaticPage.updated_at.desc()).all()
    
    return pages


@router.get("/pages/{slug}", response_model=StaticPageResponse)
async def get_page(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get page by slug
    
    - Public endpoint
    - Returns page content
    """
    page = db.query(StaticPage).filter(
        StaticPage.slug == slug,
        StaticPage.is_published == True
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    return page


@router.post("/pages", response_model=StaticPageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: StaticPageCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create static page
    
    - Requires admin role
    - Creates new page
    """
    # Check if slug exists
    existing = db.query(StaticPage).filter(
        StaticPage.slug == page_data.slug
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page with this slug already exists"
        )
    
    page = StaticPage(
        slug=page_data.slug,
        title=page_data.title,
        content=page_data.content,
        is_published=page_data.is_published
    )
    
    db.add(page)
    db.commit()
    db.refresh(page)
    
    return page


@router.put("/pages/{page_id}", response_model=StaticPageResponse)
async def update_page(
    page_id: int,
    update_data: StaticPageUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update static page
    
    - Requires admin role
    - Updates page content
    """
    page = db.query(StaticPage).filter(StaticPage.id == page_id).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    if update_data.title is not None:
        page.title = update_data.title
    
    if update_data.content is not None:
        page.content = update_data.content
    
    if update_data.is_published is not None:
        page.is_published = update_data.is_published
    
    page.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(page)
    
    return page


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete static page
    
    - Requires admin role
    - Deletes page permanently
    """
    page = db.query(StaticPage).filter(StaticPage.id == page_id).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    db.delete(page)
    db.commit()
    
    return None


# FAQs
@router.get("/faqs", response_model=List[FAQResponse])
async def list_faqs(
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """
    List FAQs
    
    - Public endpoint
    - Filter by category
    - Sorted by sort_order
    """
    query = db.query(FAQ)
    
    if category:
        query = query.filter(FAQ.category == category)
    
    faqs = query.order_by(FAQ.sort_order.asc()).all()
    
    return faqs


@router.get("/faqs/categories")
async def list_faq_categories(
    db: Session = Depends(get_db)
):
    """
    List FAQ categories
    
    - Public endpoint
    - Returns unique categories
    """
    categories = db.query(FAQ.category).distinct().all()
    
    return {"categories": [cat[0] for cat in categories]}


@router.post("/faqs", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_data: FAQCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Create FAQ
    
    - Requires admin role
    - Creates new FAQ entry
    """
    faq = FAQ(
        category=faq_data.category,
        question=faq_data.question,
        answer=faq_data.answer,
        sort_order=faq_data.sort_order
    )
    
    db.add(faq)
    db.commit()
    db.refresh(faq)
    
    return faq


@router.put("/faqs/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    update_data: FAQUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update FAQ
    
    - Requires admin role
    - Updates FAQ entry
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    if update_data.category is not None:
        faq.category = update_data.category
    
    if update_data.question is not None:
        faq.question = update_data.question
    
    if update_data.answer is not None:
        faq.answer = update_data.answer
    
    if update_data.sort_order is not None:
        faq.sort_order = update_data.sort_order
    
    db.commit()
    db.refresh(faq)
    
    return faq


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Delete FAQ
    
    - Requires admin role
    - Deletes FAQ permanently
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    db.delete(faq)
    db.commit()
    
    return None
