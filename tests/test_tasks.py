"""Tests for task management endpoints."""

import pytest
from datetime import datetime, timedelta


class TestTaskCRUD:
    """Test task CRUD operations."""
    
    def test_create_task_minimal(self, client, auth_headers, test_user):
        """Test creating a task with minimal fields."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"title": "New Task"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["priority"] == "Medium"
        assert data["column"] == "Backlog"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_task_full(self, client, auth_headers, test_user):
        """Test creating a task with all fields."""
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={
                "title": "Full Task",
                "description": "A complete task",
                "priority": "High",
                "category": "Work",
                "column": "In Progress",
                "due_date": due_date
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full Task"
        assert data["description"] == "A complete task"
        assert data["priority"] == "High"
        assert data["category"] == "Work"
        assert data["column"] == "In Progress"
    
    def test_create_task_invalid_column(self, client, auth_headers, test_user):
        """Test creating a task with invalid column."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"title": "Task", "column": "Invalid"}
        )
        assert response.status_code == 400
        assert "Invalid column" in response.json()["detail"]
    
    def test_create_task_invalid_priority(self, client, auth_headers, test_user):
        """Test creating a task with invalid priority."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"title": "Task", "priority": "Invalid"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_all_tasks(self, client, auth_headers, test_user, sample_task):
        """Test getting all tasks."""
        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_task_by_id(self, client, auth_headers, test_user, sample_task):
        """Test getting a specific task by ID."""
        response = client.get(f"/api/tasks/{sample_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_task.id
        assert data["title"] == sample_task.title
    
    def test_get_task_not_found(self, client, auth_headers, test_user):
        """Test getting a non-existent task."""
        response = client.get("/api/tasks/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_task(self, client, auth_headers, test_user, sample_task):
        """Test updating a task."""
        response = client.put(
            f"/api/tasks/{sample_task.id}",
            headers=auth_headers,
            json={"title": "Updated Title", "priority": "High"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == "High"
    
    def test_update_task_not_found(self, client, auth_headers, test_user):
        """Test updating a non-existent task."""
        response = client.put(
            "/api/tasks/nonexistent-id",
            headers=auth_headers,
            json={"title": "Updated"}
        )
        assert response.status_code == 404
    
    def test_delete_task(self, client, auth_headers, test_user, sample_task):
        """Test deleting a task."""
        response = client.delete(f"/api/tasks/{sample_task.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deletion
        response = client.get(f"/api/tasks/{sample_task.id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_task_not_found(self, client, auth_headers, test_user):
        """Test deleting a non-existent task."""
        response = client.delete("/api/tasks/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404


class TestTaskMove:
    """Test task movement between columns."""
    
    def test_move_task(self, client, auth_headers, test_user, sample_task):
        """Test moving a task to a different column."""
        response = client.patch(
            f"/api/tasks/{sample_task.id}/move",
            headers=auth_headers,
            json={"column": "In Progress"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["column"] == "In Progress"
    
    def test_move_task_invalid_column(self, client, auth_headers, test_user, sample_task):
        """Test moving a task to an invalid column."""
        response = client.patch(
            f"/api/tasks/{sample_task.id}/move",
            headers=auth_headers,
            json={"column": "Invalid Column"}
        )
        assert response.status_code == 400
    
    def test_move_task_not_found(self, client, auth_headers, test_user):
        """Test moving a non-existent task."""
        response = client.patch(
            "/api/tasks/nonexistent-id/move",
            headers=auth_headers,
            json={"column": "Done"}
        )
        assert response.status_code == 404


class TestTaskFilters:
    """Test task filtering and board views."""
    
    def test_get_board(self, client, auth_headers, test_user, sample_task):
        """Test getting the board view."""
        response = client.get("/api/tasks/board", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "Recurring" in data
        assert "Backlog" in data
        assert "In Progress" in data
        assert "Review" in data
        assert "Done" in data
        assert len(data["Backlog"]) >= 1
    
    def test_filter_by_column(self, client, auth_headers, test_user, sample_task):
        """Test filtering tasks by column."""
        response = client.get("/api/tasks?column=Backlog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["column"] == "Backlog" for t in data)
    
    def test_filter_by_priority(self, client, auth_headers, test_user, sample_task):
        """Test filtering tasks by priority."""
        response = client.get("/api/tasks?priority=Medium", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["priority"] == "Medium" for t in data)
    
    def test_get_columns(self, client, auth_headers, test_user):
        """Test getting available columns."""
        response = client.get("/api/tasks/columns", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
        assert "Backlog" in data["columns"]
        assert "Done" in data["columns"]
    
    def test_get_priorities(self, client, auth_headers, test_user):
        """Test getting available priorities."""
        response = client.get("/api/tasks/priorities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "priorities" in data
        assert "High" in data["priorities"]
        assert "Medium" in data["priorities"]
        assert "Low" in data["priorities"]
    
    def test_get_categories(self, client, auth_headers, test_user, sample_task):
        """Test getting categories from existing tasks."""
        response = client.get("/api/tasks/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "Testing" in data["categories"]


class TestTaskValidation:
    """Test input validation for tasks."""
    
    def test_title_required(self, client, auth_headers, test_user):
        """Test that title is required."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"description": "No title"}
        )
        assert response.status_code == 422
    
    def test_title_max_length(self, client, auth_headers, test_user):
        """Test title maximum length validation."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"title": "x" * 201}  # Over 200 chars
        )
        assert response.status_code == 422
    
    def test_description_max_length(self, client, auth_headers, test_user):
        """Test description maximum length validation."""
        response = client.post(
            "/api/tasks",
            headers=auth_headers,
            json={"title": "Task", "description": "x" * 2001}  # Over 2000 chars
        )
        assert response.status_code == 422


class TestUnauthorizedAccess:
    """Test that endpoints require authentication."""
    
    def test_get_tasks_unauthorized(self, client):
        """Test getting tasks without auth."""
        response = client.get("/api/tasks")
        assert response.status_code == 401
    
    def test_create_task_unauthorized(self, client):
        """Test creating a task without auth."""
        response = client.post("/api/tasks", json={"title": "Test"})
        assert response.status_code == 401
    
    def test_update_task_unauthorized(self, client):
        """Test updating a task without auth."""
        response = client.put("/api/tasks/some-id", json={"title": "Test"})
        assert response.status_code == 401
    
    def test_delete_task_unauthorized(self, client):
        """Test deleting a task without auth."""
        response = client.delete("/api/tasks/some-id")
        assert response.status_code == 401
