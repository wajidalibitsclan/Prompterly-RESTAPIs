"""
JWT authentication dependencies
Provides utilities for extracting and validating JWT tokens from requests
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.db.session import get_db
from app.db.models.user import User


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active User object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.email_verified_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return current_user


async def get_current_mentor(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is a mentor
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object with mentor role
        
    Raises:
        HTTPException: If user is not a mentor
    """
    if current_user.role != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Mentor access required."
        )
    
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is an admin
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object with admin role
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin access required."
        )
    
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user (allows anonymous access)
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != "access":
        return None
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user
