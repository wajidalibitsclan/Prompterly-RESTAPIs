"""
Email service for sending transactional emails
Uses SMTP configuration from settings

All email sending functions have sync versions for use with FastAPI BackgroundTasks
to prevent blocking the main application thread.

Email logs are written to a dedicated log file for easy debugging.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.services.email_templates import (
    get_otp_email_template,
    get_mfa_otp_email_template,
    get_welcome_email_template,
    get_password_reset_otp_template,
    get_user_credentials_email_template,
    get_mentor_welcome_email_template,
    get_contact_confirmation_email_template,
    get_contact_admin_notification_template,
    get_subscription_confirmation_email_template,
    get_subscription_expiry_warning_email_template,
    get_subscription_upgrade_email_template,
    get_subscription_cancellation_email_template,
    get_payment_method_update_email_template,
    get_email_change_confirmation_template,
    get_email_change_alert_template,
    get_suspicious_login_alert_template,
    get_annual_renewal_30day_template,
    get_annual_renewal_7day_template,
    get_annual_renewal_confirmed_template,
    get_payment_failed_day0_template,
    get_payment_failed_day3_template,
    get_access_paused_template,
    get_data_deletion_reminder_template,
    get_data_deleted_template,
    get_time_capsule_delivery_template,
)


def setup_email_logger() -> logging.Logger:
    """
    Set up dedicated email logger with file handler.
    Logs are written to the file specified in EMAIL_LOG_FILE setting.
    """
    email_logger = logging.getLogger("email_service")
    email_logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers
    if email_logger.handlers:
        return email_logger

    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.EMAIL_LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    # Detailed format for email logs
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    email_logger.addHandler(file_handler)

    # Also add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    email_logger.addHandler(console_handler)

    return email_logger


# Initialize the email logger
logger = setup_email_logger()


def _send_via_postmark(
    to: List[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """Send email via Postmark API."""
    from postmarker.core import PostmarkClient

    client = PostmarkClient(server_token=settings.POSTMARK_SERVER_TOKEN)

    kwargs = {
        "From": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
        "To": ", ".join(to),
        "Subject": subject,
        "TextBody": body,
    }
    if html:
        kwargs["HtmlBody"] = html
    if cc:
        kwargs["Cc"] = ", ".join(cc)
    if bcc:
        kwargs["Bcc"] = ", ".join(bcc)

    response = client.emails.send(**kwargs)
    logger.info(f"Postmark response: MessageID={response.get('MessageID', 'N/A')}, ErrorCode={response.get('ErrorCode', 'N/A')}")

    return response.get("ErrorCode", -1) == 0


def _send_via_smtp(
    to: List[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """Send email via legacy SMTP (Mailtrap fallback)."""
    server = None
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject

        text_part = MIMEText(body, "plain")
        msg.attach(text_part)
        if html:
            html_part = MIMEText(html, "html")
            msg.attach(html_part)

        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=60)
        if settings.MAIL_TLS:
            server.ehlo()
            server.starttls()
            server.ehlo()
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        recipients = to + (cc or []) + (bcc or [])
        server.sendmail(settings.MAIL_FROM, recipients, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"SMTP Error: {type(e).__name__}: {e}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


def send_email_sync(
    to: str | List[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """
    Send email (synchronous version for background tasks).

    Uses Postmark API if POSTMARK_SERVER_TOKEN is configured,
    otherwise falls back to legacy SMTP.
    """
    if isinstance(to, str):
        to = [to]
    recipients_str = ", ".join(to)

    provider = "Postmark" if settings.POSTMARK_SERVER_TOKEN else "SMTP"
    logger.info("=" * 60)
    logger.info(f"EMAIL SEND ATTEMPT via {provider}")
    logger.info(f"To: {recipients_str}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("-" * 60)

    try:
        if settings.POSTMARK_SERVER_TOKEN:
            success = _send_via_postmark(to, subject, body, html, cc, bcc)
        else:
            success = _send_via_smtp(to, subject, body, html, cc, bcc)

        if success:
            logger.info(f"SUCCESS - Email sent to: {recipients_str}")
        else:
            logger.error(f"FAILED - Email to: {recipients_str}")
        logger.info("=" * 60)
        return success

    except Exception as e:
        logger.error(f"FAILED - {provider} Error")
        logger.error(f"To: {recipients_str}")
        logger.error(f"Subject: {subject}")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.info("=" * 60)
        return False


async def send_email(
    to: str | List[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """Send email (async wrapper)."""
    return send_email_sync(to, subject, body, html, cc, bcc)


async def send_verification_email(email: str, name: str, token: str) -> bool:
    """
    Send email verification email
    
    Args:
        email: User email
        name: User name
        token: Verification token
        
    Returns:
        True if sent successfully
    """
    verification_url = f"{settings.CORS_ORIGINS[0]}/verify-email?token={token}"
    
    body = f"""
Hi {name},

Welcome to AI Coaching Platform!

Please verify your email by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
AI Coaching Team
    """
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Welcome to AI Coaching Platform!</h2>
    <p>Hi {name},</p>
    <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" 
           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Verify Email
        </a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="word-break: break-all; color: #666;">{verification_url}</p>
    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This link will expire in 24 hours.<br>
        If you didn't create an account, please ignore this email.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">
        AI Coaching Platform<br>
        © 2025 All rights reserved
    </p>
</body>
</html>
    """
    
    return await send_email(
        to=email,
        subject="Verify your email - AI Coaching Platform",
        body=body,
        html=html
    )


async def send_password_reset_email(email: str, name: str, token: str) -> bool:
    """
    Send password reset email
    
    Args:
        email: User email
        name: User name
        token: Reset token
        
    Returns:
        True if sent successfully
    """
    reset_url = f"{settings.CORS_ORIGINS[0]}/reset-password?token={token}"
    
    body = f"""
Hi {name},

You requested a password reset for your AI Coaching Platform account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
AI Coaching Team
    """
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Password Reset Request</h2>
    <p>Hi {name},</p>
    <p>You requested a password reset for your AI Coaching Platform account.</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{reset_url}" 
           style="background-color: #DC2626; color: white; padding: 12px 30px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Reset Password
        </a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="word-break: break-all; color: #666;">{reset_url}</p>
    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This link will expire in 1 hour.<br>
        If you didn't request this, please ignore this email and your password will remain unchanged.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">
        AI Coaching Platform<br>
        © 2025 All rights reserved
    </p>
</body>
</html>
    """
    
    return await send_email(
        to=email,
        subject="Password Reset - AI Coaching Platform",
        body=body,
        html=html
    )


def send_welcome_email_sync(email: str, name: str) -> bool:
    """
    Send welcome email after successful registration (synchronous for background tasks)

    Args:
        email: User email
        name: User name

    Returns:
        True if sent successfully
    """
    # Determine the correct dashboard URL based on environment
    dashboard_url = f"{settings.CORS_ORIGINS[0]}/dashboard" if settings.CORS_ORIGINS else "https://prompterly.ai/dashboard"

    body, html = get_welcome_email_template(name, dashboard_url)

    return send_email_sync(
        to=email,
        subject="Welcome to prompterly",
        body=body,
        html=html
    )


async def send_welcome_email(email: str, name: str) -> bool:
    """
    Send welcome email after successful registration (async wrapper)

    Args:
        email: User email
        name: User name

    Returns:
        True if sent successfully
    """
    return send_welcome_email_sync(email, name)


def send_otp_email_sync(email: str, name: str, otp: str) -> bool:
    """
    Send OTP verification email (synchronous version for background tasks)

    Args:
        email: User email
        name: User name
        otp: 6-digit OTP code

    Returns:
        True if sent successfully
    """
    body, html = get_otp_email_template(name, otp)

    return send_email_sync(
        to=email,
        subject=f"{otp} is your prompterly verification code",
        body=body,
        html=html
    )


async def send_otp_email(email: str, name: str, otp: str) -> bool:
    """
    Send OTP verification email (async wrapper)
    """
    return send_otp_email_sync(email, name, otp)


def send_password_reset_otp_sync(email: str, name: str, otp: str) -> bool:
    """
    Send password reset OTP email (synchronous version for background tasks)

    Args:
        email: User email
        name: User name
        otp: 6-digit OTP code

    Returns:
        True if sent successfully
    """
    body, html = get_password_reset_otp_template(name, otp)

    return send_email_sync(
        to=email,
        subject="Reset your password",
        body=body,
        html=html
    )


async def send_notification_email(
    email: str,
    name: str,
    notification_type: str,
    data: dict
) -> bool:
    """
    Send notification email based on type
    
    Args:
        email: User email
        name: User name
        notification_type: Type of notification
        data: Notification data
        
    Returns:
        True if sent successfully
    """
    # Map notification types to email templates
    templates = {
        "capsule_unlocked": {
            "subject": "Your Time Capsule is Ready! 🎁",
            "body": f"Hi {name},\n\nYour time capsule '{data.get('title')}' has been unlocked!\nLog in to view your message from the past.\n\nBest regards,\nAI Coaching Team"
        },
        "new_message": {
            "subject": "New Message from Your Mentor",
            "body": f"Hi {name},\n\nYou have a new message in {data.get('lounge_name')}.\nLog in to view and respond.\n\nBest regards,\nAI Coaching Team"
        },
        "subscription_expiring": {
            "subject": "Your Subscription is Expiring Soon",
            "body": f"Hi {name},\n\nYour subscription will expire on {data.get('expires_at')}.\nRenew now to continue enjoying all features.\n\nBest regards,\nAI Coaching Team"
        }
    }
    
    template = templates.get(notification_type)
    if not template:
        logger.warning(f"Unknown notification type: {notification_type}")
        return False
    
    return await send_email(
        to=email,
        subject=template["subject"],
        body=template["body"]
    )


def send_user_credentials_email_sync(email: str, name: str, password: str) -> bool:
    """
    Send credentials email to user created by admin (synchronous for background tasks)

    Args:
        email: User's email (also login username)
        name: User's name
        password: Temporary password

    Returns:
        True if sent successfully
    """
    # Determine login URL from CORS origins
    login_url = f"{settings.CORS_ORIGINS[0]}/login" if settings.CORS_ORIGINS else "https://prompterly.ai/login"

    body, html = get_user_credentials_email_template(name, email, password, login_url)

    return send_email_sync(
        to=email,
        subject="Welcome to Prompterly - Your Account Credentials",
        body=body,
        html=html
    )


def send_mentor_welcome_email_sync(email: str, name: str) -> bool:
    """
    Send welcome email to mentor created by admin (synchronous for background tasks)
    No credentials since there's no mentor portal

    Args:
        email: Mentor's email
        name: Mentor's name

    Returns:
        True if sent successfully
    """
    # Determine Prompterly URL from CORS origins
    prompterly_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "https://prompterly.ai"

    body, html = get_mentor_welcome_email_template(name, prompterly_url)

    return send_email_sync(
        to=email,
        subject="Welcome to Prompterly - You're Now a Mentor!",
        body=body,
        html=html
    )


def send_contact_confirmation_email_sync(email: str, name: str, subject: str) -> bool:
    """
    Send contact form confirmation email to user (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        subject: Subject of their inquiry

    Returns:
        True if sent successfully
    """
    body, html = get_contact_confirmation_email_template(name, subject)

    return send_email_sync(
        to=email,
        subject="Thank you for contacting Prompterly",
        body=body,
        html=html
    )


def send_contact_admin_notification_sync(
    admin_email: str,
    name: str,
    email: str,
    subject: str,
    message: str,
    ip_address: str,
    submitted_at: str,
    message_id: int
) -> bool:
    """
    Send contact form notification to admin (synchronous for background tasks)

    Args:
        admin_email: Admin email to receive notification
        name: Sender's name
        email: Sender's email
        subject: Message subject
        message: Message content
        ip_address: Sender's IP
        submitted_at: Submission timestamp
        message_id: Database message ID

    Returns:
        True if sent successfully
    """
    body, html = get_contact_admin_notification_template(
        name, email, subject, message, ip_address, submitted_at, message_id
    )

    return send_email_sync(
        to=admin_email,
        subject=f"[Prompterly Contact] {subject}",
        body=body,
        html=html
    )


def send_subscription_confirmation_email_sync(
    email: str,
    name: str,
    lounge_name: str,
    mentor_name: str,
    plan_type: str,
    price: str,
    next_billing_date: str
) -> bool:
    """
    Send subscription confirmation email (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        lounge_name: Name of the subscribed lounge
        mentor_name: Name of the lounge mentor
        plan_type: Subscription plan type (monthly/yearly)
        price: Subscription price
        next_billing_date: Next billing date

    Returns:
        True if sent successfully
    """
    dashboard_url = f"{settings.CORS_ORIGINS[0]}/dashboard" if settings.CORS_ORIGINS else "https://prompterly.ai/dashboard"

    body, html = get_subscription_confirmation_email_template(
        name, lounge_name, mentor_name, plan_type, price, next_billing_date, dashboard_url
    )

    return send_email_sync(
        to=email,
        subject=f"Welcome to {lounge_name} - Subscription Confirmed!",
        body=body,
        html=html
    )


def send_subscription_expiry_warning_email_sync(
    email: str,
    name: str,
    lounge_name: str,
    expiry_date: str,
    days_remaining: int
) -> bool:
    """
    Send subscription expiry warning email (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        lounge_name: Name of the lounge
        expiry_date: Subscription expiry date
        days_remaining: Days until expiry

    Returns:
        True if sent successfully
    """
    renewal_url = f"{settings.CORS_ORIGINS[0]}/lounges" if settings.CORS_ORIGINS else "https://prompterly.ai/lounges"

    body, html = get_subscription_expiry_warning_email_template(
        name, lounge_name, expiry_date, days_remaining, renewal_url
    )

    return send_email_sync(
        to=email,
        subject=f"Your {lounge_name} subscription expires in {days_remaining} days",
        body=body,
        html=html
    )


def send_subscription_upgrade_email_sync(
    email: str,
    name: str,
    lounge_name: str,
    old_plan: str,
    new_plan: str,
    new_price: str,
    savings: str,
    next_billing_date: str
) -> bool:
    """
    Send subscription upgrade confirmation email (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        lounge_name: Name of the lounge
        old_plan: Previous plan type
        new_plan: New plan type
        new_price: New subscription price
        savings: Amount saved by upgrading
        next_billing_date: Next billing date

    Returns:
        True if sent successfully
    """
    dashboard_url = f"{settings.CORS_ORIGINS[0]}/dashboard" if settings.CORS_ORIGINS else "https://prompterly.ai/dashboard"

    body, html = get_subscription_upgrade_email_template(
        name, lounge_name, old_plan, new_plan, new_price, savings, next_billing_date, dashboard_url
    )

    return send_email_sync(
        to=email,
        subject=f"Subscription Upgraded - You're saving {savings}!",
        body=body,
        html=html
    )


def send_subscription_cancellation_email_sync(
    email: str,
    name: str,
    lounge_name: str,
    access_end_date: str,
    feedback_url: Optional[str] = None
) -> bool:
    """
    Send subscription cancellation confirmation email (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        lounge_name: Name of the lounge
        access_end_date: Date when access ends
        feedback_url: Optional URL for feedback form

    Returns:
        True if sent successfully
    """
    body, html = get_subscription_cancellation_email_template(
        name, lounge_name, access_end_date, feedback_url
    )

    return send_email_sync(
        to=email,
        subject=f"Your {lounge_name} subscription has been cancelled",
        body=body,
        html=html
    )


def send_payment_method_update_email_sync(
    email: str,
    name: str,
    card_last_four: str,
    card_brand: str,
    updated_at: str
) -> bool:
    """
    Send payment method update confirmation email (synchronous for background tasks)

    Args:
        email: User's email
        name: User's name
        card_last_four: Last 4 digits of the card
        card_brand: Card brand (Visa, Mastercard, etc.)
        updated_at: Timestamp of the update

    Returns:
        True if sent successfully
    """
    body, html = get_payment_method_update_email_template(
        name, card_last_four, card_brand, updated_at
    )

    return send_email_sync(
        to=email,
        subject="Payment Method Updated - Prompterly",
        body=body,
        html=html
    )


def send_email_change_confirmation_sync(email: str, name: str) -> bool:
    """
    Send email change confirmation to the NEW email address.
    PDF Email #3: 'Your account details have been updated'
    """
    body, html = get_email_change_confirmation_template(name)
    return send_email_sync(
        to=email,
        subject="Your account details have been updated",
        body=body,
        html=html
    )


def send_email_change_alert_sync(
    email: str, name: str, secure_account_url: str
) -> bool:
    """
    Send security alert to the OLD email address when email is changed.
    PDF Email #4: 'Important: Your account details were updated'
    Includes tokenised 'Secure my account' recovery link.
    """
    body, html = get_email_change_alert_template(name, secure_account_url)
    return send_email_sync(
        to=email,
        subject="Important: Your account details were updated",
        body=body,
        html=html
    )


def send_suspicious_login_alert_sync(
    email: str,
    name: str,
    login_time: str,
    device_info: str,
    reset_password_url: str,
) -> bool:
    """
    Send suspicious login / new device alert email.
    PDF Email #7: 'New login detected'
    """
    body, html = get_suspicious_login_alert_template(
        name, login_time, device_info, reset_password_url
    )
    return send_email_sync(
        to=email,
        subject="New login detected",
        body=body,
        html=html
    )


# ── New Email Sending Functions (PDF Emails #6, #9-16, #18) ──────────────────

def send_mfa_otp_email_sync(email: str, name: str, otp: str) -> bool:
    """PDF Email #6: One Time Password (MFA) for new device/email change."""
    body, html = get_mfa_otp_email_template(name, otp)
    return send_email_sync(
        to=email,
        subject=f"{otp} is your prompterly verification code",
        body=body,
        html=html
    )


def send_annual_renewal_30day_sync(
    email: str, name: str, mentor_name: str,
    renewal_date: str, amount: str, manage_url: str
) -> bool:
    """PDF Email #9: Annual Auto-Renew (30 days before)."""
    body, html = get_annual_renewal_30day_template(name, mentor_name, renewal_date, amount, manage_url)
    return send_email_sync(
        to=email,
        subject="Upcoming renewal for your Coaching Lounge",
        body=body,
        html=html
    )


def send_annual_renewal_7day_sync(
    email: str, name: str, mentor_name: str,
    renewal_date: str, amount: str, manage_url: str
) -> bool:
    """PDF Email #10: Annual Auto-Renew (7 days before)."""
    body, html = get_annual_renewal_7day_template(name, mentor_name, renewal_date, amount, manage_url)
    return send_email_sync(
        to=email,
        subject="Reminder: your subscription renews soon",
        body=body,
        html=html
    )


def send_annual_renewal_confirmed_sync(
    email: str, name: str, mentor_name: str,
    amount: str, renewal_date: str, next_renewal_date: str, dashboard_url: str
) -> bool:
    """PDF Email #11: Annual Subscription Renewed."""
    body, html = get_annual_renewal_confirmed_template(
        name, mentor_name, amount, renewal_date, next_renewal_date, dashboard_url
    )
    return send_email_sync(
        to=email,
        subject=f"Renewal confirmed: {mentor_name}'s Coaching Lounge",
        body=body,
        html=html
    )


def send_payment_failed_day0_sync(
    email: str, name: str, mentor_name: str,
    plan_type: str, amount: str, update_payment_url: str
) -> bool:
    """PDF Email #12: Payment Failed — Day 0."""
    body, html = get_payment_failed_day0_template(name, mentor_name, plan_type, amount, update_payment_url)
    return send_email_sync(
        to=email,
        subject="We couldn't process your payment",
        body=body,
        html=html
    )


def send_payment_failed_day3_sync(
    email: str, name: str, mentor_name: str,
    plan_type: str, amount: str, update_payment_url: str
) -> bool:
    """PDF Email #13: Payment Failed — Day 3."""
    body, html = get_payment_failed_day3_template(name, mentor_name, plan_type, amount, update_payment_url)
    return send_email_sync(
        to=email,
        subject="Your payment still needs attention",
        body=body,
        html=html
    )


def send_access_paused_sync(
    email: str, name: str, data_deletion_date: str, update_payment_url: str
) -> bool:
    """PDF Email #14: Access Paused (Day 7)."""
    body, html = get_access_paused_template(name, data_deletion_date, update_payment_url)
    return send_email_sync(
        to=email,
        subject="Access paused - update your payment to continue",
        body=body,
        html=html
    )


def send_data_deletion_reminder_sync(
    email: str, name: str, deletion_date: str, reactivate_url: str
) -> bool:
    """PDF Email #15: Data Deletion Reminder (60 days after pause)."""
    body, html = get_data_deletion_reminder_template(name, deletion_date, reactivate_url)
    return send_email_sync(
        to=email,
        subject="Your Prompterly data will be deleted in 30 days",
        body=body,
        html=html
    )


def send_data_deleted_sync(email: str, name: str, signup_url: str) -> bool:
    """PDF Email #16: Data Deleted."""
    body, html = get_data_deleted_template(name, signup_url)
    return send_email_sync(
        to=email,
        subject="Your Prompterly data has been permanently deleted",
        body=body,
        html=html
    )


def send_subscription_cancelled_sync(
    email: str, name: str, mentor_name: str,
    plan_type: str, access_end_date: str, deletion_date: str, dashboard_url: str
) -> bool:
    """PDF Email #17: Subscription Cancelled."""
    body, html = get_subscription_cancellation_email_template(
        name, mentor_name, plan_type, access_end_date, deletion_date, dashboard_url
    )
    return send_email_sync(
        to=email,
        subject=f"You've unsubscribed from {mentor_name}'s Coaching Lounge",
        body=body,
        html=html
    )


def send_time_capsule_delivery_sync(email: str, name: str, login_url: str) -> bool:
    """PDF Email #18: Time Capsule Delivery."""
    body, html = get_time_capsule_delivery_template(name, login_url)
    return send_email_sync(
        to=email,
        subject="A new message is ready",
        body=body,
        html=html
    )
