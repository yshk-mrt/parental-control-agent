#!/usr/bin/env python3
"""
Test WebSocket client to verify approval requests are being sent correctly
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestWebSocketClient:
    def __init__(self, uri="ws://localhost:8080"):
        self.uri = uri
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to WebSocket server at {self.uri}")
            self.running = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")
    
    async def send_message(self, message_type: str, data: dict):
        """Send a message to the server"""
        if not self.websocket:
            logger.error("Not connected to WebSocket server")
            return
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent message: {message_type}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def listen_for_messages(self):
        """Listen for messages from the server"""
        if not self.websocket:
            logger.error("Not connected to WebSocket server")
            return
        
        logger.info("Listening for messages...")
        try:
            while self.running:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    async def handle_message(self, data: dict):
        """Handle incoming messages"""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        timestamp = data.get("timestamp")
        
        logger.info(f"Received message: {msg_type}")
        
        if msg_type == "APPROVAL_REQUEST":
            logger.info("🚨 APPROVAL REQUEST RECEIVED!")
            logger.info(f"   Request ID: {msg_data.get('id')}")
            logger.info(f"   Reason: {msg_data.get('reason')}")
            logger.info(f"   Application: {msg_data.get('applicationName')}")
            logger.info(f"   Confidence: {msg_data.get('confidence')}")
            logger.info(f"   Child ID: {msg_data.get('childId')}")
            logger.info(f"   Timestamp: {timestamp}")
            
            # Simulate parent approval after 5 seconds
            request_id = msg_data.get('id')
            if request_id:
                asyncio.create_task(self.simulate_approval(request_id))
        
        elif msg_type == "SYSTEM_LOCKED":
            logger.info("🔒 SYSTEM LOCKED!")
            logger.info(f"   Data: {msg_data}")
        
        elif msg_type == "SYSTEM_UNLOCKED":
            logger.info("🔓 SYSTEM UNLOCKED!")
            logger.info(f"   Data: {msg_data}")
        
        elif msg_type == "CONNECTION_STATUS":
            logger.info("📡 CONNECTION STATUS UPDATE")
            logger.info(f"   Status: {msg_data.get('status')}")
            logger.info(f"   Health: {msg_data.get('connectionHealth')}")
        
        elif msg_type == "ACTIVITY_UPDATE":
            logger.info("📊 ACTIVITY UPDATE")
            logger.info(f"   Application: {msg_data.get('applicationName')}")
            logger.info(f"   Duration: {msg_data.get('duration')}")
            logger.info(f"   Category: {msg_data.get('category')}")
        
        else:
            logger.info(f"Unknown message type: {msg_type}")
            logger.info(f"Data: {msg_data}")
    
    async def simulate_approval(self, request_id: str):
        """Simulate parent approval after delay"""
        await asyncio.sleep(5)
        logger.info(f"🟢 Simulating approval for request: {request_id}")
        
        await self.send_message("APPROVAL_RESPONSE", {
            "requestId": request_id,
            "approved": True,
            "parentId": "parent-001"
        })
    
    async def send_heartbeat(self):
        """Send periodic heartbeat"""
        while self.running:
            await self.send_message("HEARTBEAT", {})
            await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    """Main function to run the test client"""
    client = TestWebSocketClient()
    
    # Connect to server
    if not await client.connect():
        return
    
    try:
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        # Listen for messages
        await client.listen_for_messages()
        
    except KeyboardInterrupt:
        logger.info("Test client interrupted by user")
    except Exception as e:
        logger.error(f"Test client error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🧪 Starting WebSocket Test Client")
    print("This client will connect to the WebSocket server and listen for approval requests")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    asyncio.run(main()) 