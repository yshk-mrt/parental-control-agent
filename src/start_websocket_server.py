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
        
        # Initialize system status only
        await asyncio.sleep(2)
        
        # Import the functions here to avoid circular imports
        from websocket_server import update_system_status
        
        logger.info("Initializing system status...")
        
        # Set initial system status
        update_system_status("monitoring", "good")
        
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