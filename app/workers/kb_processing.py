"""
Background worker for knowledge-base document processing recovery.

The upload endpoint kicks off document processing as an in-process asyncio
task, which does NOT survive a process restart/redeploy. A document uploaded
just before a restart can therefore be orphaned at `is_processed=False`
forever. This worker sweeps for such documents and re-runs the (idempotent)
full pipeline: text extraction → chunking → summary → embeddings.

Run periodically via cron (or a systemd timer) so processing is self-healing
even between restarts.
"""
import asyncio
import logging

from app.db.session import SessionLocal
from app.services.background_task_service import background_task_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_pending_documents_job():
    """Re-process any documents left unprocessed by a crash/restart."""
    logger.info("Starting KB document processing recovery job")
    try:
        count = await background_task_service.recover_stuck_documents(SessionLocal)
        logger.info(f"KB recovery job complete — re-processed {count} document(s)")
    except Exception as e:
        logger.error(f"Error in KB document processing recovery job: {e}")


if __name__ == "__main__":
    """
    Run this script periodically using cron:

    # Add to crontab (runs every 5 minutes)
    */5 * * * * cd /path/to/project && python -m app.workers.kb_processing

    Or use a systemd timer / supervisord.
    """
    asyncio.run(process_pending_documents_job())
