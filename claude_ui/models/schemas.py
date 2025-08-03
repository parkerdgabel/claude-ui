from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# Instance Schemas
class InstanceCreate(BaseModel):
    name: str
    project_id: Optional[str] = None
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    mcp_servers: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None


class InstanceUpdate(BaseModel):
    name: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    mcp_servers: Optional[List[str]] = None
    system_prompt: Optional[str] = None


class InstanceResponse(BaseModel):
    id: str
    name: str
    status: str
    pid: Optional[int] = None
    project_id: Optional[str] = None
    working_directory: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    terminated_at: Optional[datetime] = None
    environment_vars: Dict[str, str]
    mcp_servers: List[str]
    system_prompt: Optional[str] = None
    
    class Config:
        from_attributes = True


# Project Schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    path: str
    git_url: Optional[str] = None
    default_branch: str = "main"
    claude_md_content: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    claude_md_content: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    path: str
    git_url: Optional[str] = None
    default_branch: str
    created_at: datetime
    updated_at: datetime
    claude_md_content: Optional[str] = None
    settings: Dict[str, Any]
    
    class Config:
        from_attributes = True


# Worktree Schemas
class WorktreeCreate(BaseModel):
    project_id: str
    name: str
    branch: str


class WorktreeResponse(BaseModel):
    id: str
    project_id: str
    name: str
    branch: str
    path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Session Schemas
class SessionResponse(BaseModel):
    id: str
    instance_id: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_tokens: int
    total_cost_usd: float
    
    class Config:
        from_attributes = True


# Message Schemas
class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime
    tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


# Query Schemas
class QueryRequest(BaseModel):
    prompt: str
    options: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
    status: str
    total_tokens: int
    total_cost_usd: float


# MCP Server Schemas
class MCPServerCreate(BaseModel):
    name: str
    type: str  # stdio, http, sse
    command: Optional[str] = None
    url: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    command: Optional[str] = None
    url: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None


class MCPServerResponse(BaseModel):
    id: str
    name: str
    type: str
    command: Optional[str] = None
    url: Optional[str] = None
    args: List[str]
    env: Dict[str, str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# WebSocket Messages
class WSMessage(BaseModel):
    type: str  # output, error, status
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)