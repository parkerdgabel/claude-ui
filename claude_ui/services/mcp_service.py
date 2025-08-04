import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from claude_ui.models.database import MCPServer
from claude_ui.models.schemas import MCPServerCreate, MCPServerUpdate


class MCPService:
    """Service layer for MCP server management"""
    
    async def create_mcp_server(
        self,
        server_data: MCPServerCreate,
        db: AsyncSession,
    ) -> MCPServer:
        """Create a new MCP server configuration"""
        # Validate based on type
        if server_data.type == "stdio" and not server_data.command:
            raise ValueError("Command is required for stdio type MCP servers")
        
        if server_data.type in ["http", "sse"] and not server_data.url:
            raise ValueError("URL is required for http/sse type MCP servers")
        
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
    
    async def get_mcp_server(
        self,
        server_id: str,
        db: AsyncSession,
    ) -> Optional[MCPServer]:
        """Get a specific MCP server"""
        return await db.get(MCPServer, server_id)
    
    async def list_mcp_servers(
        self,
        db: AsyncSession,
        enabled_only: bool = False,
    ) -> List[MCPServer]:
        """List all MCP servers"""
        query = select(MCPServer)
        if enabled_only:
            query = query.where(MCPServer.enabled == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_mcp_server(
        self,
        server_id: str,
        update_data: MCPServerUpdate,
        db: AsyncSession,
    ) -> Optional[MCPServer]:
        """Update an MCP server"""
        server = await db.get(MCPServer, server_id)
        if not server:
            return None
        
        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(server, field, value)
        
        await db.commit()
        await db.refresh(server)
        
        return server
    
    async def delete_mcp_server(
        self,
        server_id: str,
        db: AsyncSession,
    ) -> bool:
        """Delete an MCP server"""
        server = await db.get(MCPServer, server_id)
        if not server:
            return False
        
        await db.delete(server)
        await db.commit()
        
        return True
    
    async def toggle_mcp_server(
        self,
        server_id: str,
        db: AsyncSession,
    ) -> Optional[tuple[bool, bool]]:
        """Toggle MCP server enabled state. Returns (success, new_enabled_state)"""
        server = await db.get(MCPServer, server_id)
        if not server:
            return None
        
        server.enabled = not server.enabled
        await db.commit()
        
        return True, server.enabled
    
    async def export_mcp_config(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
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


# Singleton instance
mcp_service = MCPService()