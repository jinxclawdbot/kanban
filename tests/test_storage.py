"""Tests for storage module."""

import pytest
import tempfile
import os
from pathlib import Path

# Set up test environment
os.environ["KANBAN_DATA_DIR"] = tempfile.mkdtemp()

from app.storage import TaskStorage, UserStorage
from app.models import Task, User
from app.auth import get_password_hash


class TestTaskStorage:
    """Test TaskStorage functionality."""
    
    @pytest.fixture
    def storage(self):
        """Create a fresh task storage."""
        storage = TaskStorage()
        # Clear any existing tasks
        for task in storage.get_all():
            storage.delete(task.id)
        return storage
    
    def test_create_and_get_task(self, storage):
        """Test creating and retrieving a task."""
        task = Task(title="Storage Test", priority="High", column="Backlog")
        created = storage.create(task)
        
        assert created.id == task.id
        
        retrieved = storage.get_by_id(task.id)
        assert retrieved is not None
        assert retrieved.title == "Storage Test"
        assert retrieved.priority == "High"
    
    def test_get_all_tasks(self, storage):
        """Test getting all tasks."""
        task1 = Task(title="Task 1", column="Backlog")
        task2 = Task(title="Task 2", column="Done")
        
        storage.create(task1)
        storage.create(task2)
        
        all_tasks = storage.get_all()
        assert len(all_tasks) >= 2
    
    def test_get_by_column(self, storage):
        """Test getting tasks by column."""
        task1 = Task(title="Backlog Task", column="Backlog")
        task2 = Task(title="Done Task", column="Done")
        
        storage.create(task1)
        storage.create(task2)
        
        backlog_tasks = storage.get_by_column("Backlog")
        assert all(t.column == "Backlog" for t in backlog_tasks)
    
    def test_update_task(self, storage):
        """Test updating a task."""
        task = Task(title="Original", priority="Low", column="Backlog")
        storage.create(task)
        
        updated = storage.update(task.id, {"title": "Updated", "priority": "High"})
        
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.priority == "High"
    
    def test_delete_task(self, storage):
        """Test deleting a task."""
        task = Task(title="To Delete", column="Backlog")
        storage.create(task)
        
        assert storage.delete(task.id) is True
        assert storage.get_by_id(task.id) is None
    
    def test_delete_nonexistent(self, storage):
        """Test deleting a non-existent task."""
        assert storage.delete("nonexistent-id") is False
    
    def test_move_task(self, storage):
        """Test moving a task to a different column."""
        task = Task(title="Movable", column="Backlog")
        storage.create(task)
        
        moved = storage.move(task.id, "Done")
        
        assert moved is not None
        assert moved.column == "Done"


class TestUserStorage:
    """Test UserStorage functionality."""
    
    @pytest.fixture
    def storage(self):
        """Create a fresh user storage."""
        return UserStorage()
    
    def test_create_and_get_user(self, storage):
        """Test creating and retrieving a user."""
        user = User(
            username="storagetest",
            hashed_password=get_password_hash("password"),
            disabled=False
        )
        
        if not storage.exists("storagetest"):
            storage.create(user)
        
        retrieved = storage.get_by_username("storagetest")
        assert retrieved is not None
        assert retrieved.username == "storagetest"
    
    def test_user_exists(self, storage):
        """Test checking if a user exists."""
        user = User(
            username="existstest",
            hashed_password=get_password_hash("password"),
            disabled=False
        )
        
        if not storage.exists("existstest"):
            storage.create(user)
        
        assert storage.exists("existstest") is True
        assert storage.exists("nonexistent") is False
    
    def test_get_nonexistent_user(self, storage):
        """Test getting a non-existent user."""
        user = storage.get_by_username("definitely-not-exists")
        assert user is None
