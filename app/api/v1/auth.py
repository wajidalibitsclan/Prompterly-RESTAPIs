"""
Authentication API endpoints
Handles user registration, login, OAuth, password reset
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import httpx

from app.db.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_email_verification_token,
    verify_email_token,
    generate_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings
from app.db.models.user import User, UserRole
from app.db.models.auth import UserSession, OAuthAccount, OAuthProvider
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    EmailVerification,
    PasswordResetRequest,
    PasswordReset,
    UserResponse
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - Creates user account
    - Sends verification email
    - Returns user data (without password)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        role=UserRole.MEMBER
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate verification token
    verification_token = generate_email_verification_token(new_user.email)
    
    # TODO: Send verification email in background
    # background_tasks.add_task(send_email, ...)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    - Validates credentials
    - Returns JWT access and refresh tokens
    - Creates session record
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Create session
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - Validates refresh token
    - Returns new access and refresh tokens
    """
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    verification: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    Verify user email address
    
    - Validates verification token
    - Marks email as verified
    """
    email = verify_email_token(verification.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified_at:
        return {"message": "Email already verified"}
    
    user.email_verified_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset
    
    - Generates reset token
    - Sends reset email
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    # Don't reveal if email exists
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_password_reset_token(user.email)
    
    # TODO: Send reset email in background
    # background_tasks.add_task(send_email, ...)
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password with token
    
    - Validates reset token
    - Updates password
    """
    email = verify_password_reset_token(reset.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(reset.new_password)
    
    # Revoke all sessions for security
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None)
    ).all()
    
    for session in sessions:
        session.revoked_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth flow
    
    - Redirects to Google OAuth
    """
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile"
    )
    
    return {"auth_url": google_auth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    
    - Exchanges code for tokens
    - Creates or updates user
    - Returns JWT tokens
    """
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
    
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from Google"
        )
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    # Get user info from Google
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    if user_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )
    
    user_data = user_response.json()
    google_user_id = user_data.get("id")
    email = user_data.get("email")
    name = user_data.get("name")
    
    # Check if OAuth account exists
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.provider == OAuthProvider.GOOGLE,
        OAuthAccount.provider_user_id == google_user_id
    ).first()
    
    if oauth_account:
        # Existing user
        user = oauth_account.user
        oauth_account.access_token = access_token
    else:
        # Check if user with email exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                name=name,
                password_hash=hash_password(f"google_oauth_{google_user_id}"),
                role=UserRole.MEMBER,
                email_verified_at=datetime.utcnow()  # Google emails are verified
            )
            db.add(user)
            db.flush()
        
        # Create OAuth account
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=OAuthProvider.GOOGLE,
            provider_user_id=google_user_id,
            access_token=access_token
        )
        db.add(oauth_account)
    
    db.commit()
    
    # Create JWT tokens
    jwt_access_token = create_access_token(data={"sub": user.id})
    jwt_refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Create session
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": jwt_access_token,
        "refresh_token": jwt_refresh_token,
        "token_type": "bearer"
    }
