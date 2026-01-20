"""
Knowledge Base API endpoints
Admin-only endpoints for managing KB content (prompts, documents, FAQs)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.jwt import get_current_admin
from app.db.models.user import User
from app.services.knowledge_base_service import knowledge_base_service
from app.services import file_service
from app.schemas.knowledge_base import (
    # Category
    KBCategoryCreate, KBCategoryUpdate, KBCategoryResponse,
    # Prompt
    KBPromptCreate, KBPromptUpdate, KBPromptResponse, PaginatedPromptsResponse,
    # Document
    KBDocumentUpdate, KBDocumentResponse, PaginatedDocumentsResponse,
    # FAQ
    KBFaqCreate, KBFaqUpdate, KBFaqResponse, PaginatedFaqsResponse,
    # Search
    KBSearchRequest, KBSearchResponse, KBSearchResultItem,
    KBRAGContextRequest, KBRAGContextResponse, KBRAGContextSource,
    # Stats
    KBStatsResponse
)

router = APIRouter()


def get_mentor_name(item) -> Optional[str]:
    """Helper to get mentor name from a KB item's lounge"""
    if item.lounge and item.lounge.mentor and item.lounge.mentor.user:
        return item.lounge.mentor.user.name
    return None


async def get_lounge_image(item, db: Session) -> Optional[str]:
    """Helper to get lounge profile image URL from a KB item's lounge"""
    if item.lounge and item.lounge.profile_image_id:
        try:
            return await file_service.get_file_url(item.lounge.profile_image_id, db)
        except Exception:
            return None
    return None


def get_mentor_image(item) -> Optional[str]:
    """Helper to get mentor profile image URL from a KB item's lounge"""
    if item.lounge and item.lounge.mentor and item.lounge.mentor.user:
        return item.lounge.mentor.user.avatar_url
    return None


# ============== Categories ==============

@router.get("/categories", response_model=List[KBCategoryResponse])
async def list_categories(
    include_inactive: bool = False,
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID (null = global only)"),
    include_global: bool = Query(True, description="Include global categories when lounge_id is set"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List all KB categories (admin only)"""
    categories = await knowledge_base_service.get_categories(
        db, include_inactive, lounge_id, include_global
    )

    result = []
    for cat in categories:
        counts = knowledge_base_service.get_category_counts(db, cat)
        result.append(KBCategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            lounge_id=cat.lounge_id,
            lounge_name=cat.lounge.title if cat.lounge else None,
            mentor_name=get_mentor_name(cat),
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            prompt_count=counts["prompt_count"],
            document_count=counts["document_count"],
            faq_count=counts["faq_count"]
        ))

    return result


@router.post("/categories", response_model=KBCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: KBCategoryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Create a new KB category (admin only)"""
    category = await knowledge_base_service.create_category(db, data.model_dump())
    db.refresh(category)  # Refresh to get lounge relationship
    return KBCategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        is_active=category.is_active,
        lounge_id=category.lounge_id,
        lounge_name=category.lounge.title if category.lounge else None,
        mentor_name=get_mentor_name(category),
        created_at=category.created_at,
        updated_at=category.updated_at,
        prompt_count=0,
        document_count=0,
        faq_count=0
    )


@router.get("/categories/{category_id}", response_model=KBCategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get a specific KB category (admin only)"""
    category = await knowledge_base_service.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    counts = knowledge_base_service.get_category_counts(db, category)
    return KBCategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        is_active=category.is_active,
        lounge_id=category.lounge_id,
        lounge_name=category.lounge.title if category.lounge else None,
        mentor_name=get_mentor_name(category),
        created_at=category.created_at,
        updated_at=category.updated_at,
        **counts
    )


@router.put("/categories/{category_id}", response_model=KBCategoryResponse)
async def update_category(
    category_id: int,
    data: KBCategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Update a KB category (admin only)"""
    category = await knowledge_base_service.update_category(
        db, category_id, data.model_dump(exclude_unset=True)
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.refresh(category)  # Refresh to get lounge relationship
    counts = knowledge_base_service.get_category_counts(db, category)
    return KBCategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        is_active=category.is_active,
        lounge_id=category.lounge_id,
        lounge_name=category.lounge.title if category.lounge else None,
        mentor_name=get_mentor_name(category),
        created_at=category.created_at,
        updated_at=category.updated_at,
        **counts
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Delete a KB category (admin only)"""
    success = await knowledge_base_service.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")


# ============== Prompts ==============

@router.get("/prompts", response_model=PaginatedPromptsResponse)
async def list_prompts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID (null = global only)"),
    include_global: bool = Query(True, description="Include global prompts when lounge_id is set"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List KB prompts with pagination and filters (admin only)"""
    prompts, total = await knowledge_base_service.get_prompts_paginated(
        db, page, limit, category_id, search, is_active, lounge_id, include_global
    )
    pages = (total + limit - 1) // limit if total > 0 else 1

    items = []
    for p in prompts:
        lounge_image = await get_lounge_image(p, db)
        items.append(KBPromptResponse(
            id=p.id,
            title=p.title,
            content=p.content,
            description=p.description,
            tags=p.tags,
            is_active=p.is_active,
            is_included_in_rag=p.is_included_in_rag,
            usage_count=p.usage_count,
            has_embedding=p.embedding is not None,
            created_at=p.created_at,
            updated_at=p.updated_at,
            category_id=p.category_id,
            category_name=p.category.name if p.category else None,
            lounge_id=p.lounge_id,
            lounge_name=p.lounge.title if p.lounge else None,
            lounge_image=lounge_image,
            mentor_name=get_mentor_name(p),
            mentor_image=get_mentor_image(p),
            created_by_name=p.created_by.name if p.created_by else None
        ))

    return PaginatedPromptsResponse(
        items=items, total=total, page=page, limit=limit, pages=pages
    )


@router.post("/prompts", status_code=status.HTTP_201_CREATED)
async def create_prompt(
    data: KBPromptCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Create a new KB prompt (admin only)"""
    from app.services.background_task_service import background_task_service
    from app.db.models.background_job import JobType
    from app.db.session import SessionLocal

    prompt = await knowledge_base_service.create_prompt(
        db, data.model_dump(), admin_user.id, skip_embedding=True  # Skip sync embedding
    )
    db.refresh(prompt)

    # Start background job for embedding if RAG is enabled
    job_id = None
    if prompt.is_included_in_rag:
        job = background_task_service.create_job(
            db=db,
            job_type=JobType.PROMPT_EMBEDDING,
            entity_type="prompt",
            entity_id=prompt.id,
            created_by_id=admin_user.id,
            total_steps=3
        )
        job_id = job.id

        # Start background task
        background_task_service.start_background_task(
            db_session_factory=SessionLocal,
            job_id=job.id,
            job_type=JobType.PROMPT_EMBEDDING,
            entity_id=prompt.id
        )

    lounge_image = await get_lounge_image(prompt, db)
    return {
        "prompt": {
            "id": prompt.id,
            "title": prompt.title,
            "content": prompt.content,
            "description": prompt.description,
            "tags": prompt.tags,
            "is_active": prompt.is_active,
            "is_included_in_rag": prompt.is_included_in_rag,
            "usage_count": prompt.usage_count,
            "has_embedding": prompt.embedding is not None,
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
            "category_id": prompt.category_id,
            "category_name": prompt.category.name if prompt.category else None,
            "lounge_id": prompt.lounge_id,
            "lounge_name": prompt.lounge.title if prompt.lounge else None,
            "lounge_image": lounge_image,
            "mentor_name": get_mentor_name(prompt),
            "mentor_image": get_mentor_image(prompt),
            "created_by_name": admin_user.name
        },
        "job_id": job_id
    }


@router.get("/prompts/{prompt_id}", response_model=KBPromptResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get a specific KB prompt (admin only)"""
    prompt = await knowledge_base_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    lounge_image = await get_lounge_image(prompt, db)
    return KBPromptResponse(
        id=prompt.id,
        title=prompt.title,
        content=prompt.content,
        description=prompt.description,
        tags=prompt.tags,
        is_active=prompt.is_active,
        is_included_in_rag=prompt.is_included_in_rag,
        usage_count=prompt.usage_count,
        has_embedding=prompt.embedding is not None,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        category_id=prompt.category_id,
        category_name=prompt.category.name if prompt.category else None,
        lounge_id=prompt.lounge_id,
        lounge_name=prompt.lounge.title if prompt.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(prompt),
        mentor_image=get_mentor_image(prompt),
        created_by_name=prompt.created_by.name if prompt.created_by else None
    )


@router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    data: KBPromptUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Update a KB prompt (admin only)"""
    from app.services.background_task_service import background_task_service
    from app.db.models.background_job import JobType
    from app.db.session import SessionLocal
    from app.db.models.knowledge_base import KBPrompt

    # Get original prompt to check if content changed
    original_prompt = db.query(KBPrompt).filter(KBPrompt.id == prompt_id).first()
    if not original_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    original_content = original_prompt.content
    original_title = original_prompt.title

    # Update the prompt
    prompt = await knowledge_base_service.update_prompt(
        db, prompt_id, data.model_dump(exclude_unset=True)
    )
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    db.refresh(prompt)

    # Check if we need to regenerate embedding
    job_id = None
    content_changed = (original_content != prompt.content) or (original_title != prompt.title)

    if prompt.is_included_in_rag and content_changed:
        # Clear existing embedding since content changed
        prompt.embedding = None
        db.commit()

        # Create background job for embedding regeneration
        job = background_task_service.create_job(
            db=db,
            job_type=JobType.PROMPT_EMBEDDING,
            entity_type="prompt",
            entity_id=prompt.id,
            created_by_id=admin_user.id,
            total_steps=3
        )
        job_id = job.id

        # Start background task
        background_task_service.start_background_task(
            db_session_factory=SessionLocal,
            job_id=job.id,
            job_type=JobType.PROMPT_EMBEDDING,
            entity_id=prompt.id
        )

    lounge_image = await get_lounge_image(prompt, db)
    return {
        "prompt": {
            "id": prompt.id,
            "title": prompt.title,
            "content": prompt.content,
            "description": prompt.description,
            "tags": prompt.tags,
            "is_active": prompt.is_active,
            "is_included_in_rag": prompt.is_included_in_rag,
            "usage_count": prompt.usage_count,
            "has_embedding": prompt.embedding is not None,
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
            "category_id": prompt.category_id,
            "category_name": prompt.category.name if prompt.category else None,
            "lounge_id": prompt.lounge_id,
            "lounge_name": prompt.lounge.title if prompt.lounge else None,
            "lounge_image": lounge_image,
            "mentor_name": get_mentor_name(prompt),
            "mentor_image": get_mentor_image(prompt),
            "created_by_name": prompt.created_by.name if prompt.created_by else None
        },
        "job_id": job_id
    }


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Delete a KB prompt (admin only)"""
    success = await knowledge_base_service.delete_prompt(db, prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")


@router.post("/prompts/{prompt_id}/regenerate-embedding", response_model=KBPromptResponse)
async def regenerate_prompt_embedding(
    prompt_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Regenerate embedding for a prompt (admin only)"""
    prompt = await knowledge_base_service.regenerate_prompt_embedding(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    lounge_image = await get_lounge_image(prompt, db)
    return KBPromptResponse(
        id=prompt.id,
        title=prompt.title,
        content=prompt.content,
        description=prompt.description,
        tags=prompt.tags,
        is_active=prompt.is_active,
        is_included_in_rag=prompt.is_included_in_rag,
        usage_count=prompt.usage_count,
        has_embedding=prompt.embedding is not None,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        category_id=prompt.category_id,
        category_name=prompt.category.name if prompt.category else None,
        lounge_id=prompt.lounge_id,
        lounge_name=prompt.lounge.title if prompt.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(prompt),
        mentor_image=get_mentor_image(prompt),
        created_by_name=prompt.created_by.name if prompt.created_by else None
    )


# ============== Documents ==============

@router.get("/documents", response_model=PaginatedDocumentsResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_processed: Optional[bool] = None,
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID (null = global only)"),
    include_global: bool = Query(True, description="Include global documents when lounge_id is set"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List KB documents with pagination and filters (admin only)"""
    documents, total = await knowledge_base_service.get_documents_paginated(
        db, page, limit, category_id, search, is_active, is_processed, lounge_id, include_global
    )
    pages = (total + limit - 1) // limit if total > 0 else 1

    items = []
    for d in documents:
        lounge_image = await get_lounge_image(d, db)
        items.append(KBDocumentResponse(
            id=d.id,
            title=d.title,
            description=d.description,
            original_filename=d.original_filename,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            tags=d.tags,
            is_active=d.is_active,
            is_processed=d.is_processed,
            processing_error=d.processing_error,
            summary=d.summary,
            has_embedding=d.embedding is not None,
            chunk_count=len(d.chunks) if d.chunks else 0,
            created_at=d.created_at,
            updated_at=d.updated_at,
            category_id=d.category_id,
            category_name=d.category.name if d.category else None,
            lounge_id=d.lounge_id,
            lounge_name=d.lounge.title if d.lounge else None,
            lounge_image=lounge_image,
            mentor_name=get_mentor_name(d),
            mentor_image=get_mentor_image(d),
            created_by_name=d.created_by.name if d.created_by else None
        ))

    return PaginatedDocumentsResponse(
        items=items, total=total, page=page, limit=limit, pages=pages
    )


@router.post("/documents", response_model=KBDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    lounge_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Upload a new KB document (admin only)"""
    # Validate file type
    allowed_types = ['pdf', 'txt', 'docx']
    file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    data = {
        "title": title,
        "description": description,
        "category_id": category_id,
        "lounge_id": lounge_id,
        "tags": tags.split(',') if tags else None
    }

    document = await knowledge_base_service.create_document(
        db, file, data, admin_user.id
    )
    db.refresh(document)  # Refresh to get lounge relationship

    lounge_image = await get_lounge_image(document, db)
    return KBDocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        tags=document.tags,
        is_active=document.is_active,
        is_processed=document.is_processed,
        processing_error=document.processing_error,
        summary=document.summary,
        has_embedding=document.embedding is not None,
        chunk_count=len(document.chunks) if document.chunks else 0,
        created_at=document.created_at,
        updated_at=document.updated_at,
        category_id=document.category_id,
        category_name=document.category.name if document.category else None,
        lounge_id=document.lounge_id,
        lounge_name=document.lounge.title if document.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(document),
        mentor_image=get_mentor_image(document),
        created_by_name=admin_user.name
    )


@router.get("/documents/{document_id}", response_model=KBDocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get a specific KB document (admin only)"""
    document = await knowledge_base_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    lounge_image = await get_lounge_image(document, db)
    return KBDocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        tags=document.tags,
        is_active=document.is_active,
        is_processed=document.is_processed,
        processing_error=document.processing_error,
        summary=document.summary,
        has_embedding=document.embedding is not None,
        chunk_count=len(document.chunks) if document.chunks else 0,
        created_at=document.created_at,
        updated_at=document.updated_at,
        category_id=document.category_id,
        category_name=document.category.name if document.category else None,
        lounge_id=document.lounge_id,
        lounge_name=document.lounge.title if document.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(document),
        mentor_image=get_mentor_image(document),
        created_by_name=document.created_by.name if document.created_by else None
    )


@router.put("/documents/{document_id}", response_model=KBDocumentResponse)
async def update_document(
    document_id: int,
    data: KBDocumentUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Update a KB document metadata (admin only)"""
    document = await knowledge_base_service.update_document(
        db, document_id, data.model_dump(exclude_unset=True)
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    db.refresh(document)  # Refresh to get lounge relationship
    lounge_image = await get_lounge_image(document, db)
    return KBDocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        tags=document.tags,
        is_active=document.is_active,
        is_processed=document.is_processed,
        processing_error=document.processing_error,
        summary=document.summary,
        has_embedding=document.embedding is not None,
        chunk_count=len(document.chunks) if document.chunks else 0,
        created_at=document.created_at,
        updated_at=document.updated_at,
        category_id=document.category_id,
        category_name=document.category.name if document.category else None,
        lounge_id=document.lounge_id,
        lounge_name=document.lounge.title if document.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(document),
        mentor_image=get_mentor_image(document),
        created_by_name=document.created_by.name if document.created_by else None
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Delete a KB document (admin only)"""
    success = await knowledge_base_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/documents/{document_id}/reprocess", response_model=KBDocumentResponse)
async def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Reprocess a document (extract text, generate embeddings) (admin only)"""
    document = await knowledge_base_service.reprocess_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    lounge_image = await get_lounge_image(document, db)
    return KBDocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        tags=document.tags,
        is_active=document.is_active,
        is_processed=document.is_processed,
        processing_error=document.processing_error,
        summary=document.summary,
        has_embedding=document.embedding is not None,
        chunk_count=len(document.chunks) if document.chunks else 0,
        created_at=document.created_at,
        updated_at=document.updated_at,
        category_id=document.category_id,
        category_name=document.category.name if document.category else None,
        lounge_id=document.lounge_id,
        lounge_name=document.lounge.title if document.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(document),
        mentor_image=get_mentor_image(document),
        created_by_name=document.created_by.name if document.created_by else None
    )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get download URL for document (admin only)"""
    url = await knowledge_base_service.get_document_download_url(db, document_id)
    if not url:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"download_url": url}


# ============== FAQs ==============

@router.get("/faqs", response_model=PaginatedFaqsResponse)
async def list_faqs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    lounge_id: Optional[int] = Query(None, description="Filter by lounge ID (null = global only)"),
    include_global: bool = Query(True, description="Include global FAQs when lounge_id is set"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List KB FAQs with pagination and filters (admin only)"""
    faqs, total = await knowledge_base_service.get_faqs_paginated(
        db, page, limit, category_id, search, is_active, lounge_id, include_global
    )
    pages = (total + limit - 1) // limit if total > 0 else 1

    items = []
    for f in faqs:
        lounge_image = await get_lounge_image(f, db)
        items.append(KBFaqResponse(
            id=f.id,
            question=f.question,
            answer=f.answer,
            tags=f.tags,
            sort_order=f.sort_order,
            is_active=f.is_active,
            is_included_in_rag=f.is_included_in_rag,
            view_count=f.view_count,
            helpful_count=f.helpful_count,
            not_helpful_count=f.not_helpful_count,
            has_embedding=f.embedding is not None,
            created_at=f.created_at,
            updated_at=f.updated_at,
            category_id=f.category_id,
            category_name=f.category.name if f.category else None,
            lounge_id=f.lounge_id,
            lounge_name=f.lounge.title if f.lounge else None,
            lounge_image=lounge_image,
            mentor_name=get_mentor_name(f),
            mentor_image=get_mentor_image(f),
            created_by_name=f.created_by.name if f.created_by else None
        ))

    return PaginatedFaqsResponse(
        items=items, total=total, page=page, limit=limit, pages=pages
    )


@router.post("/faqs", response_model=KBFaqResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    data: KBFaqCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Create a new KB FAQ (admin only)"""
    faq = await knowledge_base_service.create_faq(db, data.model_dump(), admin_user.id)
    db.refresh(faq)  # Refresh to get lounge relationship
    lounge_image = await get_lounge_image(faq, db)
    return KBFaqResponse(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        tags=faq.tags,
        sort_order=faq.sort_order,
        is_active=faq.is_active,
        is_included_in_rag=faq.is_included_in_rag,
        view_count=faq.view_count,
        helpful_count=faq.helpful_count,
        not_helpful_count=faq.not_helpful_count,
        has_embedding=faq.embedding is not None,
        created_at=faq.created_at,
        updated_at=faq.updated_at,
        category_id=faq.category_id,
        category_name=faq.category.name if faq.category else None,
        lounge_id=faq.lounge_id,
        lounge_name=faq.lounge.title if faq.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(faq),
        mentor_image=get_mentor_image(faq),
        created_by_name=admin_user.name
    )


@router.get("/faqs/{faq_id}", response_model=KBFaqResponse)
async def get_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get a specific KB FAQ (admin only)"""
    faq = await knowledge_base_service.get_faq(db, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    lounge_image = await get_lounge_image(faq, db)
    return KBFaqResponse(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        tags=faq.tags,
        sort_order=faq.sort_order,
        is_active=faq.is_active,
        is_included_in_rag=faq.is_included_in_rag,
        view_count=faq.view_count,
        helpful_count=faq.helpful_count,
        not_helpful_count=faq.not_helpful_count,
        has_embedding=faq.embedding is not None,
        created_at=faq.created_at,
        updated_at=faq.updated_at,
        category_id=faq.category_id,
        category_name=faq.category.name if faq.category else None,
        lounge_id=faq.lounge_id,
        lounge_name=faq.lounge.title if faq.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(faq),
        mentor_image=get_mentor_image(faq),
        created_by_name=faq.created_by.name if faq.created_by else None
    )


@router.put("/faqs/{faq_id}", response_model=KBFaqResponse)
async def update_faq(
    faq_id: int,
    data: KBFaqUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Update a KB FAQ (admin only)"""
    faq = await knowledge_base_service.update_faq(
        db, faq_id, data.model_dump(exclude_unset=True)
    )
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.refresh(faq)  # Refresh to get lounge relationship
    lounge_image = await get_lounge_image(faq, db)
    return KBFaqResponse(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        tags=faq.tags,
        sort_order=faq.sort_order,
        is_active=faq.is_active,
        is_included_in_rag=faq.is_included_in_rag,
        view_count=faq.view_count,
        helpful_count=faq.helpful_count,
        not_helpful_count=faq.not_helpful_count,
        has_embedding=faq.embedding is not None,
        created_at=faq.created_at,
        updated_at=faq.updated_at,
        category_id=faq.category_id,
        category_name=faq.category.name if faq.category else None,
        lounge_id=faq.lounge_id,
        lounge_name=faq.lounge.title if faq.lounge else None,
        lounge_image=lounge_image,
        mentor_name=get_mentor_name(faq),
        mentor_image=get_mentor_image(faq),
        created_by_name=faq.created_by.name if faq.created_by else None
    )


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Delete a KB FAQ (admin only)"""
    success = await knowledge_base_service.delete_faq(db, faq_id)
    if not success:
        raise HTTPException(status_code=404, detail="FAQ not found")


# ============== Search & RAG ==============

@router.post("/search", response_model=KBSearchResponse)
async def search_knowledge_base(
    data: KBSearchRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Search across all KB entities (admin only)"""
    results = await knowledge_base_service.semantic_search(
        db=db,
        query=data.query,
        entity_types=data.entity_types,
        category_ids=data.category_ids,
        limit=data.limit,
        lounge_id=data.lounge_id,
        include_global=data.include_global
    )

    return KBSearchResponse(
        query=data.query,
        results=[KBSearchResultItem(**r) for r in results],
        total_results=len(results)
    )


@router.post("/rag-context", response_model=KBRAGContextResponse)
async def get_rag_context(
    data: KBRAGContextRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get RAG context for a query (admin only - for testing)"""
    context, sources = await knowledge_base_service.get_rag_context(
        db=db,
        query=data.query,
        max_items=data.max_items,
        entity_types=data.entity_types,
        lounge_id=data.lounge_id,
        include_global=data.include_global
    )

    return KBRAGContextResponse(
        context=context,
        sources=[KBRAGContextSource(**s) for s in sources]
    )


# ============== Bulk Operations ==============

@router.post("/regenerate-all-embeddings")
async def regenerate_all_embeddings(
    entity_type: Optional[str] = Query(None, pattern="^(prompts|documents|faqs)$"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Regenerate embeddings for all KB content (admin only)"""
    result = await knowledge_base_service.regenerate_all_embeddings(db, entity_type)
    return {"message": "Embeddings regenerated", "counts": result}


@router.get("/stats", response_model=KBStatsResponse)
async def get_kb_stats(
    lounge_id: Optional[int] = Query(None, description="Filter stats by lounge ID (null = global only)"),
    include_global: bool = Query(True, description="Include global items in stats when lounge_id is set"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get KB statistics (admin only)"""
    stats = await knowledge_base_service.get_stats(db, lounge_id, include_global)
    return KBStatsResponse(**stats)


# ============== Background Jobs ==============

from app.services.background_task_service import background_task_service
from app.db.models.background_job import BackgroundJob, JobStatus, JobType


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """Get status of a background job (admin only)"""
    job = background_task_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/jobs")
async def list_active_jobs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (prompt, document, faq)"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List active background jobs (admin only)"""
    jobs = background_task_service.get_active_jobs(db, entity_type, entity_id)
    return [job.to_dict() for job in jobs]


@router.get("/jobs/recent")
async def list_recent_jobs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """List recent background jobs (admin only)"""
    jobs = background_task_service.get_recent_jobs(db, limit)
    return [job.to_dict() for job in jobs]
