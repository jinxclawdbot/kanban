"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user
)
from ..models import Token, User, UserCreate
from ..storage import user_storage

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, current_user: User = Depends(get_current_active_user)):
    """Register a new user (admin only)."""
    if user_storage.exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        disabled=False
    )
    user_storage.create(new_user)
    return {"message": f"User {user_data.username} created successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return {"username": current_user.username}
