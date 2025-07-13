#!/usr/bin/env python3
"""
Test script to verify monitoring system works without screenshot capture
"""

import asyncio
import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from monitoring_agent import MonitoringAgent, MonitoringConfig

async def test_monitoring_without_screenshot():
    """Test the monitoring system without screenshot capture"""
    
    print("🧪 Testing monitoring system without screenshot capture...")
    
    # Create configuration with screenshot disabled
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="moderate",
        enable_notifications=True,
        screenshot_on_input=False,  # Disable screenshot
        cache_enabled=True,
        monitoring_interval=0.5
    )
    
    # Create monitoring agent
    agent = MonitoringAgent(config)
    
    # Start monitoring
    print("🚀 Starting monitoring...")
    start_result = await agent.start_monitoring()
    print(f"✅ Monitoring started: {start_result}")
    
    # Test manual input processing
    print("\n🧪 Testing manual input processing...")
    
    test_inputs = [
        "hello world",
        "fuck",
        "this is a test",
        "shit happens"
    ]
    
    for test_input in test_inputs:
        print(f"\n📝 Testing input: '{test_input}'")
        
        start_time = time.time()
        result = await agent.process_manual_input(test_input)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f}s")
        print(f"📊 Result: {result}")
        
        if processing_time > 5:
            print(f"⚠️  WARNING: Processing took {processing_time:.2f}s - this is too slow!")
        else:
            print(f"✅ Processing time is acceptable: {processing_time:.2f}s")
    
    # Stop monitoring
    print("\n🛑 Stopping monitoring...")
    stop_result = await agent.stop_monitoring()
    print(f"✅ Monitoring stopped: {stop_result}")

if __name__ == "__main__":
    asyncio.run(test_monitoring_without_screenshot()) 