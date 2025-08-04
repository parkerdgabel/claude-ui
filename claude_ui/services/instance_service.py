import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.models.database import Instance
from claude_ui.models.schemas import (
    InstanceCreate,
    InstanceUpdate,
    InstanceResponse,
    QueryRequest,
    QueryResponse,
)
from claude_ui.services.claude_manager import ClaudeManager


class InstanceService:
    """Service layer for instance management"""
    
    def __init__(self):
        self.claude_manager = ClaudeManager()
    
    async def create_instance(
        self,
        instance_data: InstanceCreate,
        db: AsyncSession,
    ) -> Instance:
        """Create a new Claude Code instance"""
        # Generate unique ID
        instance_id = str(uuid.uuid4())
        
        # Create database record
        instance = Instance(
            id=instance_id,
            name=instance_data.name,
            project_id=instance_data.project_id,
            working_directory=instance_data.working_directory,
            environment_vars=instance_data.environment_vars,
            mcp_servers=instance_data.mcp_servers,
            system_prompt=instance_data.system_prompt,
        )
        
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        
        # Start Claude Code process
        try:
            await self.claude_manager.start_instance(instance)
        except Exception as e:
            # Update status to error
            instance.status = "error"
            await db.commit()
            raise ValueError(f"Failed to start instance: {str(e)}")
        
        return instance
    
    async def get_instance(
        self,
        instance_id: str,
        db: AsyncSession,
    ) -> Optional[Instance]:
        """Get a specific instance"""
        return await db.get(Instance, instance_id)
    
    async def list_instances(
        self,
        db: AsyncSession,
    ) -> List[Instance]:
        """List all instances"""
        result = await db.execute(select(Instance))
        return result.scalars().all()
    
    async def update_instance(
        self,
        instance_id: str,
        update_data: InstanceUpdate,
        db: AsyncSession,
    ) -> Optional[Instance]:
        """Update an instance"""
        instance = await db.get(Instance, instance_id)
        if not instance:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        
        await db.commit()
        await db.refresh(instance)
        
        # Restart instance if configuration changed and it's active
        if instance.status == "active":
            await self.claude_manager.restart_instance(instance)
        
        return instance
    
    async def delete_instance(
        self,
        instance_id: str,
        db: AsyncSession,
    ) -> bool:
        """Delete an instance"""
        instance = await db.get(Instance, instance_id)
        if not instance:
            return False
        
        # Terminate the process if active
        if instance.status == "active":
            await self.claude_manager.terminate_instance(instance)
        
        # Delete from database
        await db.delete(instance)
        await db.commit()
        
        return True
    
    async def query_instance(
        self,
        instance_id: str,
        query: QueryRequest,
        db: AsyncSession,
    ) -> QueryResponse:
        """Send a query to an instance"""
        instance = await db.get(Instance, instance_id)
        if not instance:
            raise ValueError("Instance not found")
        
        if instance.status != "active":
            raise ValueError("Instance is not active")
        
        # Execute query
        return await self.claude_manager.query_instance(
            instance,
            query.prompt,
            query.options,
        )
    
    async def restart_instance(
        self,
        instance_id: str,
        db: AsyncSession,
    ) -> bool:
        """Restart an instance"""
        instance = await db.get(Instance, instance_id)
        if not instance:
            return False
        
        await self.claude_manager.restart_instance(instance)
        await db.commit()
        
        return True


# Singleton instance
instance_service = InstanceService()