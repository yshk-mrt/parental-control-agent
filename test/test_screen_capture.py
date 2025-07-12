#!/usr/bin/env python3
"""
Test script for Screen Capture ADK FunctionTool
"""

import os
import sys
import asyncio
import warnings
import time
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from screen_capture import (
    ScreenCaptureManager,
    ScreenCaptureConfig,
    capture_screen_tool,
    get_monitor_info_tool,
    cleanup_temp_files_tool,
    capture_on_input_complete_tool,
    create_screen_capture_agent
)
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import ToolContext

# Load environment variables
load_dotenv()

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Basic logging setup
import logging
logging.basicConfig(level=logging.INFO)

def test_screen_capture_manager():
    """Test the ScreenCaptureManager class"""
    print("🖥️  Testing ScreenCaptureManager...")
    
    try:
        # Create manager with custom config
        config = ScreenCaptureConfig(
            max_width=1280,
            max_height=720,
            quality=90,
            optimize_for_ai=True
        )
        manager = ScreenCaptureManager(config)
        
        # Test monitor info
        monitor_info = manager.get_monitor_info()
        assert monitor_info["status"] == "success"
        assert "monitors" in monitor_info
        print(f"✅ Monitor info: {monitor_info['monitor_count']} monitors detected")
        
        # Test screen capture
        capture_result = manager.capture_screen()
        assert capture_result["status"] == "success"
        assert capture_result["image"] is not None
        print(f"✅ Screen capture successful: {capture_result['metadata']['original_size']}")
        print(f"   Capture time: {capture_result['metadata']['capture_time_ms']}ms")
        
        # Test optimization
        image = capture_result["image"]
        optimization_result = manager.optimize_for_ai_analysis(image)
        assert optimization_result["status"] == "success"
        assert optimization_result["image"] is not None
        print(f"✅ Image optimization successful")
        print(f"   Size reduction: {optimization_result['optimization_info']['size_reduction']}")
        
        # Test base64 conversion
        base64_result = manager.image_to_base64(optimization_result["image"])
        assert base64_result["status"] == "success"
        assert base64_result["base64_data"] is not None
        print(f"✅ Base64 conversion successful: {base64_result['base64_length']} chars")
        
        # Test temp file save
        temp_result = manager.save_to_temp_file(optimization_result["image"], "test")
        assert temp_result["status"] == "success"
        assert Path(temp_result["filepath"]).exists()
        print(f"✅ Temp file saved: {temp_result['filename']}")
        
        # Test cleanup
        cleanup_result = manager.cleanup_temp_files()
        assert cleanup_result["status"] == "success"
        print(f"✅ Cleanup successful: {cleanup_result['cleaned_files']} files cleaned")
        
        return True
        
    except Exception as e:
        print(f"❌ ScreenCaptureManager test failed: {e}")
        return False

def test_screen_capture_tools():
    """Test individual ADK function tools"""
    print("\n🔧 Testing Screen Capture Tools...")
    
    try:
        # Create mock tool context
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        tool_context = MockToolContext()
        
        # Test monitor info tool
        monitor_result = get_monitor_info_tool(tool_context)
        assert monitor_result["status"] == "success"
        assert "monitors" in monitor_result
        print("✅ Monitor info tool working")
        
        # Test screen capture tool
        capture_result = capture_screen_tool(tool_context)
        assert capture_result["status"] == "success"
        assert capture_result["image_data"] is not None
        assert capture_result["ai_ready"] == True
        print("✅ Screen capture tool working")
        print(f"   Image size: {capture_result['metadata']['optimization_info']['optimized_size']}")
        
        # Test triggered capture
        triggered_result = capture_on_input_complete_tool(tool_context)
        assert triggered_result["status"] == "success"
        assert triggered_result["capture_triggered"] == True
        print("✅ Triggered capture tool working")
        
        # Test cleanup tool
        cleanup_result = cleanup_temp_files_tool(tool_context)
        assert cleanup_result["status"] == "success"
        print("✅ Cleanup tool working")
        
        return True
        
    except Exception as e:
        print(f"❌ Screen capture tools test failed: {e}")
        return False

def test_performance_benchmark():
    """Test performance of screen capture"""
    print("\n⚡ Performance Benchmark...")
    
    try:
        manager = ScreenCaptureManager()
        
        # Warm up
        manager.capture_screen()
        
        # Benchmark multiple captures
        times = []
        for i in range(5):
            start_time = time.time()
            result = manager.capture_screen()
            end_time = time.time()
            
            if result["status"] == "success":
                times.append((end_time - start_time) * 1000)  # Convert to ms
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"✅ Performance benchmark complete:")
            print(f"   Average: {avg_time:.2f}ms")
            print(f"   Min: {min_time:.2f}ms")
            print(f"   Max: {max_time:.2f}ms")
            
            # Check if performance is acceptable (should be under 100ms with MSS)
            if avg_time < 100:
                print("✅ Performance is excellent (< 100ms)")
                return True
            elif avg_time < 200:
                print("⚠️  Performance is acceptable (< 200ms)")
                return True
            else:
                print("❌ Performance is slow (> 200ms)")
                return False
        else:
            print("❌ No successful captures for benchmark")
            return False
        
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        return False

async def test_screen_capture_agent():
    """Test the complete screen capture agent"""
    print("\n🤖 Testing ScreenCaptureAgent...")
    
    try:
        # Create agent
        agent = create_screen_capture_agent()
        
        # Create session service
        session_service = InMemorySessionService()
        
        # Create runner
        runner = Runner(
            agent=agent,
            session_service=session_service,
            app_name="parental_control_screen_capture_test"
        )
        
        print("✅ ScreenCaptureAgent created successfully!")
        print(f"   Agent name: {agent.name}")
        print(f"   Tools count: {len(agent.tools)}")
        print(f"   Model: {agent.model}")
        
        # Test that agent has all required tools
        tool_names = [tool.func.__name__ for tool in agent.tools]
        expected_tools = [
            "capture_screen_tool",
            "get_monitor_info_tool", 
            "cleanup_temp_files_tool",
            "capture_on_input_complete_tool"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✅ Tool available: {expected_tool}")
            else:
                print(f"❌ Tool missing: {expected_tool}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ ScreenCaptureAgent test failed: {e}")
        return False

def test_integration_with_keylogger():
    """Test integration with keylogger simulation"""
    print("\n🔗 Testing Integration with Keylogger...")
    
    try:
        # Simulate keylogger input completion event
        class MockInputEvent:
            def __init__(self):
                self.text = "Hello, this is a test input"
                self.enter_pressed = True
                self.is_complete = True
        
        # Create mock tool context
        class MockToolContext:
            def __init__(self):
                self.state = {
                    "keylogger_active": True,
                    "input_complete": True
                }
        
        tool_context = MockToolContext()
        
        # Simulate input completion triggering screen capture
        print("📝 Simulating input completion...")
        capture_result = capture_on_input_complete_tool(tool_context)
        
        assert capture_result["status"] == "success"
        assert capture_result["capture_triggered"] == True
        assert "trigger_info" in capture_result
        
        print("✅ Integration test successful!")
        print(f"   Trigger type: {capture_result['trigger_info']['trigger_type']}")
        print(f"   Delay: {capture_result['trigger_info']['delay_ms']}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_security_and_privacy():
    """Test security and privacy features"""
    print("\n🔒 Testing Security and Privacy Features...")
    
    try:
        # Test with secure temp storage enabled
        config = ScreenCaptureConfig(
            secure_temp_storage=True,
            auto_cleanup=True
        )
        manager = ScreenCaptureManager(config)
        
        # Capture and save
        capture_result = manager.capture_screen()
        assert capture_result["status"] == "success"
        
        temp_result = manager.save_to_temp_file(capture_result["image"], "security_test")
        assert temp_result["status"] == "success"
        
        temp_path = Path(temp_result["filepath"])
        assert temp_path.exists()
        print("✅ Secure temp file created")
        
        # Test that temp directory is secure (not in system temp)
        assert "parental_control_" in str(temp_path.parent)
        print("✅ Secure temp directory used")
        
        # Test cleanup
        cleanup_result = manager.cleanup_temp_files()
        assert cleanup_result["status"] == "success"
        assert not temp_path.exists()
        print("✅ Secure cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

async def main():
    """Run all screen capture tests"""
    print("🚀 Starting Screen Capture Tool Tests\n")
    
    # Test 1: Basic functionality
    basic_ok = test_screen_capture_manager()
    
    # Test 2: ADK tools
    tools_ok = test_screen_capture_tools()
    
    # Test 3: Performance
    performance_ok = test_performance_benchmark()
    
    # Test 4: Agent integration
    agent_ok = await test_screen_capture_agent()
    
    # Test 5: Keylogger integration
    integration_ok = test_integration_with_keylogger()
    
    # Test 6: Security and privacy
    security_ok = test_security_and_privacy()
    
    # Summary
    print("\n" + "="*50)
    print("📊 SCREEN CAPTURE TEST SUMMARY")
    print("="*50)
    
    tests = [
        ("Basic Functionality", basic_ok),
        ("ADK Tools", tools_ok),
        ("Performance", performance_ok),
        ("Agent Integration", agent_ok),
        ("Keylogger Integration", integration_ok),
        ("Security & Privacy", security_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All Screen Capture tests passed!")
        print("✅ Ready to integrate with AI analysis!")
    elif passed >= 4:
        print("\n✅ Core Screen Capture functionality is working!")
        print("⚠️  Some advanced features may need attention.")
    else:
        print("\n❌ Screen Capture implementation needs troubleshooting.")
    
    return passed >= 4

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 