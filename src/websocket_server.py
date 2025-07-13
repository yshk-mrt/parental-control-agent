"""
WebSocket Server for Parental Control System

This server handles real-time communication between the backend monitoring system
and the parent dashboard frontend. It provides:
- System status updates
- Approval request notifications
- Activity monitoring updates
- Two-way communication for parent responses
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: str

@dataclass
class SystemStatus:
    """System status information"""
    status: str  # 'monitoring', 'locked', 'offline'
    lastUpdate: str
    connectionHealth: str  # 'good', 'poor', 'disconnected'

@dataclass
class ApprovalRequest:
    """Approval request from child system"""
    id: str
    reason: str
    timestamp: str
    applicationName: Optional[str] = None
    blockedUrl: Optional[str] = None
    keywords: Optional[List[str]] = None
    confidence: float = 0.0
    childId: str = "child-001"

@dataclass
class ActivityUpdate:
    """Activity update information"""
    childId: str
    applicationName: str
    duration: int  # in seconds
    category: str
    timestamp: str
    isActive: bool

class WebSocketServer:
    """WebSocket server for parent dashboard communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.message_queue: queue.Queue = queue.Queue()
        self.system_status = SystemStatus(
            status="offline",
            lastUpdate=datetime.now().isoformat(),
            connectionHealth="disconnected"
        )
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.current_activity: Optional[ActivityUpdate] = None
        self.running = False
        self.server = None
        
        logger.info(f"WebSocket server initialized on {host}:{port}")
    
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        # Send current system status to new client
        await self.send_to_client(websocket, WebSocketMessage(
            type="CONNECTION_STATUS",
            data=asdict(self.system_status),
            timestamp=datetime.now().isoformat()
        ))
        
        # Send current activity if available
        if self.current_activity:
            await self.send_to_client(websocket, WebSocketMessage(
                type="ACTIVITY_UPDATE",
                data=asdict(self.current_activity),
                timestamp=datetime.now().isoformat()
            ))
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: WebSocketMessage):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(asdict(message)))
            logger.debug(f"Sent message to client: {message.type}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Client connection closed while sending message")
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
    
    async def broadcast_message(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        if not self.clients:
            logger.debug("No clients connected, skipping broadcast")
            return
        
        logger.info(f"Broadcasting message: {message.type} to {len(self.clients)} clients")
        
        # Create tasks for all clients
        tasks = []
        for websocket in self.clients.copy():  # Copy to avoid modification during iteration
            tasks.append(self.send_to_client(websocket, message))
        
        # Execute all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handle_client_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            msg_data = data.get("data", {})
            
            logger.info(f"Received message from client: {msg_type}")
            
            if msg_type == "HEARTBEAT":
                # Respond to heartbeat
                await self.send_to_client(websocket, WebSocketMessage(
                    type="HEARTBEAT_RESPONSE",
                    data={"timestamp": datetime.now().isoformat()},
                    timestamp=datetime.now().isoformat()
                ))
            
            elif msg_type == "APPROVAL_RESPONSE":
                # Handle approval response from parent
                request_id = msg_data.get("requestId")
                approved = msg_data.get("approved", False)
                parent_id = msg_data.get("parentId", "parent-001")
                
                if request_id in self.approval_requests:
                    request = self.approval_requests[request_id]
                    logger.info(f"Approval response for {request_id}: {'Approved' if approved else 'Denied'}")
                    
                    # Remove from pending requests
                    del self.approval_requests[request_id]
                    
                    # TODO: Forward approval response to monitoring system
                    # This would typically unlock the system or take other actions
                    self.process_approval_response(request_id, approved, parent_id)
                
            elif msg_type == "SYSTEM_STATUS_REQUEST" or msg_type == "REQUEST_SYSTEM_STATUS":
                # Send current system status
                await self.send_to_client(websocket, WebSocketMessage(
                    type="CONNECTION_STATUS",
                    data=asdict(self.system_status),
                    timestamp=datetime.now().isoformat()
                ))
            
            elif msg_type == "SETTINGS_UPDATE":
                # Handle settings update
                settings = msg_data
                logger.info(f"Settings update received: {settings}")
                # TODO: Apply settings to monitoring system
                self.apply_settings(settings)
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle individual client connection"""
        logger.info(f"New client connecting from: {websocket.remote_address}")
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        self.running = True
        logger.info("WebSocket server started successfully")
        
        # Start background task to process messages
        asyncio.create_task(self.process_message_queue())
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            logger.info("Stopping WebSocket server")
            self.running = False
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def process_message_queue(self):
        """Process messages from the message queue"""
        while self.running:
            try:
                # Check for messages from monitoring system
                if not self.message_queue.empty():
                    message_data = self.message_queue.get_nowait()
                    await self.handle_monitoring_message(message_data)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
    
    async def handle_monitoring_message(self, message_data: Dict[str, Any]):
        """Handle messages from the monitoring system"""
        msg_type = message_data.get("type")
        
        if msg_type == "SYSTEM_LOCKED":
            self.system_status.status = "locked"
            self.system_status.lastUpdate = datetime.now().isoformat()
            
            await self.broadcast_message(WebSocketMessage(
                type="SYSTEM_LOCKED",
                data=message_data.get("data", {}),
                timestamp=datetime.now().isoformat()
            ))
        
        elif msg_type == "SYSTEM_UNLOCKED":
            self.system_status.status = "monitoring"
            self.system_status.lastUpdate = datetime.now().isoformat()
            
            await self.broadcast_message(WebSocketMessage(
                type="SYSTEM_UNLOCKED",
                data=message_data.get("data", {}),
                timestamp=datetime.now().isoformat()
            ))
        
        elif msg_type == "APPROVAL_REQUEST":
            # Create approval request
            request_data = message_data.get("data", {})
            request = ApprovalRequest(
                id=request_data.get("id", f"req_{int(time.time())}"),
                reason=request_data.get("reason", "Inappropriate content detected"),
                timestamp=datetime.now().isoformat(),
                applicationName=request_data.get("applicationName"),
                blockedUrl=request_data.get("blockedUrl"),
                keywords=request_data.get("keywords"),
                confidence=request_data.get("confidence", 0.0),
                childId=request_data.get("childId", "child-001")
            )
            
            self.approval_requests[request.id] = request
            
            await self.broadcast_message(WebSocketMessage(
                type="APPROVAL_REQUEST",
                data=asdict(request),
                timestamp=datetime.now().isoformat()
            ))
        
        elif msg_type == "ACTIVITY_UPDATE":
            # Update current activity
            activity_data = message_data.get("data", {})
            self.current_activity = ActivityUpdate(
                childId=activity_data.get("childId", "child-001"),
                applicationName=activity_data.get("applicationName", "Unknown"),
                duration=activity_data.get("duration", 0),
                category=activity_data.get("category", "Unknown"),
                timestamp=datetime.now().isoformat(),
                isActive=activity_data.get("isActive", True)
            )
            
            await self.broadcast_message(WebSocketMessage(
                type="ACTIVITY_UPDATE",
                data=asdict(self.current_activity),
                timestamp=datetime.now().isoformat()
            ))
    
    def send_message_to_clients(self, message_type: str, data: Dict[str, Any]):
        """Thread-safe method to send messages to clients"""
        self.message_queue.put({
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def process_approval_response(self, request_id: str, approved: bool, parent_id: str):
        """Process approval response from parent"""
        logger.info(f"Processing approval response: {request_id} = {'Approved' if approved else 'Denied'}")
        
        # TODO: Integrate with monitoring system
        # This should unlock the system if approved, or maintain lock if denied
        if approved:
            self.send_message_to_clients("SYSTEM_UNLOCKED", {
                "requestId": request_id,
                "parentId": parent_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.info(f"Request {request_id} denied, maintaining system lock")
    
    def apply_settings(self, settings: Dict[str, Any]):
        """Apply settings from parent dashboard"""
        logger.info(f"Applying settings: {settings}")
        # TODO: Integrate with monitoring system to apply settings
        pass
    
    def update_system_status(self, status: str, connection_health: str = "good"):
        """Update system status"""
        self.system_status.status = status
        self.system_status.lastUpdate = datetime.now().isoformat()
        self.system_status.connectionHealth = connection_health
        
        # Broadcast status update
        self.send_message_to_clients("CONNECTION_STATUS", asdict(self.system_status))


# Global WebSocket server instance
_websocket_server: Optional[WebSocketServer] = None

def get_websocket_server() -> WebSocketServer:
    """Get or create the global WebSocket server instance"""
    global _websocket_server
    if _websocket_server is None:
        _websocket_server = WebSocketServer()
    return _websocket_server

async def start_websocket_server(host: str = "localhost", port: int = 8080):
    """Start the WebSocket server"""
    server = get_websocket_server()
    server.host = host
    server.port = port
    await server.start_server()
    return server

async def stop_websocket_server():
    """Stop the WebSocket server"""
    global _websocket_server
    if _websocket_server:
        await _websocket_server.stop_server()
        _websocket_server = None

def send_system_lock_notification(reason: str, **kwargs):
    """Send system lock notification to parent dashboard"""
    server = get_websocket_server()
    server.send_message_to_clients("SYSTEM_LOCKED", {
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    })

def send_approval_request(request_id: str, reason: str, **kwargs):
    """Send approval request to parent dashboard"""
    server = get_websocket_server()
    server.send_message_to_clients("APPROVAL_REQUEST", {
        "id": request_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    })

def send_activity_update(application_name: str, duration: int, category: str, **kwargs):
    """Send activity update to parent dashboard"""
    server = get_websocket_server()
    server.send_message_to_clients("ACTIVITY_UPDATE", {
        "applicationName": application_name,
        "duration": duration,
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "isActive": True,
        **kwargs
    })

def update_system_status(status: str, connection_health: str = "good"):
    """Update system status"""
    server = get_websocket_server()
    server.update_system_status(status, connection_health)

if __name__ == "__main__":
    # Test the WebSocket server
    async def main():
        server = await start_websocket_server()
        
        # Simulate some events for testing
        await asyncio.sleep(2)
        send_system_lock_notification("Test lock notification")
        
        await asyncio.sleep(2)
        send_approval_request("test-001", "Test approval request")
        
        await asyncio.sleep(2)
        send_activity_update("Test App", 300, "Education")
        
        # Keep server running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            await stop_websocket_server()
    
    asyncio.run(main()) 