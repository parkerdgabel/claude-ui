from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from claude_ui.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page"""
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {"request": request}
    )


@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Render the projects page"""
    return templates.TemplateResponse(
        "pages/projects.html",
        {"request": request}
    )


@router.get("/instances", response_class=HTMLResponse)
async def instances_page(request: Request):
    """Render the instances page"""
    return templates.TemplateResponse(
        "pages/instances.html",
        {"request": request}
    )


@router.get("/mcp", response_class=HTMLResponse)
async def mcp_page(request: Request):
    """Render the MCP servers page"""
    return templates.TemplateResponse(
        "pages/mcp.html",
        {"request": request}
    )