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

The catalogue lives in code (not a DB table) because:
  * The set changes at the speed of product decisions, not user edits
  * Prompt snippets are version-controlled alongside the rest of the
    system prompt so behavioural changes are reviewable in PRs
  * Security Standard §15 (mentor IP versioning) tracks prompt template
    changes via git history, not a runtime table

Per-user preference is stored on `User.support_style`; per-thread override
on `ChatThread.support_style`. `resolve_style()` returns the effective
style for a given (thread, user) pair.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


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


def list_styles() -> List[SupportStyle]:
    """Return the catalogue in display order. Default first."""
    return [
        _STYLES["mentors_style"],
        _STYLES["soundboard"],
        _STYLES["reality_check"],
        _STYLES["pep_talk"],
    ]


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
