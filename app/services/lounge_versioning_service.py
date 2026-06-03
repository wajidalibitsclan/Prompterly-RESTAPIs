"""
Mentor IP versioning service (Security Standard §15).

Every change to a Coaching Lounge's config produces a new immutable
`LoungeConfigVersion` row. Previous versions are never overwritten —
they are referenced by the chat threads that ran against them so we can
prove later which configuration generated which response.

The Lounge model itself doesn't carry the full prompt config today; the
versioning system snapshots the lounge fields that affect mentor IP
(title/description/about/category/access/mentor) into the version's
`prompt_templates` JSON. Additional fields on `LoungeConfigVersion`
(system_prompt, mentor_framework, behavioural_guardrails, tone_config,
ai_model) stay nullable until the platform exposes an editor for them —
the versioning machinery is forward-compatible.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.lounge import Lounge, LoungeConfigVersion
from app.db.models.user import User

logger = logging.getLogger(__name__)


def _snapshot_payload(lounge: Lounge) -> dict:
    """The lounge-identity fields we treat as part of mentor IP today."""
    return {
        "title": lounge.title,
        "description": lounge.description,
        "about": lounge.about,
        "category_id": lounge.category_id,
        "access_type": lounge.access_type.value if lounge.access_type else None,
        "max_members": lounge.max_members,
        "brand_color": lounge.brand_color,
        "mentor_id": lounge.mentor_id,
        "is_public_listing": lounge.is_public_listing,
    }


def snapshot(
    lounge: Lounge,
    *,
    db: Session,
    created_by: Optional[User] = None,
    change_notes: Optional[str] = None,
    system_prompt: Optional[str] = None,
    mentor_framework: Optional[str] = None,
    behavioural_guardrails: Optional[str] = None,
    tone_config: Optional[dict] = None,
    ai_model: Optional[str] = None,
) -> LoungeConfigVersion:
    """
    Create a new immutable version for this lounge.

    Marks any currently active version as inactive (`is_active=False`)
    and inserts the new one as active. Caller is responsible for
    committing the surrounding transaction.

    The lounge identity fields (title/description/about/...) are captured
    automatically into `prompt_templates`. The explicit kwargs are for
    fields that don't live on the Lounge row yet — when an editor for them
    exists, the caller can pass the new values here and they'll be frozen
    into the version snapshot.
    """
    # Deactivate the prior active version. There should be at most one,
    # but the loop is defensive in case manual SQL has left several.
    current = db.query(LoungeConfigVersion).filter(
        LoungeConfigVersion.lounge_id == lounge.id,
        LoungeConfigVersion.is_active == True,  # noqa: E712 SQLAlchemy idiom
    ).all()
    for prev in current:
        prev.is_active = False

    # Next version number = max + 1. Includes inactive rows so rollbacks
    # don't reuse numbers and the history stays a monotonic sequence.
    max_version = db.query(LoungeConfigVersion.version_number).filter(
        LoungeConfigVersion.lounge_id == lounge.id,
    ).order_by(LoungeConfigVersion.version_number.desc()).first()
    next_number = (max_version[0] + 1) if max_version else 1

    version = LoungeConfigVersion(
        lounge_id=lounge.id,
        version_number=next_number,
        system_prompt=system_prompt,
        mentor_framework=mentor_framework,
        prompt_templates=_snapshot_payload(lounge),
        behavioural_guardrails=behavioural_guardrails,
        tone_config=tone_config,
        ai_model=ai_model,
        created_by=created_by.id if created_by else None,
        change_notes=change_notes,
        is_active=True,
    )
    db.add(version)
    db.flush()  # populate version.id without committing the caller's tx
    logger.info(
        "Lounge %s config version %d created (by user_id=%s)",
        lounge.id, next_number, created_by.id if created_by else None,
    )
    return version


def get_active_version(lounge_id: int, db: Session) -> Optional[LoungeConfigVersion]:
    """Return the currently-active config version for a lounge, if any."""
    return db.query(LoungeConfigVersion).filter(
        LoungeConfigVersion.lounge_id == lounge_id,
        LoungeConfigVersion.is_active == True,  # noqa: E712
    ).first()


def rollback_to(
    lounge: Lounge,
    target_version_id: int,
    *,
    db: Session,
    created_by: Optional[User] = None,
    change_notes: Optional[str] = None,
) -> LoungeConfigVersion:
    """
    Restore the lounge's *content* to a previous version's snapshot and
    record this as a NEW version (versioning history is append-only).

    The historical version row is never modified. The lounge row IS
    mutated to match the snapshot — that's the user-visible effect of a
    rollback. A new `LoungeConfigVersion` with the restored payload
    becomes the active version.
    """
    target = db.query(LoungeConfigVersion).filter(
        LoungeConfigVersion.id == target_version_id,
        LoungeConfigVersion.lounge_id == lounge.id,
    ).first()
    if target is None:
        raise ValueError(
            f"No config version {target_version_id} found for lounge {lounge.id}"
        )

    # Apply the snapshot back onto the live lounge row. We only touch
    # fields that the snapshot is authoritative for — fields like
    # stripe_product_id that were never part of the snapshot are left
    # alone so a rollback doesn't break billing wiring.
    payload = target.prompt_templates or {}
    if "title" in payload:
        lounge.title = payload["title"]
    if "description" in payload:
        lounge.description = payload["description"]
    if "about" in payload:
        lounge.about = payload["about"]
    if "category_id" in payload:
        lounge.category_id = payload["category_id"]
    if "max_members" in payload:
        lounge.max_members = payload["max_members"]
    if "brand_color" in payload:
        lounge.brand_color = payload["brand_color"]
    if "is_public_listing" in payload:
        lounge.is_public_listing = payload["is_public_listing"]
    # `access_type` and `mentor_id` are intentionally NOT auto-applied —
    # changing those has billing / Stripe consequences (see
    # admin_setup_lounge_stripe and lounge subscription migration). An
    # admin who wants to revert those must do so via the regular update
    # endpoint, which will re-run the right side effects.

    return snapshot(
        lounge, db=db,
        created_by=created_by,
        change_notes=change_notes or f"Rolled back to version {target.version_number}",
    )
