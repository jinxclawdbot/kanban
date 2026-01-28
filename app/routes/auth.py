"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user
)
from ..models import Token, User, UserCreate, PasswordChange
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
    return {
        "username": current_user.username,
        "is_admin": current_user.is_admin or current_user.username == "admin"
    }


@router.get("/users")
async def list_users(current_user: User = Depends(get_current_active_user)):
    """List all users (admin only)."""
    if not (current_user.is_admin or current_user.username == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = user_storage.list_all()
    return {"users": [{"username": u.username, "is_admin": u.is_admin or u.username == "admin"} for u in users]}


@router.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(get_current_active_user)):
    """Delete a user (admin only)."""
    if not (current_user.is_admin or current_user.username == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user"
        )
    
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    if not user_storage.exists(username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_storage.delete(username)
    return {"message": f"User {username} deleted"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change the current user's password."""
    from ..auth import verify_password
    
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    user_storage.update(current_user)
    return {"message": "Password changed successfully"}
