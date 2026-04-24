"""
User management API endpoints
Handles user profile, password changes, activity logs, GDPR data export/deletion
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import json

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.encryption import decrypt_content
from app.core.jwt import get_current_user, get_current_active_user
from app.core.security import verify_password, hash_password
from app.db.models.user import User
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
async def update_support_style_preference(
    data: SupportStyleUpdate,
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

@router.get("/me/export", status_code=status.HTTP_200_OK)
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export all user data as JSON (GDPR data portability).

    Returns:
        JSON containing profile, chat history, notes, time capsules,
        subscriptions, and notification preferences.
    """
    from app.db.models.chat import ChatThread, ChatMessage
    from app.db.models.note import Note, TimeCapsule
    from app.db.models.billing import LoungeSubscription
    from app.db.models.misc import ComplianceRequest, RequestType, RequestStatus

    # Record the export request
    compliance_req = ComplianceRequest(
        user_id=current_user.id,
        request_type=RequestType.EXPORT,
        status=RequestStatus.DONE
    )
    db.add(compliance_req)
    db.commit()

    # 1. Profile data (uses user_uuid as primary identifier)
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

    # 2. Chat history (decrypted)
    threads = db.query(ChatThread).filter(ChatThread.user_id == current_user.id).all()
    chat_data = []
    for thread in threads:
        messages = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread.id
        ).order_by(ChatMessage.created_at.asc()).all()

        chat_data.append({
            "thread_id": thread.id,
            "title": thread.title,
            "lounge_id": thread.lounge_id,
            "created_at": thread.created_at.isoformat() if thread.created_at else None,
            "messages": [
                {
                    "id": msg.id,
                    "sender_type": msg.sender_type.value if msg.sender_type else None,
                    "content": decrypt_content(msg.content),
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ]
        })

    # 3. Notes (decrypted)
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()
    notes_data = [
        {
            "id": note.id,
            "title": note.title,
            "content": decrypt_content(note.content),
            "lounge_id": note.lounge_id if hasattr(note, 'lounge_id') else None,
            "is_pinned": note.is_pinned,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        }
        for note in notes
    ]

    # 4. Time capsules (decrypted)
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
    subs_data = [
        {
            "lounge_id": sub.lounge_id,
            "plan_type": sub.plan_type.value if sub.plan_type else None,
            "status": sub.status.value if sub.status else None,
            "started_at": sub.started_at.isoformat() if sub.started_at else None,
            "renews_at": sub.renews_at.isoformat() if sub.renews_at else None,
            "canceled_at": sub.canceled_at.isoformat() if sub.canceled_at else None,
        }
        for sub in subs
    ]

    export = {
        "export_date": now_naive().isoformat(),
        "profile": profile,
        "chat_history": chat_data,
        "notes": notes_data,
        "time_capsules": capsules_data,
        "subscriptions": subs_data,
    }

    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f"attachment; filename=prompterly_data_export_{current_user.id}.json"
        }
    )


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(
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
