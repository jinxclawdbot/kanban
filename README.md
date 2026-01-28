# 🎯 Kanban Board

A simple, self-hosted Kanban board application built with FastAPI and vanilla JavaScript.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **5 Columns:** Recurring, Backlog, In Progress, Review, Done
- **Task Properties:**
  - Title (required)
  - Description (optional)
  - Priority (High, Medium, Low)
  - Category (customizable)
  - Created date (automatic)
  - Due date (optional)
- **Drag-and-drop** between columns
- **JWT-based authentication**
- **RESTful API** with full CRUD operations
- **JSON file storage** (no database required)
- **Responsive UI** with Pico CSS
- **Dark mode support**

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jinxclawdbot/kanban.git
   cd kanban
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables (optional but recommended for production):**
   ```bash
   export KANBAN_SECRET_KEY="your-secure-secret-key-here"
   export KANBAN_ADMIN_USERNAME="admin"
   export KANBAN_ADMIN_PASSWORD="your-secure-password"
   export KANBAN_DATA_DIR="/path/to/data"  # Optional, defaults to ./data
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

6. **Open your browser:**
   Navigate to `http://localhost:8000`

### Default Credentials

- **Username:** `admin`
- **Password:** `changeme`

⚠️ **Change these in production!** Set the `KANBAN_ADMIN_USERNAME` and `KANBAN_ADMIN_PASSWORD` environment variables.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `KANBAN_SECRET_KEY` | (insecure default) | JWT signing key - **MUST change in production** |
| `KANBAN_ADMIN_USERNAME` | `admin` | Default admin username |
| `KANBAN_ADMIN_PASSWORD` | `changeme` | Default admin password |
| `KANBAN_DATA_DIR` | `./data` | Directory for JSON data files |

## API Documentation

Once running, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Authentication

All API endpoints (except `/health` and `/api/auth/token`) require authentication.

**Get a token:**
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme"
```

**Use the token:**
```bash
curl -X GET "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token` | Get access token |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/register` | Register new user (admin only) |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/{id}` | Get a specific task |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| PATCH | `/api/tasks/{id}/move` | Move task to column |
| GET | `/api/tasks/board` | Get board view (tasks by column) |
| GET | `/api/tasks/columns` | List available columns |
| GET | `/api/tasks/priorities` | List available priorities |
| GET | `/api/tasks/categories` | List categories in use |
| GET | `/health` | Health check |

### Task Schema

```json
{
  "title": "Task title",
  "description": "Optional description",
  "priority": "High|Medium|Low",
  "category": "Optional category",
  "column": "Backlog",
  "due_date": "2024-12-31T23:59:59"
}
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run tests verbosely
pytest -v
```

### Project Structure

```
kanban/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration
│   ├── models.py        # Pydantic models
│   ├── auth.py          # Authentication utilities
│   ├── storage.py       # JSON file storage
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py      # Auth endpoints
│   │   └── tasks.py     # Task endpoints
│   └── static/
│       ├── index.html   # Main HTML
│       ├── style.css    # Styles
│       └── app.js       # Frontend JavaScript
├── tests/
│   ├── conftest.py      # Pytest fixtures
│   ├── test_auth.py     # Auth tests
│   ├── test_tasks.py    # Task tests
│   ├── test_storage.py  # Storage tests
│   └── test_health.py   # Health endpoint tests
├── data/                # JSON data files (auto-created)
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

## Deployment

### Behind a Reverse Proxy (Recommended)

The app is designed to run behind a reverse proxy like nginx or Caddy that handles HTTPS.

**Example nginx configuration:**
```nginx
server {
    listen 443 ssl;
    server_name kanban.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t kanban .
docker run -p 8000:8000 \
  -e KANBAN_SECRET_KEY="your-secret" \
  -e KANBAN_ADMIN_PASSWORD="secure-password" \
  -v kanban-data:/app/data \
  kanban
```

### Systemd Service

```ini
[Unit]
Description=Kanban Board
After=network.target

[Service]
Type=simple
User=kanban
WorkingDirectory=/opt/kanban
Environment="KANBAN_SECRET_KEY=your-secret-key"
Environment="KANBAN_ADMIN_PASSWORD=secure-password"
ExecStart=/opt/kanban/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Considerations

1. **Change default credentials** - Always set custom `KANBAN_ADMIN_USERNAME` and `KANBAN_ADMIN_PASSWORD`
2. **Use a strong secret key** - Set a random `KANBAN_SECRET_KEY` (at least 32 characters)
3. **Use HTTPS** - Deploy behind a reverse proxy with TLS
4. **Protect data directory** - Ensure proper file permissions on the data directory
5. **Regular backups** - Back up the `data/` directory regularly

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
