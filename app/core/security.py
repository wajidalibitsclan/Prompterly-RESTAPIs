"""
Security utilities for password hashing, verification, and token generation
"""
# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any
# from passlib.context import CryptContext
# from jose import JWTError, jwt
# from app.core.config import settings


# # Password hashing context
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


print(">>> USING SECURITY FILE:", __file__)


def _pre_hash(password: str) -> str:
    """
    Convert any-length password into a fixed 64-char SHA256 hex.
    Avoids bcrypt 72-byte limitation.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def hash_password(password: str) -> str:
    """
    Secure password hashing:
    1. SHA-256 pre-hash (fixes length)
    2. bcrypt hash (final storage)
    """
    pre_hashed = _pre_hash(password)
    return pwd_context.hash(pre_hashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using the same pre-hash process.
    """
    pre_hashed = _pre_hash(plain_password)
    return pwd_context.verify(pre_hashed, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary of claims to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Dictionary of claims to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        print(f"[JWT DECODE ERROR] {type(e).__name__}: {e}")
        print(f"[JWT DECODE ERROR] Token (first 50 chars): {token[:50] if token else 'None'}...")
        return None


def generate_email_verification_token(email: str) -> str:
    """
    Generate a token for email verification
    
    Args:
        email: User's email address
        
    Returns:
        Verification token
    """
    data = {"email": email, "purpose": "email_verification"}
    expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_email_token(token: str) -> Optional[str]:
    """
    Verify an email verification token
    
    Args:
        token: Email verification token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("purpose") == "email_verification":
            return payload.get("email")
        
        return None
    except JWTError:
        return None


def generate_password_reset_token(email: str) -> str:
    """
    Generate a token for password reset
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    data = {"email": email, "purpose": "password_reset"}
    expire = datetime.utcnow() + timedelta(hours=1)
    
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token
    
    Args:
        token: Password reset token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("purpose") == "password_reset":
            return payload.get("email")
        
        return None
    except JWTError:
        return None
