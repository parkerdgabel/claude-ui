from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.core.database import get_db
from claude_ui.models.schemas import (
    InstanceCreate,
    InstanceUpdate,
    InstanceResponse,
    QueryRequest,
    QueryResponse,
)
from claude_ui.services.instance_service import instance_service

router = APIRouter()


@router.post("/", response_model=InstanceResponse)
async def create_instance(
    instance_data: InstanceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new Claude Code instance"""
    try:
        instance = await instance_service.create_instance(instance_data, db)
        return instance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/", response_model=List[InstanceResponse])
async def list_instances(
    db: AsyncSession = Depends(get_db),
):
    """List all Claude Code instances"""
    instances = await instance_service.list_instances(db)
    return instances


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific Claude Code instance"""
    instance = await instance_service.get_instance(instance_id, db)
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
    instance = await instance_service.update_instance(instance_id, update_data, db)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    return instance


@router.delete("/{instance_id}")
async def delete_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Terminate and delete a Claude Code instance"""
    success = await instance_service.delete_instance(instance_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found",
        )
    return {"message": "Instance deleted successfully"}


@router.post("/{instance_id}/query", response_model=QueryResponse)
async def query_instance(
    instance_id: str,
    query: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a query to a Claude Code instance"""
    try:
        response = await instance_service.query_instance(instance_id, query, db)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
    try:
        success = await instance_service.restart_instance(instance_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instance not found",
            )
        return {"message": "Instance restarted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart instance: {str(e)}",
        )