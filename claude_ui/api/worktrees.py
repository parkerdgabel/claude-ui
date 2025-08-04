from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.core.database import get_db
from claude_ui.models.schemas import WorktreeCreate, WorktreeResponse
from claude_ui.services.worktree_service import worktree_service

router = APIRouter()


@router.post("/", response_model=WorktreeResponse)
async def create_worktree(
    worktree_data: WorktreeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new git worktree"""
    try:
        worktree = await worktree_service.create_worktree(worktree_data, db)
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
    worktrees = await worktree_service.list_worktrees(db, project_id)
    return worktrees


@router.get("/{worktree_id}", response_model=WorktreeResponse)
async def get_worktree(
    worktree_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific worktree"""
    worktree = await worktree_service.get_worktree(worktree_id, db)
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
    try:
        success = await worktree_service.delete_worktree(worktree_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worktree not found",
            )
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
    try:
        status = await worktree_service.get_worktree_status(worktree_id, db)
        return status
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worktree not found",
        )