"""
Notes API endpoints
Handles note management, search, and time capsules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.jwt import get_current_active_user
from app.db.models.user import User
from app.db.models.note import Note, TimeCapsule, CapsuleStatus
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    TimeCapsuleCreate,
    TimeCapsuleUpdate,
    TimeCapsuleResponse,
    NoteSearchRequest
)
from app.services.note_service import note_service

router = APIRouter()


@router.get("")
async def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: int = Query(1, ge=1),
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID"),
    pinned_only: bool = False,
    tags: Optional[str] = None  # Comma-separated tags
):
    """
    List user's notes

    - Returns notes owned by current user
    - Supports filtering by lounge, pinned status and tags
    - Paginated results
    """
    query = db.query(Note).filter(Note.user_id == current_user.id)

    # Filter by lounge_id if provided
    if lounge_id is not None:
        query = query.filter(Note.lounge_id == lounge_id)

    if pinned_only:
        query = query.filter(Note.is_pinned == True)

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(',')]
        for tag in tag_list:
            query = query.filter(Note.tags.contains([tag]))

    # Get total count for pagination
    total = query.count()

    # Calculate offset from page
    offset = (page - 1) * limit

    # Order by newest first (descending), with pinned notes at top
    notes = query.order_by(
        Note.is_pinned.desc(),
        Note.updated_at.desc()
    ).offset(offset).limit(limit).all()

    items = []
    for note in notes:
        content_preview = note.content[:200] + "..." if len(note.content) > 200 else note.content
        word_count = len(note.content.split())

        items.append({
            "id": note.id,
            "user_id": note.user_id,
            "lounge_id": note.lounge_id,
            "section": note.section,  # Section for grouping
            "title": note.title,
            "content": note.content,  # Include full content for notebook display
            "is_pinned": note.is_pinned,
            "is_included_in_rag": note.is_included_in_rag,
            "tags": note.tags or [],
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "content_preview": content_preview,
            "word_count": word_count
        })

    # Calculate total pages
    pages = (total + limit - 1) // limit if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new note
    
    - Creates note for current user
    - Optionally include in RAG
    - Supports tags for organization
    """
    try:
        note = await note_service.create_note(
            user_id=current_user.id,
            lounge_id=note_data.lounge_id,
            section=note_data.section,
            title=note_data.title,
            content=note_data.content,
            db=db,
            is_pinned=note_data.is_pinned,
            is_included_in_rag=note_data.is_included_in_rag,
            tags=note_data.tags
        )

        word_count = len(note.content.split())

        return NoteResponse(
            id=note.id,
            user_id=note.user_id,
            lounge_id=note.lounge_id,
            title=note.title,
            content=note.content,
            is_pinned=note.is_pinned,
            is_included_in_rag=note.is_included_in_rag,
            tags=note.tags or [],
            created_at=note.created_at,
            updated_at=note.updated_at,
            word_count=word_count
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating note: {str(e)}"
        )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get note by ID
    
    - Returns note details
    - Only owner can access
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    word_count = len(note.content.split())

    return NoteResponse(
        id=note.id,
        user_id=note.user_id,
        lounge_id=note.lounge_id,
        title=note.title,
        content=note.content,
        is_pinned=note.is_pinned,
        is_included_in_rag=note.is_included_in_rag,
        tags=note.tags or [],
        created_at=note.created_at,
        updated_at=note.updated_at,
        word_count=word_count
    )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    update_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update note
    
    - Updates note details
    - Only owner can update
    """
    try:
        note = await note_service.update_note(
            note_id=note_id,
            user_id=current_user.id,
            db=db,
            title=update_data.title,
            content=update_data.content,
            is_pinned=update_data.is_pinned,
            is_included_in_rag=update_data.is_included_in_rag,
            tags=update_data.tags
        )
        
        word_count = len(note.content.split())

        return NoteResponse(
            id=note.id,
            user_id=note.user_id,
            lounge_id=note.lounge_id,
            title=note.title,
            content=note.content,
            is_pinned=note.is_pinned,
            is_included_in_rag=note.is_included_in_rag,
            tags=note.tags or [],
            created_at=note.created_at,
            updated_at=note.updated_at,
            word_count=word_count
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete note
    
    - Deletes note permanently
    - Only owner can delete
    """
    try:
        await note_service.delete_note(
            note_id=note_id,
            user_id=current_user.id,
            db=db
        )
        return None
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/search", response_model=List[NoteListResponse])
async def search_notes(
    search_request: NoteSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search notes
    
    - Full-text search in title and content
    - Filter by tags
    - Returns matching notes
    """
    try:
        notes = await note_service.search_notes(
            user_id=current_user.id,
            query=search_request.query,
            db=db,
            tags=search_request.tags,
            limit=search_request.limit
        )
        
        result = []
        for note in notes:
            if search_request.include_content:
                content_preview = note.content[:200] + "..." if len(note.content) > 200 else note.content
            else:
                content_preview = ""
            
            word_count = len(note.content.split())
            
            result.append(NoteListResponse(
                id=note.id,
                user_id=note.user_id,
                title=note.title,
                is_pinned=note.is_pinned,
                is_included_in_rag=note.is_included_in_rag,
                tags=note.tags or [],
                created_at=note.created_at,
                updated_at=note.updated_at,
                content_preview=content_preview,
                word_count=word_count
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching notes: {str(e)}"
        )


@router.get("/sections/list", response_model=List[str])
async def get_sections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID")
):
    """
    Get distinct sections for user's notes

    - Returns list of unique section names
    - Excludes null/empty sections
    - Optionally filter by lounge
    """
    query = db.query(Note.section).filter(
        Note.user_id == current_user.id,
        Note.section.isnot(None),
        Note.section != ''
    )

    if lounge_id is not None:
        query = query.filter(Note.lounge_id == lounge_id)

    sections = query.distinct().order_by(Note.section.asc()).all()

    return [s[0] for s in sections]


@router.get("/pinned/list", response_model=List[NoteListResponse])
async def get_pinned_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get pinned notes

    - Returns all pinned notes
    - Sorted by update date
    """
    try:
        notes = await note_service.get_pinned_notes(
            user_id=current_user.id,
            db=db
        )
        
        result = []
        for note in notes:
            content_preview = note.content[:200] + "..." if len(note.content) > 200 else note.content
            word_count = len(note.content.split())
            
            result.append(NoteListResponse(
                id=note.id,
                user_id=note.user_id,
                title=note.title,
                is_pinned=note.is_pinned,
                is_included_in_rag=note.is_included_in_rag,
                tags=note.tags or [],
                created_at=note.created_at,
                updated_at=note.updated_at,
                content_preview=content_preview,
                word_count=word_count
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pinned notes: {str(e)}"
        )


# Time Capsule endpoints
@router.get("/capsules/list", response_model=List[TimeCapsuleResponse])
async def list_capsules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = None,
    lounge_id: Optional[int] = None
):
    """
    List time capsules

    - Returns user's time capsules
    - Filter by status (locked/unlocked)
    - Filter by lounge_id (required for lounge-specific capsules)
    """
    try:
        capsule_status = CapsuleStatus(status) if status else None
        capsules = await note_service.get_user_capsules(
            user_id=current_user.id,
            db=db,
            status=capsule_status,
            lounge_id=lounge_id
        )

        result = []
        for capsule in capsules:
            is_unlocked = capsule.status == CapsuleStatus.UNLOCKED
            days_until = note_service.get_capsule_days_until_unlock(capsule)

            result.append(TimeCapsuleResponse(
                id=capsule.id,
                user_id=capsule.user_id,
                lounge_id=capsule.lounge_id,
                lounge_name=capsule.lounge.title if capsule.lounge else None,
                title=capsule.title,
                content=capsule.content if is_unlocked else None,
                unlock_at=capsule.unlock_at,
                status=capsule.status.value,
                created_at=capsule.created_at,
                updated_at=capsule.updated_at,
                is_unlocked=is_unlocked,
                days_until_unlock=days_until,
                can_view_content=is_unlocked
            ))

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching capsules: {str(e)}"
        )


@router.post("/capsules", response_model=TimeCapsuleResponse, status_code=status.HTTP_201_CREATED)
async def create_capsule(
    capsule_data: TimeCapsuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create time capsule

    - Creates locked capsule for future
    - Will auto-unlock at specified date
    - Can optionally be associated with a lounge
    """
    try:
        capsule = await note_service.create_time_capsule(
            user_id=current_user.id,
            title=capsule_data.title,
            content=capsule_data.content,
            unlock_at=capsule_data.unlock_at,
            lounge_id=capsule_data.lounge_id,
            db=db
        )

        days_until = note_service.get_capsule_days_until_unlock(capsule)

        return TimeCapsuleResponse(
            id=capsule.id,
            user_id=capsule.user_id,
            lounge_id=capsule.lounge_id,
            lounge_name=capsule.lounge.title if capsule.lounge else None,
            title=capsule.title,
            content=None,  # Hidden until unlocked
            unlock_at=capsule.unlock_at,
            status=capsule.status.value,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
            is_unlocked=False,
            days_until_unlock=days_until,
            can_view_content=False
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/capsules/{capsule_id}", response_model=TimeCapsuleResponse)
async def get_capsule(
    capsule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get time capsule

    - Returns capsule details
    - Content only shown if unlocked
    """
    capsule = db.query(TimeCapsule).filter(
        TimeCapsule.id == capsule_id,
        TimeCapsule.user_id == current_user.id
    ).first()

    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time capsule not found"
        )

    is_unlocked = capsule.status == CapsuleStatus.UNLOCKED
    days_until = note_service.get_capsule_days_until_unlock(capsule)

    return TimeCapsuleResponse(
        id=capsule.id,
        user_id=capsule.user_id,
        lounge_id=capsule.lounge_id,
        lounge_name=capsule.lounge.title if capsule.lounge else None,
        title=capsule.title,
        content=capsule.content if is_unlocked else None,
        unlock_at=capsule.unlock_at,
        status=capsule.status.value,
        created_at=capsule.created_at,
        updated_at=capsule.updated_at,
        is_unlocked=is_unlocked,
        days_until_unlock=days_until,
        can_view_content=is_unlocked
    )


@router.put("/capsules/{capsule_id}", response_model=TimeCapsuleResponse)
async def update_capsule(
    capsule_id: int,
    update_data: TimeCapsuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update time capsule

    - Can only update locked capsules
    - Once unlocked, capsules are immutable
    """
    try:
        capsule = await note_service.update_capsule(
            capsule_id=capsule_id,
            user_id=current_user.id,
            db=db,
            title=update_data.title,
            content=update_data.content,
            unlock_at=update_data.unlock_at
        )

        days_until = note_service.get_capsule_days_until_unlock(capsule)

        return TimeCapsuleResponse(
            id=capsule.id,
            user_id=capsule.user_id,
            lounge_id=capsule.lounge_id,
            lounge_name=capsule.lounge.title if capsule.lounge else None,
            title=capsule.title,
            content=None,
            unlock_at=capsule.unlock_at,
            status=capsule.status.value,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
            is_unlocked=False,
            days_until_unlock=days_until,
            can_view_content=False
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/capsules/{capsule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capsule(
    capsule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete time capsule

    - Permanently deletes capsule
    - Works for both locked and unlocked
    """
    try:
        await note_service.delete_capsule(
            capsule_id=capsule_id,
            user_id=current_user.id,
            db=db
        )
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/capsules/{capsule_id}/unlock", response_model=TimeCapsuleResponse)
async def unlock_capsule(
    capsule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually unlock a time capsule

    - Only works if unlock time has passed
    - Changes status from locked to unlocked
    """
    try:
        capsule = await note_service.unlock_single_capsule(
            capsule_id=capsule_id,
            user_id=current_user.id,
            db=db
        )

        return TimeCapsuleResponse(
            id=capsule.id,
            user_id=capsule.user_id,
            lounge_id=capsule.lounge_id,
            lounge_name=capsule.lounge.title if capsule.lounge else None,
            title=capsule.title,
            content=capsule.content,
            unlock_at=capsule.unlock_at,
            status=capsule.status.value,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
            is_unlocked=True,
            days_until_unlock=None,
            can_view_content=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
