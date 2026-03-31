"""
Secrets Manager integration.
Loads secrets from AWS Secrets Manager if configured, otherwise falls back to .env.

To enable:
  1. Set AWS_SECRETS_MANAGER_ARN in .env
  2. Ensure AWS credentials have secretsmanager:GetSecretValue permission
  3. Store secrets in AWS Secrets Manager as a JSON object with the same key names as .env

The secret JSON should look like:
{
  "SECRET_KEY": "...",
  "JWT_SECRET_KEY": "...",
  "ENCRYPTION_KEY": "...",
  "DATABASE_URL": "...",
  "POSTMARK_SERVER_TOKEN": "...",
  "STRIPE_SECRET_KEY": "...",
  ...
}
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


def load_secrets_from_aws():
    """
    Load secrets from AWS Secrets Manager and inject into environment variables.
    Only runs if AWS_SECRETS_MANAGER_ARN is set.
    Falls back silently to .env if not configured or on error.
    """
    secret_arn = os.environ.get("AWS_SECRETS_MANAGER_ARN")
    if not secret_arn:
        return  # Not configured — use .env

    try:
        import boto3

        region = os.environ.get("AWS_REGION", "ap-southeast-2")
        client = boto3.client("secretsmanager", region_name=region)

        response = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")

        if not secret_string:
            logger.warning("AWS Secrets Manager returned empty secret")
            return

        secrets = json.loads(secret_string)

        # Inject into environment (won't override existing env vars)
        loaded = 0
        for key, value in secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
                loaded += 1

        logger.info(f"Loaded {loaded} secrets from AWS Secrets Manager")

    except ImportError:
        logger.warning("boto3 not installed — cannot use AWS Secrets Manager")
    except Exception as e:
        logger.warning(f"Failed to load from AWS Secrets Manager: {e}. Falling back to .env")


# Auto-load on import (before Settings class reads env vars)
load_secrets_from_aws()
