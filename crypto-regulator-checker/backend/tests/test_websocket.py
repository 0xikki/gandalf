import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import WebSocket, WebSocketDisconnect, status
from src.api.websocket import (
    ConnectionManager,
    get_current_user_from_token,
    websocket_endpoint,
    MAX_CONNECTIONS,
    HEARTBEAT_INTERVAL,
    router,
    Document
)
from src.core.config import settings
from src.core.database import get_db
from src.core.security import verify_token
from src.models.document import Document
from fastapi.testclient import TestClient
from src.main import app
import asyncio

# Test data
TEST_USER_ID = "test_user_123"
TEST_DOCUMENT_ID = 1
TEST_TOKEN = "valid.test.token"
TEST_HEARTBEAT_INTERVAL = 0.1  # Short interval for testing

@pytest.fixture
def mock_websocket():
    websocket = AsyncMock(spec=WebSocket)
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    return websocket

@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test."""
    return ConnectionManager()

@pytest.fixture
def mock_document():
    document = MagicMock()
    document.id = TEST_DOCUMENT_ID
    document.user_id = TEST_USER_ID
    document.content = ""
    return document

@pytest.fixture
def mock_db(mock_document):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_document
    return db

@pytest.fixture
def test_token():
    """Create a valid test JWT token."""
    return "test_token"

@pytest.fixture
def client(mock_db):
    app = TestClient(router)
    app.dependency_overrides[get_db] = lambda: mock_db
    return app

@pytest.mark.asyncio
async def test_connection_manager_connect(mock_websocket, connection_manager):
    """Test WebSocket connection establishment."""
    document_id = 1
    user_id = "test_user"
    
    # Test successful connection
    success = await connection_manager.connect(mock_websocket, document_id, user_id)
    assert success
    assert connection_manager.total_connections == 1
    assert document_id in connection_manager.active_connections
    assert user_id in connection_manager.active_connections[document_id]

    # Test connection limit
    connection_manager.total_connections = MAX_CONNECTIONS
    success = await connection_manager.connect(mock_websocket, document_id, user_id)
    assert not success
    assert mock_websocket.close.called

@pytest.mark.asyncio
async def test_connection_manager_disconnect(mock_websocket, connection_manager):
    """Test WebSocket disconnection."""
    document_id = 1
    user_id = "test_user"
    
    await connection_manager.connect(mock_websocket, document_id, user_id)
    connection_manager.disconnect(document_id, user_id)
    
    assert connection_manager.total_connections == 0
    assert document_id not in connection_manager.active_connections

@pytest.mark.asyncio
async def test_connection_manager_broadcast(mock_websocket, connection_manager):
    """Test broadcasting messages to connected clients."""
    document_id = 1
    user_id = "test_user"
    
    await connection_manager.connect(mock_websocket, document_id, user_id)
    
    # Test status update
    await connection_manager.send_status_update(document_id, "processing", 0.5)
    mock_websocket.send_json.assert_called_with({
        "type": "status",
        "documentId": document_id,
        "status": "processing",
        "progress": 0.5
    })
    
    # Test error message
    await connection_manager.send_error(document_id, "test error")
    mock_websocket.send_json.assert_called_with({
        "type": "error",
        "documentId": document_id,
        "error": "test error"
    })

@pytest.mark.asyncio
async def test_heartbeat(mock_websocket):
    with patch('src.api.websocket.HEARTBEAT_INTERVAL', TEST_HEARTBEAT_INTERVAL):
        manager = ConnectionManager()
        
        # Connect the websocket
        await manager.connect(mock_websocket, TEST_DOCUMENT_ID, TEST_USER_ID)
        
        # Wait for heartbeat
        await asyncio.sleep(TEST_HEARTBEAT_INTERVAL + 0.1)
        
        # Verify heartbeat was sent
        mock_websocket.send_json.assert_called_with({"type": "heartbeat"})

@pytest.mark.asyncio
async def test_websocket_endpoint_authentication(mock_websocket):
    """Test WebSocket endpoint authentication."""
    document_id = 1
    mock_db = Mock()
    
    # Test authentication timeout
    mock_websocket.receive_json.side_effect = TimeoutError()
    await websocket_endpoint(mock_websocket, document_id, mock_db)
    mock_websocket.close.assert_called_with(code=status.WS_1008_POLICY_VIOLATION)
    
    # Test invalid authentication message
    mock_websocket.receive_json.return_value = {"type": "invalid"}
    await websocket_endpoint(mock_websocket, document_id, mock_db)
    mock_websocket.close.assert_called_with(code=status.WS_1008_POLICY_VIOLATION)

@pytest.mark.asyncio
async def test_websocket_connection(mock_websocket, mock_db):
    with patch("src.api.websocket.verify_token", return_value=TEST_USER_ID):
        # Configure receive_json to return auth message first, then raise WebSocketDisconnect
        mock_websocket.receive_json.side_effect = [
            {"type": "authenticate", "token": TEST_TOKEN},
            WebSocketDisconnect()
        ]
        
        # Call the endpoint
        await websocket_endpoint(mock_websocket, TEST_DOCUMENT_ID, mock_db)
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()

@pytest.mark.asyncio
async def test_websocket_document_update(mock_websocket, mock_db):
    with patch("src.api.websocket.verify_token", return_value=TEST_USER_ID):
        # Set up messages
        messages = [
            {"type": "authenticate", "token": TEST_TOKEN},
            {"type": "document_update", "content": "Updated content"},
            WebSocketDisconnect()
        ]
        
        # Configure receive_json to return messages in sequence
        mock_websocket.receive_json.side_effect = messages
        
        # Call the endpoint
        await websocket_endpoint(mock_websocket, TEST_DOCUMENT_ID, mock_db)
        
        # Verify document was updated
        mock_db.commit.assert_called_once()
        
        # Verify success response was sent
        assert any(
            call.args == ({"type": "document_status", "status": "updated"},)
            for call in mock_websocket.send_json.call_args_list
        )

@pytest.mark.asyncio
async def test_websocket_invalid_message(mock_websocket, mock_db):
    with patch("src.api.websocket.verify_token", return_value=TEST_USER_ID):
        # Set up messages
        messages = [
            {"type": "authenticate", "token": TEST_TOKEN},
            {"type": "invalid_type"},
            WebSocketDisconnect()
        ]
        
        # Configure receive_json to return messages in sequence
        mock_websocket.receive_json.side_effect = messages
        
        # Call the endpoint
        await websocket_endpoint(mock_websocket, TEST_DOCUMENT_ID, mock_db)
        
        # Verify error response was sent
        assert any(
            call.args == ({"type": "error", "message": "Invalid message type: invalid_type"},)
            for call in mock_websocket.send_json.call_args_list
        ) 