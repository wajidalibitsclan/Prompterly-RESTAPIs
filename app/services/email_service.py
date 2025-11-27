"""
Email service for sending transactional emails
Uses SMTP configuration from settings
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str | List[str],
    subject: str,
    body: str,
    html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """
    Send email via SMTP
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        body: Plain text email body
        html: Optional HTML email body
        cc: Optional CC recipients
        bcc: Optional BCC recipients
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        
        # Handle single or multiple recipients
        if isinstance(to, str):
            to = [to]
        msg["To"] = ", ".join(to)
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        
        msg["Subject"] = subject
        
        # Add plain text part
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html:
            html_part = MIMEText(html, "html")
            msg.attach(html_part)
        
        # Connect to SMTP server
        if settings.MAIL_TLS:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
            server.starttls()
        elif settings.MAIL_SSL:
            server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT)
        else:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        
        # Login if credentials provided
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        
        # Send email
        recipients = to + (cc or []) + (bcc or [])
        server.sendmail(settings.MAIL_FROM, recipients, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


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


async def send_welcome_email(email: str, name: str) -> bool:
    """
    Send welcome email after email verification
    
    Args:
        email: User email
        name: User name
        
    Returns:
        True if sent successfully
    """
    dashboard_url = f"{settings.CORS_ORIGINS[0]}/dashboard"
    
    body = f"""
Hi {name},

Welcome to AI Coaching Platform!

Your email has been verified and your account is now active.

Get started by:
1. Exploring available lounges
2. Joining a mentor's coaching session
3. Starting a conversation with your AI coach

Visit your dashboard: {dashboard_url}

Best regards,
AI Coaching Team
    """
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Welcome to AI Coaching Platform! 🎉</h2>
    <p>Hi {name},</p>
    <p>Your email has been verified and your account is now active.</p>
    <h3>Get Started:</h3>
    <ul style="line-height: 2;">
        <li>Explore available coaching lounges</li>
        <li>Join a mentor's coaching session</li>
        <li>Start a conversation with your AI coach</li>
    </ul>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{dashboard_url}" 
           style="background-color: #10B981; color: white; padding: 12px 30px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Go to Dashboard
        </a>
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
        subject="Welcome to AI Coaching Platform! 🎉",
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
