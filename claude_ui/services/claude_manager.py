import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, AsyncIterator

from claude_code_sdk import query, ClaudeCodeOptions, Message
from claude_code_sdk.messages import AssistantMessage, TextBlock

from claude_ui.config import settings
from claude_ui.models.database import Instance, Session, Message as DBMessage
from claude_ui.models.schemas import QueryResponse, MessageResponse
from claude_ui.core.database import get_db_context

logger = logging.getLogger(__name__)


class ClaudeInstance:
    """Represents a running Claude Code instance"""
    
    def __init__(self, instance_id: str, working_dir: str, env_vars: Dict[str, str]):
        self.instance_id = instance_id
        self.working_dir = working_dir
        self.env_vars = env_vars
        self.active = True
        self.current_session_id: Optional[str] = None
        
    async def query(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> AsyncIterator[Message]:
        """Send a query to this Claude instance"""
        claude_options = ClaudeCodeOptions(
            working_dir=self.working_dir,
            max_turns=options.get("max_turns", 10) if options else 10,
            system_prompt=options.get("system_prompt") if options else None,
        )
        
        # Merge environment variables
        env = os.environ.copy()
        env.update(self.env_vars)
        
        async for message in query(prompt=prompt, options=claude_options, env=env):
            yield message


class ClaudeManager:
    """Manages multiple Claude Code instances"""
    
    def __init__(self):
        self.instances: Dict[str, ClaudeInstance] = {}
        self._lock = asyncio.Lock()
        
    async def start_instance(self, db_instance: Instance) -> None:
        """Start a new Claude Code instance"""
        async with self._lock:
            if db_instance.id in self.instances:
                raise ValueError(f"Instance {db_instance.id} already exists")
            
            # Validate instance limit
            if len(self.instances) >= settings.max_instances:
                raise ValueError(f"Maximum number of instances ({settings.max_instances}) reached")
            
            # Create working directory if needed
            working_dir = db_instance.working_directory or os.getcwd()
            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)
            
            # Create Claude instance
            claude_instance = ClaudeInstance(
                instance_id=db_instance.id,
                working_dir=working_dir,
                env_vars=db_instance.environment_vars or {},
            )
            
            self.instances[db_instance.id] = claude_instance
            
            # Update database status
            async with get_db_context() as db:
                instance = await db.get(Instance, db_instance.id)
                instance.status = "active"
                instance.pid = os.getpid()  # Using current process PID as placeholder
                await db.commit()
            
            logger.info(f"Started instance {db_instance.id}")
    
    async def terminate_instance(self, db_instance: Instance) -> None:
        """Terminate a Claude Code instance"""
        async with self._lock:
            if db_instance.id not in self.instances:
                logger.warning(f"Instance {db_instance.id} not found in manager")
                return
            
            # Mark instance as inactive
            instance = self.instances[db_instance.id]
            instance.active = False
            
            # Remove from active instances
            del self.instances[db_instance.id]
            
            # Update database
            async with get_db_context() as db:
                instance_db = await db.get(Instance, db_instance.id)
                instance_db.status = "terminated"
                instance_db.terminated_at = datetime.utcnow()
                await db.commit()
            
            logger.info(f"Terminated instance {db_instance.id}")
    
    async def restart_instance(self, db_instance: Instance) -> None:
        """Restart a Claude Code instance"""
        # Terminate if running
        if db_instance.id in self.instances:
            await self.terminate_instance(db_instance)
        
        # Start again
        await self.start_instance(db_instance)
    
    async def query_instance(
        self,
        db_instance: Instance,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> QueryResponse:
        """Query a Claude Code instance and track the session"""
        if db_instance.id not in self.instances:
            raise ValueError(f"Instance {db_instance.id} not found")
        
        instance = self.instances[db_instance.id]
        
        # Create new session
        session_id = str(uuid.uuid4())
        instance.current_session_id = session_id
        
        async with get_db_context() as db:
            # Create session record
            session = Session(
                id=session_id,
                instance_id=db_instance.id,
                status="active",
            )
            db.add(session)
            
            # Add user message
            user_msg = DBMessage(
                session_id=session_id,
                role="user",
                content=prompt,
            )
            db.add(user_msg)
            await db.commit()
            
            messages = [MessageResponse.model_validate(user_msg)]
            total_tokens = 0
            total_cost = 0.0
            
            try:
                # Query Claude
                response_content = []
                async for message in instance.query(prompt, options):
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_content.append(block.text)
                
                # Create assistant message
                assistant_content = "\n".join(response_content)
                assistant_msg = DBMessage(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                )
                db.add(assistant_msg)
                
                # Update session
                session.status = "completed"
                session.ended_at = datetime.utcnow()
                
                await db.commit()
                
                messages.append(MessageResponse.model_validate(assistant_msg))
                
            except Exception as e:
                logger.error(f"Query failed: {e}")
                session.status = "error"
                await db.commit()
                raise
            
            return QueryResponse(
                session_id=session_id,
                messages=messages,
                status=session.status,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
            )
    
    async def get_instance_status(self, instance_id: str) -> str:
        """Get the status of an instance"""
        if instance_id in self.instances:
            return "active" if self.instances[instance_id].active else "inactive"
        return "terminated"
    
    async def cleanup_terminated_instances(self) -> None:
        """Clean up terminated instances from memory"""
        async with self._lock:
            terminated = [
                instance_id
                for instance_id, instance in self.instances.items()
                if not instance.active
            ]
            
            for instance_id in terminated:
                del self.instances[instance_id]
                logger.info(f"Cleaned up terminated instance {instance_id}")