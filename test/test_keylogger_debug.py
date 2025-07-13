#!/usr/bin/env python3
"""
Debug script to test keylogger functionality directly
"""

import sys
import os
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from key import EnhancedKeylogger, get_keylogger_instance

def test_keylogger_direct():
    """Test keylogger directly without ADK wrapper"""
    print("🔍 Testing Enhanced Keylogger Directly")
    print("=" * 50)
    
    try:
        # Create keylogger instance
        print("📊 Creating keylogger instance...")
        keylogger = EnhancedKeylogger()
        print("✅ Keylogger instance created")
        
        # Test if we can start it
        print("🚀 Starting keylogger...")
        keylogger.start()
        
        if keylogger.is_running:
            print("✅ Keylogger started successfully!")
            print("💡 Type something and press Enter to test...")
            print("💡 Press ESC to stop")
            
            # Monitor for 10 seconds
            start_time = time.time()
            while time.time() - start_time < 10 and keylogger.is_running:
                buffer_info = keylogger.get_buffered_input()
                
                if buffer_info['length'] > 0:
                    print(f"📝 Buffer: {buffer_info['text'][:50]}...")
                    print(f"   Length: {buffer_info['length']}")
                    print(f"   Complete: {buffer_info['is_complete']}")
                    
                    if buffer_info['is_complete']:
                        print("✅ Input complete detected!")
                        keylogger.clear_buffer()
                        print("🧹 Buffer cleared")
                
                time.sleep(0.5)
            
            print("🛑 Stopping keylogger...")
            keylogger.stop()
            print("✅ Keylogger stopped")
            
        else:
            print("❌ Failed to start keylogger")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_keylogger_via_tools():
    """Test keylogger via ADK tools"""
    print("\n🔍 Testing Keylogger via ADK Tools")
    print("=" * 50)
    
    try:
        from key import start_keylogger, stop_keylogger, get_current_input, clear_input_buffer
        
        # Create mock tool context
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        context = MockToolContext()
        
        print("🚀 Starting keylogger via tool...")
        result = start_keylogger(context)
        print(f"Result: {result}")
        
        if result.get('status') == 'success':
            print("✅ Keylogger started via tool!")
            
            # Test getting current input
            print("📊 Testing get_current_input...")
            input_result = get_current_input(context)
            print(f"Input result: {input_result}")
            
            # Test clearing buffer
            print("🧹 Testing clear_input_buffer...")
            clear_result = clear_input_buffer(context)
            print(f"Clear result: {clear_result}")
            
            # Stop keylogger
            print("🛑 Stopping keylogger...")
            stop_result = stop_keylogger(context)
            print(f"Stop result: {stop_result}")
            
            return True
        else:
            print(f"❌ Failed to start keylogger: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Enhanced Keylogger Debug Test")
    print("=" * 50)
    
    # Test 1: Direct keylogger test
    success1 = test_keylogger_direct()
    
    # Test 2: ADK tools test
    success2 = test_keylogger_via_tools()
    
    print("\n📊 Summary:")
    print(f"   Direct test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   ADK tools test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Keylogger is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 