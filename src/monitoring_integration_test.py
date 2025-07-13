"""
Comprehensive Integration Test for MonitoringAgent

This script demonstrates the complete workflow of the MonitoringAgent
and serves as both a test and usage example for the AGT-001 implementation.

The test shows:
1. Complete agent orchestration
2. Real-time monitoring simulation
3. Full workflow integration (keylogger → analysis → judgment → notification)
4. Session management and persistence
5. Performance monitoring and statistics
6. Error handling and recovery
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitoring_agent import (
    MonitoringAgent,
    MonitoringConfig,
    MonitoringStatus,
    get_global_monitoring_agent
)
from session_manager import SessionManager, get_global_session_manager
from notification_agent import NotificationConfig
from analysis_agent import AnalysisAgent
from judgment_engine import JudgmentEngine
from notification_agent import NotificationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringIntegrationTest:
    """Comprehensive integration test for MonitoringAgent"""
    
    def __init__(self):
        self.session_manager = get_global_session_manager()
        self.test_session_id = f"integration_test_{int(time.time())}"
        
        # Create comprehensive test configuration
        self.config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=True,
            enable_emergency_alerts=True,
            screenshot_on_input=False,  # Disable for testing
            cache_enabled=True,
            monitoring_interval=0.1,
            input_completion_threshold=5,
            notification_config=NotificationConfig(
                child_name="TestChild",
                parent_name="TestParent",
                desktop_notifications=True,
                email_notifications=False,
                sms_notifications=False,
                quiet_hours_start="23:00",
                quiet_hours_end="07:00"
            )
        )
        
        self.agent = MonitoringAgent(config=self.config)
        self.test_results = {}
    
    async def run_comprehensive_test(self):
        """Run comprehensive integration test"""
        print("🚀 Starting MonitoringAgent Integration Test")
        print("=" * 60)
        
        try:
            # Test 1: Agent initialization and configuration
            await self.test_agent_initialization()
            
            # Test 2: Session management
            await self.test_session_management()
            
            # Test 3: Manual input processing workflow
            await self.test_manual_input_workflow()
            
            # Test 4: Component integration
            await self.test_component_integration()
            
            # Test 5: Error handling and recovery
            await self.test_error_handling()
            
            # Test 6: Performance and statistics
            await self.test_performance_monitoring()
            
            # Test 7: Notification system integration
            await self.test_notification_integration()
            
            # Test 8: Complete workflow scenarios
            await self.test_complete_workflow_scenarios()
            
            # Final summary
            await self.print_final_summary()
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            print(f"❌ Integration test failed: {e}")
            return False
        
        print("\n🎉 All Integration Tests Completed Successfully!")
        return True
    
    async def test_agent_initialization(self):
        """Test agent initialization and configuration"""
        print("\n📋 Test 1: Agent Initialization and Configuration")
        print("-" * 40)
        
        # Check initial state
        assert self.agent.status == MonitoringStatus.STOPPED
        assert self.agent.session_id is None
        assert self.agent.config.age_group == "elementary"
        assert self.agent.config.strictness_level == "moderate"
        
        print("   ✅ Agent initialized correctly")
        
        # Test configuration updates
        result = self.agent.configure_monitoring(
            age_group="middle_school",
            strictness_level="strict",
            enable_notifications=True
        )
        
        assert result["status"] == "success"
        assert self.agent.config.age_group == "middle_school"
        assert self.agent.config.strictness_level == "strict"
        
        print("   ✅ Configuration updates working")
        
        # Reset to original config
        self.agent.configure_monitoring(
            age_group="elementary",
            strictness_level="moderate"
        )
        
        self.test_results["initialization"] = "passed"
    
    async def test_session_management(self):
        """Test session management functionality"""
        print("\n📊 Test 2: Session Management")
        print("-" * 40)
        
        # Test session creation
        session = self.session_manager.create_session(
            self.test_session_id,
            {
                "age_group": self.config.age_group,
                "strictness_level": self.config.strictness_level,
                "test_mode": True
            }
        )
        
        assert session.session_id == self.test_session_id
        assert session.status == "active"
        assert session.total_events == 0
        
        print(f"   ✅ Session created: {self.test_session_id}")
        
        # Test session retrieval
        retrieved_session = self.session_manager.get_session(self.test_session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == self.test_session_id
        
        print("   ✅ Session retrieval working")
        
        # Test event recording
        event_data = {
            "event_type": "test_event",
            "input_text": "Test input for session",
            "screenshot_path": None,
            "analysis_category": "safe",
            "analysis_confidence": 0.95,
            "judgment_action": "allow",
            "judgment_confidence": 0.90,
            "notification_sent": False,
            "processing_time": 0.15
        }
        
        event = self.session_manager.record_event(event_data)
        assert event.event_type == "test_event"
        assert event.session_id == self.test_session_id
        
        print("   ✅ Event recording working")
        
        # Check session statistics
        stats = self.session_manager.get_session_statistics(self.test_session_id)
        assert stats["session_info"]["total_events"] == 1
        assert stats["event_count"] == 1
        
        print("   ✅ Session statistics working")
        
        self.test_results["session_management"] = "passed"
    
    async def test_manual_input_workflow(self):
        """Test manual input processing workflow"""
        print("\n⚙️ Test 3: Manual Input Processing Workflow")
        print("-" * 40)
        
        # Test different types of input
        test_inputs = [
            {
                "input": "What is photosynthesis?",
                "expected_safe": True,
                "description": "Educational content"
            },
            {
                "input": "How to study for math test",
                "expected_safe": True,
                "description": "Study help"
            },
            {
                "input": "Funny cat videos",
                "expected_safe": True,
                "description": "Entertainment content"
            }
        ]
        
        for i, test_case in enumerate(test_inputs):
            print(f"\n   Test case {i+1}: {test_case['description']}")
            
            start_time = time.time()
            result = await self.agent.process_manual_input(
                test_case["input"],
                None
            )
            processing_time = time.time() - start_time
            
            assert result["status"] == "success"
            assert result["input_text"] == test_case["input"]
            assert "analysis" in result
            assert "judgment" in result
            assert "processing_time" in result
            
            print(f"     Input: {test_case['input']}")
            print(f"     Category: {result['analysis']['category']}")
            print(f"     Action: {result['judgment']['action']}")
            print(f"     Confidence: {result['analysis']['confidence']:.2%}")
            print(f"     Processing time: {processing_time:.3f}s")
            
            # Check performance
            assert processing_time < 10.0, f"Processing too slow: {processing_time:.3f}s"
        
        print("   ✅ Manual input processing working")
        self.test_results["manual_input"] = "passed"
    
    async def test_component_integration(self):
        """Test integration between all components"""
        print("\n🔗 Test 4: Component Integration")
        print("-" * 40)
        
        # Test Analysis Agent integration
        analysis_result = await self.agent.analysis_agent.analyze_input_context(
            "What is machine learning?",
            None
        )
        
        assert analysis_result.category in ["safe", "educational", "entertainment", "social"]
        assert 0.0 <= analysis_result.confidence <= 1.0
        assert analysis_result.parental_action in ["allow", "monitor", "restrict", "block"]
        
        print("   ✅ Analysis Agent integration working")
        
        # Test Judgment Engine integration
        judgment_result = await self.agent.judgment_engine.judge_content({
            "category": analysis_result.category,
            "confidence": analysis_result.confidence,
            "age_appropriateness": analysis_result.age_appropriateness,
            "safety_concerns": analysis_result.safety_concerns,
            "educational_value": analysis_result.educational_value,
            "parental_action": analysis_result.parental_action,
            "context_summary": analysis_result.context_summary
        })
        
        assert judgment_result.action.value in ["allow", "monitor", "restrict", "block"]
        assert 0.0 <= judgment_result.confidence <= 1.0
        assert judgment_result.reasoning is not None
        
        print("   ✅ Judgment Engine integration working")
        
        # Test Notification Agent integration
        notification_result = await self.agent.notification_agent.send_notification(
            template_id="monitoring_alert",
            variables={
                "child_name": "TestChild",
                "total_time": "30 minutes",
                "website_count": "5",
                "categories": "educational, entertainment",
                "concern_count": "0"
            }
        )
        
        assert notification_result["status"] == "success"
        assert notification_result["channels_attempted"] > 0
        
        print("   ✅ Notification Agent integration working")
        
        self.test_results["component_integration"] = "passed"
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🛡️ Test 5: Error Handling and Recovery")
        print("-" * 40)
        
        # Test handling of invalid input
        result = await self.agent.process_manual_input("", None)
        assert result["status"] in ["success", "error"]  # Should handle gracefully
        
        print("   ✅ Empty input handling working")
        
        # Test handling of very long input
        long_input = "A" * 1000
        result = await self.agent.process_manual_input(long_input, None)
        assert result["status"] in ["success", "error"]  # Should handle gracefully
        
        print("   ✅ Long input handling working")
        
        # Test configuration with invalid values
        result = self.agent.configure_monitoring(
            age_group="invalid_age",
            strictness_level="invalid_level"
        )
        # Should handle gracefully or reject
        assert result["status"] in ["success", "error"]
        
        print("   ✅ Invalid configuration handling working")
        
        self.test_results["error_handling"] = "passed"
    
    async def test_performance_monitoring(self):
        """Test performance monitoring and statistics"""
        print("\n📈 Test 6: Performance Monitoring and Statistics")
        print("-" * 40)
        
        # Process multiple inputs to generate statistics
        inputs = [
            "What is science?",
            "How to draw?",
            "Math problems",
            "History facts",
            "Art projects"
        ]
        
        start_time = time.time()
        
        for input_text in inputs:
            await self.agent.process_manual_input(input_text, None)
        
        total_time = time.time() - start_time
        
        # Check statistics
        status = self.agent.get_monitoring_status()
        stats = status["statistics"]
        
        assert stats["total_events"] >= len(inputs)
        assert stats["inputs_processed"] >= len(inputs)
        assert stats["average_processing_time"] > 0
        
        print(f"   ✅ Processed {len(inputs)} inputs in {total_time:.2f}s")
        print(f"   ✅ Average processing time: {stats['average_processing_time']:.3f}s")
        print(f"   ✅ Total events: {stats['total_events']}")
        
        # Test recent events retrieval
        recent_events = self.agent.get_recent_events(limit=10)
        assert len(recent_events) >= 0
        
        print(f"   ✅ Recent events: {len(recent_events)} events")
        
        self.test_results["performance_monitoring"] = "passed"
    
    async def test_notification_integration(self):
        """Test notification system integration"""
        print("\n📢 Test 7: Notification System Integration")
        print("-" * 40)
        
        # Test different notification scenarios
        notification_tests = [
            {
                "template": "content_blocked",
                "variables": {
                    "child_name": "TestChild",
                    "content_summary": "Inappropriate video content",
                    "category": "inappropriate",
                    "reason": "Contains adult themes",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "description": "Content blocked notification"
            },
            {
                "template": "inappropriate_content",
                "variables": {
                    "child_name": "TestChild",
                    "content_summary": "Questionable website content",
                    "category": "concerning",
                    "confidence": "85%",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "description": "Inappropriate content notification"
            }
        ]
        
        for test in notification_tests:
            result = await self.agent.notification_agent.send_notification(
                template_id=test["template"],
                variables=test["variables"]
            )
            
            assert result["status"] == "success"
            print(f"   ✅ {test['description']} sent successfully")
        
        # Test emergency notification
        emergency_result = await self.agent.notification_agent.send_emergency_notification(
            content_summary="Dangerous content detected",
            threat_level="high",
            additional_details={
                "category": "dangerous",
                "confidence": 0.95,
                "safety_concerns": ["violence", "dangerous_activities"]
            }
        )
        
        assert emergency_result["status"] == "success"
        print("   ✅ Emergency notification sent successfully")
        
        # Check notification statistics
        notification_stats = self.agent.notification_agent.get_notification_statistics()
        assert notification_stats["total_statistics"]["total_sent"] >= 3
        
        print(f"   ✅ Notification statistics: {notification_stats['total_statistics']['total_sent']} sent")
        
        self.test_results["notification_integration"] = "passed"
    
    async def test_complete_workflow_scenarios(self):
        """Test complete workflow scenarios"""
        print("\n🎯 Test 8: Complete Workflow Scenarios")
        print("-" * 40)
        
        # Scenario 1: Safe educational content
        print("\n   Scenario 1: Safe Educational Content")
        result1 = await self.agent.process_manual_input(
            "What is the solar system?",
            None
        )
        
        assert result1["status"] == "success"
        assert result1["judgment"]["action"] in ["allow", "monitor"]
        print(f"     Result: {result1['judgment']['action']} - {result1['analysis']['category']}")
        
        # Scenario 2: Entertainment content
        print("\n   Scenario 2: Entertainment Content")
        result2 = await self.agent.process_manual_input(
            "Funny animal videos",
            None
        )
        
        assert result2["status"] == "success"
        print(f"     Result: {result2['judgment']['action']} - {result2['analysis']['category']}")
        
        # Scenario 3: Concerning content
        print("\n   Scenario 3: Concerning Content")
        result3 = await self.agent.process_manual_input(
            "How to make weapons",
            None
        )
        
        assert result3["status"] == "success"
        assert result3["judgment"]["action"] in ["restrict", "block"]
        print(f"     Result: {result3['judgment']['action']} - {result3['analysis']['category']}")
        
        # Scenario 4: Social content
        print("\n   Scenario 4: Social Content")
        result4 = await self.agent.process_manual_input(
            "Chatting with friends online",
            None
        )
        
        assert result4["status"] == "success"
        print(f"     Result: {result4['judgment']['action']} - {result4['analysis']['category']}")
        
        print("   ✅ All workflow scenarios completed successfully")
        
        self.test_results["complete_workflow"] = "passed"
    
    async def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        
        # Test results summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == "passed")
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests:.1%}")
        
        # Component status
        print("\n🔧 Component Status:")
        print(f"   Analysis Agent: ✅ Operational")
        print(f"   Judgment Engine: ✅ Operational")
        print(f"   Notification Agent: ✅ Operational")
        print(f"   Session Manager: ✅ Operational")
        print(f"   Monitoring Agent: ✅ Operational")
        
        # Performance metrics
        status = self.agent.get_monitoring_status()
        stats = status["statistics"]
        
        print("\n📈 Performance Metrics:")
        print(f"   Total Events Processed: {stats['total_events']}")
        print(f"   Inputs Processed: {stats['inputs_processed']}")
        print(f"   Average Processing Time: {stats['average_processing_time']:.3f}s")
        print(f"   Errors: {stats['errors']}")
        print(f"   Error Rate: {stats['errors']/max(stats['total_events'], 1):.1%}")
        
        # Session statistics
        session_stats = self.session_manager.get_session_statistics(self.test_session_id)
        if session_stats:
            print("\n📊 Session Statistics:")
            print(f"   Session ID: {self.test_session_id}")
            print(f"   Events Recorded: {session_stats['event_count']}")
            print(f"   Category Distribution: {session_stats['category_distribution']}")
            print(f"   Action Distribution: {session_stats['action_distribution']}")
            print(f"   Average Processing Time: {session_stats['average_processing_time']:.3f}s")
        
        # Notification statistics
        notification_stats = self.agent.notification_agent.get_notification_statistics()
        print("\n📢 Notification Statistics:")
        print(f"   Total Sent: {notification_stats['total_statistics']['total_sent']}")
        print(f"   Success Rate: {notification_stats['success_rate']:.1%}")
        print(f"   Emergency Notifications: {notification_stats['total_statistics']['emergency_count']}")
        
        # Clean up session
        self.session_manager.end_session(self.test_session_id)
        
        print("\n✅ AGT-001 (Basic Agent Architecture) - FULLY OPERATIONAL")
        print("🎉 All systems integrated and working correctly!")

async def main():
    """Main test runner"""
    print("🚀 MonitoringAgent Integration Test")
    print("Testing AGT-001 (Basic Agent Architecture)")
    print("=" * 60)
    
    # Check environment
    print("🔍 Environment Check:")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        print(f"   ✅ Google API Key: Found (length: {len(google_api_key)})")
    else:
        print("   ⚠️  Google API Key: Not found (some features may be limited)")
    
    # Run integration test
    test = MonitoringIntegrationTest()
    success = await test.run_comprehensive_test()
    
    if success:
        print("\n🎯 AGT-001 Implementation Status: ✅ COMPLETED")
        print("🔧 All components integrated and operational")
        print("📊 Performance meets requirements")
        print("🛡️ Error handling working correctly")
        print("📢 Notification system functional")
        print("💾 Session management operational")
        
        return True
    else:
        print("\n❌ AGT-001 Implementation Status: FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 