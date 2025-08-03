from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.core.database import get_db
from claude_ui.models.database import Instance
from claude_ui.models.schemas import (
    InstanceCreate,
    InstanceUpdate,
    InstanceResponse,
    QueryRequest,
    QueryResponse,
)
from claude_ui.services.claude_manager import ClaudeManager

router = APIRouter()
claude_manager = ClaudeManager()


@router.post("/", response_model=InstanceResponse)
async def create_instance(
    instance_data: InstanceCreate,
    db: AsyncSession = Depends(get_db),
):
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
        await claude_manager.start_instance(instance)
    except Exception as e:
        # Update status to error
        instance.status = "error"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start instance: {str(e)}",
        )
    
    return instance


@router.get("/", response_model=List[InstanceResponse])
async def list_instances(
    db: AsyncSession = Depends(get_db),
):
    """List all Claude Code instances"""
    result = await db.execute(select(Instance))
    instances = result.scalars().all()
    return instances


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific Claude Code instance"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    return instance


@router.put("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: str,
    update_data: InstanceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a Claude Code instance"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    
    await db.commit()
    await db.refresh(instance)
    
    # Restart instance if configuration changed
    if instance.status == "active":
        await claude_manager.restart_instance(instance)
    
    return instance


@router.delete("/{instance_id}")
async def delete_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Terminate and delete a Claude Code instance"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    
    # Terminate the process
    if instance.status == "active":
        await claude_manager.terminate_instance(instance)
    
    # Delete from database
    await db.delete(instance)
    await db.commit()
    
    return {"message": "Instance deleted successfully"}


@router.post("/{instance_id}/query", response_model=QueryResponse)
async def query_instance(
    instance_id: str,
    query: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a query to a Claude Code instance"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    
    if instance.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance is not active",
        )
    
    # Execute query
    try:
        response = await claude_manager.query_instance(
            instance,
            query.prompt,
            query.options,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/{instance_id}/restart")
async def restart_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Restart a Claude Code instance"""
    instance = await db.get(Instance, instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    
    try:
        await claude_manager.restart_instance(instance)
        await db.commit()
        return {"message": "Instance restarted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart instance: {str(e)}",
        )