"""
Short Test for Continuous Monitoring

This script demonstrates continuous monitoring for a short period (30 seconds)
to show how the system works without running indefinitely.
"""

import asyncio
import sys
import os
from datetime import datetime
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from monitoring_agent import (
    MonitoringAgent,
    MonitoringConfig,
    MonitoringStatus
)
from notification_agent import NotificationConfig

async def test_continuous_monitoring():
    """Test continuous monitoring for a short period"""
    print("🚀 Testing Continuous Monitoring (30 seconds)")
    print("=" * 50)
    
    # Create configuration
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="moderate",
        enable_notifications=True,
        screenshot_on_input=False,  # Disable for testing
        cache_enabled=True,
        monitoring_interval=1.0,  # 1 second intervals
        notification_config=NotificationConfig(
            child_name="テスト子供",
            parent_name="テスト親",
            desktop_notifications=True,
            email_notifications=False,
            sms_notifications=False
        )
    )
    
    # Create monitoring agent
    agent = MonitoringAgent(config=config)
    
    # Start monitoring
    print("📊 Starting monitoring...")
    result = await agent.start_monitoring()
    
    if result['status'] != 'success':
        print(f"❌ Failed to start monitoring: {result.get('error')}")
        return
    
    print(f"✅ Monitoring started: {result['session_id']}")
    print("🔍 Monitoring keyboard input for 30 seconds...")
    print("💡 Try typing something to see the system in action!")
    print("=" * 50)
    
    # Monitor for 30 seconds
    start_time = time.time()
    last_status_time = time.time()
    
    try:
        while time.time() - start_time < 30:  # 30 seconds
            # Show status every 5 seconds
            if time.time() - last_status_time >= 5:
                status = agent.get_monitoring_status()
                stats = status.get('statistics', {})
                
                elapsed = time.time() - start_time
                remaining = 30 - elapsed
                
                print(f"\n⏱️  Status [{remaining:.0f}s remaining]:")
                print(f"   Events: {stats.get('total_events', 0)}")
                print(f"   Inputs: {stats.get('inputs_processed', 0)}")
                print(f"   Errors: {stats.get('errors', 0)}")
                
                # Show recent events
                if agent.event_history:
                    recent = agent.event_history[-1]
                    category = recent.analysis_result.category if recent.analysis_result else "unknown"
                    action = recent.judgment_result.action.value if recent.judgment_result else "unknown"
                    print(f"   Last: {recent.input_text[:20]}... → {category} → {action}")
                
                last_status_time = time.time()
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    # Stop monitoring
    print("\n🛑 Stopping monitoring...")
    stop_result = await agent.stop_monitoring()
    
    if stop_result['status'] == 'success':
        print("✅ Monitoring stopped successfully!")
        
        # Display final summary
        summary = stop_result.get('session_summary', {})
        print(f"\n📊 Final Summary:")
        print(f"   Session ID: {summary.get('session_id', 'N/A')}")
        print(f"   Total Events: {summary.get('total_events', 0)}")
        print(f"   Inputs Processed: {summary.get('inputs_processed', 0)}")
        print(f"   Uptime: {summary.get('uptime', 0):.1f} seconds")
        
        # Show final statistics
        status = agent.get_monitoring_status()
        stats = status.get('statistics', {})
        print(f"\n📈 Statistics:")
        print(f"   Screenshots: {stats.get('screenshots_taken', 0)}")
        print(f"   Analyses: {stats.get('analyses_completed', 0)}")
        print(f"   Judgments: {stats.get('judgments_made', 0)}")
        print(f"   Notifications: {stats.get('notifications_sent', 0)}")
        print(f"   Errors: {stats.get('errors', 0)}")
        print(f"   Avg Processing Time: {stats.get('average_processing_time', 0):.3f}s")
        
        # Show event history
        if agent.event_history:
            print(f"\n📋 Event History:")
            for i, event in enumerate(agent.event_history[-5:], 1):  # Last 5 events
                category = event.analysis_result.category if event.analysis_result else "unknown"
                action = event.judgment_result.action.value if event.judgment_result else "unknown"
                print(f"   {i}. {event.input_text[:30]}... → {category} → {action} ({event.processing_time:.3f}s)")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_continuous_monitoring())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!") 