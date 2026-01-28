"""Pytest fixtures for Kanban board tests."""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["KANBAN_DATA_DIR"] = tempfile.mkdtemp()
os.environ["KANBAN_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["KANBAN_ADMIN_USERNAME"] = "testadmin"
os.environ["KANBAN_ADMIN_PASSWORD"] = "testpass123"

from app.main import app
from app.auth import get_password_hash, create_access_token
from app.storage import user_storage, task_storage
from app.models import User, Task


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers with valid token."""
    token = create_access_token(data={"sub": "testadmin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user():
    """Create a test user if not exists."""
    if not user_storage.exists("testadmin"):
        user = User(
            username="testadmin",
            hashed_password=get_password_hash("testpass123"),
            disabled=False
        )
        user_storage.create(user)
    return user_storage.get_by_username("testadmin")


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task = Task(
        title="Test Task",
        description="Test description",
        priority="Medium",
        category="Testing",
        column="Backlog"
    )
    return task_storage.create(task)


@pytest.fixture(autouse=True)
def cleanup_tasks():
    """Clean up tasks before each test."""
    # Clear all tasks before test
    for task in task_storage.get_all():
        task_storage.delete(task.id)
    yield
    # Clean up after test
    for task in task_storage.get_all():
        task_storage.delete(task.id)
