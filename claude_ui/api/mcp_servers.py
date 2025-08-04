from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.core.database import get_db
from claude_ui.models.schemas import MCPServerCreate, MCPServerUpdate, MCPServerResponse
from claude_ui.services.mcp_service import mcp_service

router = APIRouter()


@router.post("/servers", response_model=MCPServerResponse)
async def create_mcp_server(
    server_data: MCPServerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCP server configuration"""
    try:
        server = await mcp_service.create_mcp_server(server_data, db)
        return server
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all MCP server configurations"""
    servers = await mcp_service.list_mcp_servers(db, enabled_only)
    return servers


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific MCP server configuration"""
    server = await mcp_service.get_mcp_server(server_id, db)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    return server


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str,
    update_data: MCPServerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an MCP server configuration"""
    server = await mcp_service.update_mcp_server(server_id, update_data, db)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    return server


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an MCP server configuration"""
    success = await mcp_service.delete_mcp_server(server_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    return {"message": "MCP server deleted successfully"}


@router.post("/servers/{server_id}/toggle")
async def toggle_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Toggle the enabled state of an MCP server"""
    result = await mcp_service.toggle_mcp_server(server_id, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    _, enabled = result
    return {
        "message": f"MCP server {'enabled' if enabled else 'disabled'}",
        "enabled": enabled,
    }


@router.get("/servers/export")
async def export_mcp_config(
    db: AsyncSession = Depends(get_db),
):
    """Export MCP configuration in .mcp.json format"""
    mcp_config = await mcp_service.export_mcp_config(db)
    return mcp_config