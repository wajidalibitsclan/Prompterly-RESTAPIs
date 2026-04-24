"""
KMS-backed master key provider — Security Standard §3 (Task 14).

Encryption keys MUST be managed through a secure key management service and
MUST NOT be stored in the application database. This module is the single
entry point the rest of the app uses to obtain the 32-byte AES-256 master key.

## Production mode (AWS KMS envelope encryption)

Set two environment variables:

    AWS_KMS_KEY_ID               = arn:aws:kms:<region>:<acct>:key/<uuid>
    AWS_KMS_DATA_KEY_CIPHERTEXT  = <base64-encoded ciphertext blob>

The ciphertext blob is produced ONCE during setup by
`scripts/generate_kms_data_key.py`. It is the output of
`kms.GenerateDataKey(KeyId=..., KeySpec='AES_256')['CiphertextBlob']`.

At runtime this module:
  1. Reads the ciphertext blob from settings.
  2. Calls `kms.Decrypt(CiphertextBlob=...)` to unwrap the data key.
  3. Caches the 32-byte plaintext key **in memory only** for the life of
     the process.
  4. Never logs, prints, or persists the plaintext key.

The AWS KMS customer-managed key (CMK) never leaves KMS. Rotating the data
key is a matter of generating a new ciphertext blob and redeploying.

## Development / CI fallback

If `AWS_KMS_KEY_ID` is not set, the module falls back to deriving a 32-byte
key from `ENCRYPTION_KEY` via SHA-256. This path is explicitly for local
development and must NOT be used in production — `APP_ENV=production` with
no KMS configuration raises an error at import.
"""
import base64
import hashlib
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class KmsConfigurationError(RuntimeError):
    """Raised when KMS is required but misconfigured."""


_cached_master_key: Optional[bytes] = None


def _load_key_from_kms() -> bytes:
    """
    Decrypt the configured data-key ciphertext blob via AWS KMS and return
    the plaintext 32-byte key.

    Raises KmsConfigurationError on any failure — never silently falls back.
    """
    key_id = settings.AWS_KMS_KEY_ID
    ciphertext_b64 = settings.AWS_KMS_DATA_KEY_CIPHERTEXT

    if not ciphertext_b64:
        raise KmsConfigurationError(
            "AWS_KMS_KEY_ID is set but AWS_KMS_DATA_KEY_CIPHERTEXT is missing. "
            "Run scripts/generate_kms_data_key.py to create one."
        )

    try:
        import boto3
    except ImportError as exc:
        raise KmsConfigurationError(
            "boto3 is required for KMS integration but is not installed."
        ) from exc

    try:
        ciphertext_blob = base64.b64decode(ciphertext_b64)
    except Exception as exc:
        raise KmsConfigurationError(
            "AWS_KMS_DATA_KEY_CIPHERTEXT is not valid base64."
        ) from exc

    region = settings.AWS_REGION or "ap-southeast-2"
    client = boto3.client("kms", region_name=region)

    try:
        response = client.decrypt(
            CiphertextBlob=ciphertext_blob,
            KeyId=key_id,
        )
    except Exception as exc:
        # Deliberately do NOT include request data in the error — it may
        # contain key material in some boto failure modes.
        raise KmsConfigurationError(
            f"KMS Decrypt call failed for key {key_id}: {type(exc).__name__}"
        ) from exc

    plaintext = response.get("Plaintext")
    if not plaintext or len(plaintext) != 32:
        raise KmsConfigurationError(
            "KMS returned a data key of unexpected length "
            "(expected 32 bytes for AES-256)."
        )

    logger.info("Master encryption key unwrapped from AWS KMS (CMK=%s)", key_id)
    return plaintext


def _derive_local_key() -> bytes:
    """
    Dev-only fallback: derive a 32-byte key from ENCRYPTION_KEY via SHA-256.
    """
    raw_key = settings.ENCRYPTION_KEY
    if not raw_key:
        raise KmsConfigurationError(
            "No key material available: set AWS_KMS_KEY_ID + "
            "AWS_KMS_DATA_KEY_CIPHERTEXT for production, or ENCRYPTION_KEY "
            "for local development."
        )
    logger.warning(
        "Using ENCRYPTION_KEY-derived local master key. "
        "This path is for development only — configure AWS KMS in production."
    )
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def get_master_key() -> bytes:
    """
    Return the 32-byte AES-256 master key.

    First call fetches from KMS (or derives locally) and caches the result.
    Subsequent calls reuse the cached value. The plaintext key lives only
    in process memory.
    """
    global _cached_master_key
    if _cached_master_key is not None:
        return _cached_master_key

    if settings.AWS_KMS_KEY_ID:
        _cached_master_key = _load_key_from_kms()
    else:
        if settings.APP_ENV == "production":
            raise KmsConfigurationError(
                "AWS_KMS_KEY_ID is required when APP_ENV=production. "
                "Application-level encryption keys must not be derived from "
                "environment variables in production (Security Standard §3)."
            )
        _cached_master_key = _derive_local_key()

    return _cached_master_key


def reset_cache_for_tests() -> None:
    """Clear the cached key — test-only helper."""
    global _cached_master_key
    _cached_master_key = None
