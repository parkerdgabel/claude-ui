from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from claude_ui.core.database import get_db
from claude_ui.models.database import Session, Message
from claude_ui.models.schemas import SessionResponse, MessageResponse

router = APIRouter()


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    instance_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all sessions, optionally filtered by instance"""
    query = select(Session)
    if instance_id:
        query = query.where(Session.instance_id == instance_id)
    
    result = await db.execute(query.order_by(Session.started_at.desc()))
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific session"""
    session = await db.get(Session, session_id)
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
    # Verify session exists
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp)
    )
    messages = result.scalars().all()
    return messages


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages"""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Delete session (cascade will handle messages)
    await db.delete(session)
    await db.commit()
    
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Export session messages as JSON"""
    # Get session with messages
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.messages))
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Format for export
    export_data = {
        "session_id": session.id,
        "instance_id": session.instance_id,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "total_tokens": session.total_tokens,
        "total_cost_usd": session.total_cost_usd,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "tokens": msg.tokens,
                "cost_usd": msg.cost_usd,
            }
            for msg in sorted(session.messages, key=lambda m: m.timestamp)
        ],
    }
    
    return export_data