"""
Pydantic schemas for authentication and user management
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.db.models.user import UserRole


# Authentication Schemas
class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        # Check byte length for bcrypt compatibility
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: Optional[bool] = None
    temp_token: Optional[str] = None
    # Which second-factor method the user must use to complete login:
    # 'totp' (authenticator app) or 'email' (one-time code sent to inbox).
    # Populated alongside requires_2fa=True.
    two_factor_method: Optional[str] = None


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


class EmailVerification(BaseModel):
    """Schema for email verification"""
    token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class OTPVerification(BaseModel):
    """Schema for OTP verification during registration"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class PasswordResetOTPVerification(BaseModel):
    """Schema for OTP verification during password reset"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    avatar_url: Optional[str]
    role: UserRole
    email_verified_at: Optional[datetime]
    language: str = "en"
    timezone: str = "Australia/Sydney"
    is_2fa_enabled: bool = False
    # Notification preferences
    notify_email_enabled: bool = True
    notify_in_app_enabled: bool = True
    notify_capsule_unlock: bool = True
    notify_new_message: bool = True
    notify_subscription_updates: bool = True
    notify_mentor_approved: bool = True
    # Privacy / Legal
    privacy_accepted_at: Optional[datetime] = None
    tos_accepted_at: Optional[datetime] = None
    age_confirmed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user update"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserActivity(BaseModel):
    """Schema for user activity log"""
    id: int
    action: str
    timestamp: datetime
    details: Optional[dict]

    class Config:
        from_attributes = True


# Email Change Schemas
class EmailChangeRequest(BaseModel):
    """Schema for requesting email change - sends OTP to new email"""
    new_email: EmailStr
    password: str  # Require current password for security


class EmailChangeVerify(BaseModel):
    """Schema for verifying email change OTP"""
    new_email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class EmailChangeRevert(BaseModel):
    """Schema for reverting an email change using recovery token"""
    token: str


# 2FA / MFA Schemas
class TwoFactorSetupRequest(BaseModel):
    """
    Request body for POST /auth/2fa/setup.

    Picks which second-factor method the user wants to enrol in:
      - 'totp'  → authenticator app (Google Authenticator, Authy, 1Password)
      - 'email' → one-time code sent to the account's email address
    """
    method: str = Field("totp", pattern="^(totp|email)$")


class TwoFactorSetupResponse(BaseModel):
    """
    Response when setting up 2FA.

    For method='totp' the secret + QR code fields are populated so the user
    can scan it in their authenticator app. For method='email' those fields
    are empty — the caller shows "check your inbox" instead.
    """
    method: str
    secret: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_code_base64: Optional[str] = None
    # For email method, tells the UI where we sent the code (masked).
    email_destination: Optional[str] = None


class TwoFactorEnable(BaseModel):
    """Schema for enabling 2FA — requires a valid code to confirm setup."""
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorDisable(BaseModel):
    """Schema for disabling 2FA — requires password and current code."""
    password: str
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorVerify(BaseModel):
    """Schema for verifying 2FA during login."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    temp_token: str  # Temporary token issued after password verification


class TwoFactorEmailResend(BaseModel):
    """Schema for re-sending an email OTP during the login flow."""
    email: EmailStr
    temp_token: str


# =============================================================================
# Settings Schemas
# =============================================================================

class LanguageTimezoneUpdate(BaseModel):
    """Schema for updating language and timezone preferences"""
    language: Optional[str] = Field(None, min_length=2, max_length=10, description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')")
    timezone: Optional[str] = Field(None, max_length=50, description="IANA timezone (e.g., 'Australia/Sydney', 'America/New_York')")


class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences"""
    notify_email_enabled: Optional[bool] = None
    notify_in_app_enabled: Optional[bool] = None
    notify_capsule_unlock: Optional[bool] = None
    notify_new_message: Optional[bool] = None
    notify_subscription_updates: Optional[bool] = None
    notify_mentor_approved: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    """Schema for notification preferences response"""
    notify_email_enabled: bool
    notify_in_app_enabled: bool
    notify_capsule_unlock: bool
    notify_new_message: bool
    notify_subscription_updates: bool
    notify_mentor_approved: bool

    class Config:
        from_attributes = True


class PrivacyAcceptance(BaseModel):
    """Schema for accepting privacy policy and/or ToS"""
    accept_privacy_policy: bool = False
    accept_terms_of_service: bool = False
    confirm_age_18_plus: bool = False
