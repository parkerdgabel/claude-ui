import os
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.models.database import Project
from claude_ui.models.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service layer for project management"""
    
    async def create_project(
        self,
        project_data: ProjectCreate,
        db: AsyncSession,
    ) -> Project:
        """Create a new project"""
        # Validate path exists
        if not os.path.exists(project_data.path):
            raise ValueError(f"Path {project_data.path} does not exist")
        
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
    
    async def get_project(
        self,
        project_id: str,
        db: AsyncSession,
    ) -> Optional[Project]:
        """Get a specific project"""
        return await db.get(Project, project_id)
    
    async def list_projects(
        self,
        db: AsyncSession,
    ) -> List[Project]:
        """List all projects"""
        result = await db.execute(select(Project))
        return result.scalars().all()
    
    async def update_project(
        self,
        project_id: str,
        update_data: ProjectUpdate,
        db: AsyncSession,
    ) -> Optional[Project]:
        """Update a project"""
        project = await db.get(Project, project_id)
        if not project:
            return None
        
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
    
    async def delete_project(
        self,
        project_id: str,
        db: AsyncSession,
    ) -> bool:
        """Delete a project"""
        project = await db.get(Project, project_id)
        if not project:
            return False
        
        # Delete from database (cascade will handle related records)
        await db.delete(project)
        await db.commit()
        
        return True
    
    async def scan_project(
        self,
        project_id: str,
        db: AsyncSession,
    ) -> bool:
        """Scan project directory for updates"""
        project = await db.get(Project, project_id)
        if not project:
            return False
        
        # Re-read CLAUDE.md if it exists
        claude_md_path = os.path.join(project.path, "CLAUDE.md")
        if os.path.exists(claude_md_path):
            with open(claude_md_path, "r") as f:
                project.claude_md_content = f.read()
        
        await db.commit()
        
        return True


# Singleton instance
project_service = ProjectService()