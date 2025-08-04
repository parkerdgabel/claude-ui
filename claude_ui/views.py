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


@router.get("/instances/new", response_class=HTMLResponse)
async def new_instance_form(request: Request):
    """Render the new instance form"""
    return templates.TemplateResponse(
        "forms/new_instance.html",
        {"request": request}
    )


@router.get("/projects/new", response_class=HTMLResponse)
async def new_project_form(request: Request):
    """Render the new project form"""
    return templates.TemplateResponse(
        "forms/new_project.html",
        {"request": request}
    )


@router.get("/instances/{instance_id}/chat", response_class=HTMLResponse)
async def instance_chat_page(request: Request, instance_id: str):
    """Render the instance chat page"""
    # TODO: Fetch instance details from service
    instance = {"id": instance_id, "name": "Instance", "status": "active"}
    return templates.TemplateResponse(
        "pages/instance_chat.html",
        {"request": request, "instance": instance}
    )