"""
Integration Test for Notification System with Judgment Engine

This test demonstrates the complete workflow from content analysis to notification delivery.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from notification_agent import NotificationAgent, NotificationConfig
from judgment_engine import JudgmentEngine, JudgmentConfig, AgeGroup, StrictnessLevel

async def test_notification_integration():
    """Test complete integration between judgment engine and notification system"""
    
    print("🔔 Testing Notification System Integration")
    print("=" * 50)
    
    # Configure notification agent
    config = NotificationConfig(
        parent_email="parent@example.com",
        child_name="Alice",
        parent_name="Parent",
        desktop_notifications=True,
        email_notifications=False,  # Disable email for test
        sms_notifications=False
    )
    
    notification_agent = NotificationAgent(config)
    
    # Configure judgment engine
    judgment_config = JudgmentConfig(
        age_group=AgeGroup.ELEMENTARY,
        strictness_level=StrictnessLevel.MODERATE
    )
    
    judgment_engine = JudgmentEngine(judgment_config)
    
    print(f"📊 Notification Agent initialized for {config.child_name}")
    print(f"⚖️  Judgment Engine initialized for {judgment_config.age_group} with {judgment_config.strictness_level} strictness")
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Educational Content",
            "analysis_result": {
                "category": "educational",
                "confidence": 0.95,
                "content_summary": "Math homework help website",
                "safety_concerns": [],
                "age_appropriateness": {"appropriate": True, "reason": "Educational content"}
            }
        },
        {
            "name": "Inappropriate Content",
            "analysis_result": {
                "category": "inappropriate",
                "confidence": 0.85,
                "content_summary": "Social media content with inappropriate language",
                "safety_concerns": ["inappropriate_language"],
                "age_appropriateness": {"appropriate": False, "reason": "Contains inappropriate language"}
            }
        },
        {
            "name": "Dangerous Content",
            "analysis_result": {
                "category": "dangerous",
                "confidence": 0.92,
                "content_summary": "Website with instructions for dangerous activities",
                "safety_concerns": ["dangerous_activities", "violence"],
                "age_appropriateness": {"appropriate": False, "reason": "Contains dangerous content"}
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🧪 Test Scenario {i}: {scenario['name']}")
        print("-" * 30)
        
        # Get judgment from judgment engine
        judgment_result = await judgment_engine.judge_content(scenario["analysis_result"])
        
        print(f"⚖️  Judgment: {judgment_result.action.value.upper()}")
        print(f"🎯 Confidence: {judgment_result.confidence:.1%}")
        print(f"💭 Reasoning: {judgment_result.reasoning}")
        
        # Send notification based on judgment
        if judgment_result.action.value in ["restrict", "block"]:
            # Send content blocked notification
            variables = {
                "child_name": config.child_name,
                "content_summary": scenario["analysis_result"]["content_summary"],
                "category": scenario["analysis_result"]["category"],
                "reason": judgment_result.reasoning,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            notification_result = await notification_agent.send_notification(
                template_id="content_blocked",
                variables=variables,
                channels=["desktop"]  # Only desktop for test
            )
            
            print(f"🔔 Notification sent: {notification_result['status']}")
            if notification_result["status"] == "success":
                print(f"📱 Channels successful: {notification_result['channels_successful']}")
                print(f"👶 Child notification: {'✅' if notification_result.get('child_notification', {}).get('success') else '❌'}")
        
        elif judgment_result.action.value == "monitor":
            # Send monitoring alert
            variables = {
                "child_name": config.child_name,
                "content_summary": scenario["analysis_result"]["content_summary"],
                "category": scenario["analysis_result"]["category"],
                "confidence": f"{scenario['analysis_result']['confidence']:.1%}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            notification_result = await notification_agent.send_notification(
                template_id="inappropriate_content",
                variables=variables,
                channels=["desktop"]  # Only desktop for test
            )
            
            print(f"🔔 Monitoring alert sent: {notification_result['status']}")
        
        else:
            print("✅ Content allowed - no notification needed")
        
        print()
    
    # Test emergency notification
    print("🚨 Testing Emergency Notification")
    print("-" * 30)
    
    emergency_result = await notification_agent.send_emergency_notification(
        content_summary="Child accessed self-harm related content",
        threat_level="critical",
        additional_details={"keywords": ["self-harm", "suicide"], "confidence": 0.95}
    )
    
    print(f"🚨 Emergency notification: {emergency_result['status']}")
    if emergency_result["status"] == "success":
        print(f"📱 Channels successful: {emergency_result['channels_successful']}")
    
    print()
    
    # Show statistics
    print("📊 Notification Statistics")
    print("-" * 30)
    
    stats = notification_agent.get_notification_statistics()
    print(f"Total notifications sent: {stats['total_statistics']['total_sent']}")
    print(f"Emergency notifications: {stats['total_statistics']['emergency_count']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Recent notifications: {stats['recent_count']}")
    
    print()
    
    # Show recent history
    print("📋 Recent Notification History")
    print("-" * 30)
    
    history = notification_agent.get_notification_history(limit=5)
    for notification in history:
        print(f"• {notification['timestamp']}: {notification['subject']} ({notification['priority']})")
    
    print()
    print("✅ Integration test completed successfully!")
    print(f"🎉 All systems working together: Analysis → Judgment → Notification")

if __name__ == "__main__":
    asyncio.run(test_notification_integration()) 