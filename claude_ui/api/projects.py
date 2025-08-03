from typing import List
import uuid
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.core.database import get_db
from claude_ui.models.database import Project
from claude_ui.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project"""
    # Validate path exists
    if not os.path.exists(project_data.path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path {project_data.path} does not exist",
        )
    
    # Generate unique ID
    project_id = str(uuid.uuid4())
    
    # Check for CLAUDE.md file
    claude_md_path = os.path.join(project_data.path, "CLAUDE.md")
    claude_md_content = project_data.claude_md_content
    
    if not claude_md_content and os.path.exists(claude_md_path):
        with open(claude_md_path, "r") as f:
            claude_md_content = f.read()
    
    # Create database record
    project = Project(
        id=project_id,
        name=project_data.name,
        description=project_data.description,
        path=project_data.path,
        git_url=project_data.git_url,
        default_branch=project_data.default_branch,
        claude_md_content=claude_md_content,
        settings=project_data.settings,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
):
    """List all projects"""
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    
    # Save CLAUDE.md if updated
    if update_data.claude_md_content is not None:
        claude_md_path = os.path.join(project.path, "CLAUDE.md")
        with open(claude_md_path, "w") as f:
            f.write(update_data.claude_md_content)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Delete from database (cascade will handle related records)
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/scan")
async def scan_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Scan project directory for updates"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Re-read CLAUDE.md if it exists
    claude_md_path = os.path.join(project.path, "CLAUDE.md")
    if os.path.exists(claude_md_path):
        with open(claude_md_path, "r") as f:
            project.claude_md_content = f.read()
    
    await db.commit()
    
    return {"message": "Project scanned successfully"}