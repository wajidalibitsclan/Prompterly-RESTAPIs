"""
Audit log cleanup worker.
Deletes audit log entries older than 12 months per security doc.
Run monthly via cron.
"""
import logging
from datetime import timedelta

from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.timezone import now_naive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_audit_logs():
    """Delete audit log entries older than 12 months."""
    db = SessionLocal()
    cutoff = now_naive() - timedelta(days=365)

    try:
        result = db.execute(
            text("DELETE FROM audit_logs WHERE created_at < :cutoff"),
            {"cutoff": cutoff}
        )
        deleted = result.rowcount
        db.commit()
        logger.info(f"Audit log cleanup: deleted {deleted} entries older than {cutoff.date()}")
    except Exception as e:
        db.rollback()
        logger.error(f"Audit log cleanup failed: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_audit_logs()
