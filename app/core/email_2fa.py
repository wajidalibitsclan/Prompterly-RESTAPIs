"""
Email-based 2FA helpers.

This module owns the lifecycle of email-delivered one-time codes used as a
second-factor method alongside TOTP. Codes are:

  * 6 digits (generated via `secrets.randbelow` for uniform distribution)
  * Stored hashed in the users table (SHA-256 hex) — the DB never holds a
    plaintext OTP
  * Scoped by `purpose` so a code issued during enrolment setup cannot be
    replayed on the login path (and vice versa)
  * Time-boxed — default TTL 5 minutes, enforced on verify
  * Single-use — cleared on successful verification
"""
import hashlib
import secrets
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.timezone import now_naive
from app.db.models.user import User


# A code valid for 5 minutes gives the user time to switch to their inbox
# without making brute-force attacks easier — the search space is 10^6 and
# login endpoints are rate-limited.
EMAIL_OTP_TTL = timedelta(minutes=5)

PURPOSE_SETUP = "setup"
PURPOSE_LOGIN = "login"


def generate_code() -> str:
    """Return a 6-digit numeric OTP as a zero-padded string."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_code(code: str) -> str:
    """SHA-256 hex digest of a code. Used for both storage and comparison."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def issue_email_code(
    user: User,
    db: Session,
    purpose: str,
) -> str:
    """
    Generate a fresh email OTP for `user`, store its hash on the user row,
    and return the plaintext code so the caller can send it in an email.

    Replaces any previous outstanding code — only the most recent OTP is
    valid. Caller is responsible for committing the session if it wants
    the write persisted before sending the email.
    """
    code = generate_code()
    user.email_2fa_code_hash = hash_code(code)
    user.email_2fa_expires_at = now_naive() + EMAIL_OTP_TTL
    user.email_2fa_purpose = purpose
    db.add(user)
    db.commit()
    return code


def verify_email_code(
    user: User,
    code: str,
    purpose: str,
) -> bool:
    """
    Check a user-supplied code against the stored hash. Constant-time
    comparison, purpose-scoped, TTL-enforced. Does NOT clear the stored
    code — the caller should call `clear_email_code` on success so the
    code cannot be replayed.
    """
    if not user.email_2fa_code_hash or not user.email_2fa_expires_at:
        return False
    if user.email_2fa_purpose != purpose:
        return False
    if now_naive() >= user.email_2fa_expires_at:
        return False
    return secrets.compare_digest(user.email_2fa_code_hash, hash_code(code))


def clear_email_code(user: User, db: Session) -> None:
    """Invalidate any outstanding email OTP on the user row."""
    user.email_2fa_code_hash = None
    user.email_2fa_expires_at = None
    user.email_2fa_purpose = None
    db.add(user)
    db.commit()


def mask_email(email: str) -> Optional[str]:
    """
    Mask an email address for display in API responses. Returns e.g.
    'w********@example.com' so the UI can confirm where the OTP went
    without echoing the full address in logs or browser devtools.
    """
    if not email or "@" not in email:
        return None
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}{'*' * max(1, len(local) - 1)}@{domain}"
