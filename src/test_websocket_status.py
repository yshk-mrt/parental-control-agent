#!/usr/bin/env python3
"""
Test WebSocket Server Status

This script tests the WebSocket server connection and status reporting.
"""

import asyncio
import websockets
import json
import sys
import time
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection and status"""
    uri = "ws://localhost:8080"
    
    print("🔗 Testing WebSocket Connection...")
    print(f"URI: {uri}")
    print("=" * 50)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send heartbeat
            heartbeat_msg = {
                "type": "HEARTBEAT",
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(heartbeat_msg))
            print("📡 Sent heartbeat")
            
            # Request system status
            status_msg = {
                "type": "SYSTEM_STATUS_REQUEST",
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(status_msg))
            print("📊 Requested system status")
            
            # Listen for responses
            print("\n📥 Listening for responses...")
            timeout = 5  # 5 seconds timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    print(f"📨 Received: {data['type']}")
                    if data['type'] == 'CONNECTION_STATUS':
                        status_data = data['data']
                        print(f"   Status: {status_data['status']}")
                        print(f"   Health: {status_data['connectionHealth']}")
                        print(f"   Updated: {status_data['lastUpdate']}")
                    elif data['type'] == 'HEARTBEAT_RESPONSE':
                        print(f"   Heartbeat OK")
                    else:
                        print(f"   Data: {data['data']}")
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connection closed")
                    break
            
            print("\n✅ WebSocket test completed")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - WebSocket server not running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

async def test_status_updates():
    """Test status updates from monitoring system"""
    print("\n🔍 Testing Status Updates...")
    print("=" * 50)
    
    # Import monitoring components
    try:
        from websocket_server import get_websocket_server, update_system_status
        from monitoring_agent import MonitoringAgent, MonitoringConfig
        
        # Get WebSocket server instance
        server = get_websocket_server()
        print(f"📊 Current status: {server.system_status.status}")
        print(f"📊 Connection health: {server.system_status.connectionHealth}")
        print(f"📊 Last update: {server.system_status.lastUpdate}")
        
        # Test manual status update
        print("\n📡 Testing manual status update...")
        update_system_status("monitoring", "good")
        
        print(f"📊 Updated status: {server.system_status.status}")
        print(f"📊 Updated health: {server.system_status.connectionHealth}")
        
        # Test monitoring agent creation
        print("\n🤖 Testing monitoring agent...")
        config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=False,
            screenshot_on_input=False,
            cache_enabled=False
        )
        
        agent = MonitoringAgent(config=config)
        print(f"✅ Monitoring agent created")
        print(f"📊 Agent status: {agent.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing status updates: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 WebSocket Server Status Test")
    print("=" * 50)
    
    # Test WebSocket connection
    connection_ok = await test_websocket_connection()
    
    if connection_ok:
        # Test status updates
        await test_status_updates()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 