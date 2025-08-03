from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, default="inactive")  # inactive, active, error, terminated
    pid = Column(Integer, nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    working_directory = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    terminated_at = Column(DateTime, nullable=True)
    
    # Configuration
    environment_vars = Column(JSON, default=dict)
    mcp_servers = Column(JSON, default=list)
    system_prompt = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="instances")
    sessions = relationship("Session", back_populates="instance", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    path = Column(String, nullable=False)
    git_url = Column(String, nullable=True)
    default_branch = Column(String, default="main")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Claude.md content
    claude_md_content = Column(Text, nullable=True)
    
    # Project settings
    settings = Column(JSON, default=dict)
    
    # Relationships
    instances = relationship("Instance", back_populates="project", cascade="all, delete-orphan")
    worktrees = relationship("Worktree", back_populates="project", cascade="all, delete-orphan")


class Worktree(Base):
    __tablename__ = "worktrees"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="worktrees")


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    instance_id = Column(String, ForeignKey("instances.id"), nullable=False)
    status = Column(String, default="active")  # active, paused, completed
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Cost tracking
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    
    # Relationships
    instance = relationship("Instance", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    tokens = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="messages")


class MCPServer(Base):
    __tablename__ = "mcp_servers"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # stdio, http, sse
    command = Column(String, nullable=True)  # For stdio type
    url = Column(String, nullable=True)  # For http/sse types
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)