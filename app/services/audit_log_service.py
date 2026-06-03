"""
Audit-log writer (Security Standard §8/§9).

Records security-relevant actions to the dedicated `audit_logs` table. This
sink is intentionally separate from the application log file so the two
have independent retention (audit_logs: 12 months, system logs: 60 days)
and can be queried independently for compliance evidence.

Callers should NEVER block on this. We open a fresh session per write so a
caller's transaction rollback doesn't lose the audit entry, and we swallow
exceptions so an audit-write failure does not break the user-facing flow.
The exception is logged via the standard logger so it's still investigable.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models.misc import AuditLog
from app.db.models.user import User
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


# Action vocabulary — kept as plain strings rather than an enum so adding a
# new event in a feature module doesn't require a schema migration. Use
# SCREAMING_SNAKE_CASE so they're greppable.
class AuditAction:
    # Account lifecycle
    ACCOUNT_REGISTER = "ACCOUNT_REGISTER"
    ACCOUNT_DELETE = "ACCOUNT_DELETE"
    ACCOUNT_PASSWORD_RESET = "ACCOUNT_PASSWORD_RESET"
    ACCOUNT_EMAIL_CHANGE = "ACCOUNT_EMAIL_CHANGE"

    # Authentication / security
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TWO_FA_ENABLED = "TWO_FA_ENABLED"
    TWO_FA_DISABLED = "TWO_FA_DISABLED"

    # Admin actions on other users
    ADMIN_USER_CREATE = "ADMIN_USER_CREATE"
    ADMIN_USER_UPDATE = "ADMIN_USER_UPDATE"
    ADMIN_USER_DELETE = "ADMIN_USER_DELETE"
    ADMIN_USER_ROLE_CHANGE = "ADMIN_USER_ROLE_CHANGE"

    # Compliance
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETION_REQUEST = "DATA_DELETION_REQUEST"
    LEGAL_HOLD_SET = "LEGAL_HOLD_SET"
    LEGAL_HOLD_REMOVED = "LEGAL_HOLD_REMOVED"

    # Mentor IP versioning (Security Standard §15)
    LOUNGE_CONFIG_VERSION_CREATED = "LOUNGE_CONFIG_VERSION_CREATED"
    LOUNGE_CONFIG_ROLLBACK = "LOUNGE_CONFIG_ROLLBACK"

    # Subscription / billing
    SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED"
    SUBSCRIPTION_CANCELED = "SUBSCRIPTION_CANCELED"
    SUBSCRIPTION_UPDATED = "SUBSCRIPTION_UPDATED"


def _extract_request_context(request: Optional[Request]) -> dict:
    if request is None:
        return {}
    ip = None
    if request.client:
        ip = request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    return {
        "ip_address": ip,
        "user_agent": (request.headers.get("user-agent") or "")[:500] or None,
    }


def record(
    action: str,
    *,
    actor: Optional[User] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    changes: Optional[dict] = None,
    audit_metadata: Optional[dict] = None,
    request: Optional[Request] = None,
    db: Optional[Session] = None,
) -> None:
    """
    Write a single audit entry. Best-effort: never raises.

    Args:
        action: One of `AuditAction.*` (or any short uppercase string).
        actor: User who performed the action (None for system / pre-auth).
        entity_type/entity_id: What was affected (e.g. "User", 42).
        changes: JSON-serialisable dict of {field: {"old": ..., "new": ...}}.
        audit_metadata: Free-form context (avoid raw PII; use user_uuid).
        request: FastAPI Request — captures IP and user agent if provided.
        db: Optional existing session. When omitted, opens a fresh session
            so the audit row commits independently of the caller's tx.
    """
    ctx = _extract_request_context(request)
    own_session = db is None
    session: Session = db or SessionLocal()
    try:
        entry = AuditLog(
            user_id=actor.id if actor else None,
            user_uuid=actor.user_uuid if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ctx.get("ip_address"),
            user_agent=ctx.get("user_agent"),
            changes=changes,
            audit_metadata=audit_metadata,
        )
        session.add(entry)
        if own_session:
            session.commit()
        else:
            session.flush()
    except Exception as exc:
        if own_session:
            session.rollback()
        # Never let an audit-write failure propagate into a user flow. We
        # still surface it via the standard logger so it can be triaged.
        logger.error(
            "Failed to write audit log entry action=%s entity=%s/%s: %s",
            action, entity_type, entity_id, exc,
            exc_info=True,
        )
    finally:
        if own_session:
            session.close()
