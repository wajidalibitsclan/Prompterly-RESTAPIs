"""
Support Style / Tone Modes configuration.

Three tone modes the user can pick for AI coaching replies:
  * motivational  — encouraging, action-oriented, affirmations
  * analytical    — structured, probing questions, framework-driven
  * empathetic    — warm, validating, emotional support

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


DEFAULT_STYLE = "motivational"


@dataclass(frozen=True)
class SupportStyle:
    slug: str
    name: str
    description: str
    prompt_snippet: str


# The prompt snippets are appended to the lounge's base system prompt under
# a "TONE MODE" section, so the language here is instructions to the AI,
# not the user-facing description.
_STYLES: Dict[str, SupportStyle] = {
    "motivational": SupportStyle(
        slug="motivational",
        name="Motivational",
        description="Encouraging and uplifting — celebrates progress and pushes you forward.",
        prompt_snippet=(
            "TONE MODE — MOTIVATIONAL:\n"
            "Lead with encouragement. Affirm effort, celebrate progress however small, "
            "and keep responses action-oriented. Use phrases like \"you've got this\", "
            "\"next step\", \"let's build on that\". Avoid dwelling on obstacles — reframe "
            "them as challenges to work through. Keep energy high but never dismissive "
            "of the user's concerns."
        ),
    ),
    "analytical": SupportStyle(
        slug="analytical",
        name="Analytical",
        description="Structured and reflective — breaks things down with frameworks and probing questions.",
        prompt_snippet=(
            "TONE MODE — ANALYTICAL:\n"
            "Lead with structure. Break down the user's situation into components, "
            "ask probing clarifying questions when relevant, and use frameworks or "
            "models from your knowledge base where they fit. Prefer numbered points, "
            "compare-and-contrast, and trade-off analysis. Be direct and precise — "
            "favour clarity over warmth, but never cold or clinical."
        ),
    ),
    "empathetic": SupportStyle(
        slug="empathetic",
        name="Empathetic",
        description="Warm and validating — acknowledges feelings and offers emotional support.",
        prompt_snippet=(
            "TONE MODE — EMPATHETIC:\n"
            "Lead with warmth. Acknowledge the feelings behind what the user shares "
            "before offering advice. Use validating language (\"that makes sense\", "
            "\"it's understandable to feel that way\") and listen more than you "
            "prescribe. When giving guidance, frame it gently and leave room for the "
            "user to hold their own pace. Keep safety-critical advice (see guardrails) "
            "unchanged — empathy does not soften safety language."
        ),
    ),
}


def list_styles() -> List[SupportStyle]:
    """Return the full tone catalogue in display order."""
    return [_STYLES["motivational"], _STYLES["analytical"], _STYLES["empathetic"]]


def is_valid(slug: Optional[str]) -> bool:
    """Whether `slug` matches a supported tone. None is accepted (means 'default')."""
    return slug is None or slug in _STYLES


def resolve_style(
    thread_style: Optional[str],
    user_style: Optional[str],
) -> SupportStyle:
    """
    Pick the effective tone for an AI reply.

    Precedence: per-thread override → user's account preference → global default.
    Unknown slugs (e.g. data from a rolled-back feature flag) fall through to
    the next tier so prompt assembly never fails on bad values.
    """
    for candidate in (thread_style, user_style, DEFAULT_STYLE):
        if candidate and candidate in _STYLES:
            return _STYLES[candidate]
    return _STYLES[DEFAULT_STYLE]


def get_prompt_snippet(
    thread_style: Optional[str],
    user_style: Optional[str],
) -> str:
    """Convenience wrapper that returns only the prompt snippet string."""
    return resolve_style(thread_style, user_style).prompt_snippet
