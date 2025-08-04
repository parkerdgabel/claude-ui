from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.core.database import get_db
from claude_ui.models.schemas import SessionResponse, MessageResponse
from claude_ui.services.session_service import session_service

router = APIRouter()


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    instance_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all sessions, optionally filtered by instance"""
    sessions = await session_service.list_sessions(db, instance_id)
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific session"""
    session = await session_service.get_session(session_id, db)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a session"""
    try:
        messages = await session_service.get_session_messages(session_id, db)
        return messages
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages"""
    success = await session_service.delete_session(session_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Export session messages as JSON"""
    try:
        export_data = await session_service.export_session(session_id, db)
        return export_data
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )