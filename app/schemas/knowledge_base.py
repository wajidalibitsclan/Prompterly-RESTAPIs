"""
Pydantic schemas for Knowledge Base module
Handles validation for prompts, documents, FAQs, and search
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ============== Category Schemas ==============

class KBCategoryBase(BaseModel):
    """Base schema for KB category"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    lounge_id: Optional[int] = None  # NULL = global, set = lounge-specific


class KBCategoryCreate(KBCategoryBase):
    """Schema for creating a KB category"""
    pass


class KBCategoryUpdate(BaseModel):
    """Schema for updating a KB category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    lounge_id: Optional[int] = None


class KBCategoryResponse(KBCategoryBase):
    """Schema for KB category response"""
    id: int
    lounge_id: Optional[int] = None
    lounge_name: Optional[str] = None
    mentor_name: Optional[str] = None  # Mentor who owns the lounge
    created_at: datetime
    updated_at: datetime
    prompt_count: int = 0
    document_count: int = 0
    faq_count: int = 0

    class Config:
        from_attributes = True


# ============== Prompt Schemas ==============

class KBPromptBase(BaseModel):
    """Base schema for KB prompt"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool = True
    is_included_in_rag: bool = True
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None  # NULL = global, set = lounge-specific

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError('Maximum 20 tags allowed')
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v


class KBPromptCreate(KBPromptBase):
    """Schema for creating a KB prompt"""
    pass


class KBPromptUpdate(BaseModel):
    """Schema for updating a KB prompt"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_included_in_rag: Optional[bool] = None
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None


class KBPromptResponse(BaseModel):
    """Schema for KB prompt response"""
    id: int
    title: str
    content: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool
    is_included_in_rag: bool
    usage_count: int
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    lounge_id: Optional[int] = None
    lounge_name: Optional[str] = None
    mentor_name: Optional[str] = None  # Mentor who owns the lounge
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedPromptsResponse(BaseModel):
    """Paginated response for prompts list"""
    items: List[KBPromptResponse]
    total: int
    page: int
    limit: int
    pages: int


# ============== Document Schemas ==============

class KBDocumentBase(BaseModel):
    """Base schema for KB document"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool = True
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None  # NULL = global, set = lounge-specific


class KBDocumentCreate(KBDocumentBase):
    """Schema for creating a KB document (metadata only, file handled separately)"""
    pass


class KBDocumentUpdate(BaseModel):
    """Schema for updating a KB document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None


class KBDocumentResponse(BaseModel):
    """Schema for KB document response"""
    id: int
    title: str
    description: Optional[str] = None
    original_filename: str
    file_type: str
    file_size_bytes: int
    tags: Optional[List[str]] = None
    is_active: bool
    is_processed: bool
    processing_error: Optional[str] = None
    summary: Optional[str] = None
    has_embedding: bool = False
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    lounge_id: Optional[int] = None
    lounge_name: Optional[str] = None
    mentor_name: Optional[str] = None  # Mentor who owns the lounge
    created_by_name: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedDocumentsResponse(BaseModel):
    """Paginated response for documents list"""
    items: List[KBDocumentResponse]
    total: int
    page: int
    limit: int
    pages: int


# ============== FAQ Schemas ==============

class KBFaqBase(BaseModel):
    """Base schema for KB FAQ"""
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None
    sort_order: int = 0
    is_active: bool = True
    is_included_in_rag: bool = True
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None  # NULL = global, set = lounge-specific


class KBFaqCreate(KBFaqBase):
    """Schema for creating a KB FAQ"""
    pass


class KBFaqUpdate(BaseModel):
    """Schema for updating a KB FAQ"""
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_included_in_rag: Optional[bool] = None
    category_id: Optional[int] = None
    lounge_id: Optional[int] = None


class KBFaqResponse(BaseModel):
    """Schema for KB FAQ response"""
    id: int
    question: str
    answer: str
    tags: Optional[List[str]] = None
    sort_order: int
    is_active: bool
    is_included_in_rag: bool
    view_count: int
    helpful_count: int
    not_helpful_count: int
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    lounge_id: Optional[int] = None
    lounge_name: Optional[str] = None
    mentor_name: Optional[str] = None  # Mentor who owns the lounge
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedFaqsResponse(BaseModel):
    """Paginated response for FAQs list"""
    items: List[KBFaqResponse]
    total: int
    page: int
    limit: int
    pages: int


# ============== Search Schemas ==============

class KBSearchRequest(BaseModel):
    """Schema for KB search request"""
    query: str = Field(..., min_length=1)
    entity_types: Optional[List[str]] = None  # ["prompts", "documents", "faqs"]
    category_ids: Optional[List[int]] = None
    lounge_id: Optional[int] = None  # Filter by lounge (NULL = include global only)
    include_global: bool = True  # Include global KB items when lounge_id is set
    limit: int = Field(10, ge=1, le=50)
    use_semantic: bool = True

    @field_validator('entity_types')
    @classmethod
    def validate_entity_types(cls, v):
        if v is not None:
            allowed = {'prompts', 'documents', 'faqs'}
            for t in v:
                if t not in allowed:
                    raise ValueError(f"Invalid entity type: {t}. Allowed: {allowed}")
        return v


class KBSearchResultItem(BaseModel):
    """Schema for a single search result item"""
    entity_type: str
    entity_id: int
    title: str
    content_preview: str
    similarity_score: float
    category_name: Optional[str] = None


class KBSearchResponse(BaseModel):
    """Schema for KB search response"""
    query: str
    results: List[KBSearchResultItem]
    total_results: int


# ============== RAG Context Schemas ==============

class KBRAGContextRequest(BaseModel):
    """Schema for RAG context request"""
    query: str = Field(..., min_length=1)
    max_items: int = Field(5, ge=1, le=20)
    entity_types: Optional[List[str]] = None
    lounge_id: Optional[int] = None  # Filter by lounge
    include_global: bool = True  # Include global KB items


class KBRAGContextSource(BaseModel):
    """Schema for RAG context source"""
    type: str
    id: int
    title: str


class KBRAGContextResponse(BaseModel):
    """Schema for RAG context response"""
    context: str
    sources: List[KBRAGContextSource]


# ============== Stats Schema ==============

class KBStatsResponse(BaseModel):
    """Schema for KB statistics"""
    total_categories: int
    total_prompts: int
    total_documents: int
    total_faqs: int
    prompts_with_embeddings: int
    documents_with_embeddings: int
    faqs_with_embeddings: int
    total_document_chunks: int
    unprocessed_documents: int
