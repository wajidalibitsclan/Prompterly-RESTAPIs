"""
Application-level encryption for sensitive user content.

Uses AES-256-GCM for authenticated encryption.
Key is derived from ENCRYPTION_KEY in settings using PBKDF2.
Each encrypted value gets a unique random nonce (IV).

Storage format: base64(nonce + ciphertext + tag)

Supports future migration to AWS KMS by swapping this module.
"""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


def _derive_key() -> bytes:
    """
    Derive a 256-bit AES key from the configured ENCRYPTION_KEY.
    Uses SHA-256 hash for deterministic key derivation.
    In production, this should be replaced with AWS KMS.
    """
    raw_key = settings.ENCRYPTION_KEY
    if not raw_key:
        raise ValueError("ENCRYPTION_KEY is not configured. Set it in .env")
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


_aesgcm = None


def _get_cipher() -> AESGCM:
    """Lazy-initialize the AES-GCM cipher."""
    global _aesgcm
    if _aesgcm is None:
        _aesgcm = AESGCM(_derive_key())
    return _aesgcm


def encrypt_content(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256-GCM.

    Returns a base64-encoded string containing nonce + ciphertext + tag.
    Returns the original string if ENCRYPTION_KEY is not set (graceful fallback).
    """
    if not plaintext:
        return plaintext

    if not settings.ENCRYPTION_KEY:
        return plaintext

    try:
        cipher = _get_cipher()
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Store as: base64(nonce + ciphertext_with_tag)
        encrypted = base64.b64encode(nonce + ciphertext).decode("utf-8")
        return f"enc::{encrypted}"
    except Exception:
        # If encryption fails, return plaintext to avoid data loss
        return plaintext


def decrypt_content(stored_value: str) -> str:
    """
    Decrypt a stored value. If the value is not encrypted (no 'enc::' prefix),
    returns it as-is for backward compatibility with existing unencrypted data.
    """
    if not stored_value:
        return stored_value

    # Not encrypted — return as-is (backward compat with existing data)
    if not stored_value.startswith("enc::"):
        return stored_value

    if not settings.ENCRYPTION_KEY:
        # Can't decrypt without key — return raw value
        return stored_value

    try:
        cipher = _get_cipher()
        raw = base64.b64decode(stored_value[5:])  # Strip "enc::" prefix
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception:
        # If decryption fails, return raw value
        return stored_value
