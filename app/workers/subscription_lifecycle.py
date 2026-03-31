"""
Subscription lifecycle background worker.
Handles automated email triggers for:
  - Annual renewal reminders (30 days and 7 days before)
  - Data deletion reminder at 60 days after pause (PDF #15)
  - Actual data deletion at 90 days / scheduled date (PDF #16)
  - Voluntary unsubscribe 30-day deletion

Should be run as a daily scheduled task (cron job or celery beat).
"""
import logging
from datetime import timedelta

from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.billing import LoungeSubscription, SubscriptionStatus
from app.db.models.chat import ChatThread, ChatMessage
from app.db.models.note import Note, TimeCapsule
from app.core.timezone import now_naive
from app.core.config import settings
from app.core.security import hash_password
from app.services.email_service import (
    send_annual_renewal_30day_sync,
    send_annual_renewal_7day_sync,
    send_data_deletion_reminder_sync,
    send_data_deleted_sync,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_base_urls() -> dict:
    base = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "https://prompterly.ai"
    return {
        "manage": f"{base}/settings/subscriptions",
        "dashboard": f"{base}/dashboard",
        "update_payment": f"{base}/settings/payment",
        "reactivate": f"{base}/settings/payment",
        "signup": base,
    }


def run_renewal_reminders():
    """
    Send renewal reminder emails for annual subscriptions.
    - 30 days before renewal (PDF Email #9)
    - 7 days before renewal  (PDF Email #10)
    """
    db = SessionLocal()
    urls = _get_base_urls()
    today = now_naive().date()
    sent_count = 0

    try:
        active_subs = db.query(LoungeSubscription).filter(
            LoungeSubscription.status == SubscriptionStatus.ACTIVE,
            LoungeSubscription.plan_type == "yearly",
        ).all()

        for sub in active_subs:
            if not sub.renews_at:
                continue

            days_until = (sub.renews_at.date() - today).days
            user = db.query(User).filter(User.id == sub.user_id).first()
            if not user:
                continue

            lounge = sub.lounge
            mentor_name = lounge.title if lounge else "your mentor"
            renewal_date = sub.renews_at.strftime("%B %d, %Y")
            amount = f"${sub.price_cents / 100:.2f} USD"

            if days_until == 30:
                send_annual_renewal_30day_sync(
                    user.email, user.name, mentor_name,
                    renewal_date, amount, urls["manage"]
                )
                sent_count += 1
                logger.info(f"Sent 30-day renewal reminder to {user.email}")

            elif days_until == 7:
                send_annual_renewal_7day_sync(
                    user.email, user.name, mentor_name,
                    renewal_date, amount, urls["manage"]
                )
                sent_count += 1
                logger.info(f"Sent 7-day renewal reminder to {user.email}")

    except Exception as e:
        logger.error(f"Error in renewal reminders: {e}", exc_info=True)
    finally:
        db.close()

    logger.info(f"Renewal reminders: {sent_count} emails sent")


def run_data_lifecycle():
    """
    Handle data lifecycle based on User.data_deletion_scheduled_at and account_paused_at.

    - 60 days after pause: send deletion reminder (PDF #15)
    - At scheduled deletion date: permanently delete user content + send email (PDF #16)
    """
    db = SessionLocal()
    urls = _get_base_urls()
    now = now_naive()
    today = now.date()
    sent_count = 0
    deleted_count = 0

    try:
        # ── Send 60-day deletion reminders ────────────────────────────────
        # Users whose account was paused ~60 days ago and deletion is scheduled
        paused_users = db.query(User).filter(
            User.account_paused_at.isnot(None),
            User.data_deletion_scheduled_at.isnot(None),
        ).all()

        for user in paused_users:
            days_since_pause = (today - user.account_paused_at.date()).days

            # Send reminder at exactly 60 days after pause
            if days_since_pause == 60:
                deletion_date = user.data_deletion_scheduled_at.strftime("%B %d, %Y")
                send_data_deletion_reminder_sync(
                    user.email, user.name, deletion_date, urls["reactivate"]
                )
                sent_count += 1
                logger.info(f"Sent 60-day deletion reminder to {user.email}")

        # ── Execute scheduled data deletions ──────────────────────────────
        # Users whose deletion date has arrived
        users_to_delete = db.query(User).filter(
            User.data_deletion_scheduled_at.isnot(None),
            User.data_deletion_scheduled_at <= now,
        ).all()

        for user in users_to_delete:
            # Skip users under legal hold
            if user.legal_hold:
                logger.info(f"Skipping deletion for user {user.id} — under legal hold")
                continue

            try:
                _permanently_delete_user_data(user, db)

                # Send data deleted email (PDF #16)
                send_data_deleted_sync(user.email, user.name, urls["signup"])
                deleted_count += 1
                logger.info(f"Data permanently deleted for user {user.id} ({user.email})")

            except Exception as e:
                logger.error(f"Error deleting data for user {user.id}: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in data lifecycle: {e}", exc_info=True)
    finally:
        db.close()

    logger.info(f"Data lifecycle: {sent_count} reminders, {deleted_count} deletions")


def _permanently_delete_user_data(user: User, db):
    """
    Permanently delete all user-generated content and anonymise identity.

    Deletes:
      - All chat messages in user's threads
      - All chat threads
      - All notes
      - All time capsules

    Anonymises:
      - Name, email, avatar, stripe_customer_id
      - Password hash, TOTP secret

    Clears:
      - data_deletion_scheduled_at (marks as complete)
      - account_paused_at
      - payment_failure_count
    """
    user_id = user.id

    # 1. Delete chat messages for all user's threads
    thread_ids = [t.id for t in db.query(ChatThread.id).filter(ChatThread.user_id == user_id).all()]
    if thread_ids:
        db.query(ChatMessage).filter(ChatMessage.thread_id.in_(thread_ids)).delete(synchronize_session=False)
        db.query(ChatThread).filter(ChatThread.id.in_(thread_ids)).delete(synchronize_session=False)

    # 2. Delete notes
    db.query(Note).filter(Note.user_id == user_id).delete(synchronize_session=False)

    # 3. Delete time capsules
    db.query(TimeCapsule).filter(TimeCapsule.user_id == user_id).delete(synchronize_session=False)

    # 4. Anonymise user identity
    user.email = f"deleted_{user_id}@deleted.prompterly.ai"
    user.name = "Deleted User"
    user.avatar_url = None
    user.stripe_customer_id = None
    user.password_hash = hash_password(f"deleted_{user_id}_{now_naive().timestamp()}")
    user.totp_secret = None
    user.is_2fa_enabled = False

    # 5. Clear lifecycle fields
    user.data_deletion_scheduled_at = None
    user.account_paused_at = None
    user.payment_failure_count = 0

    db.commit()


def run_all():
    """Run all subscription lifecycle jobs."""
    logger.info("=" * 60)
    logger.info("Starting subscription lifecycle worker")
    logger.info("=" * 60)

    run_renewal_reminders()
    run_data_lifecycle()

    logger.info("Subscription lifecycle worker completed")


if __name__ == "__main__":
    """
    Run daily via cron:
      0 8 * * * cd /path/to/project && .venv/bin/python -m app.workers.subscription_lifecycle
    """
    run_all()
