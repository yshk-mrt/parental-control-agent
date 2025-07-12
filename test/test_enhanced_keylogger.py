#!/usr/bin/env python3
"""
Test script for Enhanced Keylogger ADK FunctionTool
"""

import os
import sys
import asyncio
import warnings
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from key import (
    start_keylogger_tool,
    stop_keylogger_tool,
    get_current_input_tool,
    clear_input_buffer_tool,
    create_monitoring_agent
)
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Load environment variables
load_dotenv()

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Basic logging setup
import logging
logging.basicConfig(level=logging.INFO)

def test_keylogger_tools():
    """Test the individual keylogger tools"""
    print("🔧 Testing Enhanced Keylogger Tools...")
    
    try:
        # Mock ToolContext for testing
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        mock_context = MockToolContext()
        
        # Test 1: Start keylogger
        print("\n📤 Testing start_keylogger...")
        result = start_keylogger_tool.func(mock_context)
        print(f"✅ Start result: {result}")
        
        # Test 2: Get current input
        print("\n📤 Testing get_current_input...")
        result = get_current_input_tool.func(mock_context)
        print(f"✅ Get input result: {result}")
        
        # Test 3: Clear buffer
        print("\n📤 Testing clear_input_buffer...")
        result = clear_input_buffer_tool.func(mock_context)
        print(f"✅ Clear buffer result: {result}")
        
        # Test 4: Stop keylogger
        print("\n📤 Testing stop_keylogger...")
        result = stop_keylogger_tool.func(mock_context)
        print(f"✅ Stop result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool test error: {e}")
        return False

async def test_monitoring_agent():
    """Test the monitoring agent with keylogger tools"""
    print("\n🤖 Testing Monitoring Agent...")
    
    try:
        # Create monitoring agent
        agent = create_monitoring_agent()
        print(f"✅ Agent created: {agent.name}")
        
        # Create session service
        session_service = InMemorySessionService()
        
        # Create runner
        runner = Runner(
            agent=agent,
            session_service=session_service,
            app_name="enhanced_keylogger_test"
        )
        
        print("✅ Runner created successfully!")
        
        # Create session
        session = await session_service.create_session(
            app_name="enhanced_keylogger_test",
            user_id="test_user",
            session_id="test_session"
        )
        
        print(f"✅ Session created: {session.id}")
        
        # Test simple query
        print("\n📤 Testing agent query...")
        content = types.Content(
            role='user',
            parts=[types.Part(text="Start the keylogger and check its status")]
        )
        
        # Run the agent
        events = runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=content
        )
        
        print("📥 Agent responses:")
        async for event in events:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print(f"🤖 Agent: {final_response}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test error: {e}")
        return False

def test_input_buffer_logic():
    """Test the input buffer logic"""
    print("\n📊 Testing Input Buffer Logic...")
    
    try:
        from key import InputBuffer
        
        # Test 1: Basic buffer operations
        buffer = InputBuffer()
        print("✅ Buffer created")
        
        # Test 2: Add characters
        buffer.add_char('H')
        buffer.add_char('e')
        buffer.add_char('l')
        buffer.add_char('l')
        buffer.add_char('o')
        
        summary = buffer.get_summary()
        print(f"✅ Buffer after 'Hello': {summary}")
        
        # Test 3: Check substantial input
        for i in range(10):
            buffer.add_char(str(i))
        
        print(f"✅ Is substantial: {buffer.is_substantial_input()}")
        print(f"✅ Is complete: {buffer.is_input_complete()}")
        
        # Test 4: Enter key press
        buffer.mark_enter_pressed()
        print(f"✅ After Enter press - Is complete: {buffer.is_input_complete()}")
        
        # Test 5: Clear buffer
        buffer.clear()
        summary = buffer.get_summary()
        print(f"✅ Buffer after clear: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Buffer test error: {e}")
        return False

def test_keylogger_class():
    """Test the EnhancedKeylogger class (without actually starting it)"""
    print("\n🔐 Testing EnhancedKeylogger Class...")
    
    try:
        from key import EnhancedKeylogger
        
        # Test 1: Create keylogger
        keylogger = EnhancedKeylogger()
        print("✅ Keylogger created")
        
        # Test 2: Check initial state
        print(f"✅ Initial running state: {keylogger.is_running}")
        print(f"✅ Initial buffer: {keylogger.get_buffered_input()}")
        
        # Test 3: Test completion callback
        callback_called = False
        def test_callback(buffer_info):
            nonlocal callback_called
            callback_called = True
            print(f"✅ Callback triggered: {buffer_info}")
        
        keylogger.add_completion_callback(test_callback)
        print("✅ Completion callback added")
        
        # Test 4: Manual buffer manipulation
        keylogger.buffer.add_char('T')
        keylogger.buffer.add_char('e')
        keylogger.buffer.add_char('s')
        keylogger.buffer.add_char('t')
        keylogger.buffer.mark_enter_pressed()
        
        # Trigger completion check manually
        keylogger._check_completion()
        
        print(f"✅ Callback called: {callback_called}")
        
        return True
        
    except Exception as e:
        print(f"❌ Keylogger class test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Keylogger Test Suite\n")
    
    # Test 1: Input buffer logic
    buffer_ok = test_input_buffer_logic()
    
    # Test 2: Keylogger class
    keylogger_ok = test_keylogger_class()
    
    # Test 3: Individual tools
    tools_ok = test_keylogger_tools()
    
    # Test 4: Monitoring agent
    agent_ok = await test_monitoring_agent()
    
    # Summary
    print("\n" + "="*50)
    print("📊 ENHANCED KEYLOGGER TEST SUMMARY")
    print("="*50)
    
    tests = [
        ("Input Buffer Logic", buffer_ok),
        ("Keylogger Class", keylogger_ok),
        ("Individual Tools", tools_ok),
        ("Monitoring Agent", agent_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All Enhanced Keylogger tests passed!")
        print("✅ Ready to proceed with Screen Capture Tool development!")
    elif passed >= 3:
        print("\n✅ Core Enhanced Keylogger functionality is working!")
        print("⚠️  Some advanced features may need attention.")
    else:
        print("\n❌ Enhanced Keylogger integration needs troubleshooting.")
    
    return passed >= 3

if __name__ == "__main__":
    asyncio.run(main()) 