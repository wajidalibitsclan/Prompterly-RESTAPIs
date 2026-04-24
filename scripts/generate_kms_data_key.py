#!/usr/bin/env python3
"""
One-time bootstrap: generate a KMS-wrapped AES-256 data key.

Usage:
    export AWS_REGION=ap-southeast-2
    export AWS_PROFILE=prompterly-prod          # or AWS_ACCESS_KEY_ID/SECRET
    python scripts/generate_kms_data_key.py <kms-cmk-arn>

The AWS principal running this must have `kms:GenerateDataKey` on the CMK.

Output is a single base64 string — the encrypted data key. Store it as
`AWS_KMS_DATA_KEY_CIPHERTEXT` in AWS Secrets Manager (NOT in .env, NOT in
git). Combined with `AWS_KMS_KEY_ID=<cmk-arn>`, the app will unwrap it at
startup via `kms:Decrypt` and cache the plaintext key in memory only.

IMPORTANT: the plaintext data key is printed ONCE (for sanity-check
verification against an existing encrypted database). After the first run
in production you should regenerate and re-encrypt every encrypted column,
then discard the plaintext — see docs/encryption-rotation.md.
"""
import base64
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    cmk_arn = sys.argv[1]

    try:
        import boto3
    except ImportError:
        print("boto3 is required. pip install boto3", file=sys.stderr)
        return 1

    client = boto3.client("kms")
    try:
        resp = client.generate_data_key(KeyId=cmk_arn, KeySpec="AES_256")
    except Exception as exc:
        print(f"KMS GenerateDataKey failed: {exc}", file=sys.stderr)
        return 1

    ciphertext_b64 = base64.b64encode(resp["CiphertextBlob"]).decode()
    plaintext_fingerprint = base64.b64encode(resp["Plaintext"][:8]).decode()

    print("=" * 72)
    print("KMS DATA KEY GENERATED")
    print("=" * 72)
    print(f"CMK ARN:  {cmk_arn}")
    print()
    print("Store these two values in AWS Secrets Manager (or equivalent):")
    print()
    print(f"  AWS_KMS_KEY_ID={cmk_arn}")
    print(f"  AWS_KMS_DATA_KEY_CIPHERTEXT={ciphertext_b64}")
    print()
    print("Sanity-check fingerprint (first 8 bytes of plaintext key, base64):")
    print(f"  {plaintext_fingerprint}")
    print()
    print("The plaintext key is NOT printed. It only exists in KMS's response")
    print("and is discarded when this script exits. Restart the API after")
    print("rotating secrets so the new key is loaded.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
