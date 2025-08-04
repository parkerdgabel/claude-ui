import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from claude_ui.config import settings
from claude_ui.core.database import init_db
from claude_ui.api import instances, projects, sessions, mcp_servers, websocket, worktrees
from claude_ui.services.cleanup import start_cleanup_task
from claude_ui import views


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Claude UI...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start background cleanup task
    cleanup_task = await start_cleanup_task()
    logger.info("Background cleanup task started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Claude UI...")
    if cleanup_task:
        cleanup_task.cancel()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(views.router, tags=["views"])
app.include_router(instances.router, prefix="/api/instances", tags=["instances"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(mcp_servers.router, prefix="/api/mcp", tags=["mcp"])
app.include_router(worktrees.router, prefix="/api/worktrees", tags=["worktrees"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    from fastapi.responses import FileResponse
    return FileResponse("static/favicon.ico")