#!/usr/bin/env python3
"""
Test script for Cocoa overlay functionality

This script tests the native macOS Cocoa overlay implementation
to ensure it works correctly for the parental control lock screen.
"""

import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cocoa_overlay():
    """Test the Cocoa overlay functionality"""
    print("Testing Cocoa Overlay for Parental Control Lock Screen")
    print("=" * 60)
    
    # Check if running on macOS
    if sys.platform != 'darwin':
        print("❌ This test requires macOS")
        return False
    
    # Try to import the overlay module
    try:
        import cocoa_overlay
        print("✅ Cocoa overlay module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import cocoa_overlay: {e}")
        print("💡 Install dependencies with: pip install PyObjC-framework-Cocoa PyObjC-framework-Quartz")
        return False
    
    # Check if Cocoa is available
    if not cocoa_overlay.is_overlay_available():
        print("❌ Cocoa overlay not available")
        return False
    
    print("✅ Cocoa overlay is available")
    
    # Test 1: Basic overlay display
    print("\n🧪 Test 1: Basic overlay display (5 seconds)")
    start_time = time.time()
    
    def unlock_after_5_seconds():
        return time.time() - start_time > 5
    
    try:
        cocoa_overlay.show_overlay(
            "Test: Basic overlay display - will unlock in 5 seconds",
            unlock_after_5_seconds
        )
        
        # Wait for overlay to auto-unlock
        while cocoa_overlay._overlay_instance and cocoa_overlay._overlay_instance.is_showing:
            time.sleep(0.1)
        
        print("✅ Test 1 passed - Basic overlay display works")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Status updates
    print("\n🧪 Test 2: Status updates (10 seconds)")
    start_time = time.time()
    
    def unlock_after_10_seconds():
        return time.time() - start_time > 10
    
    try:
        cocoa_overlay.show_overlay(
            "Test: Status updates - watch the status change",
            unlock_after_10_seconds
        )
        
        # Update status periodically
        for i in range(10):
            time.sleep(1)
            remaining = 10 - i
            cocoa_overlay.update_overlay_status(f"Status update test - {remaining} seconds remaining")
            
            if not cocoa_overlay._overlay_instance or not cocoa_overlay._overlay_instance.is_showing:
                break
        
        print("✅ Test 2 passed - Status updates work")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    # Test 3: Manual unlock
    print("\n🧪 Test 3: Manual unlock (press Ctrl+C to unlock)")
    
    def never_unlock():
        return False
    
    try:
        cocoa_overlay.show_overlay(
            "Test: Manual unlock - press Ctrl+C to unlock",
            never_unlock
        )
        
        # Wait for manual interrupt
        try:
            while cocoa_overlay._overlay_instance and cocoa_overlay._overlay_instance.is_showing:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🔓 Manual unlock triggered")
            cocoa_overlay.hide_overlay()
        
        print("✅ Test 3 passed - Manual unlock works")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Cocoa overlay is working correctly")
    return True

def test_integration_with_lock_screen():
    """Test integration with the lock screen system"""
    print("\n" + "=" * 60)
    print("Testing Integration with Lock Screen System")
    print("=" * 60)
    
    try:
        from lock_screen import SystemLockScreen
        print("✅ Lock screen module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import lock_screen: {e}")
        return False
    
    # Test lock screen with Cocoa overlay
    print("\n🧪 Testing lock screen with Cocoa overlay (5 seconds)")
    
    lock_screen = SystemLockScreen()
    
    def approval_callback():
        print("✅ Approval callback triggered")
    
    def timeout_callback():
        print("⏰ Timeout callback triggered")
    
    try:
        lock_screen.show_lock_screen(
            reason="Integration test - Cocoa overlay with lock screen system",
            timeout=5,
            approval_callback=approval_callback,
            timeout_callback=timeout_callback
        )
        
        # Wait for timeout
        time.sleep(6)
        
        # Check if unlocked
        if not lock_screen.is_screen_locked():
            print("✅ Integration test passed - Lock screen with Cocoa overlay works")
            return True
        else:
            print("❌ Integration test failed - Lock screen still locked")
            return False
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Parental Control System - Cocoa Overlay Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test Cocoa overlay functionality
    if not test_cocoa_overlay():
        success = False
    
    # Test integration with lock screen
    if not test_integration_with_lock_screen():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Cocoa overlay is ready for use.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 