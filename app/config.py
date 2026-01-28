"""Application configuration."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data storage
DATA_DIR = Path(os.getenv("KANBAN_DATA_DIR", BASE_DIR / "data"))
TASKS_FILE = DATA_DIR / "tasks.json"
USERS_FILE = DATA_DIR / "users.json"

# Security
SECRET_KEY = os.getenv("KANBAN_SECRET_KEY", "change-this-in-production-use-a-real-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Default admin credentials (change in production!)
DEFAULT_ADMIN_USERNAME = os.getenv("KANBAN_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("KANBAN_ADMIN_PASSWORD", "changeme")

# Kanban columns
COLUMNS = ["Recurring", "Backlog", "In Progress", "Review", "Done"]

# Priority levels
PRIORITIES = ["High", "Medium", "Low"]
