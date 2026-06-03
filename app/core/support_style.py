"""
Support Style / Tone Modes configuration.

Four user-facing styles per the Prompterly Support Style spec. Each is a
distinct way the lounge should respond to the user; the default is
"Mentor's Style", which intentionally does NOT impose a tone — the
lounge stays on whatever coaching style the mentor uploaded in admin.

  * mentors_style  — DEFAULT. No prompt override; lounge follows the
                     mentor's own coaching cues.
  * soundboard     — Reflective thinking partner. Asks questions, never
                     prescribes.
  * reality_check  — Honest, direct, grounded. Surfaces blind spots and
                     practical next steps without being harsh.
  * pep_talk       — Encouraging and energising. Builds momentum while
                     staying realistic.

Snippets live in this module so that prompt changes are reviewable in PRs
(Security Standard §15 — mentor IP versioning is enforced via code review
for human-authored copy). The DB tables `support_styles` and
`support_style_versions` are a *write-mostly* audit trail: every unique
snippet ever deployed gets a row, and chat threads pin to the version row
that was active at thread creation so we can later prove which exact text
generated a given message. The DB write happens on startup; admins do not
edit snippets through a runtime UI.

Per-user preference is stored on `User.support_style`; per-thread override
on `ChatThread.support_style`. `resolve_style()` returns the effective
style for a given (thread, user) pair.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from threading import RLock
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


DEFAULT_STYLE = "mentors_style"


@dataclass(frozen=True)
class SupportStyle:
    slug: str
    name: str
    description: str
    prompt_snippet: str


# Prompt snippets are appended to the lounge's base system prompt under a
# "TONE MODE" section, so the language here is instructions to the AI,
# not the user-facing label.
#
# Snippets follow the same structure for review consistency:
#   - one-line core purpose
#   - bulleted "do this" guidance
#   - bulleted "don't do this" guardrails (mirrors the spec)
_STYLES: Dict[str, SupportStyle] = {
    "mentors_style": SupportStyle(
        slug="mentors_style",
        name="Mentor's Style",
        description="Default — the lounge follows the mentor's own coaching style.",
        # Empty snippet on purpose: the lounge's existing system prompt is
        # already shaped by the mentor's uploaded content, so this mode
        # contributes no additional tone instructions. Defining the slug
        # here lets the UI surface it as a selectable option without any
        # branching in the prompt builder.
        prompt_snippet="",
    ),
    "soundboard": SupportStyle(
        slug="soundboard",
        name="Soundboard",
        description="Help me think things through — reflect, don't prescribe.",
        prompt_snippet=(
            "TONE MODE — SOUNDBOARD:\n"
            "Core purpose: help the user think things through, not give answers.\n"
            "How to respond:\n"
            " - Reflect back what the user is saying in a clear, structured way.\n"
            " - Ask thoughtful, open-ended questions.\n"
            " - Offer perspectives, not conclusions.\n"
            " - Gently highlight patterns, assumptions, or contradictions.\n"
            " - Avoid being directive or prescriptive.\n"
            "Tone: calm, curious, neutral, non-judgmental.\n"
            "Do NOT: give strong advice; over-motivate or challenge aggressively."
        ),
    ),
    "reality_check": SupportStyle(
        slug="reality_check",
        name="Reality Check",
        description="Be honest with me — challenge my thinking and ground it in facts.",
        prompt_snippet=(
            "TONE MODE — REALITY CHECK:\n"
            "Core purpose: give the user clear, honest, grounded feedback.\n"
            "How to respond:\n"
            " - Be direct and concise.\n"
            " - Call out inconsistencies, avoidance, or flawed thinking.\n"
            " - Highlight what the user may not want to hear.\n"
            " - Bring the conversation back to reality, facts, or likely outcomes.\n"
            " - Offer practical next steps where appropriate.\n"
            "Tone: direct, honest, slightly firm but not harsh or disrespectful.\n"
            "Do NOT: be overly soft or validating; avoid difficult truths; "
            "be aggressive, critical, or condescending."
        ),
    ),
    "pep_talk": SupportStyle(
        slug="pep_talk",
        name="Pep Talk",
        description="Pump me up — build confidence and momentum without being hypey.",
        prompt_snippet=(
            "TONE MODE — PEP TALK:\n"
            "Core purpose: build confidence, energy, and momentum.\n"
            "How to respond:\n"
            " - Reinforce the user's capability and potential.\n"
            " - Reframe doubt into possibility.\n"
            " - Highlight strengths and progress.\n"
            " - Encourage action and forward movement.\n"
            " - Keep responses energising but still grounded in reality.\n"
            "Tone: encouraging, uplifting, confident, warm.\n"
            "Do NOT: be unrealistic or overly hypey; ignore real challenges; "
            "sound generic or cliché."
        ),
    ),
}


# Legacy slugs from previous iterations of this feature. The resolver
# maps them transparently so any row written before migration 025 still
# renders correctly. New writes should only use slugs in `_STYLES`.
#
#   motivational  — closest to pep_talk (encouraging, momentum-building)
#   empathetic    — closest to soundboard (warm, reflective listener)
#   analytical    — closest to reality_check (direct, grounded)
_LEGACY_ALIASES: Dict[str, str] = {
    "motivational": "pep_talk",
    "empathetic": "soundboard",
    "analytical": "reality_check",
}


# Display order is kept distinct from dict iteration so reordering the
# `_STYLES` dict above doesn't accidentally reshuffle the UI.
_DISPLAY_ORDER: List[str] = ["mentors_style", "soundboard", "reality_check", "pep_talk"]


def list_styles() -> List[SupportStyle]:
    """Return the catalogue in display order. Default first."""
    return [_STYLES[slug] for slug in _DISPLAY_ORDER]


def _canonical_slug(slug: Optional[str]) -> Optional[str]:
    """Normalise a stored slug through the legacy alias table."""
    if slug is None:
        return None
    return _LEGACY_ALIASES.get(slug, slug)


def is_valid(slug: Optional[str]) -> bool:
    """Whether `slug` matches a supported tone. None means 'default'."""
    if slug is None:
        return True
    return _canonical_slug(slug) in _STYLES


def resolve_style(
    thread_style: Optional[str],
    user_style: Optional[str],
) -> SupportStyle:
    """
    Pick the effective tone for an AI reply.

    Precedence: per-thread override → user's account preference → global
    default. Unknown slugs (e.g. data from a rolled-back feature flag)
    fall through to the next tier so prompt assembly never fails on
    bad values.
    """
    for candidate in (thread_style, user_style, DEFAULT_STYLE):
        canonical = _canonical_slug(candidate)
        if canonical and canonical in _STYLES:
            return _STYLES[canonical]
    return _STYLES[DEFAULT_STYLE]


def get_prompt_snippet(
    thread_style: Optional[str],
    user_style: Optional[str],
) -> str:
    """Convenience wrapper that returns only the prompt snippet string."""
    return resolve_style(thread_style, user_style).prompt_snippet


# ---------------------------------------------------------------------------
# DB versioning (S1 / S19 / S20)
# ---------------------------------------------------------------------------
#
# The in-code catalogue above is the source of truth. The DB tables exist
# so we can prove later which snippet text was active when a particular
# chat thread was opened. Workflow:
#
#   1. On app startup we call `sync_support_style_versions_with_db(db)`.
#      For each style we ensure a `support_styles` row exists and that the
#      *current* `prompt_snippet` is present as the active
#      `support_style_versions` row.
#   2. New snippet text deployed via PR → next startup writes a new
#      version row, demotes the prior one to `is_active=False`.
#   3. Chat threads opened after sync pin to the active version's id via
#      `ChatThread.support_style_version_id`.
#
# The active-version cache below avoids a DB query on every chat turn.

_active_version_cache: Dict[str, int] = {}
_cache_lock = RLock()


def _snippet_hash(snippet: str) -> str:
    return hashlib.sha256(snippet.encode("utf-8")).hexdigest()


def sync_support_style_versions_with_db(db) -> None:
    """
    Reconcile the in-code catalogue with the DB tables. Idempotent — safe
    to call on every startup. Refreshes the active-version cache used by
    `active_version_id_for`.

    Raises nothing on failure: the DB sync is best-effort. If the tables
    don't exist yet (early in a migration sequence) or the session is
    broken, we log and carry on with no version pinning rather than
    blocking app startup.
    """
    # Import here so this module is safe to load before the DB layer is
    # fully wired up (e.g. during alembic offline rendering).
    from app.db.models.support_style import (
        SupportStyleConfig, SupportStyleVersion,
    )

    try:
        with _cache_lock:
            new_cache: Dict[str, int] = {}
            for display_position, slug in enumerate(_DISPLAY_ORDER):
                style_def = _STYLES[slug]

                # 1. Ensure the catalogue row exists / is fresh.
                cfg = db.query(SupportStyleConfig).filter(
                    SupportStyleConfig.slug == slug,
                ).first()
                if cfg is None:
                    cfg = SupportStyleConfig(
                        slug=slug,
                        name=style_def.name,
                        description=style_def.description,
                        display_order=display_position,
                        is_active=True,
                    )
                    db.add(cfg)
                else:
                    # Keep display metadata in sync with the in-code source
                    # of truth so a PR that renames a style propagates
                    # without manual SQL.
                    cfg.name = style_def.name
                    cfg.description = style_def.description
                    cfg.display_order = display_position
                    cfg.is_active = True

                # 2. Ensure the current snippet is recorded as a version.
                target_hash = _snippet_hash(style_def.prompt_snippet)
                existing = db.query(SupportStyleVersion).filter(
                    SupportStyleVersion.style_slug == slug,
                    SupportStyleVersion.snippet_hash == target_hash,
                ).first()

                if existing is None:
                    # Snippet text is new to this DB — record a fresh
                    # version, demoting any currently-active row.
                    db.query(SupportStyleVersion).filter(
                        SupportStyleVersion.style_slug == slug,
                        SupportStyleVersion.is_active == True,  # noqa: E712
                    ).update({"is_active": False})

                    max_v = db.query(SupportStyleVersion.version_number).filter(
                        SupportStyleVersion.style_slug == slug,
                    ).order_by(SupportStyleVersion.version_number.desc()).first()
                    next_n = (max_v[0] + 1) if max_v else 1

                    version = SupportStyleVersion(
                        style_slug=slug,
                        version_number=next_n,
                        prompt_snippet=style_def.prompt_snippet,
                        snippet_hash=target_hash,
                        is_active=True,
                        change_notes=f"Synced from code on startup (v{next_n})",
                    )
                    db.add(version)
                    db.flush()
                    new_cache[slug] = version.id
                    logger.info(
                        "Support style %r: new snippet version %d recorded",
                        slug, next_n,
                    )
                else:
                    # We've seen this exact snippet before. Make sure it's
                    # the active version — covers the case where text was
                    # reverted to a previous value.
                    if not existing.is_active:
                        db.query(SupportStyleVersion).filter(
                            SupportStyleVersion.style_slug == slug,
                            SupportStyleVersion.is_active == True,  # noqa: E712
                        ).update({"is_active": False})
                        existing.is_active = True
                        db.flush()
                        logger.info(
                            "Support style %r: reverted to existing version %d",
                            slug, existing.version_number,
                        )
                    new_cache[slug] = existing.id

            db.commit()
            _active_version_cache.clear()
            _active_version_cache.update(new_cache)
            logger.info(
                "Support style DB sync complete (%d styles, cache: %s)",
                len(new_cache), new_cache,
            )
    except Exception:
        logger.exception(
            "Support style DB sync failed — chat will continue with no "
            "version pinning. Investigate the support_styles tables."
        )
        try:
            db.rollback()
        except Exception:
            pass


def active_version_id_for(slug: Optional[str]) -> Optional[int]:
    """
    Return the id of the active `SupportStyleVersion` for a slug, or
    None if the cache hasn't been populated yet (e.g. sync failed).

    Cheap — pure in-memory dict lookup. Called from chat.create_thread
    and from each AI message-generation path.
    """
    canonical = _canonical_slug(slug) or DEFAULT_STYLE
    return _active_version_cache.get(canonical)
