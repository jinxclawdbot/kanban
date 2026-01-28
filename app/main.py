"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .routes import auth, tasks
from .auth import ensure_default_admin

# Create app
app = FastAPI(
    title="Kanban Board",
    description="A simple Kanban board for task management",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)

# Static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("startup")
async def startup():
    """Run on application startup."""
    ensure_default_admin()


@app.get("/")
async def root():
    """Serve the main application."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Kanban Board API", "docs": "/docs"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
