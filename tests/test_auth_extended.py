"""Extended authentication tests for new features."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.storage import user_storage, DATA_DIR
from app.auth import get_password_hash
from app.models import User
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
def admin_user():
    """Create an admin user."""
    user = User(
        username="admin",
        hashed_password=get_password_hash("adminpass"),
        disabled=False,
        is_admin=True
    )
    user_storage.create(user)
    return user


@pytest.fixture
def regular_user():
    """Create a regular (non-admin) user."""
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
class TestPasswordChange:
    """Tests for password change functionality."""

    async def test_change_password_success(self, admin_user):
        """Test successful password change."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={"current_password": "adminpass", "new_password": "newpassword123"}
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "Password changed successfully"
            
            # Verify new password works
            new_token = await get_token(client, "admin", "newpassword123")
            assert new_token is not None

    async def test_change_password_wrong_current(self, admin_user):
        """Test password change with wrong current password."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={"current_password": "wrongpassword", "new_password": "newpassword123"}
            )
            
            assert response.status_code == 400
            assert "incorrect" in response.json()["detail"].lower()

    async def test_change_password_too_short(self, admin_user):
        """Test password change with too short new password."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={"current_password": "adminpass", "new_password": "short"}
            )
            
            assert response.status_code == 422  # Validation error

    async def test_change_password_unauthenticated(self):
        """Test password change without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/auth/change-password",
                json={"current_password": "test", "new_password": "newpassword123"}
            )
            
            assert response.status_code == 401


@pytest.mark.asyncio
class TestUserManagement:
    """Tests for user management (admin only)."""

    async def test_list_users_as_admin(self, admin_user, regular_user):
        """Test listing users as admin."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.get(
                "/api/auth/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            users = response.json()["users"]
            assert len(users) == 2
            usernames = [u["username"] for u in users]
            assert "admin" in usernames
            assert "testuser" in usernames

    async def test_list_users_as_non_admin(self, admin_user, regular_user):
        """Test listing users as non-admin (should fail)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.get(
                "/api/auth/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 403

    async def test_delete_user_as_admin(self, admin_user, regular_user):
        """Test deleting a user as admin."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.delete(
                "/api/auth/users/testuser",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            
            # Verify user is deleted
            assert not user_storage.exists("testuser")

    async def test_delete_user_as_non_admin(self, admin_user, regular_user):
        """Test deleting a user as non-admin (should fail)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "testuser", "testpass")
            
            response = await client.delete(
                "/api/auth/users/admin",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 403

    async def test_cannot_delete_admin(self, admin_user):
        """Test that admin user cannot be deleted."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.delete(
                "/api/auth/users/admin",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 400
            assert "Cannot delete admin" in response.json()["detail"]

    async def test_cannot_delete_self(self, admin_user, regular_user):
        """Test that users cannot delete themselves."""
        # Create another admin to test this
        admin2 = User(
            username="admin2",
            hashed_password=get_password_hash("admin2pass"),
            disabled=False,
            is_admin=True
        )
        user_storage.create(admin2)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin2", "admin2pass")
            
            response = await client.delete(
                "/api/auth/users/admin2",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 400
            assert "Cannot delete yourself" in response.json()["detail"]

    async def test_delete_nonexistent_user(self, admin_user):
        """Test deleting a user that doesn't exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            token = await get_token(client, "admin", "adminpass")
            
            response = await client.delete(
                "/api/auth/users/nonexistent",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 404


@pytest.mark.asyncio  
class TestAdminFlag:
    """Tests for is_admin functionality."""

    async def test_me_returns_admin_flag(self, admin_user, regular_user):
        """Test that /me endpoint returns is_admin flag."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Test admin user
            admin_token = await get_token(client, "admin", "adminpass")
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.json()["is_admin"] == True
            
            # Test regular user
            user_token = await get_token(client, "testuser", "testpass")
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.json()["is_admin"] == False
