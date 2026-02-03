"""
User management API endpoints
Handles user profile, password changes, activity logs
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.jwt import get_current_user, get_current_active_user
from app.core.security import verify_password, hash_password
from app.db.models.user import User
from app.schemas.auth import (
    UserResponse,
    UserUpdate,
    PasswordChange
)
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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account
    
    - Soft deletes user data
    - Anonymizes personal information
    - Keeps historical records for compliance
    """
    # Anonymize user data instead of hard delete
    current_user.email = f"deleted_{current_user.id}@deleted.com"
    current_user.name = f"Deleted User {current_user.id}"
    current_user.avatar_url = None
    current_user.password_hash = hash_password(f"deleted_{current_user.id}")
    
    # Mark all sessions as revoked
    from app.db.models.auth import UserSession
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).all()
    
    for session in sessions:
        session.revoked_at = now_naive()
    
    db.commit()
    
    return None


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
