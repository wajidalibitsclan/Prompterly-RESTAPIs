"""
In-process search helpers for AES-256-GCM-encrypted user content.

Security Standard §3 / Task 15:

    "If chat message content is encrypted at the application layer,
     developers must implement a search method that allows thread-level
     search without exposing full plaintext content unnecessarily."

The functions in this module are designed so that:

  1. Plaintext only exists inside the Python process for the duration of
     the search call. It is never logged and never returned in full.
  2. Callers receive a match flag and a small **snippet** (a window of
     characters around the match) — not the whole message. If the caller
     explicitly asks for full content (e.g., to render the matching
     message when the user clicks it), that is a separate, authenticated
     fetch.
  3. Searching is scoped to records the authenticated user already owns
     (thread or notebook), so an encrypted-content scan cannot become a
     corpus-wide leak.
"""
from typing import Optional


DEFAULT_SNIPPET_WINDOW = 60
"""Characters of context shown on each side of a match in a snippet."""

MAX_SNIPPET_LENGTH = 240
"""Hard cap on snippet length returned to clients."""


def matches_query(plaintext: str, query: str) -> bool:
    """
    Case-insensitive substring match. Returns False for empty inputs.
    """
    if not plaintext or not query:
        return False
    return query.casefold() in plaintext.casefold()


def build_snippet(
    plaintext: str,
    query: str,
    window: int = DEFAULT_SNIPPET_WINDOW,
) -> Optional[str]:
    """
    Return a short excerpt of `plaintext` centred on the first occurrence
    of `query`. Returns None if there is no match.

    The snippet is capped at MAX_SNIPPET_LENGTH characters and is padded
    with "…" when it is clipped from either end. The snippet is the ONLY
    portion of plaintext the caller should expose back to the client —
    full plaintext is fetched separately through the normal read path.
    """
    if not plaintext or not query:
        return None

    haystack_cf = plaintext.casefold()
    needle_cf = query.casefold()
    idx = haystack_cf.find(needle_cf)
    if idx == -1:
        return None

    start = max(0, idx - window)
    end = min(len(plaintext), idx + len(query) + window)
    snippet = plaintext[start:end]

    if start > 0:
        snippet = "…" + snippet
    if end < len(plaintext):
        snippet = snippet + "…"

    if len(snippet) > MAX_SNIPPET_LENGTH:
        snippet = snippet[: MAX_SNIPPET_LENGTH - 1] + "…"

    return snippet
