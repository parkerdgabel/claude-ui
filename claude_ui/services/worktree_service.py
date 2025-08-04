from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.models.database import Worktree, Project
from claude_ui.models.schemas import WorktreeCreate
from claude_ui.services.git_manager import GitManager


class WorktreeService:
    """Service layer for worktree management"""
    
    def __init__(self):
        self.git_manager = GitManager()
    
    async def create_worktree(
        self,
        worktree_data: WorktreeCreate,
        db: AsyncSession,
    ) -> Worktree:
        """Create a new git worktree"""
        # Get project
        project = await db.get(Project, worktree_data.project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Create worktree
        worktree = await self.git_manager.create_worktree(
            project=project,
            branch_name=worktree_data.branch,
            worktree_name=worktree_data.name,
        )
        
        return worktree
    
    async def get_worktree(
        self,
        worktree_id: str,
        db: AsyncSession,
    ) -> Optional[Worktree]:
        """Get a specific worktree"""
        return await db.get(Worktree, worktree_id)
    
    async def list_worktrees(
        self,
        db: AsyncSession,
        project_id: Optional[str] = None,
    ) -> List[Worktree]:
        """List all worktrees, optionally filtered by project"""
        query = select(Worktree)
        if project_id:
            query = query.where(Worktree.project_id == project_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def delete_worktree(
        self,
        worktree_id: str,
        db: AsyncSession,
    ) -> bool:
        """Remove a git worktree"""
        worktree = await db.get(Worktree, worktree_id)
        if not worktree:
            return False
        
        await self.git_manager.remove_worktree(worktree)
        return True
    
    async def get_worktree_status(
        self,
        worktree_id: str,
        db: AsyncSession,
    ) -> dict:
        """Get git status for a worktree"""
        worktree = await db.get(Worktree, worktree_id)
        if not worktree:
            raise ValueError("Worktree not found")
        
        return await self.git_manager.get_git_status(worktree.path)


# Singleton instance
worktree_service = WorktreeService()