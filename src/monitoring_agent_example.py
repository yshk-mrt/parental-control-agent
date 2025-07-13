"""
MonitoringAgent Usage Example

This example demonstrates how to use the AGT-001 MonitoringAgent
for parental control monitoring.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from monitoring_agent import (
    MonitoringAgent,
    MonitoringConfig,
    MonitoringStatus,
    get_global_monitoring_agent
)
from notification_agent import NotificationConfig

async def main():
    """Main example function"""
    print("🚀 MonitoringAgent Usage Example")
    print("=" * 50)
    
    # Step 1: Create configuration
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="moderate",
        enable_notifications=True,
        screenshot_on_input=False,  # Disable for example
        cache_enabled=True,
        notification_config=NotificationConfig(
            child_name="Alice",
            parent_name="Parent",
            desktop_notifications=True,
            email_notifications=False,
            sms_notifications=False
        )
    )
    
    # Step 2: Create monitoring agent
    agent = MonitoringAgent(config=config)
    print("✅ MonitoringAgent created")
    
    # Step 3: Check initial status
    status = agent.get_monitoring_status()
    print(f"📊 Initial status: {status['status']}")
    print(f"📋 Configuration: {status['config']['age_group']}, {status['config']['strictness_level']}")
    
    # Step 4: Process some example inputs
    print("\n🔍 Processing example inputs...")
    
    test_inputs = [
        "What is photosynthesis?",
        "How to study for math test",
        "Funny cat videos",
        "Science homework help"
    ]
    
    for i, input_text in enumerate(test_inputs, 1):
        print(f"\n   Example {i}: {input_text}")
        
        result = await agent.process_manual_input(input_text, None)
        
        if result["status"] == "success":
            print(f"     ✅ Category: {result['analysis']['category']}")
            print(f"     ✅ Action: {result['judgment']['action']}")
            print(f"     ✅ Confidence: {result['analysis']['confidence']:.1%}")
            print(f"     ✅ Processing time: {result['processing_time']:.3f}s")
            
            if result.get('notification'):
                print(f"     📢 Notification: {result['notification']['status']}")
        else:
            print(f"     ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Step 5: Check statistics
    print("\n📊 Final Statistics:")
    final_status = agent.get_monitoring_status()
    stats = final_status["statistics"]
    
    print(f"   Total events: {stats['total_events']}")
    print(f"   Inputs processed: {stats['inputs_processed']}")
    print(f"   Average processing time: {stats['average_processing_time']:.3f}s")
    print(f"   Errors: {stats['errors']}")
    
    # Step 6: Get recent events
    print("\n📋 Recent Events:")
    recent_events = agent.get_recent_events(limit=3)
    
    for event in recent_events:
        print(f"   {event['timestamp']}: {event['input_text'][:50]}...")
        print(f"     Category: {event['category']}, Action: {event['action']}")
    
    # Step 7: Configuration update example
    print("\n⚙️ Configuration Update Example:")
    update_result = agent.configure_monitoring(
        age_group="middle_school",
        strictness_level="strict"
    )
    
    if update_result["status"] == "success":
        print("   ✅ Configuration updated successfully")
        print(f"   New settings: {update_result['updated_config']['age_group']}, {update_result['updated_config']['strictness_level']}")
    
    print("\n🎉 MonitoringAgent example completed!")
    print("\n📖 Key Features Demonstrated:")
    print("   ✅ Agent initialization and configuration")
    print("   ✅ Manual input processing")
    print("   ✅ Analysis and judgment workflow")
    print("   ✅ Statistics and monitoring")
    print("   ✅ Event history tracking")
    print("   ✅ Runtime configuration updates")
    
    print("\n🔧 AGT-001 (Basic Agent Architecture) - FULLY OPERATIONAL")

if __name__ == "__main__":
    asyncio.run(main()) 