import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.config import settings
from claude_ui.core.database import get_db_context
from claude_ui.models.database import Session, Instance

logger = logging.getLogger(__name__)


async def cleanup_old_sessions():
    """Clean up old sessions based on max age setting"""
    cutoff_date = datetime.utcnow() - timedelta(days=settings.max_session_age_days)
    
    async with get_db_context() as db:
        # Find old sessions
        result = await db.execute(
            select(Session).where(Session.started_at < cutoff_date)
        )
        old_sessions = result.scalars().all()
        
        if old_sessions:
            for session in old_sessions:
                await db.delete(session)
            
            await db.commit()
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")


async def cleanup_inactive_instances():
    """Clean up instances marked as terminated"""
    async with get_db_context() as db:
        # Find terminated instances older than 1 hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        result = await db.execute(
            select(Instance).where(
                Instance.status == "terminated",
                Instance.terminated_at < cutoff_time,
            )
        )
        terminated_instances = result.scalars().all()
        
        if terminated_instances:
            for instance in terminated_instances:
                await db.delete(instance)
            
            await db.commit()
            logger.info(f"Cleaned up {len(terminated_instances)} terminated instances")


async def cleanup_task():
    """Background task to periodically clean up old data"""
    while True:
        try:
            await cleanup_old_sessions()
            await cleanup_inactive_instances()
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        
        # Wait for the configured interval
        await asyncio.sleep(settings.session_cleanup_interval)


async def start_cleanup_task():
    """Start the cleanup background task"""
    task = asyncio.create_task(cleanup_task())
    logger.info("Started cleanup background task")
    return task