"""
Custom Exception Classes for AI Coaching Platform
Provides structured error responses with error codes for frontend handling
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception class for application errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        response = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            response["details"] = self.details
        return response


# =============================================================================
# Authentication Exceptions
# =============================================================================

class AuthenticationError(AppException):
    """Base authentication error"""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password"""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS"
        )


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token"""

    def __init__(
        self,
        message: str = "Invalid or expired token",
        token_type: str = "access"
    ):
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            details={"token_type": token_type}
        )


class TokenExpiredError(AuthenticationError):
    """Token has expired"""

    def __init__(self, token_type: str = "access"):
        super().__init__(
            message=f"Your {token_type} token has expired. Please log in again.",
            error_code="TOKEN_EXPIRED",
            details={"token_type": token_type}
        )


class EmailNotVerifiedError(AuthenticationError):
    """Email address not verified"""

    def __init__(self):
        super().__init__(
            message="Please verify your email address before logging in",
            error_code="EMAIL_NOT_VERIFIED"
        )


class AccountInactiveError(AuthenticationError):
    """User account is inactive/disabled"""

    def __init__(self):
        super().__init__(
            message="Your account has been deactivated. Please contact support.",
            error_code="ACCOUNT_INACTIVE"
        )


# =============================================================================
# Authorization Exceptions
# =============================================================================

class AuthorizationError(AppException):
    """Base authorization error"""

    def __init__(
        self,
        message: str = "You don't have permission to perform this action",
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""

    def __init__(self, required_role: Optional[str] = None):
        details = {"required_role": required_role} if required_role else None
        super().__init__(
            message="You don't have the required permissions for this action",
            error_code="INSUFFICIENT_PERMISSIONS",
            details=details
        )


class MentorNotApprovedError(AuthorizationError):
    """Mentor application not yet approved"""

    def __init__(self):
        super().__init__(
            message="Your mentor application is pending approval",
            error_code="MENTOR_NOT_APPROVED"
        )


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(AppException):
    """Base validation error"""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if field and not details:
            details = {"field": field}
        elif field and details:
            details["field"] = field

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details
        )


class EmailAlreadyExistsError(ValidationError):
    """Email already registered"""

    def __init__(self, email: Optional[str] = None):
        super().__init__(
            message="This email address is already registered",
            error_code="EMAIL_ALREADY_EXISTS",
            field="email"
        )


class InvalidEmailFormatError(ValidationError):
    """Invalid email format"""

    def __init__(self):
        super().__init__(
            message="Please enter a valid email address",
            error_code="INVALID_EMAIL_FORMAT",
            field="email"
        )


class WeakPasswordError(ValidationError):
    """Password doesn't meet requirements"""

    def __init__(self, requirements: Optional[list] = None):
        message = "Password must be at least 8 characters with one uppercase letter and one number"
        super().__init__(
            message=message,
            error_code="WEAK_PASSWORD",
            field="password",
            details={"requirements": requirements} if requirements else None
        )


class PasswordMismatchError(ValidationError):
    """Passwords don't match"""

    def __init__(self):
        super().__init__(
            message="Passwords do not match",
            error_code="PASSWORD_MISMATCH",
            field="confirm_password"
        )


class InvalidResetTokenError(ValidationError):
    """Invalid or expired password reset token"""

    def __init__(self):
        super().__init__(
            message="This password reset link is invalid or has expired. Please request a new one.",
            error_code="INVALID_RESET_TOKEN",
            field="token"
        )


class InvalidVerificationTokenError(ValidationError):
    """Invalid or expired email verification token"""

    def __init__(self):
        super().__init__(
            message="This verification link is invalid or has expired. Please request a new one.",
            error_code="INVALID_VERIFICATION_TOKEN",
            field="token"
        )


# =============================================================================
# Resource Exceptions
# =============================================================================

class ResourceNotFoundError(AppException):
    """Resource not found"""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None
    ):
        details = {"resource_id": resource_id} if resource_id else None
        super().__init__(
            message=f"{resource} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details
        )


class UserNotFoundError(ResourceNotFoundError):
    """User not found"""

    def __init__(self, user_id: Optional[str] = None):
        super().__init__(resource="User", resource_id=user_id)


class LoungeNotFoundError(ResourceNotFoundError):
    """Lounge not found"""

    def __init__(self, lounge_id: Optional[str] = None):
        super().__init__(resource="Lounge", resource_id=lounge_id)


class MentorNotFoundError(ResourceNotFoundError):
    """Mentor not found"""

    def __init__(self, mentor_id: Optional[str] = None):
        super().__init__(resource="Mentor", resource_id=mentor_id)


# =============================================================================
# Business Logic Exceptions
# =============================================================================

class BusinessError(AppException):
    """Base business logic error"""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details
        )


class SubscriptionRequiredError(BusinessError):
    """Active subscription required"""

    def __init__(self, feature: Optional[str] = None):
        details = {"feature": feature} if feature else None
        super().__init__(
            message="An active subscription is required for this feature",
            error_code="SUBSCRIPTION_REQUIRED",
            details=details
        )


class SubscriptionLimitExceededError(BusinessError):
    """Subscription limit exceeded"""

    def __init__(self, limit_type: str, current: int, max_allowed: int):
        super().__init__(
            message=f"You've reached your {limit_type} limit ({current}/{max_allowed})",
            error_code="SUBSCRIPTION_LIMIT_EXCEEDED",
            details={
                "limit_type": limit_type,
                "current": current,
                "max_allowed": max_allowed
            }
        )


class AlreadyMemberError(BusinessError):
    """Already a member of the resource"""

    def __init__(self, resource: str = "lounge"):
        super().__init__(
            message=f"You are already a member of this {resource}",
            error_code="ALREADY_MEMBER"
        )


# =============================================================================
# External Service Exceptions
# =============================================================================

class ExternalServiceError(AppException):
    """External service error"""

    def __init__(
        self,
        service: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Failed to communicate with {service}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service}
        )


class GoogleOAuthError(ExternalServiceError):
    """Google OAuth error"""

    def __init__(self, message: str = "Failed to authenticate with Google"):
        super().__init__(service="Google OAuth", message=message)


class StripeError(ExternalServiceError):
    """Stripe payment error"""

    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(service="Stripe", message=message)


class OpenAIError(ExternalServiceError):
    """OpenAI API error"""

    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(service="OpenAI", message=message)


# =============================================================================
# Rate Limiting Exceptions
# =============================================================================

class RateLimitExceededError(AppException):
    """Rate limit exceeded"""

    def __init__(self, retry_after: Optional[int] = None):
        details = {"retry_after_seconds": retry_after} if retry_after else None
        super().__init__(
            message="Too many requests. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )
