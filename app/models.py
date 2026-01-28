"""Pydantic models for the Kanban board."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class TaskBase(BaseModel):
    """Base task model with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: str = Field("Medium", pattern="^(High|Medium|Low)$")
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    column: str = Field("Backlog")


class TaskUpdate(BaseModel):
    """Model for updating a task (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(High|Medium|Low)$")
    category: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None
    column: Optional[str] = None


class Task(TaskBase):
    """Complete task model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    column: str = Field("Backlog")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskMove(BaseModel):
    """Model for moving a task to a different column."""
    column: str
    position: Optional[int] = None  # Position within the column


class User(BaseModel):
    """User model."""
    username: str
    hashed_password: str
    disabled: bool = False
    is_admin: bool = False


class UserCreate(BaseModel):
    """Model for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    username: Optional[str] = None


class PasswordChange(BaseModel):
    """Model for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8)
