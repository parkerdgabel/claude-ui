import asyncio
import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from claude_ui.core.database import get_db_context
from claude_ui.models.database import Instance
from claude_ui.models.schemas import WSMessage
from claude_ui.services.claude_manager import ClaudeManager

logger = logging.getLogger(__name__)

router = APIRouter()
claude_manager = ClaudeManager()

# Track active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/instances/{instance_id}/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    instance_id: str,
):
    """WebSocket endpoint for streaming Claude Code output"""
    await websocket.accept()
    active_connections[instance_id] = websocket
    
    try:
        # Verify instance exists and is active
        async with get_db_context() as db:
            instance = await db.get(Instance, instance_id)
            if not instance or instance.status != "active":
                await websocket.send_json({
                    "type": "error",
                    "data": "Instance not found or not active",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await websocket.close()
                return
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": "Connected to instance",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                elif data.get("type") == "status":
                    # Send current instance status
                    status = await claude_manager.get_instance_status(instance_id)
                    await websocket.send_json({
                        "type": "status",
                        "data": status,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    finally:
        # Clean up connection
        if instance_id in active_connections:
            del active_connections[instance_id]
        logger.info(f"WebSocket disconnected for instance {instance_id}")


@router.websocket("/instances/{instance_id}/interact")
async def websocket_interact_endpoint(
    websocket: WebSocket,
    instance_id: str,
):
    """WebSocket endpoint for interactive Claude Code sessions"""
    await websocket.accept()
    
    try:
        # Verify instance exists and is active
        async with get_db_context() as db:
            instance = await db.get(Instance, instance_id)
            if not instance or instance.status != "active":
                await websocket.send_json({
                    "type": "error",
                    "data": "Instance not found or not active",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await websocket.close()
                return
        
        # Send ready status
        await websocket.send_json({
            "type": "status",
            "data": "Ready for interaction",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        while True:
            try:
                # Receive query from client
                data = await websocket.receive_json()
                
                if data.get("type") == "query":
                    prompt = data.get("prompt")
                    options = data.get("options", {})
                    
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "status",
                        "data": "Processing query...",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
                    # Query Claude instance
                    try:
                        claude_instance = claude_manager.instances.get(instance_id)
                        if not claude_instance:
                            raise ValueError("Instance not found in manager")
                        
                        # Stream responses
                        async for message in claude_instance.query(prompt, options):
                            # Convert message to JSON-serializable format
                            await websocket.send_json({
                                "type": "output",
                                "data": str(message),
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        
                        # Send completion status
                        await websocket.send_json({
                            "type": "status",
                            "data": "Query completed",
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "data": f"Query error: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Interactive WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    finally:
        logger.info(f"Interactive WebSocket disconnected for instance {instance_id}")


async def broadcast_to_instance(instance_id: str, message: WSMessage):
    """Broadcast a message to connected WebSocket for an instance"""
    if instance_id in active_connections:
        websocket = active_connections[instance_id]
        try:
            await websocket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"Failed to broadcast to instance {instance_id}: {e}")
            # Remove dead connection
            del active_connections[instance_id]