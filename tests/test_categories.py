"""Tests for category management."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.storage import user_storage, category_storage, task_storage, DATA_DIR
from app.auth import get_password_hash
from app.models import User, Task
import shutil


@pytest.fixture(autouse=True)
def clean_data():
    """Clean up data before and after each test."""
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)


@pytest.fixture
def test_user():
    """Create a test user."""
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        disabled=False,
        is_admin=False
    )
    user_storage.create(user)
    return user


async def get_token(client: AsyncClient, username: str, password: str) -> str:
    """Helper to get auth token."""
    response = await client.post(
        "/api/auth/token",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
class TestCategoryStorage:
    """Tests for CategoryStorage class."""

    def test_add_category(self):
        """Test adding a category."""
        assert category_storage.add("Work")
        assert "Work" in category_storage.get_all()

    def test_add_duplicate_category(self):
        """Test adding a duplicate category returns False."""
        category_storage.add("Work")
        assert category_storage.add("Work") == False

    def test_delete_category(self):
        """Test deleting a category."""
        category_storage.add("Work")
        assert category_storage.delete("Work")
        assert "Work" not in category_storage.get_all()

    def test_delete_nonexistent_category(self):
        """Test deleting a category that doesn't exist."""
        assert category_storage.delete("Nonexistent") == False

    def test_get_all_sorted(self):
        """Test that categories are returned sorted."""
        category_storage.add("Zebra")
        category_storage.add("Apple")
        category_storage.add("Mango")
        
        categories = category_storage.get_all()
        assert categories == ["Apple", "Mango", "Zebra"]

    def test_exists(self):
        """Test category exists check."""
        category_storage.add("Work")
        assert category_storage.exists("Work")
        assert not category_storage.exists("Personal")


@pytest.mark.asyncio
class TestCategoryEndpoints:
    """Tests for category API endpoints."""

    async def test_get_categories_empty(self, test_user):
        """Test getting categories when none exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.get(
                "/api/tasks/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert response.json()["categories"] == []

    async def test_create_category(self, test_user):
        """Test creating a category."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.post(
                "/api/tasks/categories?name=Work",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert response.json()["category"] == "Work"

    async def test_create_category_strips_whitespace(self, test_user):
        """Test that category names are trimmed."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.post(
                "/api/tasks/categories?name=  Work  ",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert response.json()["category"] == "Work"

    async def test_create_category_empty_name(self, test_user):
        """Test creating a category with empty name."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.post(
                "/api/tasks/categories?name=   ",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 400

    async def test_create_category_too_long(self, test_user):
        """Test creating a category with name too long."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            long_name = "x" * 51
            response = await client.post(
                f"/api/tasks/categories?name={long_name}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 400

    async def test_delete_category(self, test_user):
        """Test deleting a category."""
        category_storage.add("Work")
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.delete(
                "/api/tasks/categories/Work",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert not category_storage.exists("Work")

    async def test_delete_nonexistent_category(self, test_user):
        """Test deleting a category that doesn't exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.delete(
                "/api/tasks/categories/Nonexistent",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 404

    async def test_get_categories_includes_task_categories(self, test_user):
        """Test that categories from tasks are also returned."""
        # Add a stored category
        category_storage.add("Stored")
        
        # Create a task with a different category
        task = Task(
            title="Test Task",
            column="Backlog",
            category="FromTask"
        )
        task_storage.create(task)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.get(
                "/api/tasks/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            categories = response.json()["categories"]
            assert "Stored" in categories
            assert "FromTask" in categories

    async def test_categories_unauthenticated(self):
        """Test accessing categories without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/tasks/categories")
            assert response.status_code == 401
            
            response = await client.post("/api/tasks/categories?name=Test")
            assert response.status_code == 401
            
            response = await client.delete("/api/tasks/categories/Test")
            assert response.status_code == 401
