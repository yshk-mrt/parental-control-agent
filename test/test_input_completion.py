#!/usr/bin/env python3
"""
Test Input Completion Detection

This script tests the input completion logic step by step to identify where it's getting stuck.
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from key import get_keylogger_instance, get_current_input_tool
from monitoring_agent import MonitoringAgent, MonitoringConfig
from analysis_agent import AnalysisAgent

def test_keylogger_completion():
    """Test keylogger input completion detection"""
    print("🔍 Testing Keylogger Input Completion")
    print("=" * 50)
    
    # Mock tool context
    class MockToolContext:
        def __init__(self):
            self.state = {}
    
    try:
        # Start keylogger
        keylogger = get_keylogger_instance()
        keylogger.start()
        
        print("✅ Keylogger started")
        print("💡 Type 'I will kill you' and press Enter")
        print("💡 Press Ctrl+C to stop")
        
        context = MockToolContext()
        
        while True:
            # Check input status
            input_status = get_current_input_tool.func(context)
            
            if input_status.get('status') == 'success':
                buffer = input_status.get('buffer', {})
                text = buffer.get('text', '')
                length = buffer.get('length', 0)
                enter_pressed = buffer.get('enter_pressed', False)
                is_complete = buffer.get('is_complete', False)
                
                if length > 0:
                    print(f"\n📝 Current input: '{text}'")
                    print(f"   Length: {length}")
                    print(f"   Enter pressed: {enter_pressed}")
                    print(f"   Is complete: {is_complete}")
                    
                    if is_complete:
                        print("✅ Input completion detected!")
                        print("🔄 Testing analysis...")
                        
                        # Test analysis
                        analysis_agent = AnalysisAgent(
                            age_group="elementary",
                            strictness_level="moderate",
                            cache_enabled=False
                        )
                        
                        async def test_analysis():
                            try:
                                print("📊 Starting analysis...")
                                result = await analysis_agent.analyze_input_context(
                                    text, 
                                    screenshot_path=None,
                                    force_analysis=True
                                )
                                
                                if result:
                                    print(f"✅ Analysis completed:")
                                    print(f"   Category: {result.category}")
                                    print(f"   Confidence: {result.confidence:.1%}")
                                    print(f"   Safety concerns: {result.safety_concerns}")
                                    return True
                                else:
                                    print("❌ Analysis returned None")
                                    return False
                                    
                            except Exception as e:
                                print(f"❌ Analysis error: {e}")
                                return False
                        
                        # Run analysis test
                        analysis_success = asyncio.run(test_analysis())
                        
                        if analysis_success:
                            print("🎉 Analysis test passed!")
                        else:
                            print("💥 Analysis test failed!")
                        
                        # Clear buffer and continue
                        keylogger.clear_buffer()
                        print("🧹 Buffer cleared, ready for next input")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        keylogger.stop()
        print("✅ Keylogger stopped")

def test_monitoring_agent_step_by_step():
    """Test monitoring agent step by step"""
    print("\n🤖 Testing Monitoring Agent Step by Step")
    print("=" * 50)
    
    try:
        # Create monitoring agent
        config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=False,
            screenshot_on_input=False,
            cache_enabled=False,
            monitoring_interval=0.1
        )
        
        agent = MonitoringAgent(config=config)
        print("✅ Monitoring agent created")
        
        # Test manual input processing
        async def test_manual_processing():
            test_inputs = [
                "hello",
                "I will kill you",
                "homework help",
                "violent content test"
            ]
            
            for test_input in test_inputs:
                print(f"\n🧪 Testing input: '{test_input}'")
                
                try:
                    result = await agent.process_manual_input(test_input)
                    
                    if result.get('status') == 'success':
                        analysis = result.get('analysis', {})
                        judgment = result.get('judgment', {})
                        
                        print(f"✅ Processing successful:")
                        print(f"   Category: {analysis.get('category', 'unknown')}")
                        print(f"   Confidence: {analysis.get('confidence', 0):.1%}")
                        print(f"   Action: {judgment.get('action', 'unknown')}")
                        print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
                        
                        if judgment.get('action') == 'block':
                            print("🔒 This input would trigger lock screen")
                        
                    else:
                        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"💥 Exception during processing: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Run manual processing test
        asyncio.run(test_manual_processing())
        
    except Exception as e:
        print(f"❌ Error in monitoring agent test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 Input Completion Debug Test")
    print("=" * 50)
    
    choice = input("Choose test:\n1. Keylogger completion test\n2. Monitoring agent step-by-step\n3. Both\nEnter choice (1-3): ")
    
    if choice == "1":
        test_keylogger_completion()
    elif choice == "2":
        test_monitoring_agent_step_by_step()
    elif choice == "3":
        test_monitoring_agent_step_by_step()
        test_keylogger_completion()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 