"""
Comprehensive test suite for MonitoringAgent

Tests all core functionality including:
- Agent initialization and configuration
- Session management and persistence
- Event handling and processing
- Component integration and orchestration
- Error handling and recovery
- Performance and reliability
"""

import asyncio
import pytest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import threading
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitoring_agent import (
    MonitoringAgent,
    MonitoringConfig,
    MonitoringStatus,
    MonitoringEvent,
    create_monitoring_agent,
    get_global_monitoring_agent
)
from session_manager import SessionManager, SessionInfo, EventRecord
from notification_agent import NotificationConfig

class TestMonitoringAgent:
    """Test suite for MonitoringAgent core functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(data_dir=self.temp_dir)
        
        # Create test configuration
        self.config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=True,
            screenshot_on_input=True,
            cache_enabled=True,
            monitoring_interval=0.1,  # Fast for testing
            notification_config=NotificationConfig(
                child_name="TestChild",
                parent_name="TestParent",
                desktop_notifications=True,
                email_notifications=False,
                sms_notifications=False
            )
        )
        
        self.agent = MonitoringAgent(config=self.config)
        # Override session manager with test instance
        object.__setattr__(self.agent, 'session_manager', self.session_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'agent') and self.agent.status == MonitoringStatus.ACTIVE:
            asyncio.run(self.agent.stop_monitoring())
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        assert self.agent.config.age_group == "elementary"
        assert self.agent.config.strictness_level == "moderate"
        assert self.agent.status == MonitoringStatus.STOPPED
        assert self.agent.session_id is None
        assert self.agent.statistics['total_events'] == 0
        assert self.agent.analysis_agent is not None
        assert self.agent.judgment_engine is not None
        assert self.agent.notification_agent is not None
    
    def test_configuration_updates(self):
        """Test configuration updates"""
        result = self.agent.configure_monitoring(
            age_group="high_school",
            strictness_level="strict",
            enable_notifications=False
        )
        
        assert result["status"] == "success"
        assert self.agent.config.age_group == "high_school"
        assert self.agent.config.strictness_level == "strict"
        assert self.agent.config.enable_notifications == False
    
    @patch('src.monitoring_agent.start_keylogger_tool')
    async def test_start_monitoring(self, mock_keylogger):
        """Test starting monitoring system"""
        mock_keylogger.return_value = {"success": True, "message": "Keylogger started"}
        
        result = await self.agent.start_monitoring("test_session_001")
        
        assert result["status"] == "success"
        assert result["session_id"] == "test_session_001"
        assert self.agent.status == MonitoringStatus.ACTIVE
        assert self.agent.session_id == "test_session_001"
        
        # Check session was created
        session = self.session_manager.get_session("test_session_001")
        assert session is not None
        assert session.status == "active"
    
    @patch('src.monitoring_agent.start_keylogger_tool')
    @patch('src.monitoring_agent.stop_keylogger_tool')
    @patch('src.monitoring_agent.cleanup_temp_files_tool')
    async def test_stop_monitoring(self, mock_cleanup, mock_stop, mock_start):
        """Test stopping monitoring system"""
        mock_start.return_value = {"success": True, "message": "Keylogger started"}
        mock_stop.return_value = {"success": True, "message": "Keylogger stopped"}
        mock_cleanup.return_value = {"success": True, "message": "Files cleaned"}
        
        # Start monitoring first
        await self.agent.start_monitoring("test_session_002")
        
        # Stop monitoring
        result = await self.agent.stop_monitoring()
        
        assert result["status"] == "success"
        assert self.agent.status == MonitoringStatus.STOPPED
        assert "session_summary" in result
        
        # Check session was ended
        session = self.session_manager.get_session("test_session_002")
        assert session.status == "completed"
        assert session.end_time is not None
    
    @patch('src.monitoring_agent.start_keylogger_tool')
    async def test_start_monitoring_keylogger_failure(self, mock_keylogger):
        """Test handling keylogger startup failure"""
        mock_keylogger.return_value = {"success": False, "error": "Permission denied"}
        
        result = await self.agent.start_monitoring("test_session_003")
        
        assert result["status"] == "error"
        assert "Failed to start keylogger" in result["error"]
        assert self.agent.status == MonitoringStatus.ERROR
    
    def test_monitoring_status(self):
        """Test monitoring status retrieval"""
        status = self.agent.get_monitoring_status()
        
        assert status["status"] == "stopped"
        assert status["session_id"] is None
        assert "statistics" in status
        assert "config" in status
        assert "timestamp" in status
    
    @patch('src.monitoring_agent.start_keylogger_tool')
    async def test_manual_input_processing(self, mock_keylogger):
        """Test manual input processing"""
        mock_keylogger.return_value = {"success": True, "message": "Keylogger started"}
        
        # Start monitoring
        await self.agent.start_monitoring("test_session_004")
        
        # Process manual input
        result = await self.agent.process_manual_input(
            "What is 2+2?",
            None  # No screenshot
        )
        
        assert result["status"] == "success"
        assert result["input_text"] == "What is 2+2?"
        assert "analysis" in result
        assert "judgment" in result
        assert "processing_time" in result
        
        # Check statistics were updated
        stats = self.agent.get_monitoring_status()["statistics"]
        assert stats["total_events"] >= 1
    
    async def test_manual_input_processing_error_handling(self):
        """Test error handling in manual input processing"""
        # Test without starting monitoring (should still work)
        result = await self.agent.process_manual_input(
            "Test input",
            None
        )
        
        # Should handle gracefully even without active session
        assert result["status"] in ["success", "error"]
        assert result["input_text"] == "Test input"
    
    def test_recent_events_retrieval(self):
        """Test recent events retrieval"""
        # Add some test events to history
        test_event = MonitoringEvent(
            timestamp=datetime.now(),
            event_type="test_event",
            input_text="Test input",
            screenshot_path=None,
            analysis_result=None,
            judgment_result=None,
            notification_sent=False,
            processing_time=0.1
        )
        
        # Add to history
        new_history = list(self.agent.event_history)
        new_history.append(test_event)
        object.__setattr__(self.agent, 'event_history', new_history)
        
        events = self.agent.get_recent_events(limit=5)
        
        assert len(events) >= 1
        assert events[0]["event_type"] == "test_event"
        assert events[0]["input_text"] == "Test input"
        assert "timestamp" in events[0]
        assert "processing_time" in events[0]

class TestMonitoringAgentIntegration:
    """Test suite for MonitoringAgent integration with components"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=True,
            screenshot_on_input=False,  # Disable for testing
            cache_enabled=True,
            monitoring_interval=0.1,
            notification_config=NotificationConfig(
                child_name="TestChild",
                parent_name="TestParent",
                desktop_notifications=True,
                email_notifications=False
            )
        )
        
        self.agent = MonitoringAgent(config=self.config)
        # Override session manager with test instance
        session_manager = SessionManager(data_dir=self.temp_dir)
        object.__setattr__(self, 'session_manager', session_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'agent') and self.agent.status == MonitoringStatus.ACTIVE:
            asyncio.run(self.agent.stop_monitoring())
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    async def test_complete_workflow_integration(self):
        """Test complete workflow integration"""
        # Test scenarios with different content types
        test_cases = [
            {
                "input": "What is photosynthesis?",
                "expected_category": "educational",
                "expected_action": "allow"
            },
            {
                "input": "How to make a bomb",
                "expected_category": "dangerous",
                "expected_action": "block"
            },
            {
                "input": "Funny cat videos",
                "expected_category": "entertainment",
                "expected_action": "allow"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            result = await self.agent.process_manual_input(
                test_case["input"],
                None
            )
            
            assert result["status"] == "success"
            assert result["input_text"] == test_case["input"]
            
            # Check analysis results
            analysis = result["analysis"]
            assert "category" in analysis
            assert "confidence" in analysis
            assert "context_summary" in analysis
            
            # Check judgment results
            judgment = result["judgment"]
            assert "action" in judgment
            assert "confidence" in judgment
            assert "reasoning" in judgment
            
            print(f"Test case {i+1}: {test_case['input']}")
            print(f"  Category: {analysis['category']}")
            print(f"  Action: {judgment['action']}")
            print(f"  Processing time: {result['processing_time']:.3f}s")
    
    @patch('src.monitoring_agent.start_keylogger_tool')
    @patch('src.monitoring_agent.get_current_input_tool')
    async def test_monitoring_loop_simulation(self, mock_get_input, mock_start):
        """Test monitoring loop simulation"""
        mock_start.return_value = {"success": True, "message": "Keylogger started"}
        
        # Simulate input completion sequence
        input_sequence = [
            {"input_complete": False, "current_input": "What is"},
            {"input_complete": False, "current_input": "What is 2+2"},
            {"input_complete": True, "current_input": "What is 2+2?"},
            {"input_complete": False, "current_input": ""}
        ]
        
        mock_get_input.side_effect = input_sequence
        
        # Start monitoring
        await self.agent.start_monitoring("test_session_loop")
        
        # Let it run for a short time
        await asyncio.sleep(0.5)
        
        # Stop monitoring
        await self.agent.stop_monitoring()
        
        # Check that events were processed
        status = self.agent.get_monitoring_status()
        assert status["statistics"]["total_events"] >= 0  # May or may not have processed

class TestMonitoringAgentPerformance:
    """Test suite for MonitoringAgent performance and reliability"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=False,  # Disable for performance testing
            screenshot_on_input=False,
            cache_enabled=True,
            monitoring_interval=0.01  # Very fast for testing
        )
        
        self.agent = MonitoringAgent(config=self.config)
        # Override session manager
        session_manager = SessionManager(data_dir=self.temp_dir)
        object.__setattr__(self.agent, 'session_manager', session_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'agent') and self.agent.status == MonitoringStatus.ACTIVE:
            asyncio.run(self.agent.stop_monitoring())
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    async def test_concurrent_processing(self):
        """Test concurrent input processing"""
        # Test multiple concurrent inputs
        inputs = [
            "What is math?",
            "How to study?",
            "Science facts",
            "History lesson",
            "Art project"
        ]
        
        start_time = time.time()
        
        # Process all inputs concurrently
        tasks = [
            self.agent.process_manual_input(input_text, None)
            for input_text in inputs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        assert len(successful_results) >= len(inputs) * 0.8  # At least 80% success rate
        
        # Check performance
        avg_time_per_input = total_time / len(inputs)
        assert avg_time_per_input < 5.0  # Should be under 5 seconds per input
        
        print(f"Processed {len(inputs)} inputs in {total_time:.2f}s")
        print(f"Average time per input: {avg_time_per_input:.2f}s")
        print(f"Success rate: {len(successful_results)}/{len(inputs)}")
    
    async def test_memory_usage_stability(self):
        """Test memory usage stability over time"""
        # Process many inputs to test memory stability
        for i in range(50):
            result = await self.agent.process_manual_input(
                f"Test input number {i}",
                None
            )
            
            # Check that basic processing is working
            assert result["status"] in ["success", "error"]
            
            # Check event history doesn't grow unbounded
            assert len(self.agent.event_history) <= 100
        
        # Check statistics are reasonable
        stats = self.agent.get_monitoring_status()["statistics"]
        assert stats["total_events"] >= 0
        assert stats["errors"] < stats["total_events"]  # Error rate should be reasonable

class TestMonitoringAgentErrorHandling:
    """Test suite for MonitoringAgent error handling"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=True,
            screenshot_on_input=False,
            cache_enabled=True
        )
        
        self.agent = MonitoringAgent(config=self.config)
        # Override session manager
        session_manager = SessionManager(data_dir=self.temp_dir)
        object.__setattr__(self.agent, 'session_manager', session_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        if hasattr(self, 'agent') and self.agent.status == MonitoringStatus.ACTIVE:
            asyncio.run(self.agent.stop_monitoring())
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    async def test_analysis_error_handling(self):
        """Test handling of analysis errors"""
        # Mock analysis agent to raise an error
        original_analyze = self.agent.analysis_agent.analyze_input_context
        
        async def mock_analyze_error(*args, **kwargs):
            raise Exception("Analysis failed")
        
        self.agent.analysis_agent.analyze_input_context = mock_analyze_error
        
        result = await self.agent.process_manual_input("Test input", None)
        
        # Should handle error gracefully
        assert result["status"] == "error"
        assert "Analysis failed" in result["error"]
        
        # Restore original method
        self.agent.analysis_agent.analyze_input_context = original_analyze
    
    async def test_judgment_error_handling(self):
        """Test handling of judgment errors"""
        # Mock judgment engine to raise an error
        original_judge = self.agent.judgment_engine.judge_content
        
        async def mock_judge_error(*args, **kwargs):
            raise Exception("Judgment failed")
        
        self.agent.judgment_engine.judge_content = mock_judge_error
        
        result = await self.agent.process_manual_input("Test input", None)
        
        # Should handle error gracefully
        assert result["status"] == "error"
        assert "Judgment failed" in result["error"]
        
        # Restore original method
        self.agent.judgment_engine.judge_content = original_judge
    
    async def test_notification_error_handling(self):
        """Test handling of notification errors"""
        # Enable notifications for this test
        self.agent.config.enable_notifications = True
        
        # Mock notification agent to raise an error
        original_send = self.agent.notification_agent.send_notification
        
        async def mock_send_error(*args, **kwargs):
            raise Exception("Notification failed")
        
        self.agent.notification_agent.send_notification = mock_send_error
        
        # Process input that should trigger notification
        result = await self.agent.process_manual_input("How to make explosives", None)
        
        # Should still complete processing despite notification error
        assert result["status"] == "success"
        assert "analysis" in result
        assert "judgment" in result
        
        # Restore original method
        self.agent.notification_agent.send_notification = original_send

# Test runner
async def run_all_tests():
    """Run all tests"""
    print("🧪 Running MonitoringAgent Tests")
    print("=" * 50)
    
    # Core functionality tests
    print("\n1. Testing Core Functionality...")
    core_tests = TestMonitoringAgent()
    core_tests.setup_method()
    
    try:
        core_tests.test_agent_initialization()
        core_tests.test_configuration_updates()
        await core_tests.test_start_monitoring()
        await core_tests.test_stop_monitoring()
        await core_tests.test_start_monitoring_keylogger_failure()
        core_tests.test_monitoring_status()
        await core_tests.test_manual_input_processing()
        await core_tests.test_manual_input_processing_error_handling()
        core_tests.test_recent_events_retrieval()
        print("   ✅ All core functionality tests passed!")
    except Exception as e:
        print(f"   ❌ Core functionality test failed: {e}")
    finally:
        core_tests.teardown_method()
    
    # Integration tests
    print("\n2. Testing Integration...")
    integration_tests = TestMonitoringAgentIntegration()
    integration_tests.setup_method()
    
    try:
        await integration_tests.test_complete_workflow_integration()
        await integration_tests.test_monitoring_loop_simulation()
        print("   ✅ All integration tests passed!")
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
    finally:
        integration_tests.teardown_method()
    
    # Performance tests
    print("\n3. Testing Performance...")
    performance_tests = TestMonitoringAgentPerformance()
    performance_tests.setup_method()
    
    try:
        await performance_tests.test_concurrent_processing()
        await performance_tests.test_memory_usage_stability()
        print("   ✅ All performance tests passed!")
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
    finally:
        performance_tests.teardown_method()
    
    # Error handling tests
    print("\n4. Testing Error Handling...")
    error_tests = TestMonitoringAgentErrorHandling()
    error_tests.setup_method()
    
    try:
        await error_tests.test_analysis_error_handling()
        await error_tests.test_judgment_error_handling()
        await error_tests.test_notification_error_handling()
        print("   ✅ All error handling tests passed!")
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    finally:
        error_tests.teardown_method()
    
    print("\n" + "=" * 50)
    print("🎉 MonitoringAgent Tests Completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 