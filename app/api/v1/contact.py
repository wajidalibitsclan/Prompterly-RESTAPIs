"""
Contact form API endpoints
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models import ContactMessage
from app.services.email_service import send_email
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ContactFormRequest(BaseModel):
    """Contact form submission request schema"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=3, max_length=500)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactFormResponse(BaseModel):
    """Contact form submission response schema"""
    success: bool
    message: str


@router.post("/", response_model=ContactFormResponse)
async def submit_contact_form(
    form_data: ContactFormRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit a contact form message.

    This endpoint:
    1. Saves the message to the database
    2. Sends an email notification to the admin
    3. Sends a confirmation email to the user
    """
    try:
        # Get client info
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        # Save to database
        contact_message = ContactMessage(
            name=form_data.name,
            email=form_data.email,
            subject=form_data.subject,
            message=form_data.message,
            ip_address=client_ip,
            user_agent=user_agent
        )
        db.add(contact_message)
        db.commit()
        db.refresh(contact_message)

        logger.info(f"Contact form submitted: {form_data.email} - {form_data.subject}")

        # Send notification email to admin
        admin_email = settings.MAIL_FROM  # Send to the same email configured as sender
        admin_subject = f"[Prompterly Contact] {form_data.subject}"
        admin_body = f"""
New contact form submission received:

From: {form_data.name}
Email: {form_data.email}
Subject: {form_data.subject}

Message:
{form_data.message}

---
IP Address: {client_ip}
Submitted at: {contact_message.created_at}
Message ID: {contact_message.id}
        """

        admin_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>New Contact Form Submission</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">From:</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{form_data.name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Email:</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <a href="mailto:{form_data.email}">{form_data.email}</a>
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Subject:</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{form_data.subject}</td>
        </tr>
    </table>
    <h3>Message:</h3>
    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; white-space: pre-wrap;">
{form_data.message}
    </div>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">
        IP Address: {client_ip}<br>
        Submitted at: {contact_message.created_at}<br>
        Message ID: {contact_message.id}
    </p>
</body>
</html>
        """

        # Try to send admin notification (don't fail if email fails)
        try:
            await send_email(
                to=admin_email,
                subject=admin_subject,
                body=admin_body,
                html=admin_html
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification email: {e}")

        # Send confirmation email to user
        user_subject = "Thank you for contacting Prompterly"
        user_body = f"""
Hi {form_data.name},

Thank you for reaching out to us! We have received your message and will get back to you within 24-48 hours.

Your message summary:
Subject: {form_data.subject}

If you have any urgent inquiries, please don't hesitate to reach out to us directly at support@prompterly.com.

Best regards,
The Prompterly Team
        """

        user_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Thank you for contacting us!</h2>
    <p>Hi {form_data.name},</p>
    <p>Thank you for reaching out to us! We have received your message and will get back to you within 24-48 hours.</p>
    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <strong>Your message summary:</strong><br>
        Subject: {form_data.subject}
    </div>
    <p>If you have any urgent inquiries, please don't hesitate to reach out to us directly at
        <a href="mailto:support@prompterly.com">support@prompterly.com</a>.
    </p>
    <p>Best regards,<br>The Prompterly Team</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">
        Prompterly<br>
        &copy; 2025 All rights reserved
    </p>
</body>
</html>
        """

        # Try to send user confirmation (don't fail if email fails)
        try:
            await send_email(
                to=form_data.email,
                subject=user_subject,
                body=user_body,
                html=user_html
            )
        except Exception as e:
            logger.error(f"Failed to send user confirmation email: {e}")

        return ContactFormResponse(
            success=True,
            message="Thank you for your message! We'll get back to you soon."
        )

    except Exception as e:
        logger.error(f"Error submitting contact form: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact form. Please try again later."
        )
