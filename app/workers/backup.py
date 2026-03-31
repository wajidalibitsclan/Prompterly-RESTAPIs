"""
Automated database backup worker.
Creates daily MySQL dumps and uploads to S3 with server-side encryption (AES-256).
Retains 30 daily backups and 12 monthly backups per security doc.

Run daily via cron:
  0 2 * * * cd /path/to/project && .venv/bin/python -m app.workers.backup
"""
import subprocess
import logging
import os
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_backup():
    """Create MySQL dump and upload to S3 with encryption."""
    from app.core.config import settings

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Parse DATABASE_URL for mysqldump
    db_url = settings.DATABASE_URL
    # mysql+pymysql://user:password@host:port/database
    try:
        parts = db_url.replace("mysql+pymysql://", "").split("@")
        user_pass = parts[0]
        host_db = parts[1]
        db_user, db_pass = user_pass.split(":")
        host_port, db_name = host_db.split("/")
        if ":" in host_port:
            db_host, db_port = host_port.split(":")
        else:
            db_host = host_port
            db_port = "3306"
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        return

    dump_file = backup_dir / f"prompterly_backup_{timestamp}.sql.gz"

    # Create compressed dump
    logger.info(f"Creating database backup: {dump_file}")
    try:
        cmd = (
            f"mysqldump -h {db_host} -P {db_port} -u {db_user} "
            f"-p'{db_pass}' --single-transaction --routines --triggers "
            f"{db_name} | gzip > {dump_file}"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            logger.error(f"mysqldump failed: {result.stderr}")
            return

        file_size = dump_file.stat().st_size
        logger.info(f"Backup created: {dump_file} ({file_size / 1024 / 1024:.1f} MB)")

    except subprocess.TimeoutExpired:
        logger.error("mysqldump timed out after 10 minutes")
        return
    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        return

    # Upload to S3 with server-side encryption
    if settings.AWS_ACCESS_KEY_ID and settings.S3_BUCKET_NAME:
        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
                endpoint_url=settings.S3_ENDPOINT_URL,
            )

            s3_key = f"backups/daily/{dump_file.name}"
            s3_client.upload_file(
                str(dump_file),
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )
            logger.info(f"Backup uploaded to S3: s3://{settings.S3_BUCKET_NAME}/{s3_key}")

            # Also copy as monthly backup on 1st of month
            if datetime.now().day == 1:
                monthly_key = f"backups/monthly/{dump_file.name}"
                s3_client.copy_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    CopySource={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
                    Key=monthly_key,
                    ServerSideEncryption="AES256",
                )
                logger.info(f"Monthly backup copied: s3://{settings.S3_BUCKET_NAME}/{monthly_key}")

            # Clean up old daily backups (keep 30)
            _cleanup_old_backups(s3_client, settings.S3_BUCKET_NAME, "backups/daily/", keep=30)

            # Clean up old monthly backups (keep 12)
            _cleanup_old_backups(s3_client, settings.S3_BUCKET_NAME, "backups/monthly/", keep=12)

        except Exception as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
    else:
        logger.warning("S3 not configured — backup stored locally only")

    # Clean up local backup files (keep last 7)
    _cleanup_local_backups(backup_dir, keep=7)

    logger.info("Backup completed")


def _cleanup_old_backups(s3_client, bucket: str, prefix: str, keep: int):
    """Delete old S3 backups, keeping the most recent `keep` files."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = response.get("Contents", [])

        if len(objects) <= keep:
            return

        # Sort by last modified, oldest first
        objects.sort(key=lambda x: x["LastModified"])
        to_delete = objects[: len(objects) - keep]

        for obj in to_delete:
            s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
            logger.info(f"Deleted old backup: {obj['Key']}")

    except Exception as e:
        logger.error(f"S3 cleanup failed: {e}")


def _cleanup_local_backups(backup_dir: Path, keep: int):
    """Delete old local backups, keeping the most recent `keep` files."""
    files = sorted(backup_dir.glob("*.sql.gz"), key=lambda f: f.stat().st_mtime)
    for f in files[: max(0, len(files) - keep)]:
        f.unlink()
        logger.info(f"Deleted old local backup: {f.name}")


if __name__ == "__main__":
    run_backup()
