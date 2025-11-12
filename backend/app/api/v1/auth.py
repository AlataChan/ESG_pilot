"""
Authentication API endpoints

✅ PRODUCTION-READY:
- User registration with validation
- User login with JWT token generation
- Password security with bcrypt
- Input validation with Pydantic
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import authenticate_user, update_last_login, get_current_user
from app.core.security import get_password_hash, create_access_token
from app.models.user import (
    User, UserCreate, UserLogin, UserResponse, Token
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    ✅ PRODUCTION-READY: Register a new user

    Args:
        user_data: User registration data (username, email, password)
        db: Database session

    Returns:
        Created user information (without password)

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    try:
        hashed_password = get_password_hash(user_data.password)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            role='user'
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {new_user.username} (ID: {new_user.id})")

        return new_user

    except Exception as e:
        db.rollback()
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    ✅ PRODUCTION-READY: Authenticate user and return JWT token

    Args:
        login_data: Login credentials (username, password)
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(db, login_data.username, login_data.password)

    if not user:
        logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    update_last_login(db, user)

    # Create access token
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

    access_token = create_access_token(token_data)

    logger.info(f"User logged in: {user.username} (ID: {user.id})")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ✅ PRODUCTION-READY: Get current user information

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        Current user information
    """
    # Fetch complete user data from database
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ PRODUCTION-READY: Logout current user

    Note: With JWT, there's no server-side logout. Client should discard the token.
    This endpoint exists for API consistency and logging purposes.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user['username']} (ID: {current_user['user_id']})")

    return {
        "message": "Successfully logged out",
        "detail": "Please discard your access token on the client side"
    }
