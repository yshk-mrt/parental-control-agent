#!/usr/bin/env python3
"""
Test script to verify the asyncio fix works correctly
"""

import asyncio
import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from monitoring_agent import MonitoringAgent, MonitoringConfig
from key import get_keylogger_instance

def test_asyncio_fix():
    """Test that the asyncio fix resolves the 30+ second delay"""
    
    print("🧪 Testing asyncio fix for 30+ second delay...")
    
    # Create configuration
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="moderate",
        enable_notifications=True,
        screenshot_on_input=True,
        cache_enabled=True,
        monitoring_interval=0.5
    )
    
    # Create monitoring agent
    agent = MonitoringAgent(config)
    
    # Simulate the problematic workflow
    print("\n🔄 Simulating the monitoring loop workflow...")
    
    # Mock input status like the monitoring loop would get
    mock_input_status = {
        'input_complete': True,
        'buffer': {
            'text': 'fuck',
            'enter_pressed': True,
            'is_complete': True
        }
    }
    
    # Test the async processing in a thread context (like the monitoring loop)
    def thread_worker():
        """Worker function that runs in a thread like the monitoring loop"""
        print("🧵 Starting thread worker...")
        
        start_time = time.time()
        
        try:
            # This is the problematic pattern from the original code
            # Create a new event loop for this thread if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function in the current loop
            loop.run_until_complete(agent._process_input_event(mock_input_status))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"⏱️  Thread processing time: {processing_time:.2f}s")
            
            if processing_time > 5:
                print(f"❌ FAILED: Processing took {processing_time:.2f}s - still too slow!")
                return False
            else:
                print(f"✅ SUCCESS: Processing time is acceptable: {processing_time:.2f}s")
                return True
                
        except Exception as e:
            print(f"❌ ERROR in thread worker: {e}")
            return False
    
    # Run the thread worker
    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_asyncio_fix() 