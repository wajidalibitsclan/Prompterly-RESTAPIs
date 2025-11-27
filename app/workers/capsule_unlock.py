"""
Background worker for time capsule unlocking
This should be run as a scheduled task (cron job or celery beat)
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.note_service import note_service
from app.services.email_service import send_notification_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def unlock_capsules_job():
    """
    Check and unlock time capsules
    Should be run periodically (e.g., every hour)
    """
    logger.info("Starting capsule unlock job")
    
    db = SessionLocal()
    
    try:
        # Unlock ready capsules
        unlocked_capsules = await note_service.unlock_capsules(db)
        
        if unlocked_capsules:
            logger.info(f"Unlocked {len(unlocked_capsules)} capsules")
            
            # Send notification emails
            for capsule in unlocked_capsules:
                try:
                    # Get user email
                    from app.db.models.user import User
                    user = db.query(User).filter(User.id == capsule.user_id).first()
                    
                    if user and user.email:
                        # Send notification
                        await send_notification_email(
                            to_email=user.email,
                            user_name=user.name,
                            notification_type="capsule_unlocked",
                            data={
                                "capsule_title": capsule.title,
                                "capsule_id": capsule.id
                            }
                        )
                        
                        logger.info(f"Sent unlock notification to {user.email}")
                
                except Exception as e:
                    logger.error(f"Error sending notification for capsule {capsule.id}: {str(e)}")
        else:
            logger.info("No capsules ready to unlock")
    
    except Exception as e:
        logger.error(f"Error in unlock capsules job: {str(e)}")
    
    finally:
        db.close()
    
    logger.info("Capsule unlock job completed")


if __name__ == "__main__":
    """
    Run this script periodically using cron:
    
    # Add to crontab (runs every hour)
    0 * * * * cd /path/to/project && python -m app.workers.capsule_unlock
    
    Or use with supervisord, systemd timer, or celery beat
    """
    asyncio.run(unlock_capsules_job())
