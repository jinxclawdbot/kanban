"""Task management routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..auth import get_current_active_user
from ..models import Task, TaskCreate, TaskUpdate, TaskMove, User
from ..storage import task_storage
from ..config import COLUMNS, PRIORITIES

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[Task])
async def get_tasks(
    column: Optional[str] = Query(None, description="Filter by column"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tasks, optionally filtered."""
    tasks = task_storage.get_all()
    
    if column:
        tasks = [t for t in tasks if t.column == column]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if category:
        tasks = [t for t in tasks if t.category == category]
    
    return tasks


@router.get("/columns")
async def get_columns(current_user: User = Depends(get_current_active_user)):
    """Get available columns."""
    return {"columns": COLUMNS}


@router.get("/priorities")
async def get_priorities(current_user: User = Depends(get_current_active_user)):
    """Get available priorities."""
    return {"priorities": PRIORITIES}


@router.get("/categories")
async def get_categories(current_user: User = Depends(get_current_active_user)):
    """Get all unique categories from existing tasks."""
    tasks = task_storage.get_all()
    categories = set(t.category for t in tasks if t.category)
    return {"categories": sorted(categories)}


@router.get("/board")
async def get_board(current_user: User = Depends(get_current_active_user)):
    """Get all tasks organized by column."""
    tasks = task_storage.get_all()
    board = {col: [] for col in COLUMNS}
    
    for task in tasks:
        if task.column in board:
            board[task.column].append(task)
    
    return board


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a specific task by ID."""
    task = task_storage.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new task."""
    if task_data.column not in COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid column. Must be one of: {COLUMNS}"
        )
    
    task = Task(**task_data.model_dump())
    return task_storage.create(task)


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a task."""
    existing = task_storage.get_by_id(task_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task_data.column and task_data.column not in COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid column. Must be one of: {COLUMNS}"
        )
    
    updates = task_data.model_dump(exclude_unset=True)
    updated_task = task_storage.update(task_id, updates)
    return updated_task


@router.patch("/{task_id}/move", response_model=Task)
async def move_task(
    task_id: str,
    move_data: TaskMove,
    current_user: User = Depends(get_current_active_user)
):
    """Move a task to a different column."""
    existing = task_storage.get_by_id(task_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if move_data.column not in COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid column. Must be one of: {COLUMNS}"
        )
    
    moved_task = task_storage.move(task_id, move_data.column, move_data.position)
    return moved_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user: User = Depends(get_current_active_user)):
    """Delete a task."""
    if not task_storage.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
