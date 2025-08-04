from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from claude_ui.models.database import Session, Message


class SessionService:
    """Service layer for session management"""
    
    async def list_sessions(
        self,
        db: AsyncSession,
        instance_id: Optional[str] = None,
    ) -> List[Session]:
        """List all sessions, optionally filtered by instance"""
        query = select(Session)
        if instance_id:
            query = query.where(Session.instance_id == instance_id)
        
        result = await db.execute(query.order_by(Session.started_at.desc()))
        return result.scalars().all()
    
    async def get_session(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> Optional[Session]:
        """Get a specific session"""
        return await db.get(Session, session_id)
    
    async def get_session_messages(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> List[Message]:
        """Get all messages for a session"""
        # Verify session exists
        session = await db.get(Session, session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Get messages
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.timestamp)
        )
        return result.scalars().all()
    
    async def delete_session(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> bool:
        """Delete a session and all its messages"""
        session = await db.get(Session, session_id)
        if not session:
            return False
        
        # Delete session (cascade will handle messages)
        await db.delete(session)
        await db.commit()
        
        return True
    
    async def export_session(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Export session messages as structured data"""
        # Get session with messages
        result = await db.execute(
            select(Session)
            .options(selectinload(Session.messages))
            .where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError("Session not found")
        
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


# Singleton instance
session_service = SessionService()