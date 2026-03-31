"""
Authentication API endpoints
Handles user registration, login, OAuth, password reset
"""
from fastapi import APIRouter, Depends, BackgroundTasks, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
import httpx
import random
import string
import pyotp
import qrcode
import qrcode.constants
import io
import base64

from app.db.session import get_db
from app.core.timezone import now_naive
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_email_verification_token,
    verify_email_token,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_email_change_recovery_token,
    verify_email_change_recovery_token,
)
from app.core.config import settings
from app.core.rate_limit import limiter, STRICT, AUTH
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
from app.db.models.auth import UserSession, OAuthAccount, OAuthProvider, EmailOTP, EmailChangeRequest as EmailChangeRequestModel
from app.services.email_service import (
    send_otp_email_sync,
    send_password_reset_otp_sync,
    send_welcome_email_sync,
    send_email_change_confirmation_sync,
    send_email_change_alert_sync,
    send_suspicious_login_alert_sync,
)
from app.schemas.auth import (
    UserRegister,
    Token,
    TokenRefresh,
    EmailVerification,
    PasswordResetRequest,
    PasswordReset,
    UserResponse,
    OTPVerification,
    PasswordResetOTPVerification,
    EmailChangeRequest,
    EmailChangeVerify,
    EmailChangeRevert,
    TwoFactorSetupResponse,
    TwoFactorEnable,
    TwoFactorDisable,
    TwoFactorVerify,
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


def get_user_agent(request: Request) -> str:
    """Extract user agent string from request"""
    return request.headers.get("User-Agent", "Unknown")


def parse_device_info(user_agent: str, ip: str) -> str:
    """
    Parse user agent into a human-readable device/browser/location string.
    Example: 'Chrome, Windows 10, 203.0.113.42'
    """
    ua = user_agent.lower()

    # Detect browser
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    else:
        browser = "Unknown Browser"

    # Detect OS
    if "windows" in ua:
        os_name = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "macOS"
    elif "iphone" in ua:
        os_name = "iPhone"
    elif "ipad" in ua:
        os_name = "iPad"
    elif "android" in ua:
        os_name = "Android"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    return f"{browser}, {os_name}, {ip}"


def is_new_device(db: Session, user_id: int, ip: str, user_agent: str) -> bool:
    """
    Check if this is a new device/IP combination for the user.
    Returns True if the user has never logged in from this IP + user_agent combo.
    """
    existing = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.ip_address == ip,
        UserSession.user_agent == user_agent
    ).first()
    return existing is None


@router.post("/register/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit(AUTH)
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
        expires_at = now_naive() + timedelta(minutes=10)

        # Invalidate any existing OTPs for this email
        db.query(EmailOTP).filter(
            EmailOTP.email == user_data.email,
            EmailOTP.purpose == "registration",
            EmailOTP.verified_at.is_(None)
        ).update({"verified_at": now_naive()})

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
@limiter.limit(STRICT)
async def verify_registration_otp(
    otp_data: OTPVerification,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and complete registration

    - Validates OTP
    - Creates user account
    - Sends welcome email
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
        EmailOTP.expires_at > now_naive()
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
        email_otp.verified_at = now_naive()

        # Create new user with verified email
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.MEMBER,
            email_verified_at=now_naive()  # Email is verified via OTP
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        log_auth_event(logger, "REGISTER", new_user.email, True, client_ip)
        logger.info(f"User registered successfully via OTP: {new_user.email} (ID: {new_user.id})")

        # Send welcome email in background
        background_tasks.add_task(send_welcome_email_sync, new_user.email, new_user.name)
        logger.info(f"Welcome email queued for: {new_user.email}")

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
@limiter.limit(AUTH)
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
@limiter.limit(STRICT)
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    - Validates credentials
    - Returns JWT access and refresh tokens
    - Creates session record with device info
    - Sends suspicious login alert if new device detected (PDF Email #7)
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
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

    # If 2FA is enabled, return a temporary token and require TOTP verification
    if user.is_2fa_enabled:
        temp_token = create_access_token(
            data={"sub": str(user.id), "purpose": "2fa_pending"},
            expires_delta=timedelta(minutes=5)
        )
        log_auth_event(logger, "LOGIN_2FA_PENDING", user.email, True, client_ip)
        logger.info(f"2FA required for user: {user.email}")
        return {
            "access_token": "",
            "refresh_token": "",
            "token_type": "bearer",
            "requires_2fa": True,
            "temp_token": temp_token
        }

    # Check for new device BEFORE creating the session
    new_device = is_new_device(db, user.id, client_ip, user_agent)

    # Create tokens (sub must be a string per JWT spec)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    logger.debug(f"Tokens created for user: {user.email}")

    # Create session with device info
    session = UserSession(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=now_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    # Send suspicious login alert if new device detected (PDF Email #7)
    if new_device and user.email_verified_at:
        login_time = now_naive().strftime("%B %d, %Y at %I:%M %p")
        device_info = parse_device_info(user_agent, client_ip)
        reset_url = f"{settings.FRONTEND_URL}/auth/forgot-password"
        background_tasks.add_task(
            send_suspicious_login_alert_sync,
            user.email,
            user.name,
            login_time,
            device_info,
            reset_url
        )
        logger.info(f"New device detected for {user.email} - suspicious login alert sent")

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

    user.email_verified_at = now_naive()
    db.commit()

    log_auth_event(logger, "EMAIL_VERIFY", user.email, True, client_ip)
    logger.info(f"Email verified successfully: {user.email}")

    return {"message": "Email verified successfully"}


@router.post("/forgot-password/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit(STRICT)
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
        expires_at = now_naive() + timedelta(minutes=10)

        # Invalidate any existing OTPs for this email
        db.query(EmailOTP).filter(
            EmailOTP.email == reset_request.email,
            EmailOTP.purpose == "password_reset",
            EmailOTP.verified_at.is_(None)
        ).update({"verified_at": now_naive()})

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
@limiter.limit(STRICT)
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
        EmailOTP.expires_at > now_naive()
    ).first()

    if not email_otp:
        log_auth_event(logger, "PASSWORD_RESET_VERIFY", email, False, client_ip, "Invalid or expired OTP")
        raise InvalidTokenError(message="Invalid or expired verification code", token_type="otp")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise UserNotFoundError()

    try:
        # Mark OTP as verified
        email_otp.verified_at = now_naive()

        # Update password
        user.password_hash = hash_password(new_password)

        # Revoke all sessions for security
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None)
        ).all()

        revoked_count = 0
        for session in sessions:
            session.revoked_at = now_naive()
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
@limiter.limit(STRICT)
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
@limiter.limit(STRICT)
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
        session.revoked_at = now_naive()
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
    background_tasks: BackgroundTasks,
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
                email_verified_at=now_naive()  # Google emails are verified
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

    # Check for new device before creating session
    user_agent = get_user_agent(request)
    new_device = is_new_device(db, user.id, client_ip, user_agent)

    # Create session with device info
    session = UserSession(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=now_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    # Send suspicious login alert if new device (PDF Email #7)
    if new_device and user.email_verified_at:
        login_time = now_naive().strftime("%B %d, %Y at %I:%M %p")
        device_info = parse_device_info(user_agent, client_ip)
        reset_url = f"{settings.FRONTEND_URL}/auth/forgot-password"
        background_tasks.add_task(
            send_suspicious_login_alert_sync,
            user.email,
            user.name,
            login_time,
            device_info,
            reset_url
        )
        logger.info(f"New device detected for Google login {user.email} - alert sent")

    log_auth_event(logger, "GOOGLE_LOGIN", user.email, True, client_ip)
    logger.info(f"Google OAuth login successful: {user.email} (ID: {user.id})")

    # Redirect to frontend with tokens in URL params
    redirect_url = f"{settings.FRONTEND_URL}/auth/google/callback?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"

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
        session.revoked_at = now_naive()
        revoked_count += 1

    db.commit()

    log_auth_event(logger, "LOGOUT", current_user.email, True, client_ip)
    logger.info(f"User logged out: {current_user.email} (revoked {revoked_count} sessions)")

    return {"message": "Logged out successfully"}


# =============================================================================
# Email Change Flow (PDF Emails #3 & #4)
# =============================================================================

@router.post("/email-change/send-otp", status_code=status.HTTP_200_OK)
@limiter.limit(AUTH)
async def send_email_change_otp(
    data: EmailChangeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Request email change — sends OTP to the new email address.

    - Requires current password for security
    - Validates new email is not already taken
    - Sends 6-digit OTP to the new email
    """
    client_ip = get_client_ip(request)
    logger.info(f"Email change OTP request from user {current_user.email} to {data.new_email} IP: {client_ip}")

    # Verify current password
    if not verify_password(data.password, current_user.password_hash):
        log_auth_event(logger, "EMAIL_CHANGE_OTP", current_user.email, False, client_ip, "Invalid password")
        raise InvalidCredentialsError(message="Incorrect password")

    # Check new email is different
    if data.new_email.lower() == current_user.email.lower():
        raise EmailAlreadyExistsError()

    # Check new email is not already taken
    existing = db.query(User).filter(User.email == data.new_email).first()
    if existing:
        log_auth_event(logger, "EMAIL_CHANGE_OTP", current_user.email, False, client_ip, "New email already exists")
        raise EmailAlreadyExistsError()

    try:
        otp = generate_otp()
        expires_at = now_naive() + timedelta(minutes=10)

        # Invalidate any pending email change OTPs for this user
        db.query(EmailOTP).filter(
            EmailOTP.email == data.new_email,
            EmailOTP.purpose == "email_change",
            EmailOTP.verified_at.is_(None)
        ).update({"verified_at": now_naive()})

        # Store OTP
        email_otp = EmailOTP(
            email=data.new_email,
            otp=otp,
            purpose="email_change",
            expires_at=expires_at
        )
        db.add(email_otp)
        db.commit()

        # Send OTP to the new email
        background_tasks.add_task(send_otp_email_sync, data.new_email, current_user.name, otp)

        log_auth_event(logger, "EMAIL_CHANGE_OTP", current_user.email, True, client_ip)
        return {"message": "Verification code sent to your new email address", "new_email": data.new_email}

    except (EmailAlreadyExistsError, InvalidCredentialsError):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Email change OTP failed for {current_user.email}: {e}", exc_info=True)
        raise Exception("Failed to process email change. Please try again.")


@router.post("/email-change/verify-otp", status_code=status.HTTP_200_OK)
@limiter.limit(STRICT)
async def verify_email_change_otp(
    data: EmailChangeVerify,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 2: Verify OTP and complete email change.

    - Validates the OTP sent to the new email
    - Updates user email
    - Sends confirmation to new email (PDF #3)
    - Sends security alert to old email with recovery link (PDF #4)
    - Recovery link is valid for 48 hours
    """
    client_ip = get_client_ip(request)
    old_email = current_user.email
    logger.info(f"Email change verify from {old_email} to {data.new_email} IP: {client_ip}")

    # Validate OTP
    email_otp = db.query(EmailOTP).filter(
        EmailOTP.email == data.new_email,
        EmailOTP.otp == data.otp,
        EmailOTP.purpose == "email_change",
        EmailOTP.verified_at.is_(None),
        EmailOTP.expires_at > now_naive()
    ).first()

    if not email_otp:
        log_auth_event(logger, "EMAIL_CHANGE_VERIFY", old_email, False, client_ip, "Invalid or expired OTP")
        raise InvalidTokenError(message="Invalid or expired verification code", token_type="otp")

    # Double-check new email is still available (race condition)
    existing = db.query(User).filter(User.email == data.new_email, User.id != current_user.id).first()
    if existing:
        raise EmailAlreadyExistsError()

    try:
        # Mark OTP as verified
        email_otp.verified_at = now_naive()

        # Generate recovery token for old email (48-hour window)
        recovery_token = generate_email_change_recovery_token(
            user_id=current_user.id,
            old_email=old_email,
            new_email=data.new_email
        )

        # Record the email change request
        change_request = EmailChangeRequestModel(
            user_id=current_user.id,
            old_email=old_email,
            new_email=data.new_email,
            recovery_token=recovery_token,
            recovery_expires_at=now_naive() + timedelta(hours=48),
            completed_at=now_naive()
        )
        db.add(change_request)

        # Update user email
        current_user.email = data.new_email
        current_user.updated_at = now_naive()

        db.commit()

        # Build recovery URL for the old email
        secure_account_url = f"{settings.FRONTEND_URL}/auth/email-recovery?token={recovery_token}"

        # Send confirmation to NEW email (PDF #3)
        background_tasks.add_task(
            send_email_change_confirmation_sync,
            data.new_email,
            current_user.name
        )

        # Send security alert to OLD email with recovery link (PDF #4)
        background_tasks.add_task(
            send_email_change_alert_sync,
            old_email,
            current_user.name,
            secure_account_url
        )

        log_auth_event(logger, "EMAIL_CHANGE", old_email, True, client_ip,
                       f"Changed to {data.new_email}")
        logger.info(f"Email changed: {old_email} -> {data.new_email} (user {current_user.id})")

        return {
            "message": "Email address updated successfully. A security alert has been sent to your previous email.",
            "new_email": data.new_email
        }

    except (EmailAlreadyExistsError, InvalidTokenError):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Email change verification failed: {e}", exc_info=True)
        raise


@router.post("/email-change/revert", status_code=status.HTTP_200_OK)
@limiter.limit(STRICT)
async def revert_email_change(
    data: EmailChangeRevert,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Revert an email change using the recovery token sent to the old email.

    - Validates tokenised recovery link
    - Reverts user email to the old address
    - Revokes all active sessions (forces re-login)
    - Recovery token is valid for 48 hours from the time of the change
    """
    client_ip = get_client_ip(request)
    logger.info(f"Email change revert attempt from IP: {client_ip}")

    # Verify recovery token
    token_data = verify_email_change_recovery_token(data.token)
    if not token_data:
        logger.warning(f"Invalid email change recovery token from IP: {client_ip}")
        raise InvalidTokenError(message="Invalid or expired recovery link", token_type="email_change_recovery")

    user_id = token_data["user_id"]
    old_email = token_data["old_email"]
    new_email = token_data["new_email"]

    # Find the change request
    change_request = db.query(EmailChangeRequestModel).filter(
        EmailChangeRequestModel.user_id == user_id,
        EmailChangeRequestModel.old_email == old_email,
        EmailChangeRequestModel.new_email == new_email,
        EmailChangeRequestModel.completed_at.isnot(None),
        EmailChangeRequestModel.reverted_at.is_(None),
        EmailChangeRequestModel.recovery_expires_at > now_naive()
    ).first()

    if not change_request:
        raise InvalidTokenError(
            message="This recovery link has expired or the change has already been reverted",
            token_type="email_change_recovery"
        )

    # Find the user (should currently have the new email)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError()

    try:
        # Check old email isn't taken by someone else now
        conflict = db.query(User).filter(User.email == old_email, User.id != user_id).first()
        if conflict:
            raise EmailAlreadyExistsError()

        # Revert the email
        user.email = old_email
        user.updated_at = now_naive()

        # Mark change as reverted
        change_request.reverted_at = now_naive()

        # Revoke all sessions to force re-login
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None)
        ).all()
        for session in sessions:
            session.revoked_at = now_naive()

        # Reset password for security
        # (user should reset via forgot-password flow after reverting)

        db.commit()

        log_auth_event(logger, "EMAIL_CHANGE_REVERT", old_email, True, client_ip,
                       f"Reverted from {new_email}")
        logger.info(f"Email change reverted: {new_email} -> {old_email} (user {user_id})")

        return {
            "message": "Your email address has been reverted successfully. All sessions have been revoked. Please log in with your original email and reset your password."
        }

    except (EmailAlreadyExistsError, InvalidTokenError):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Email change revert failed: {e}", exc_info=True)
        raise


# =============================================================================
# Two-Factor Authentication (2FA / MFA)
# =============================================================================

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
@limiter.limit(AUTH)
async def setup_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Generate TOTP secret and QR code for 2FA setup.

    - Returns a base32 secret, an otpauth:// URI, and a base64 QR code image
    - User should scan QR code with Google Authenticator / Authy
    - Secret is stored but 2FA is NOT enabled until /2fa/enable is called
    """
    client_ip = get_client_ip(request)
    logger.info(f"2FA setup request from user {current_user.email} IP: {client_ip}")

    # Generate a new TOTP secret
    secret = pyotp.random_base32()

    # Store the secret (not yet enabled)
    current_user.totp_secret = secret
    db.commit()

    # Generate otpauth URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Prompterly"
    )

    # Generate QR code as base64 image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    log_auth_event(logger, "2FA_SETUP", current_user.email, True, client_ip)

    return {
        "secret": secret,
        "qr_code_url": provisioning_uri,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}"
    }


@router.post("/2fa/enable", status_code=status.HTTP_200_OK)
@limiter.limit(STRICT)
async def enable_2fa(
    data: TwoFactorEnable,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 2: Verify TOTP code and enable 2FA.

    - Validates the code from the authenticator app
    - Enables 2FA on the account
    - Must be called after /2fa/setup
    """
    client_ip = get_client_ip(request)
    logger.info(f"2FA enable request from user {current_user.email} IP: {client_ip}")

    if not current_user.totp_secret:
        raise InvalidTokenError(
            message="Please set up 2FA first using /auth/2fa/setup",
            token_type="totp"
        )

    if current_user.is_2fa_enabled:
        return {"message": "Two-factor authentication is already enabled"}

    # Verify the TOTP code
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        log_auth_event(logger, "2FA_ENABLE", current_user.email, False, client_ip, "Invalid TOTP code")
        raise InvalidTokenError(message="Invalid verification code. Please try again.", token_type="totp")

    # Enable 2FA
    current_user.is_2fa_enabled = True
    db.commit()

    log_auth_event(logger, "2FA_ENABLE", current_user.email, True, client_ip)
    logger.info(f"2FA enabled for user: {current_user.email}")

    return {"message": "Two-factor authentication has been enabled successfully"}


@router.post("/2fa/disable", status_code=status.HTTP_200_OK)
@limiter.limit(STRICT)
async def disable_2fa(
    data: TwoFactorDisable,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA on the account.

    - Requires current password and a valid TOTP code for security
    - Removes TOTP secret and disables 2FA
    """
    client_ip = get_client_ip(request)
    logger.info(f"2FA disable request from user {current_user.email} IP: {client_ip}")

    if not current_user.is_2fa_enabled:
        return {"message": "Two-factor authentication is not enabled"}

    # Verify password
    if not verify_password(data.password, current_user.password_hash):
        log_auth_event(logger, "2FA_DISABLE", current_user.email, False, client_ip, "Invalid password")
        raise InvalidCredentialsError(message="Incorrect password")

    # Verify TOTP code
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        log_auth_event(logger, "2FA_DISABLE", current_user.email, False, client_ip, "Invalid TOTP code")
        raise InvalidTokenError(message="Invalid verification code", token_type="totp")

    # Disable 2FA
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    db.commit()

    log_auth_event(logger, "2FA_DISABLE", current_user.email, True, client_ip)
    logger.info(f"2FA disabled for user: {current_user.email}")

    return {"message": "Two-factor authentication has been disabled"}


@router.post("/2fa/verify", response_model=Token)
@limiter.limit(STRICT)
async def verify_2fa(
    data: TwoFactorVerify,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify 2FA code during login.

    - Called after login returns requires_2fa=True with a temp_token
    - Validates the TOTP code
    - Returns full access + refresh tokens
    - Creates session and checks for new device
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    logger.info(f"2FA verification attempt for {data.email} from IP: {client_ip}")

    # Verify the temporary token
    payload = decode_token(data.temp_token)
    if not payload:
        raise InvalidTokenError(message="Invalid or expired temporary token", token_type="2fa_temp")

    if payload.get("purpose") != "2fa_pending":
        raise InvalidTokenError(message="Invalid token type", token_type="2fa_temp")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.email == data.email).first()

    if not user:
        raise UserNotFoundError()

    if not user.is_2fa_enabled or not user.totp_secret:
        raise InvalidTokenError(message="2FA is not enabled on this account", token_type="totp")

    # Verify TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        log_auth_event(logger, "2FA_VERIFY", user.email, False, client_ip, "Invalid TOTP code")
        raise InvalidTokenError(message="Invalid verification code", token_type="totp")

    # Check for new device
    new_device = is_new_device(db, user.id, client_ip, user_agent)

    # Create full tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Create session with device info
    session = UserSession(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=now_naive() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    db.commit()

    # Send suspicious login alert if new device (PDF Email #7)
    if new_device and user.email_verified_at:
        login_time = now_naive().strftime("%B %d, %Y at %I:%M %p")
        device_info = parse_device_info(user_agent, client_ip)
        reset_url = f"{settings.FRONTEND_URL}/auth/forgot-password"
        background_tasks.add_task(
            send_suspicious_login_alert_sync,
            user.email,
            user.name,
            login_time,
            device_info,
            reset_url
        )

    log_auth_event(logger, "LOGIN_2FA", user.email, True, client_ip)
    logger.info(f"2FA login successful for: {user.email}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/2fa/status", status_code=status.HTTP_200_OK)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
):
    """
    Check if 2FA is enabled for the current user.
    """
    return {
        "is_2fa_enabled": current_user.is_2fa_enabled,
    }
