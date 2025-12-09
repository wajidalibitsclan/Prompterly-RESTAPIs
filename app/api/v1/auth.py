"""
Authentication API endpoints
Handles user registration, login, OAuth, password reset
"""
from fastapi import APIRouter, Depends, BackgroundTasks, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import httpx
import random
import string

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
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidResetTokenError,
    InvalidVerificationTokenError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    GoogleOAuthError,
    AccountInactiveError
)
from app.core.logging import get_logger, log_auth_event
from app.core.jwt import get_current_user
from app.db.models.user import User, UserRole
from app.db.models.auth import UserSession, OAuthAccount, OAuthProvider, EmailOTP
from app.services.email_service import send_otp_email_sync, send_password_reset_otp_sync
from app.schemas.auth import (
    UserRegister,
    Token,
    TokenRefresh,
    EmailVerification,
    PasswordResetRequest,
    PasswordReset,
    UserResponse,
    OTPVerification,
    PasswordResetOTPVerification
)

router = APIRouter()
logger = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    if request.client:
        ip = request.client.host
    else:
        ip = "unknown"

    # Check for forwarded header
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    return ip


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


@router.post("/register/send-otp", status_code=status.HTTP_200_OK)
async def send_registration_otp(
    user_data: UserRegister,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send OTP for registration

    - Validates email is not already registered
    - Generates and sends OTP to email
    - Stores OTP for verification
    """
    client_ip = get_client_ip(request)
    logger.info(f"OTP request for registration: {user_data.email} from IP: {client_ip}")

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_auth_event(logger, "REGISTER_OTP", user_data.email, False, client_ip, "Email already exists")
        raise EmailAlreadyExistsError()

    try:
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Invalidate any existing OTPs for this email
        db.query(EmailOTP).filter(
            EmailOTP.email == user_data.email,
            EmailOTP.purpose == "registration",
            EmailOTP.verified_at.is_(None)
        ).update({"verified_at": datetime.utcnow()})

        # Store new OTP
        email_otp = EmailOTP(
            email=user_data.email,
            otp=otp,
            purpose="registration",
            expires_at=expires_at
        )
        db.add(email_otp)
        db.commit()

        # Send OTP email in background
        background_tasks.add_task(send_otp_email_sync, user_data.email, user_data.name, otp)

        log_auth_event(logger, "REGISTER_OTP", user_data.email, True, client_ip)
        logger.info(f"OTP queued for sending to: {user_data.email}")

        return {"message": "Verification code sent to your email", "email": user_data.email}

    except EmailAlreadyExistsError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process OTP for {user_data.email}: {e}", exc_info=True)
        raise Exception("Failed to process registration. Please try again.")


@router.post("/register/verify-otp", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def verify_registration_otp(
    otp_data: OTPVerification,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and complete registration

    - Validates OTP
    - Creates user account
    - Returns user data
    """
    client_ip = get_client_ip(request)
    email = otp_data.email
    otp = otp_data.otp
    name = otp_data.name
    password = otp_data.password
    logger.info(f"OTP verification for registration: {email} from IP: {client_ip}")

    # Find valid OTP
    email_otp = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.otp == otp,
        EmailOTP.purpose == "registration",
        EmailOTP.verified_at.is_(None),
        EmailOTP.expires_at > datetime.utcnow()
    ).first()

    if not email_otp:
        log_auth_event(logger, "REGISTER_VERIFY", email, False, client_ip, "Invalid or expired OTP")
        raise InvalidTokenError(message="Invalid or expired verification code", token_type="otp")

    # Check if user already exists (race condition protection)
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise EmailAlreadyExistsError()

    try:
        # Mark OTP as verified
        email_otp.verified_at = datetime.utcnow()

        # Create new user with verified email
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.MEMBER,
            email_verified_at=datetime.utcnow()  # Email is verified via OTP
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        log_auth_event(logger, "REGISTER", new_user.email, True, client_ip)
        logger.info(f"User registered successfully via OTP: {new_user.email} (ID: {new_user.id})")

        return new_user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise EmailAlreadyExistsError()
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed for {email}: {e}", exc_info=True)
        raise


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user (Legacy endpoint - use /register/send-otp instead)

    - Creates user account
    - Sends verification email
    - Returns user data (without password)
    """
    client_ip = get_client_ip(request)
    logger.info(f"Registration attempt for email: {user_data.email} from IP: {client_ip}")

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_auth_event(logger, "REGISTER", user_data.email, False, client_ip, "Email already exists")
        raise EmailAlreadyExistsError()

    try:
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
        logger.debug(f"Verification token generated for: {new_user.email}")

        # TODO: Send verification email in background
        # background_tasks.add_task(send_email, ...)

        log_auth_event(logger, "REGISTER", new_user.email, True, client_ip)
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")

        return new_user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        log_auth_event(logger, "REGISTER", user_data.email, False, client_ip, "Database error")
        raise EmailAlreadyExistsError()
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed for {user_data.email}: {e}", exc_info=True)
        raise


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    - Validates credentials
    - Returns JWT access and refresh tokens
    - Creates session record
    """
    client_ip = get_client_ip(request)
    logger.info(f"Login attempt for email: {form_data.username} from IP: {client_ip}")

    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        log_auth_event(logger, "LOGIN", form_data.username, False, client_ip, "User not found")
        raise InvalidCredentialsError()

    if not verify_password(form_data.password, user.password_hash):
        log_auth_event(logger, "LOGIN", form_data.username, False, client_ip, "Invalid password")
        raise InvalidCredentialsError()

    # Check if user account is active
    if hasattr(user, 'is_active') and not user.is_active:
        log_auth_event(logger, "LOGIN", form_data.username, False, client_ip, "Account inactive")
        raise AccountInactiveError()

    # Create tokens (sub must be a string per JWT spec)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    logger.debug(f"Tokens created for user: {user.email}")

    # Create session
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    log_auth_event(logger, "LOGIN", user.email, True, client_ip)
    logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    - Validates refresh token
    - Returns new access and refresh tokens
    """
    client_ip = get_client_ip(request)
    logger.info(f"Token refresh attempt from IP: {client_ip}")

    payload = decode_token(token_data.refresh_token)

    if not payload:
        logger.warning(f"Invalid refresh token from IP: {client_ip}")
        raise InvalidTokenError(
            message="Invalid or expired refresh token",
            token_type="refresh"
        )

    if payload.get("type") != "refresh":
        logger.warning(f"Wrong token type used for refresh from IP: {client_ip}")
        raise InvalidTokenError(
            message="Invalid token type. Expected refresh token.",
            token_type="refresh"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"Token refresh for non-existent user ID: {user_id}")
        raise UserNotFoundError()

    # Create new tokens (sub must be a string per JWT spec)
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: Request,
    verification: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    Verify user email address

    - Validates verification token
    - Marks email as verified
    """
    client_ip = get_client_ip(request)
    logger.info(f"Email verification attempt from IP: {client_ip}")

    email = verify_email_token(verification.token)

    if not email:
        logger.warning(f"Invalid verification token from IP: {client_ip}")
        raise InvalidVerificationTokenError()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Email verification for non-existent email: {email}")
        raise UserNotFoundError()

    if user.email_verified_at:
        logger.info(f"Email already verified: {user.email}")
        return {"message": "Email already verified"}

    user.email_verified_at = datetime.utcnow()
    db.commit()

    log_auth_event(logger, "EMAIL_VERIFY", user.email, True, client_ip)
    logger.info(f"Email verified successfully: {user.email}")

    return {"message": "Email verified successfully"}


@router.post("/forgot-password/send-otp", status_code=status.HTTP_200_OK)
async def send_password_reset_otp(
    request: Request,
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send OTP for password reset

    - Validates email exists
    - Generates and sends OTP to email
    - Stores OTP for verification
    """
    client_ip = get_client_ip(request)
    logger.info(f"Password reset OTP request for email: {reset_request.email} from IP: {client_ip}")

    user = db.query(User).filter(User.email == reset_request.email).first()

    # Always return same message for security (don't reveal if email exists)
    response_message = "If an account with that email exists, we've sent a verification code"

    if not user:
        log_auth_event(logger, "PASSWORD_RESET_OTP", reset_request.email, False, client_ip, "User not found")
        logger.info(f"Password reset OTP requested for non-existent email: {reset_request.email}")
        return {"message": response_message, "email": reset_request.email}

    try:
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Invalidate any existing OTPs for this email
        db.query(EmailOTP).filter(
            EmailOTP.email == reset_request.email,
            EmailOTP.purpose == "password_reset",
            EmailOTP.verified_at.is_(None)
        ).update({"verified_at": datetime.utcnow()})

        # Store new OTP
        email_otp = EmailOTP(
            email=reset_request.email,
            otp=otp,
            purpose="password_reset",
            expires_at=expires_at
        )
        db.add(email_otp)
        db.commit()

        # Send OTP email in background
        background_tasks.add_task(send_password_reset_otp_sync, user.email, user.name, otp)

        log_auth_event(logger, "PASSWORD_RESET_OTP", user.email, True, client_ip)
        logger.info(f"Password reset OTP queued for sending to: {user.email}")

        return {"message": response_message, "email": reset_request.email}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process password reset OTP for {reset_request.email}: {e}", exc_info=True)
        return {"message": response_message, "email": reset_request.email}


@router.post("/forgot-password/verify-otp", status_code=status.HTTP_200_OK)
async def verify_password_reset_otp(
    request: Request,
    otp_data: PasswordResetOTPVerification,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and reset password

    - Validates OTP
    - Updates password
    - Revokes all sessions
    """
    client_ip = get_client_ip(request)
    email = otp_data.email
    otp = otp_data.otp
    new_password = otp_data.new_password
    logger.info(f"Password reset OTP verification for: {email} from IP: {client_ip}")

    # Find valid OTP
    email_otp = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.otp == otp,
        EmailOTP.purpose == "password_reset",
        EmailOTP.verified_at.is_(None),
        EmailOTP.expires_at > datetime.utcnow()
    ).first()

    if not email_otp:
        log_auth_event(logger, "PASSWORD_RESET_VERIFY", email, False, client_ip, "Invalid or expired OTP")
        raise InvalidTokenError(message="Invalid or expired verification code", token_type="otp")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise UserNotFoundError()

    try:
        # Mark OTP as verified
        email_otp.verified_at = datetime.utcnow()

        # Update password
        user.password_hash = hash_password(new_password)

        # Revoke all sessions for security
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None)
        ).all()

        revoked_count = 0
        for session in sessions:
            session.revoked_at = datetime.utcnow()
            revoked_count += 1

        db.commit()

        log_auth_event(logger, "PASSWORD_RESET", user.email, True, client_ip)
        logger.info(f"Password reset successfully for: {user.email} (revoked {revoked_count} sessions)")

        return {"message": "Password reset successfully. You can now log in with your new password."}

    except Exception as e:
        db.rollback()
        logger.error(f"Password reset failed for {email}: {e}", exc_info=True)
        raise


# Legacy endpoints (keeping for backwards compatibility)
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: Request,
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset (Legacy - use /forgot-password/send-otp instead)
    """
    return await send_password_reset_otp(request, reset_request, background_tasks, db)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: Request,
    reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password with token (Legacy endpoint)

    - Validates reset token
    - Updates password
    """
    client_ip = get_client_ip(request)
    logger.info(f"Password reset attempt from IP: {client_ip}")

    email = verify_password_reset_token(reset.token)

    if not email:
        logger.warning(f"Invalid password reset token from IP: {client_ip}")
        raise InvalidResetTokenError()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Password reset for non-existent email: {email}")
        raise UserNotFoundError()

    # Update password
    user.password_hash = hash_password(reset.new_password)

    # Revoke all sessions for security
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.revoked_at.is_(None)
    ).all()

    revoked_count = 0
    for session in sessions:
        session.revoked_at = datetime.utcnow()
        revoked_count += 1

    db.commit()

    log_auth_event(logger, "PASSWORD_RESET", user.email, True, client_ip)
    logger.info(f"Password reset successfully for: {user.email} (revoked {revoked_count} sessions)")

    return {"message": "Password reset successfully. You can now log in with your new password."}


@router.get("/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow

    - Returns Google OAuth URL
    """
    client_ip = get_client_ip(request)
    logger.info(f"Google OAuth initiated from IP: {client_ip}")

    if not settings.GOOGLE_CLIENT_ID:
        logger.error("Google OAuth not configured - GOOGLE_CLIENT_ID missing")
        raise GoogleOAuthError("Google OAuth is not configured")

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile"
    )

    logger.debug(f"Google OAuth URL generated, redirect URI: {settings.GOOGLE_REDIRECT_URI}")

    return {"auth_url": google_auth_url}


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback

    - Exchanges code for tokens
    - Creates or updates user
    - Returns JWT tokens
    """
    client_ip = get_client_ip(request)
    logger.info(f"Google OAuth callback from IP: {client_ip}")

    # Exchange code for tokens
    logger.debug("Exchanging authorization code for tokens")
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                },
                timeout=10.0
            )
    except httpx.RequestError as e:
        logger.error(f"Google token exchange network error: {e}")
        raise GoogleOAuthError("Unable to connect to Google. Please try again.")

    if token_response.status_code != 200:
        logger.error(f"Google token exchange failed: {token_response.status_code} - {token_response.text}")
        raise GoogleOAuthError("Failed to authenticate with Google. Please try again.")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        logger.error("No access token in Google response")
        raise GoogleOAuthError("Invalid response from Google")

    logger.debug("Successfully obtained Google access token")

    # Get user info from Google
    logger.debug("Fetching user info from Google")
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
    except httpx.RequestError as e:
        logger.error(f"Google user info request failed: {e}")
        raise GoogleOAuthError("Unable to get user information from Google")

    if user_response.status_code != 200:
        logger.error(f"Google user info failed: {user_response.status_code}")
        raise GoogleOAuthError("Failed to get user information from Google")

    user_data = user_response.json()
    google_user_id = user_data.get("id")
    email = user_data.get("email")
    name = user_data.get("name")

    logger.info(f"Google user info received: email={email}, name={name}")

    if not email:
        logger.error("No email in Google user info")
        raise GoogleOAuthError("Could not get email from Google account")

    # Check if OAuth account exists
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.provider == OAuthProvider.GOOGLE,
        OAuthAccount.provider_user_id == google_user_id
    ).first()

    if oauth_account:
        # Existing user
        user = oauth_account.user
        oauth_account.access_token = access_token
        logger.info(f"Existing Google OAuth user: {user.email}")
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
            logger.info(f"New user created via Google OAuth: {email} (ID: {user.id})")
        else:
            logger.info(f"Linking existing user to Google OAuth: {email}")

        # Create OAuth account
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=OAuthProvider.GOOGLE,
            provider_user_id=google_user_id,
            access_token=access_token
        )
        db.add(oauth_account)

    db.commit()

    # Create JWT tokens (sub must be a string per JWT spec)
    jwt_access_token = create_access_token(data={"sub": str(user.id)})
    jwt_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Create session
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    log_auth_event(logger, "GOOGLE_LOGIN", user.email, True, client_ip)
    logger.info(f"Google OAuth login successful: {user.email} (ID: {user.id})")

    # Redirect to frontend with tokens in URL params
    frontend_url = "http://localhost:5173"
    redirect_url = f"{frontend_url}/auth/google/callback?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user

    - Revokes all active sessions for the user
    - Client should clear stored tokens
    """
    client_ip = get_client_ip(request)
    logger.info(f"Logout request for user: {current_user.email} from IP: {client_ip}")

    # Revoke all active sessions for this user
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).all()

    revoked_count = 0
    for session in sessions:
        session.revoked_at = datetime.utcnow()
        revoked_count += 1

    db.commit()

    log_auth_event(logger, "LOGOUT", current_user.email, True, client_ip)
    logger.info(f"User logged out: {current_user.email} (revoked {revoked_count} sessions)")

    return {"message": "Logged out successfully"}
