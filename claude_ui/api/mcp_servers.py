from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.core.database import get_db
from claude_ui.models.database import MCPServer
from claude_ui.models.schemas import MCPServerCreate, MCPServerUpdate, MCPServerResponse

router = APIRouter()


@router.post("/servers", response_model=MCPServerResponse)
async def create_mcp_server(
    server_data: MCPServerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new MCP server configuration"""
    # Validate based on type
    if server_data.type == "stdio" and not server_data.command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command is required for stdio type MCP servers",
        )
    
    if server_data.type in ["http", "sse"] and not server_data.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required for http/sse type MCP servers",
        )
    
    # Generate unique ID
    server_id = str(uuid.uuid4())
    
    # Create database record
    server = MCPServer(
        id=server_id,
        name=server_data.name,
        type=server_data.type,
        command=server_data.command,
        url=server_data.url,
        args=server_data.args,
        env=server_data.env,
        enabled=server_data.enabled,
    )
    
    db.add(server)
    await db.commit()
    await db.refresh(server)
    
    return server


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all MCP server configurations"""
    query = select(MCPServer)
    if enabled_only:
        query = query.where(MCPServer.enabled == True)
    
    result = await db.execute(query)
    servers = result.scalars().all()
    return servers


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific MCP server configuration"""
    server = await db.get(MCPServer, server_id)
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
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(server, field, value)
    
    await db.commit()
    await db.refresh(server)
    
    return server


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an MCP server configuration"""
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    await db.delete(server)
    await db.commit()
    
    return {"message": "MCP server deleted successfully"}


@router.post("/servers/{server_id}/toggle")
async def toggle_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Toggle the enabled state of an MCP server"""
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    server.enabled = not server.enabled
    await db.commit()
    
    return {
        "message": f"MCP server {'enabled' if server.enabled else 'disabled'}",
        "enabled": server.enabled,
    }


@router.get("/servers/export")
async def export_mcp_config(
    db: AsyncSession = Depends(get_db),
):
    """Export MCP configuration in .mcp.json format"""
    # Get all enabled servers
    result = await db.execute(
        select(MCPServer).where(MCPServer.enabled == True)
    )
    servers = result.scalars().all()
    
    # Format for .mcp.json
    mcp_config = {
        "servers": {}
    }
    
    for server in servers:
        server_config = {}
        
        if server.type == "stdio":
            server_config["command"] = server.command
            if server.args:
                server_config["args"] = server.args
        elif server.type in ["http", "sse"]:
            server_config["url"] = server.url
        
        if server.env:
            server_config["env"] = server.env
        
        mcp_config["servers"][server.name] = server_config
    
    return mcp_config