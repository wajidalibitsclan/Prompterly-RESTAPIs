"""
Application-level encryption for sensitive user content.

Uses AES-256-GCM for authenticated encryption. The 32-byte master key is
obtained from `app.core.kms.get_master_key()` — in production this unwraps
a data key from AWS KMS (Security Standard §3, Task 14). The plaintext key
lives only in process memory and is never written to the database or disk.

Each encrypted value gets a unique random 96-bit nonce (IV).
Storage format: ``enc::<base64(nonce + ciphertext + tag)>``
"""
import os
import base64
import logging
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.core.kms import get_master_key, KmsConfigurationError

logger = logging.getLogger(__name__)

_aesgcm: Optional[AESGCM] = None


def _get_cipher() -> Optional[AESGCM]:
    """
    Lazy-initialize the AES-GCM cipher from the KMS-unwrapped master key.

    Returns None if no key material is available (dev machines without
    ENCRYPTION_KEY or KMS configured) — callers treat this as "encryption
    disabled" and fall back to plaintext storage.
    """
    global _aesgcm
    if _aesgcm is not None:
        return _aesgcm

    try:
        key = get_master_key()
    except KmsConfigurationError as exc:
        # In production this should never happen — KMS misconfiguration is
        # fatal at startup via main.py. In dev, log once and fall back.
        logger.warning("Encryption disabled: %s", exc)
        return None

    _aesgcm = AESGCM(key)
    return _aesgcm


def _is_encryption_enabled() -> bool:
    return bool(settings.AWS_KMS_KEY_ID or settings.ENCRYPTION_KEY)


def encrypt_content(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256-GCM.

    Returns a string of the form ``enc::<base64>``. Returns the original
    string unchanged if no key material is configured (graceful fallback
    for dev machines without encryption set up).
    """
    if not plaintext:
        return plaintext

    if not _is_encryption_enabled():
        return plaintext

    cipher = _get_cipher()
    if cipher is None:
        return plaintext

    try:
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
        encrypted = base64.b64encode(nonce + ciphertext).decode("utf-8")
        return f"enc::{encrypted}"
    except Exception:
        # Never lose user data to an encryption bug — log and store plaintext.
        logger.exception("encrypt_content failed; storing plaintext")
        return plaintext


def decrypt_content(stored_value: str) -> str:
    """
    Decrypt a stored value. Values without the ``enc::`` prefix are returned
    as-is for backward compatibility with legacy unencrypted rows.
    """
    if not stored_value:
        return stored_value

    if not stored_value.startswith("enc::"):
        return stored_value

    cipher = _get_cipher()
    if cipher is None:
        return stored_value

    try:
        raw = base64.b64decode(stored_value[5:])
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception:
        logger.exception("decrypt_content failed; returning raw value")
        return stored_value
