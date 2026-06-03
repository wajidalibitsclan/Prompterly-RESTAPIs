"""
User management API endpoints
Handles user profile, password changes, activity logs, GDPR data export/deletion
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from typing import List, Literal
import csv
import io
import json
import zipfile

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.encryption import decrypt_content
from app.core.jwt import get_current_user, get_current_active_user
from app.core.security import verify_password, hash_password
from app.db.models.user import User
from app.services import audit_log_service as audit_log
from app.services.audit_log_service import AuditAction
from app.core.rate_limit import limiter, AUTH
from app.schemas.auth import (
    UserResponse,
    UserUpdate,
    PasswordChange,
    LanguageTimezoneUpdate,
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse,
    PrivacyAcceptance,
)
from app.schemas.chat import SupportStyleUpdate
from app.core.support_style import DEFAULT_STYLE, is_valid as is_valid_style
from app.services.file_service import file_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile

    - Returns authenticated user's profile
    - Requires valid JWT token
    - Does not require email verification
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    - Updates name and/or avatar_url
    - Returns updated profile
    """
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    current_user.updated_at = now_naive()
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar/profile picture

    - Accepts image files (jpg, jpeg, png, gif, webp)
    - Max file size: 5MB
    - Returns updated user profile with new avatar_url
    """
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file extension
    filename = file.filename or ""
    file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Upload file to storage
        file_record = await file_service.upload_file(
            file=file,
            user_id=current_user.id,
            db=db,
            folder="avatars"
        )

        # Generate URL for the uploaded file
        avatar_url = await file_service.get_file_url(file_record.id, db)

        # Update user's avatar_url
        current_user.avatar_url = avatar_url
        current_user.updated_at = now_naive()

        db.commit()
        db.refresh(current_user)

        return current_user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


@router.delete("/me/avatar", response_model=UserResponse)
async def remove_avatar(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove user avatar/profile picture

    - Sets avatar_url to null
    - Returns updated user profile
    """
    current_user.avatar_url = None
    current_user.updated_at = now_naive()

    db.commit()
    db.refresh(current_user)

    return current_user


@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password

    - Validates current password
    - Updates to new password
    - Requires re-authentication
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    current_user.updated_at = now_naive()

    db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me/activity")
async def get_user_activity(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get user activity log
    
    - Returns recent user activities
    - Includes lounge memberships, notes, capsules, etc.
    """
    activity = []
    
    # Get lounge memberships
    for membership in current_user.lounge_memberships[:limit]:
        activity.append({
            "id": membership.id,
            "action": "joined_lounge" if membership.left_at is None else "left_lounge",
            "timestamp": membership.joined_at if membership.left_at is None else membership.left_at,
            "details": {
                "lounge_id": membership.lounge_id,
                "lounge_title": membership.lounge.title if membership.lounge else None
            }
        })
    
    # Get recent chat threads
    for thread in current_user.chat_threads[:limit]:
        activity.append({
            "id": thread.id,
            "action": "created_chat_thread",
            "timestamp": thread.created_at,
            "details": {
                "thread_id": thread.id,
                "thread_title": thread.title,
                "lounge_id": thread.lounge_id
            }
        })
    
    # Get recent notes
    for note in current_user.notes[:limit]:
        activity.append({
            "id": note.id,
            "action": "created_note",
            "timestamp": note.created_at,
            "details": {
                "note_id": note.id,
                "note_title": note.title
            }
        })
    
    # Get recent time capsules
    for capsule in current_user.time_capsules[:limit]:
        activity.append({
            "id": capsule.id,
            "action": "created_capsule",
            "timestamp": capsule.created_at,
            "details": {
                "capsule_id": capsule.id,
                "capsule_title": capsule.title,
                "unlock_at": capsule.unlock_at.isoformat() if capsule.unlock_at else None
            }
        })
    
    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activity[:limit]


# =============================================================================
# Settings Endpoints
# =============================================================================

@router.get("/me/settings/language-timezone")
async def get_language_timezone(
    current_user: User = Depends(get_current_active_user),
):
    """Get current language and timezone preferences."""
    return {
        "language": current_user.language,
        "timezone": current_user.timezone,
    }


@router.put("/me/settings/language-timezone")
async def update_language_timezone(
    data: LanguageTimezoneUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update language and/or timezone preferences."""
    if data.language is not None:
        current_user.language = data.language
    if data.timezone is not None:
        current_user.timezone = data.timezone

    current_user.updated_at = now_naive()
    db.commit()
    db.refresh(current_user)

    return {
        "language": current_user.language,
        "timezone": current_user.timezone,
    }


@router.get("/me/settings/notifications", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
):
    """Get current notification preferences."""
    return current_user


@router.put("/me/settings/notifications", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences (toggle email, in-app, per-type)."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    current_user.updated_at = now_naive()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/me/settings/support-style")
async def get_support_style_preference(
    current_user: User = Depends(get_current_active_user),
):
    """
    Return the account-level tone preference.

    Falls back to the global default when the user hasn't explicitly picked
    a tone, so the UI can always render a sensible selection.
    """
    return {
        "support_style": current_user.support_style or DEFAULT_STYLE,
        "explicit": current_user.support_style is not None,
    }


@router.put("/me/settings/support-style")
@limiter.limit(AUTH)
async def update_support_style_preference(
    data: SupportStyleUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update the account-level tone preference.

    Accepts a known slug or null (null clears the override and falls back
    to the global default). Invalid slugs are rejected with 400 — we don't
    store values that prompt assembly doesn't know how to render.
    """
    if not is_valid_style(data.support_style):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown support style: {data.support_style!r}",
        )

    current_user.support_style = data.support_style
    current_user.updated_at = now_naive()
    db.commit()
    db.refresh(current_user)

    return {
        "support_style": current_user.support_style or DEFAULT_STYLE,
        "explicit": current_user.support_style is not None,
    }


@router.get("/me/settings/privacy")
async def get_privacy_status(
    current_user: User = Depends(get_current_active_user),
):
    """Get current privacy policy, ToS acceptance, and age confirmation status."""
    return {
        "privacy_accepted_at": current_user.privacy_accepted_at,
        "tos_accepted_at": current_user.tos_accepted_at,
        "age_confirmed": current_user.age_confirmed,
    }


@router.post("/me/settings/privacy", status_code=status.HTTP_200_OK)
async def accept_privacy(
    data: PrivacyAcceptance,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Accept privacy policy, terms of service, and/or confirm age (18+).
    Once accepted, timestamps are recorded and cannot be unset.
    """
    if data.accept_privacy_policy and not current_user.privacy_accepted_at:
        current_user.privacy_accepted_at = now_naive()

    if data.accept_terms_of_service and not current_user.tos_accepted_at:
        current_user.tos_accepted_at = now_naive()

    if data.confirm_age_18_plus and not current_user.age_confirmed:
        current_user.age_confirmed = True

    current_user.updated_at = now_naive()
    db.commit()
    db.refresh(current_user)

    return {
        "privacy_accepted_at": current_user.privacy_accepted_at,
        "tos_accepted_at": current_user.tos_accepted_at,
        "age_confirmed": current_user.age_confirmed,
    }


# =============================================================================
# GDPR — Data Export & Account Deletion
# =============================================================================

REMOVED_LOUNGE_PLACEHOLDER = "[lounge no longer available]"


def _build_export_payload(current_user: User, db: Session) -> dict:
    """
    Collect every category of user-owned content into a single dict.

    Mentor-IP exclusion (Security Standard §15 / Task #30): when a chat,
    note, or capsule references a lounge that has since been removed or
    deactivated, the export keeps the user's own content but strips the
    mentor's branding (lounge title, mentor name) — the lounge_id is
    retained only as an opaque integer so the user can correlate items.
    """
    from app.db.models.chat import ChatThread, ChatMessage
    from app.db.models.note import Note, TimeCapsule
    from app.db.models.billing import LoungeSubscription
    from app.db.models.lounge import Lounge
    from app.db.models.mentor import Mentor

    # 0. Resolve which referenced lounges are still active. One query per
    # category so we don't N+1; the result feeds every section below.
    referenced_lounge_ids = {
        lid for (lid,) in db.query(ChatThread.lounge_id).filter(
            ChatThread.user_id == current_user.id,
            ChatThread.lounge_id.isnot(None),
        ).distinct()
    }
    referenced_lounge_ids.update(
        lid for (lid,) in db.query(Note.lounge_id).filter(
            Note.user_id == current_user.id,
            Note.lounge_id.isnot(None),
        ).distinct()
    )
    referenced_lounge_ids.update(
        lid for (lid,) in db.query(LoungeSubscription.lounge_id).filter(
            LoungeSubscription.user_id == current_user.id,
        ).distinct()
    )

    active_lounges = {}
    if referenced_lounge_ids:
        rows = db.query(Lounge, Mentor.id).outerjoin(
            Mentor, Mentor.id == Lounge.mentor_id
        ).filter(Lounge.id.in_(referenced_lounge_ids)).all()
        for lounge, _mentor_id in rows:
            # If the lounge model carries a soft-delete or active flag, honour
            # it. Otherwise existence in the table = active.
            is_active = True
            for attr in ("deleted_at", "is_deleted"):
                if hasattr(lounge, attr):
                    val = getattr(lounge, attr)
                    if (attr == "deleted_at" and val is not None) or (attr == "is_deleted" and val):
                        is_active = False
                        break
            if hasattr(lounge, "is_active") and not lounge.is_active:
                is_active = False
            if is_active:
                active_lounges[lounge.id] = lounge

    def lounge_branding(lounge_id):
        """Return {title, mentor_name} for active lounges; sanitised placeholder otherwise."""
        if lounge_id is None:
            return {"lounge_id": None, "lounge_title": None, "mentor_name": None}
        lounge = active_lounges.get(lounge_id)
        if lounge is None:
            return {
                "lounge_id": lounge_id,
                "lounge_title": REMOVED_LOUNGE_PLACEHOLDER,
                "mentor_name": REMOVED_LOUNGE_PLACEHOLDER,
            }
        mentor_name = None
        if getattr(lounge, "mentor", None) and getattr(lounge.mentor, "user", None):
            mentor_name = lounge.mentor.user.name
        return {
            "lounge_id": lounge_id,
            "lounge_title": getattr(lounge, "title", None) or getattr(lounge, "name", None),
            "mentor_name": mentor_name,
        }

    # 1. Profile (pseudonymous identifier first)
    profile = {
        "user_uuid": current_user.user_uuid,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value if current_user.role else None,
        "language": current_user.language,
        "timezone": current_user.timezone,
        "email_verified_at": current_user.email_verified_at.isoformat() if current_user.email_verified_at else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }

    # 2. Chat history
    threads = db.query(ChatThread).filter(ChatThread.user_id == current_user.id).all()
    chat_data = []
    for thread in threads:
        messages = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread.id
        ).order_by(ChatMessage.created_at.asc()).all()
        branding = lounge_branding(thread.lounge_id)
        chat_data.append({
            "thread_id": thread.id,
            "title": thread.title,
            **branding,
            "created_at": thread.created_at.isoformat() if thread.created_at else None,
            "messages": [
                {
                    "id": msg.id,
                    "sender_type": msg.sender_type.value if msg.sender_type else None,
                    "content": decrypt_content(msg.content),
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ],
        })

    # 3. Notes
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()
    notes_data = []
    for note in notes:
        branding = lounge_branding(getattr(note, "lounge_id", None))
        notes_data.append({
            "id": note.id,
            "title": note.title,
            "content": decrypt_content(note.content),
            **branding,
            "is_pinned": note.is_pinned,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        })

    # 4. Time capsules (capsules don't carry a lounge ref in the current
    # schema, so no branding to strip — just decrypt and emit)
    capsules = db.query(TimeCapsule).filter(TimeCapsule.user_id == current_user.id).all()
    capsules_data = [
        {
            "id": capsule.id,
            "title": capsule.title,
            "content": decrypt_content(capsule.content),
            "unlock_at": capsule.unlock_at.isoformat() if capsule.unlock_at else None,
            "status": capsule.status.value if capsule.status else None,
            "created_at": capsule.created_at.isoformat() if capsule.created_at else None,
        }
        for capsule in capsules
    ]

    # 5. Subscriptions
    subs = db.query(LoungeSubscription).filter(
        LoungeSubscription.user_id == current_user.id
    ).all()
    subs_data = []
    for sub in subs:
        branding = lounge_branding(sub.lounge_id)
        subs_data.append({
            **branding,
            "plan_type": sub.plan_type.value if sub.plan_type else None,
            "status": sub.status.value if sub.status else None,
            "started_at": sub.started_at.isoformat() if sub.started_at else None,
            "renews_at": sub.renews_at.isoformat() if sub.renews_at else None,
            "canceled_at": sub.canceled_at.isoformat() if sub.canceled_at else None,
        })

    return {
        "export_date": now_naive().isoformat(),
        "profile": profile,
        "chat_history": chat_data,
        "notes": notes_data,
        "time_capsules": capsules_data,
        "subscriptions": subs_data,
    }


def _export_as_csv_zip(payload: dict) -> bytes:
    """Pack each top-level section into its own CSV inside a ZIP archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # profile.csv — single-row wide table
        profile_buf = io.StringIO()
        profile = payload["profile"]
        writer = csv.DictWriter(profile_buf, fieldnames=list(profile.keys()))
        writer.writeheader()
        writer.writerow(profile)
        zf.writestr("profile.csv", profile_buf.getvalue())

        # chat_messages.csv — flatten thread + message
        chat_buf = io.StringIO()
        chat_writer = csv.writer(chat_buf)
        chat_writer.writerow([
            "thread_id", "thread_title", "lounge_id", "lounge_title",
            "mentor_name", "thread_created_at",
            "message_id", "sender_type", "content", "message_created_at",
        ])
        for thread in payload["chat_history"]:
            for msg in thread["messages"]:
                chat_writer.writerow([
                    thread["thread_id"], thread["title"], thread["lounge_id"],
                    thread["lounge_title"], thread["mentor_name"], thread["created_at"],
                    msg["id"], msg["sender_type"], msg["content"], msg["created_at"],
                ])
        zf.writestr("chat_messages.csv", chat_buf.getvalue())

        # notes.csv
        notes_buf = io.StringIO()
        notes_writer = csv.writer(notes_buf)
        notes_writer.writerow([
            "id", "title", "content", "lounge_id", "lounge_title",
            "mentor_name", "is_pinned", "created_at",
        ])
        for n in payload["notes"]:
            notes_writer.writerow([
                n["id"], n["title"], n["content"], n["lounge_id"],
                n["lounge_title"], n["mentor_name"], n["is_pinned"], n["created_at"],
            ])
        zf.writestr("notes.csv", notes_buf.getvalue())

        # time_capsules.csv
        capsules_buf = io.StringIO()
        capsules_writer = csv.writer(capsules_buf)
        capsules_writer.writerow(["id", "title", "content", "unlock_at", "status", "created_at"])
        for c in payload["time_capsules"]:
            capsules_writer.writerow([
                c["id"], c["title"], c["content"], c["unlock_at"], c["status"], c["created_at"],
            ])
        zf.writestr("time_capsules.csv", capsules_buf.getvalue())

        # subscriptions.csv
        subs_buf = io.StringIO()
        subs_writer = csv.writer(subs_buf)
        subs_writer.writerow([
            "lounge_id", "lounge_title", "mentor_name", "plan_type",
            "status", "started_at", "renews_at", "canceled_at",
        ])
        for s in payload["subscriptions"]:
            subs_writer.writerow([
                s["lounge_id"], s["lounge_title"], s["mentor_name"], s["plan_type"],
                s["status"], s["started_at"], s["renews_at"], s["canceled_at"],
            ])
        zf.writestr("subscriptions.csv", subs_buf.getvalue())

        # README so the user knows what the placeholders mean
        zf.writestr(
            "README.txt",
            "Prompterly data export\n"
            f"Generated: {payload['export_date']}\n\n"
            f"Where you see '{REMOVED_LOUNGE_PLACEHOLDER}' in the lounge_title or "
            "mentor_name columns, the lounge has been removed from the platform "
            "since your content was created. Your own content is preserved; the "
            "mentor's branding has been excluded.\n"
        )

    return buf.getvalue()


def _export_as_pdf(payload: dict) -> bytes:
    """Render the export payload as a single PDF document."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    )
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Prompterly Data Export",
    )
    styles = getSampleStyleSheet()
    h1, h2 = styles["Heading1"], styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.grey)
    story = []

    story.append(Paragraph("Prompterly — Data Export", h1))
    story.append(Paragraph(f"Generated {payload['export_date']}", small))
    story.append(Spacer(1, 12))

    # Profile
    story.append(Paragraph("Profile", h2))
    profile_rows = [[k, str(v) if v is not None else ""] for k, v in payload["profile"].items()]
    if profile_rows:
        t = Table(profile_rows, colWidths=[5 * cm, 11 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)
    story.append(Spacer(1, 12))

    # Chat history
    story.append(PageBreak())
    story.append(Paragraph("Chat history", h2))
    if not payload["chat_history"]:
        story.append(Paragraph("(no chats)", body))
    for thread in payload["chat_history"]:
        story.append(Paragraph(
            f"<b>{thread['title'] or 'Untitled thread'}</b> &mdash; "
            f"{thread['lounge_title'] or 'No lounge'} "
            f"(thread {thread['thread_id']}, {thread['created_at']})",
            body,
        ))
        for msg in thread["messages"]:
            sender = msg["sender_type"] or "?"
            content = (msg["content"] or "").replace("\n", "<br/>")
            story.append(Paragraph(f"<b>{sender}:</b> {content}", body))
        story.append(Spacer(1, 8))

    # Notes
    story.append(PageBreak())
    story.append(Paragraph("Notes", h2))
    if not payload["notes"]:
        story.append(Paragraph("(no notes)", body))
    for n in payload["notes"]:
        story.append(Paragraph(
            f"<b>{n['title'] or 'Untitled'}</b> &mdash; "
            f"{n['lounge_title'] or 'No lounge'} ({n['created_at']})",
            body,
        ))
        content = (n["content"] or "").replace("\n", "<br/>")
        story.append(Paragraph(content, body))
        story.append(Spacer(1, 8))

    # Time capsules
    story.append(PageBreak())
    story.append(Paragraph("Time capsules", h2))
    if not payload["time_capsules"]:
        story.append(Paragraph("(no time capsules)", body))
    for c in payload["time_capsules"]:
        story.append(Paragraph(
            f"<b>{c['title'] or 'Untitled'}</b> &mdash; status: {c['status']} "
            f"&mdash; unlocks {c['unlock_at']}",
            body,
        ))
        content = (c["content"] or "").replace("\n", "<br/>")
        story.append(Paragraph(content, body))
        story.append(Spacer(1, 8))

    # Subscriptions
    story.append(PageBreak())
    story.append(Paragraph("Subscriptions", h2))
    if not payload["subscriptions"]:
        story.append(Paragraph("(no subscriptions)", body))
    else:
        sub_rows = [["Lounge", "Mentor", "Plan", "Status", "Started", "Renews", "Cancelled"]]
        for s in payload["subscriptions"]:
            sub_rows.append([
                s["lounge_title"] or str(s["lounge_id"]),
                s["mentor_name"] or "",
                s["plan_type"] or "",
                s["status"] or "",
                (s["started_at"] or "").split("T")[0],
                (s["renews_at"] or "").split("T")[0],
                (s["canceled_at"] or "").split("T")[0] if s["canceled_at"] else "",
            ])
        t = Table(sub_rows, colWidths=[4 * cm, 3 * cm, 1.8 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)

    doc.build(story)
    return buf.getvalue()


@router.get("/me/export", status_code=status.HTTP_200_OK)
async def export_user_data(
    request: Request,
    format: Literal["json", "csv", "pdf"] = Query(
        "json",
        description="Export format: json (default), csv (zip of per-section CSVs), pdf",
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Export all user data (GDPR data portability).

    Returns profile, chat history, notes, time capsules, and subscriptions
    in the requested format. Mentor branding (lounge title, mentor name) is
    stripped for content tied to lounges that no longer exist on the
    platform — see `_build_export_payload` for the rule.
    """
    from app.db.models.misc import ComplianceRequest, RequestType, RequestStatus

    # Record the export request (compliance request log + audit trail)
    compliance_req = ComplianceRequest(
        user_id=current_user.id,
        request_type=RequestType.EXPORT,
        status=RequestStatus.DONE,
    )
    db.add(compliance_req)
    db.commit()
    audit_log.record(
        AuditAction.DATA_EXPORT, actor=current_user, request=request,
        audit_metadata={"format": format},
    )

    payload = _build_export_payload(current_user, db)
    base_name = f"prompterly_data_export_{current_user.user_uuid}"

    if format == "json":
        return JSONResponse(
            content=payload,
            headers={"Content-Disposition": f'attachment; filename="{base_name}.json"'},
        )

    if format == "csv":
        body_bytes = _export_as_csv_zip(payload)
        return Response(
            content=body_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.zip"'},
        )

    # format == "pdf"
    body_bytes = _export_as_pdf(payload)
    return Response(
        content=body_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{base_name}.pdf"'},
    )


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account (GDPR right to erasure).

    - Blocked if user is under legal hold
    - Anonymises personal identity (name, email, avatar, stripe ID)
    - Revokes all auth credentials (password hash, TOTP secret, sessions)
    - Records a compliance delete request
    - Content records (chat, notes, capsules) remain associated with
      the anonymised user_id for pseudonymous retention per security doc.
    """
    # Check legal hold
    if current_user.legal_hold:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deletion is temporarily disabled due to a legal hold. Please contact support."
        )

    from app.db.models.auth import UserSession
    from app.db.models.misc import ComplianceRequest, RequestType, RequestStatus

    # 1. Record the deletion request
    compliance_req = ComplianceRequest(
        user_id=current_user.id,
        request_type=RequestType.DELETE,
        status=RequestStatus.DONE
    )
    db.add(compliance_req)

    # 2. Anonymise personal identity fields
    current_user.email = f"deleted_{current_user.id}@deleted.prompterly.ai"
    current_user.name = f"Deleted User"
    current_user.avatar_url = None
    current_user.stripe_customer_id = None

    # 3. Revoke auth credentials
    current_user.password_hash = hash_password(f"deleted_{current_user.id}_{now_naive().timestamp()}")
    current_user.totp_secret = None
    current_user.is_2fa_enabled = False

    # 4. Clear preferences (not PII but clean up)
    current_user.privacy_accepted_at = None
    current_user.tos_accepted_at = None

    # 5. Revoke all active sessions
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).all()
    for session in sessions:
        session.revoked_at = now_naive()

    db.commit()

    # Audit AFTER commit so the row carries the post-anonymisation user_uuid
    # (unchanged) but we know the anonymisation transaction succeeded.
    audit_log.record(
        AuditAction.ACCOUNT_DELETE, actor=current_user, request=request,
        entity_type="User", entity_id=current_user.id,
        audit_metadata={"revoked_sessions": len(sessions)},
    )

    return {
        "message": "Your account has been anonymised and all credentials revoked. Content records remain pseudonymous."
    }


@router.get("/me/compliance-requests")
async def get_compliance_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all GDPR compliance requests for the current user (export/delete history).
    """
    from app.db.models.misc import ComplianceRequest

    requests = db.query(ComplianceRequest).filter(
        ComplianceRequest.user_id == current_user.id
    ).order_by(ComplianceRequest.created_at.desc()).all()

    return [
        {
            "id": req.id,
            "request_type": req.request_type.value if req.request_type else None,
            "status": req.status.value if req.status else None,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        }
        for req in requests
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID
    
    - Returns public user profile
    - Limited information for privacy
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
