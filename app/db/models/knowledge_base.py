"""
Knowledge Base models for managing prompts, documents, and FAQs
Supports RAG (Retrieval Augmented Generation) with embeddings
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.core.timezone import now_naive


class KBCategory(Base):
    """Category model for organizing knowledge base content"""

    __tablename__ = "kb_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Optional lounge_id - if NULL, category is global; if set, it's lounge-specific
    lounge_id = Column(Integer, ForeignKey("lounges.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(DateTime, default=now_naive, onupdate=now_naive, nullable=False)

    # Relationships
    lounge = relationship("Lounge")
    prompts = relationship("KBPrompt", back_populates="category", cascade="all, delete-orphan")
    documents = relationship("KBDocument", back_populates="category", cascade="all, delete-orphan")
    faqs = relationship("KBFaq", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KBCategory(id={self.id}, name={self.name}, slug={self.slug})>"


class KBPrompt(Base):
    """Knowledge Base Prompt model - reusable AI prompts/instructions"""

    __tablename__ = "kb_prompts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Optional lounge_id - if NULL, prompt is global; if set, it's lounge-specific
    lounge_id = Column(Integer, ForeignKey("lounges.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("kb_categories.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_included_in_rag = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)

    # Embedding for RAG - stored as JSON array
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(DateTime, default=now_naive, onupdate=now_naive, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    lounge = relationship("Lounge")
    category = relationship("KBCategory", back_populates="prompts")
    created_by = relationship("User")

    @property
    def has_embedding(self) -> bool:
        """Check if prompt has embedding"""
        return self.embedding is not None

    def __repr__(self):
        return f"<KBPrompt(id={self.id}, title={self.title})>"


class KBDocument(Base):
    """Knowledge Base Document model - uploaded documents for RAG"""

    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Optional lounge_id - if NULL, document is global; if set, it's lounge-specific
    lounge_id = Column(Integer, ForeignKey("lounges.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("kb_categories.id", ondelete="SET NULL"), nullable=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)

    # Extracted content for RAG
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)

    # Embedding for document-level search
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(DateTime, default=now_naive, onupdate=now_naive, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    lounge = relationship("Lounge")
    category = relationship("KBCategory", back_populates="documents")
    file = relationship("File")
    created_by = relationship("User")
    chunks = relationship("KBDocumentChunk", back_populates="document", cascade="all, delete-orphan")

    @property
    def has_embedding(self) -> bool:
        """Check if document has embedding"""
        return self.embedding is not None

    @property
    def chunk_count(self) -> int:
        """Get number of chunks"""
        return len(self.chunks) if self.chunks else 0

    def __repr__(self):
        return f"<KBDocument(id={self.id}, title={self.title}, file_type={self.file_type})>"


class KBDocumentChunk(Base):
    """Document chunk for granular RAG retrieval"""

    __tablename__ = "kb_document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)

    # Embedding for RAG
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=now_naive, nullable=False)

    # Relationships
    document = relationship("KBDocument", back_populates="chunks")

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has embedding"""
        return self.embedding is not None

    def __repr__(self):
        return f"<KBDocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class KBFaq(Base):
    """Knowledge Base FAQ model - frequently asked questions with RAG support"""

    __tablename__ = "kb_faqs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Optional lounge_id - if NULL, FAQ is global; if set, it's lounge-specific
    lounge_id = Column(Integer, ForeignKey("lounges.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("kb_categories.id", ondelete="SET NULL"), nullable=True)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_included_in_rag = Column(Boolean, default=True, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)

    # Embedding for RAG (combined question + answer)
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=now_naive, nullable=False)
    updated_at = Column(DateTime, default=now_naive, onupdate=now_naive, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    lounge = relationship("Lounge")
    category = relationship("KBCategory", back_populates="faqs")
    created_by = relationship("User")

    @property
    def has_embedding(self) -> bool:
        """Check if FAQ has embedding"""
        return self.embedding is not None

    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return self.helpful_count / total

    def __repr__(self):
        return f"<KBFaq(id={self.id}, question={self.question[:50]}...)>"
