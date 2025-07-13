#!/usr/bin/env python3
"""
Start WebSocket Server for Parental Control System

This script starts the WebSocket server that enables communication
between the backend monitoring system and the parent dashboard frontend.
"""

import asyncio
import logging
import signal
import sys
from websocket_server import start_websocket_server, stop_websocket_server

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global server reference for cleanup
server = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if server:
        asyncio.create_task(stop_websocket_server())
    sys.exit(0)

async def main():
    """Main function to start the WebSocket server"""
    global server
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting WebSocket server for Parental Control System...")
        
        # Start the WebSocket server
        server = await start_websocket_server(host="localhost", port=8080)
        
        logger.info("WebSocket server started successfully!")
        logger.info("Frontend can connect at: ws://localhost:8080/parent-dashboard")
        logger.info("Press Ctrl+C to stop the server")
        
        # Simulate some test events after a delay
        await asyncio.sleep(5)
        
        # Import the functions here to avoid circular imports
        from websocket_server import (
            send_system_lock_notification,
            send_approval_request,
            send_activity_update,
            update_system_status
        )
        
        logger.info("Sending test notifications...")
        
        # Test system status update
        update_system_status("monitoring", "good")
        
        # Test activity update
        send_activity_update(
            application_name="Test Application",
            duration=120,
            category="Education",
            childId="child-001",
            isActive=True
        )
        
        # Test approval request after 10 seconds
        await asyncio.sleep(10)
        send_approval_request(
            request_id="test-001",
            reason="Test approval request - inappropriate content detected",
            applicationName="Test Browser",
            blockedUrl="https://example.com/blocked",
            keywords=["inappropriate", "content"],
            confidence=0.85
        )
        
        # Test system lock notification
        await asyncio.sleep(5)
        send_system_lock_notification(
            reason="Test system lock - inappropriate content detected",
            applicationName="Test Browser",
            blockedContent="test content",
            category="inappropriate",
            confidence=0.9
        )
        
        # Keep the server running
        await asyncio.Future()  # Run forever
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running WebSocket server: {e}")
    finally:
        if server:
            await stop_websocket_server()
        logger.info("WebSocket server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 