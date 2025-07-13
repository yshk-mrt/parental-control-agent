#!/usr/bin/env python3
"""
Test Lock Screen Integration

This script tests the integration between:
- Monitoring system
- Lock screen
- Approval manager
- WebSocket server
"""

import asyncio
import threading
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_lock_screen_only():
    """Test lock screen functionality only"""
    print("🔒 Testing Lock Screen Only...")
    
    from lock_screen import show_system_lock, unlock_system, is_system_locked, update_lock_status
    
    def on_approval():
        print("✅ Lock screen approved")
    
    def on_timeout():
        print("⏰ Lock screen timeout")
    
    def on_emergency():
        print("🚨 Emergency unlock")
    
    # Show lock screen
    show_system_lock(
        reason="Test lock screen - inappropriate content detected",
        timeout=15,  # 15 seconds for testing
        approval_callback=on_approval,
        timeout_callback=on_timeout
    )
    
    # Simulate approval after 5 seconds
    def simulate_approval():
        time.sleep(5)
        print("📱 Simulating approval...")
        update_lock_status("Parent approved! Unlocking...")
        time.sleep(2)
        unlock_system()
    
    approval_thread = threading.Thread(target=simulate_approval, daemon=True)
    approval_thread.start()
    
    # Wait for unlock
    try:
        while is_system_locked():
            time.sleep(0.5)
        print("🔓 Lock screen test completed")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        unlock_system()

def test_approval_manager():
    """Test approval manager functionality"""
    print("🔐 Testing Approval Manager...")
    
    from approval_manager import get_approval_manager, request_approval
    
    manager = get_approval_manager()
    
    # Create approval request
    request_id = request_approval(
        reason="Test approval manager - inappropriate content detected",
        content="test inappropriate content",
        application_name="Test Browser",
        confidence=0.85,
        timeout_seconds=20
    )
    
    print(f"📋 Created approval request: {request_id}")
    
    # Simulate parent approval after 8 seconds
    def simulate_approval():
        time.sleep(8)
        print("📱 Simulating parent approval...")
        success = manager.process_approval_response(request_id, True, "parent-001")
        print(f"✅ Approval processed: {success}")
    
    approval_thread = threading.Thread(target=simulate_approval, daemon=True)
    approval_thread.start()
    
    # Wait for unlock
    try:
        while manager.is_system_currently_locked():
            time.sleep(0.5)
        print("🔓 Approval manager test completed")
        print("📊 Statistics:", manager.get_statistics())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        manager.cancel_request(request_id)

def test_websocket_integration():
    """Test WebSocket server integration"""
    print("🌐 Testing WebSocket Integration...")
    
    from websocket_server import start_websocket_server, stop_websocket_server
    from approval_manager import get_approval_manager, request_approval
    
    async def websocket_test():
        # Start WebSocket server
        server = await start_websocket_server(host="localhost", port=8081)
        print("📡 WebSocket server started on port 8081")
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Create approval request (this should send WebSocket message)
        manager = get_approval_manager()
        request_id = request_approval(
            reason="Test WebSocket integration - inappropriate content detected",
            content="test content",
            application_name="Test App",
            confidence=0.9,
            timeout_seconds=15
        )
        
        print(f"📋 Created request with WebSocket: {request_id}")
        
        # Simulate parent approval after 5 seconds
        async def simulate_approval():
            await asyncio.sleep(5)
            print("📱 Simulating parent approval via WebSocket...")
            success = manager.process_approval_response(request_id, True, "parent-001")
            print(f"✅ Approval processed: {success}")
        
        # Run approval simulation
        await simulate_approval()
        
        # Wait for unlock
        while manager.is_system_currently_locked():
            await asyncio.sleep(0.5)
        
        print("🔓 WebSocket integration test completed")
        
        # Stop WebSocket server
        await stop_websocket_server()
        print("📡 WebSocket server stopped")
    
    # Run async test
    try:
        asyncio.run(websocket_test())
    except KeyboardInterrupt:
        print("\n🛑 WebSocket test interrupted")

def test_monitoring_integration():
    """Test monitoring system integration"""
    print("🔍 Testing Monitoring System Integration...")
    
    from monitoring_agent import MonitoringAgent, MonitoringConfig
    from judgment_engine import JudgmentAction
    
    # Create monitoring agent
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="strict",
        enable_notifications=True,
        screenshot_on_input=False,  # Disable for testing
        cache_enabled=False
    )
    
    agent = MonitoringAgent(config=config)
    
    print("🤖 Monitoring agent created")
    
    # Test manual input processing (simulates inappropriate content detection)
    async def test_inappropriate_content():
        print("🧪 Testing inappropriate content detection...")
        
        # This should trigger the lock screen
        result = await agent.process_manual_input(
            input_text="inappropriate test content",
            screenshot_path=None
        )
        
        print(f"📊 Processing result: {result}")
        
        # Check if system is locked
        from approval_manager import get_approval_manager
        manager = get_approval_manager()
        
        if manager.is_system_currently_locked():
            print("🔒 System is locked - test successful!")
            
            # Simulate approval after 3 seconds
            await asyncio.sleep(3)
            
            # Get active requests
            active_requests = manager.get_active_requests()
            if active_requests:
                request_id = active_requests[0].id
                print(f"📱 Approving request: {request_id}")
                manager.process_approval_response(request_id, True, "parent-001")
                
                # Wait for unlock
                while manager.is_system_currently_locked():
                    await asyncio.sleep(0.5)
                
                print("🔓 System unlocked - integration test completed")
            else:
                print("❌ No active requests found")
        else:
            print("⚠️ System not locked - check content analysis")
    
    try:
        asyncio.run(test_inappropriate_content())
        print("📊 Final statistics:", get_approval_manager().get_statistics())
    except Exception as e:
        print(f"❌ Error in monitoring integration test: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Monitoring test interrupted")

def main():
    """Main test function"""
    print("🧪 Lock Screen Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Lock Screen Only", test_lock_screen_only),
        ("Approval Manager", test_approval_manager),
        ("WebSocket Integration", test_websocket_integration),
        ("Monitoring Integration", test_monitoring_integration)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
            print(f"✅ {test_name} test completed successfully")
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
        except KeyboardInterrupt:
            print(f"\n🛑 {test_name} test interrupted")
            break
        
        print(f"{'='*50}")
        
        # Wait between tests
        time.sleep(2)
    
    print("\n🏁 All tests completed!")

if __name__ == "__main__":
    main() 