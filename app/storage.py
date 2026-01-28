"""JSON file storage for tasks and users."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

from .models import Task, User
from .config import TASKS_FILE, USERS_FILE, DATA_DIR


class JSONStorage:
    """Thread-safe JSON file storage."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._ensure_file()
    
    def _ensure_file(self):
        """Ensure the storage file and directory exist."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_data([])
    
    def _read_data(self) -> List[Dict]:
        """Read data from JSON file."""
        with self._lock:
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
    
    def _write_data(self, data: List[Dict]):
        """Write data to JSON file."""
        with self._lock:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)


class TaskStorage(JSONStorage):
    """Storage for tasks."""
    
    def __init__(self):
        super().__init__(TASKS_FILE)
    
    def get_all(self) -> List[Task]:
        """Get all tasks."""
        data = self._read_data()
        return [Task(**item) for item in data]
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        tasks = self.get_all()
        for task in tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_by_column(self, column: str) -> List[Task]:
        """Get all tasks in a column."""
        tasks = self.get_all()
        return [t for t in tasks if t.column == column]
    
    def create(self, task: Task) -> Task:
        """Create a new task."""
        data = self._read_data()
        task_dict = task.model_dump()
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'updated_at', 'due_date']:
            if task_dict.get(key) and isinstance(task_dict[key], datetime):
                task_dict[key] = task_dict[key].isoformat()
        data.append(task_dict)
        self._write_data(data)
        return task
    
    def update(self, task_id: str, updates: Dict) -> Optional[Task]:
        """Update a task."""
        data = self._read_data()
        for i, item in enumerate(data):
            if item['id'] == task_id:
                # Apply updates
                for key, value in updates.items():
                    if value is not None:
                        if isinstance(value, datetime):
                            item[key] = value.isoformat()
                        else:
                            item[key] = value
                item['updated_at'] = datetime.utcnow().isoformat()
                self._write_data(data)
                return Task(**item)
        return None
    
    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        data = self._read_data()
        original_len = len(data)
        data = [item for item in data if item['id'] != task_id]
        if len(data) < original_len:
            self._write_data(data)
            return True
        return False
    
    def move(self, task_id: str, column: str, position: Optional[int] = None) -> Optional[Task]:
        """Move a task to a different column."""
        return self.update(task_id, {'column': column})


class UserStorage(JSONStorage):
    """Storage for users."""
    
    def __init__(self):
        super().__init__(USERS_FILE)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        data = self._read_data()
        for item in data:
            if item['username'] == username:
                return User(**item)
        return None
    
    def create(self, user: User) -> User:
        """Create a new user."""
        data = self._read_data()
        data.append(user.model_dump())
        self._write_data(data)
        return user
    
    def exists(self, username: str) -> bool:
        """Check if a user exists."""
        return self.get_by_username(username) is not None


# Singleton instances
task_storage = TaskStorage()
user_storage = UserStorage()
