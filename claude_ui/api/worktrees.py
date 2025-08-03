from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.core.database import get_db
from claude_ui.models.database import Worktree, Project
from claude_ui.models.schemas import WorktreeCreate, WorktreeResponse
from claude_ui.services.git_manager import GitManager

router = APIRouter()
git_manager = GitManager()


@router.post("/", response_model=WorktreeResponse)
async def create_worktree(
    worktree_data: WorktreeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new git worktree"""
    # Get project
    project = await db.get(Project, worktree_data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    try:
        # Create worktree
        worktree = await git_manager.create_worktree(
            project=project,
            branch_name=worktree_data.branch,
            worktree_name=worktree_data.name,
        )
        return worktree
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[WorktreeResponse])
async def list_worktrees(
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all worktrees, optionally filtered by project"""
    query = select(Worktree)
    if project_id:
        query = query.where(Worktree.project_id == project_id)
    
    result = await db.execute(query)
    worktrees = result.scalars().all()
    return worktrees


@router.get("/{worktree_id}", response_model=WorktreeResponse)
async def get_worktree(
    worktree_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific worktree"""
    worktree = await db.get(Worktree, worktree_id)
    if not worktree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worktree not found",
        )
    return worktree


@router.delete("/{worktree_id}")
async def delete_worktree(
    worktree_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a git worktree"""
    worktree = await db.get(Worktree, worktree_id)
    if not worktree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worktree not found",
        )
    
    try:
        await git_manager.remove_worktree(worktree)
        return {"message": "Worktree removed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{worktree_id}/status")
async def get_worktree_status(
    worktree_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get git status for a worktree"""
    worktree = await db.get(Worktree, worktree_id)
    if not worktree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worktree not found",
        )
    
    status = await git_manager.get_git_status(worktree.path)
    return status