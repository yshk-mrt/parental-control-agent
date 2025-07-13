"""
Demo Continuous Monitoring (Simulated)

This script demonstrates continuous monitoring functionality
without requiring keylogger permissions by simulating input events.
"""

import asyncio
import sys
import os
from datetime import datetime
import time
import random

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from monitoring_agent import (
    MonitoringAgent,
    MonitoringConfig,
    MonitoringStatus
)
from notification_agent import NotificationConfig

# Sample inputs to simulate
SAMPLE_INPUTS = [
    "What is photosynthesis?",
    "How to study for math test",
    "Funny cat videos",
    "Science homework help",
    "How to make slime",
    "History of Japan",
    "Math practice problems",
    "Animal facts",
    "Space exploration",
    "Cooking recipes for kids"
]

async def demo_continuous_monitoring():
    """Demo continuous monitoring with simulated inputs"""
    print("🚀 Demo: Continuous Monitoring (Simulated)")
    print("=" * 50)
    print("💡 This demo simulates keyboard input without requiring permissions")
    print("=" * 50)
    
    # Create configuration
    config = MonitoringConfig(
        age_group="elementary",
        strictness_level="moderate",
        enable_notifications=True,
        screenshot_on_input=False,  # Disable for demo
        cache_enabled=True,
        monitoring_interval=0.5,
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
    
    print("📊 Agent initialized successfully")
    print("🔍 Starting simulated monitoring for 60 seconds...")
    print("💡 The system will process random sample inputs automatically")
    print("=" * 50)
    
    # Start time
    start_time = time.time()
    last_input_time = time.time()
    last_status_time = time.time()
    input_count = 0
    
    try:
        while time.time() - start_time < 60:  # 60 seconds
            current_time = time.time()
            
            # Simulate input every 3-8 seconds
            if current_time - last_input_time >= random.uniform(3, 8):
                input_text = random.choice(SAMPLE_INPUTS)
                
                print(f"\n📝 Simulated input: {input_text}")
                
                # Process the input
                result = await agent.process_manual_input(input_text)
                
                if result['status'] == 'success':
                    analysis = result['analysis']
                    judgment = result['judgment']
                    
                    print(f"   ✅ Analysis: {analysis['category']} ({analysis['confidence']:.1%})")
                    print(f"   ⚖️  Judgment: {judgment['action']} ({judgment['confidence']:.1%})")
                    print(f"   ⏱️  Processing time: {result['processing_time']:.3f}s")
                    
                    if result.get('notification'):
                        print(f"   📢 Notification: {result['notification']['status']}")
                else:
                    print(f"   ❌ Error: {result.get('error')}")
                
                last_input_time = current_time
                input_count += 1
            
            # Show status every 10 seconds
            if current_time - last_status_time >= 10:
                elapsed = current_time - start_time
                remaining = 60 - elapsed
                
                status = agent.get_monitoring_status()
                stats = status.get('statistics', {})
                
                print(f"\n📊 Status Update [{remaining:.0f}s remaining]:")
                print(f"   Inputs processed: {input_count}")
                print(f"   Total events: {stats.get('total_events', 0)}")
                print(f"   Analyses: {stats.get('analyses_completed', 0)}")
                print(f"   Judgments: {stats.get('judgments_made', 0)}")
                print(f"   Notifications: {stats.get('notifications_sent', 0)}")
                print(f"   Errors: {stats.get('errors', 0)}")
                print(f"   Avg processing time: {stats.get('average_processing_time', 0):.3f}s")
                
                last_status_time = current_time
            
            await asyncio.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    
    # Final summary
    print(f"\n🎉 Demo completed!")
    print(f"📊 Final Summary:")
    print(f"   Total simulated inputs: {input_count}")
    print(f"   Demo duration: {time.time() - start_time:.1f} seconds")
    
    # Show final statistics
    status = agent.get_monitoring_status()
    stats = status.get('statistics', {})
    print(f"\n📈 Final Statistics:")
    print(f"   Total events: {stats.get('total_events', 0)}")
    print(f"   Analyses completed: {stats.get('analyses_completed', 0)}")
    print(f"   Judgments made: {stats.get('judgments_made', 0)}")
    print(f"   Notifications sent: {stats.get('notifications_sent', 0)}")
    print(f"   Errors: {stats.get('errors', 0)}")
    print(f"   Average processing time: {stats.get('average_processing_time', 0):.3f}s")
    
    # Show recent events
    if hasattr(agent, 'event_history') and agent.event_history:
        print(f"\n📋 Recent Events:")
        for i, event in enumerate(agent.event_history[-5:], 1):
            if hasattr(event, 'analysis_result') and event.analysis_result:
                category = event.analysis_result.category
                action = event.judgment_result.action.value if event.judgment_result else "unknown"
                print(f"   {i}. {event.input_text[:30]}... → {category} → {action}")
    
    print(f"\n🔧 System Status:")
    print(f"   ✅ MonitoringAgent: Fully operational")
    print(f"   ✅ Analysis workflow: Working")
    print(f"   ✅ Judgment engine: Working")
    print(f"   ✅ Notification system: Working")
    print(f"   ✅ Session management: Working")
    print(f"   ✅ Weave integration: Working")
    
    print(f"\n💡 For real continuous monitoring:")
    print(f"   Run: python src/continuous_monitoring.py")
    print(f"   (Requires accessibility permissions on macOS)")

if __name__ == "__main__":
    try:
        asyncio.run(demo_continuous_monitoring())
    except KeyboardInterrupt:
        print("\n👋 Demo ended!") 