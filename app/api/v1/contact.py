"""
Contact form API endpoints
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models import ContactMessage
from app.services.email_service import (
    send_contact_confirmation_email_sync,
    send_contact_admin_notification_sync
)
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a contact form message.

    This endpoint:
    1. Saves the message to the database
    2. Sends an email notification to the admin (background)
    3. Sends a confirmation email to the user (background)
    """
    try:
        # Get client info
        client_ip = request.client.host if request.client else "Unknown"
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

        # Send admin notification email in background
        admin_email = settings.MAIL_FROM  # Send to the same email configured as sender
        background_tasks.add_task(
            send_contact_admin_notification_sync,
            admin_email,
            form_data.name,
            form_data.email,
            form_data.subject,
            form_data.message,
            client_ip,
            str(contact_message.created_at),
            contact_message.id
        )

        # Send user confirmation email in background
        background_tasks.add_task(
            send_contact_confirmation_email_sync,
            form_data.email,
            form_data.name,
            form_data.subject
        )

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
