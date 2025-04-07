import logging
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter, status
from typing import Dict, Optional, Set
import asyncio
import json
from sqlalchemy.orm import Session
from ..core.security import verify_token
from ..models.document import Document
from ..crud.document import get_document
from ..core.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Constants
HEARTBEAT_INTERVAL = 30  # seconds
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB maximum message size
AUTH_TIMEOUT = 5.0  # seconds
MAX_CONNECTIONS = 100  # Maximum number of simultaneous connections

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        self.total_connections: int = 0
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        logger.info("WebSocket connection manager initialized")

    async def connect(self, websocket: WebSocket, document_id: int, user_id: str):
        try:
            if self.total_connections >= MAX_CONNECTIONS:
                logger.warning(f"Connection limit exceeded. Rejecting connection for user {user_id}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return False
            
            if document_id not in self.active_connections:
                self.active_connections[document_id] = {}
            self.active_connections[document_id][user_id] = websocket
            self.total_connections += 1
            
            # Start heartbeat task for this connection
            connection_id = f"{document_id}:{user_id}"
            self.heartbeat_tasks[connection_id] = asyncio.create_task(
                self.send_heartbeat(websocket, connection_id)
            )
            
            logger.info(f"New WebSocket connection established for document {document_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error establishing connection for user {user_id}: {str(e)}")
            return False

    def disconnect(self, document_id: int, user_id: str):
        try:
            if document_id in self.active_connections:
                if user_id in self.active_connections[document_id]:
                    self.active_connections[document_id].pop(user_id)
                    self.total_connections -= 1
                    
                    # Cancel heartbeat task
                    connection_id = f"{document_id}:{user_id}"
                    if connection_id in self.heartbeat_tasks:
                        self.heartbeat_tasks[connection_id].cancel()
                        self.heartbeat_tasks.pop(connection_id)
                    
                    if not self.active_connections[document_id]:
                        del self.active_connections[document_id]
                    logger.info(f"WebSocket connection closed for document {document_id} by user {user_id}")
        except Exception as e:
            logger.error(f"Error during disconnect for user {user_id}: {str(e)}")

    async def send_status_update(self, document_id: int, status: str, progress: Optional[float] = None):
        if document_id in self.active_connections:
            message = {
                "type": "status",
                "documentId": document_id,
                "status": status,
                "progress": progress
            }
            logger.debug(f"Sending status update for document {document_id}: {message}")
            await self._broadcast_to_document(document_id, message)

    async def send_error(self, document_id: int, error: str):
        if document_id in self.active_connections:
            message = {
                "type": "error",
                "documentId": document_id,
                "error": error
            }
            logger.warning(f"Sending error message for document {document_id}: {error}")
            await self._broadcast_to_document(document_id, message)

    async def _broadcast_to_document(self, document_id: int, message: dict):
        if document_id in self.active_connections:
            disconnected_users = set()
            for user_id, connection in self.active_connections[document_id].items():
                try:
                    await connection.send_json(message)
                    logger.debug(f"Message sent to user {user_id}")
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected_users.add(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(document_id, user_id)

    async def send_heartbeat(self, websocket: WebSocket, connection_id: str):
        """Send periodic heartbeat messages to keep the connection alive."""
        try:
            logger.debug(f"Starting heartbeat task for connection {connection_id}")
            while True:
                logger.debug(f"Waiting {HEARTBEAT_INTERVAL} seconds before next heartbeat for {connection_id}")
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                logger.debug(f"Sending heartbeat for connection {connection_id}")
                await websocket.send_json({"type": "heartbeat"})
                logger.debug(f"Heartbeat sent successfully for connection {connection_id}")
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat task cancelled for connection {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Error sending heartbeat for connection {connection_id}: {str(e)}")

manager = ConnectionManager()

async def get_current_user_from_token(token: str) -> str:
    try:
        user_id = verify_token(token)
        logger.debug(f"Authenticated WebSocket connection for user {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise

@router.websocket("/{document_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    document_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection request received for document {document_id}")

        # Wait for authentication message with timeout
        try:
            auth_message = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=AUTH_TIMEOUT
            )
            logger.debug(f"Received auth message: {auth_message}")
        except asyncio.TimeoutError:
            logger.warning("Authentication timeout")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        except WebSocketDisconnect:
            logger.warning("Client disconnected during authentication")
            return
        except Exception as e:
            logger.error(f"Error receiving auth message: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Validate authentication message
        if not isinstance(auth_message, dict) or auth_message.get("type") != "authenticate" or "token" not in auth_message:
            logger.warning("Invalid authentication message format")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Verify token and get user ID
        try:
            user_id = verify_token(auth_message["token"])
            if not user_id:
                logger.warning("Invalid token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            logger.debug(f"Token verified for user {user_id}")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if document exists and user has access
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.warning(f"Document {document_id} not found")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            logger.debug(f"Document {document_id} user_id: {document.user_id}, requesting user_id: {user_id}")
            if str(document.user_id).strip() != str(user_id).strip():
                logger.warning(f"User {user_id} does not have access to document {document_id} (owned by {document.user_id})")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            logger.debug(f"Document access verified for user {user_id}")
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect to manager
        success = await manager.connect(websocket, document_id, user_id)
        if not success:
            logger.error("Failed to establish connection")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Send connection established message
        try:
            await websocket.send_json({
                "type": "connection_established",
                "document_id": document_id
            })
            logger.info(f"Connection established message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending connection established message: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Handle incoming messages
        try:
            while True:
                message = await websocket.receive_json()
                logger.debug(f"Received message: {message}")
                
                if not isinstance(message, dict) or "type" not in message:
                    logger.warning("Invalid message format")
                    continue

                if message["type"] == "heartbeat":
                    await websocket.send_json({"type": "heartbeat"})
                    logger.debug("Heartbeat response sent")
                elif message["type"] == "document_update":
                    # Process document update
                    await websocket.send_json({
                        "type": "document_status",
                        "status": "updated"
                    })
                    logger.debug("Document update processed")
                else:
                    logger.warning(f"Unknown message type: {message['type']}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"Error handling messages: {str(e)}")
        finally:
            manager.disconnect(document_id, user_id)
            logger.info(f"Connection cleaned up for user {user_id}")

    except Exception as e:
        logger.error(f"Unexpected error in websocket_endpoint: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass 