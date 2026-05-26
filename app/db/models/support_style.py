"""
Support Style catalogue + immutable version history (Security Standard §15).

S1, S19, S20 of the Prompterly Support Style task list:
  - S1  Catalogue table — one row per slug
  - S19 Immutable version table — one row per unique prompt snippet ever shipped
  - S20 Per-thread pin — `ChatThread.support_style_version_id` (added in
        the chat model) records the version active when the thread opened

Snippets are still authored in `app/core/support_style.py` and shipped via
code review (the rationale documented there still holds). The DB tables
are a *write-mostly* audit trail: on startup the service inserts any
new-to-this-deploy snippet as a new version row, so we can prove later
which exact text generated a given message — without giving admins a
runtime editor that would bypass PR review.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.core.timezone import now_naive


class SupportStyleConfig(Base):
    """One row per tone-mode slug. Identity only — the snippet lives on
    `SupportStyleVersion` so changes produce a new immutable version row."""

    __tablename__ = "support_styles"

    # Slug is the natural primary key — it's stable, short, and already the
    # value stored on `users.support_style` and `chat_threads.support_style`.
    slug = Column(String(24), primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    # Display order in the catalogue (0 = first).
    display_order = Column(Integer, nullable=False, default=0)
    # Soft-delete a style without losing the version history.
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now_naive, nullable=False)

    versions = relationship(
        "SupportStyleVersion",
        back_populates="style",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<SupportStyleConfig(slug={self.slug}, name={self.name!r})>"


class SupportStyleVersion(Base):
    """
    Immutable prompt-snippet version. New rows are written on startup when
    the in-code snippet's hash doesn't match any existing version for that
    slug. Rows are never updated or deleted in normal operation.
    """

    __tablename__ = "support_style_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    style_slug = Column(
        String(24),
        ForeignKey("support_styles.slug"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    # The actual prompt fragment. Empty string is valid (the default
    # "mentor's style" mode intentionally contributes no override text).
    prompt_snippet = Column(Text, nullable=False, default="")
    # SHA-256 hex digest of `prompt_snippet`. Indexed because lookup at
    # startup goes `(slug, hash) -> existing version | None`.
    snippet_hash = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    change_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=now_naive, nullable=False)

    style = relationship("SupportStyleConfig", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("style_slug", "version_number", name="uq_support_style_version_number"),
        Index("ix_support_style_version_slug_hash", "style_slug", "snippet_hash"),
    )

    def __repr__(self):
        return (
            f"<SupportStyleVersion(id={self.id}, slug={self.style_slug}, "
            f"v={self.version_number}, active={self.is_active})>"
        )
