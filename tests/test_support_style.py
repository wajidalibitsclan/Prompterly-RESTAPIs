"""
Support Style Selector tests (S21–S25 of the task list).

  S21 — Style selection persists across sessions / page reloads.
  S22 — AI tone adapts per style (Motivational vs Analytical vs Empathetic).
  S23 — Mid-conversation style switch applies to subsequent messages only.
  S24 — Default fallback when no style is selected.
  S25 — Invalid style slugs are rejected by the API.

The catalogue today is `mentors_style` / `soundboard` / `reality_check` /
`pep_talk`; the legacy slugs from the spec (`motivational` etc.) are
mapped via `_LEGACY_ALIASES`. Tests use the current slugs but verify
the legacy aliases still resolve for S22.
"""
from __future__ import annotations

import asyncio

import pytest


def _create_thread_sync(chat_service, *, user_id: int, db):
    """Helper: drive the async create_thread coroutine to completion."""
    return asyncio.run(chat_service.create_thread(user_id=user_id, db=db))


# ---------------------------------------------------------------------------
# S25 — Invalid style rejection
# ---------------------------------------------------------------------------

def test_s25_api_rejects_invalid_thread_style(
    client, make_user, auth_headers, synced_support_styles, db_session,
):
    """PATCH /chat/threads/{id}/support-style with bogus slug -> 400."""
    user = make_user()
    headers = auth_headers(user)

    from app.services.chat_service import chat_service
    thread = _create_thread_sync(chat_service, user_id=user.id, db=db_session)

    response = client.patch(
        f"/api/v1/chat/threads/{thread.id}/support-style",
        json={"support_style": "not_a_real_style"},
        headers=headers,
    )
    assert response.status_code == 400, response.text


def test_s25_user_setting_rejects_invalid_style(client, make_user, auth_headers):
    """PUT /users/me/settings/support-style with bogus slug -> 400."""
    user = make_user()
    headers = auth_headers(user)

    response = client.put(
        "/api/v1/users/me/settings/support-style",
        json={"support_style": "definitely_invalid"},
        headers=headers,
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# S24 — Default fallback
# ---------------------------------------------------------------------------

def test_s24_resolver_falls_back_to_default():
    """resolve_style(None, None) returns the global default."""
    from app.core.support_style import resolve_style, DEFAULT_STYLE
    style = resolve_style(thread_style=None, user_style=None)
    assert style.slug == DEFAULT_STYLE


def test_s24_user_endpoint_returns_default_when_unset(client, make_user, auth_headers):
    """GET /users/me/settings/support-style with no preference set."""
    user = make_user()
    headers = auth_headers(user)
    response = client.get(
        "/api/v1/users/me/settings/support-style",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    from app.core.support_style import DEFAULT_STYLE
    assert body["support_style"] == DEFAULT_STYLE
    assert body["explicit"] is False


# ---------------------------------------------------------------------------
# S21 — Selection persists
# ---------------------------------------------------------------------------

def test_s21_user_preference_persists(client, make_user, auth_headers):
    """PUT then GET — the user's saved style is returned."""
    user = make_user()
    headers = auth_headers(user)

    put_resp = client.put(
        "/api/v1/users/me/settings/support-style",
        json={"support_style": "pep_talk"},
        headers=headers,
    )
    assert put_resp.status_code == 200, put_resp.text

    get_resp = client.get(
        "/api/v1/users/me/settings/support-style",
        headers=headers,
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["support_style"] == "pep_talk"
    assert body["explicit"] is True


def test_s21_thread_pin_persists_and_records_version(
    client, make_user, auth_headers, synced_support_styles, db_session,
):
    """A thread's support_style + support_style_version_id survive a refetch.
    Together this covers S20 (version recorded per session) too."""
    user = make_user()
    headers = auth_headers(user)

    from app.services.chat_service import chat_service
    thread = _create_thread_sync(chat_service, user_id=user.id, db=db_session)

    patch_resp = client.patch(
        f"/api/v1/chat/threads/{thread.id}/support-style",
        json={"support_style": "soundboard"},
        headers=headers,
    )
    assert patch_resp.status_code == 200, patch_resp.text

    db_session.expire_all()
    from app.db.models.chat import ChatThread
    refetched = db_session.query(ChatThread).filter_by(id=thread.id).first()
    assert refetched.support_style == "soundboard"
    # S20: per-session version is recorded.
    assert refetched.support_style_version_id is not None


# ---------------------------------------------------------------------------
# S22 — AI tone adapts per style
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "slug, snippet_marker",
    [
        ("soundboard", "SOUNDBOARD"),
        ("reality_check", "REALITY CHECK"),
        ("pep_talk", "PEP TALK"),
        # Legacy aliases should also resolve to the same underlying snippets.
        ("motivational", "PEP TALK"),
        ("empathetic", "SOUNDBOARD"),
        ("analytical", "REALITY CHECK"),
    ],
)
def test_s22_prompt_snippet_changes_per_style(slug, snippet_marker):
    """Each style's prompt snippet contains a distinctive header."""
    from app.core.support_style import resolve_style
    style = resolve_style(thread_style=slug, user_style=None)
    assert snippet_marker in style.prompt_snippet


def test_s22_default_style_has_no_override_snippet():
    """`mentors_style` deliberately contributes no tone instructions."""
    from app.core.support_style import resolve_style, DEFAULT_STYLE
    default = resolve_style(thread_style=None, user_style=None)
    assert default.slug == DEFAULT_STYLE
    assert default.prompt_snippet == ""


# ---------------------------------------------------------------------------
# S23 — Mid-conversation switch
# ---------------------------------------------------------------------------

def test_s23_thread_switch_does_not_affect_account_preference(
    client, make_user, auth_headers, synced_support_styles, db_session,
):
    """Switching a thread's style does NOT alter the account-level pref."""
    user = make_user(support_style="reality_check")
    db_session.commit()
    headers = auth_headers(user)

    from app.services.chat_service import chat_service
    thread = _create_thread_sync(chat_service, user_id=user.id, db=db_session)

    client.patch(
        f"/api/v1/chat/threads/{thread.id}/support-style",
        json={"support_style": "pep_talk"},
        headers=headers,
    ).raise_for_status()

    db_session.expire_all()
    from app.db.models.user import User
    fresh_user = db_session.query(User).filter_by(id=user.id).first()
    assert fresh_user.support_style == "reality_check"

    from app.db.models.chat import ChatThread
    fresh_thread = db_session.query(ChatThread).filter_by(id=thread.id).first()
    assert fresh_thread.support_style == "pep_talk"


def test_s23_clearing_thread_override_falls_back_to_user_pref(
    client, make_user, auth_headers, synced_support_styles, db_session,
):
    """PATCH support_style=None clears the thread override; resolver then
    picks up the user's account preference."""
    user = make_user(support_style="reality_check")
    db_session.commit()
    headers = auth_headers(user)

    from app.services.chat_service import chat_service
    thread = _create_thread_sync(chat_service, user_id=user.id, db=db_session)

    client.patch(
        f"/api/v1/chat/threads/{thread.id}/support-style",
        json={"support_style": "pep_talk"},
        headers=headers,
    ).raise_for_status()
    client.patch(
        f"/api/v1/chat/threads/{thread.id}/support-style",
        json={"support_style": None},
        headers=headers,
    ).raise_for_status()

    db_session.expire_all()
    from app.db.models.chat import ChatThread
    fresh_thread = db_session.query(ChatThread).filter_by(id=thread.id).first()
    assert fresh_thread.support_style is None

    from app.core.support_style import resolve_style
    resolved = resolve_style(thread_style=None, user_style=user.support_style)
    assert resolved.slug == "reality_check"
