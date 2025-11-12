"""
User authentication and authorization

✅ PRODUCTION-READY JWT AUTHENTICATION:
- Real JWT token verification with jose
- Password-based authentication with bcrypt
- Role-based access control
- Session tracking with last_login
- Secure error handling

🔒 REPLACES: Fake authentication stub from Week 1 Day 1
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_token, verify_password, get_password_hash, create_access_token
from app.db.session import get_db
from app.models.user import User, UserInDB, TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token authentication scheme
security = HTTPBearer()


# ========== Token Verification ==========

def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    ✅ PRODUCTION-READY: Extract and verify JWT token from Authorization header

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User information dictionary

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify and decode the JWT token
    payload = verify_token(token)

    if payload is None:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token payload
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        logger.warning("Token missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        logger.warning(f"User not found for ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Return user information as dictionary for compatibility
    return {
        "id": str(user.id),  # Convert to string for compatibility with existing code
        "user_id": user.id,  # Keep numeric ID for database operations
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_superuser": user.is_superuser,
        "permissions": _get_user_permissions(user)
    }


def _get_user_permissions(user: User) -> list:
    """
    Get user permissions based on role

    Args:
        user: User database object

    Returns:
        List of permission strings
    """
    if user.is_superuser:
        return ["read", "write", "admin", "delete", "manage_users"]
    elif user.role == "admin":
        return ["read", "write", "admin", "delete"]
    else:
        return ["read", "write"]


# ========== Dependency Alias ==========

async def get_current_user(
    user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """
    ✅ PRODUCTION-READY: Get current authenticated user

    This is the main dependency used throughout the application.
    It replaces the fake authentication stub.

    Usage in endpoints:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"message": f"Hello {current_user['username']}"}

    Args:
        user: User dict from token verification

    Returns:
        User information dictionary
    """
    return user


# ========== User Authentication ==========

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    ✅ PRODUCTION-READY: Authenticate user with username and password

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Find user by username
    user = db.query(User).filter(User.username == username).first()

    if not user:
        logger.info(f"Authentication failed: User not found - {username}")
        return None

    # Verify password
    if not verify_password(password, user.hashed_password):
        logger.info(f"Authentication failed: Invalid password - {username}")
        return None

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Authentication failed: Inactive user - {username}")
        return None

    logger.info(f"Authentication successful: {username}")
    return user


def update_last_login(db: Session, user: User) -> None:
    """
    Update user's last login timestamp

    Args:
        db: Database session
        user: User object to update
    """
    try:
        user.last_login = datetime.utcnow()
        db.commit()
        logger.debug(f"Updated last login for user: {user.username}")
    except Exception as e:
        logger.error(f"Failed to update last login: {e}")
        db.rollback()


# ========== Permission Checking ==========

def require_permission(permission: str):
    """
    ✅ PRODUCTION-READY: Permission checker decorator

    Now works with real JWT authentication

    Args:
        permission: Required permission string

    Returns:
        FastAPI dependency function
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {permission} 权限"
            )
        return current_user

    return permission_checker


# ========== Legacy Compatibility ==========

def verify_token_legacy(token: str) -> Optional[Dict[str, Any]]:
    """
    ⚠️ LEGACY COMPATIBILITY: Direct token verification without database lookup

    This function is kept for backward compatibility but should not be used
    for authentication. Use get_current_user dependency instead.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None otherwise
    """
    logger.warning("Using legacy verify_token - prefer get_current_user dependency")
    return verify_token(token)


def create_access_token_legacy(user_data: Dict[str, Any]) -> str:
    """
    ⚠️ LEGACY COMPATIBILITY: Create access token

    Use app.core.security.create_access_token directly instead.

    Args:
        user_data: User data to encode

    Returns:
        JWT token string
    """
    logger.warning("Using legacy create_access_token - use security.create_access_token")
    return create_access_token(user_data)
