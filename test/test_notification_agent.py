"""
Comprehensive Test Suite for Notification Agent

Tests all notification functionality including:
- Notification agent core functionality
- Template rendering and management
- Delivery channel testing
- Emergency notifications
- ADK tool integration
- Configuration management
- Statistics and history tracking
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json

# Import the notification agent components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from notification_agent import (
    NotificationAgent, NotificationHelper, NotificationConfig,
    NotificationPriority, NotificationChannel, NotificationStatus,
    send_notification_function_tool, send_emergency_notification_function_tool,
    get_notification_statistics_function_tool, configure_notifications_function_tool,
    get_notification_history_function_tool, get_global_notification_agent
)

class TestNotificationAgent:
    """Test the core NotificationAgent functionality"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return NotificationConfig(
            parent_email="parent@example.com",
            parent_phone="+1234567890",
            child_name="TestChild",
            parent_name="TestParent",
            desktop_notifications=True,
            email_notifications=True,
            sms_notifications=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00"
        )
    
    @pytest.fixture
    def agent(self, config):
        """Create test notification agent"""
        return NotificationAgent(config)
    
    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.config.child_name == "TestChild"
        assert agent.config.parent_name == "TestParent"
        assert len(agent.templates) == 5  # 5 default templates
        assert "content_blocked" in agent.templates
        assert "emergency_alert" in agent.templates
        assert agent.statistics["total_sent"] == 0
    
    def test_default_templates(self, agent):
        """Test default template loading"""
        templates = agent.templates
        
        # Check all expected templates exist
        expected_templates = [
            "content_blocked", "inappropriate_content", "emergency_alert",
            "monitoring_alert", "system_status"
        ]
        
        for template_id in expected_templates:
            assert template_id in templates
            template = templates[template_id]
            assert template.id == template_id
            assert template.subject_template
            assert template.body_template
            assert isinstance(template.priority, NotificationPriority)
            assert isinstance(template.channels, list)
    
    def test_template_rendering(self, agent):
        """Test template variable rendering"""
        template_str = "Hello {name}, you have {count} messages"
        variables = {"name": "John", "count": 5}
        
        result = agent._render_template(template_str, variables)
        assert result == "Hello John, you have 5 messages"
    
    def test_template_rendering_missing_variable(self, agent):
        """Test template rendering with missing variable"""
        template_str = "Hello {name}, you have {count} messages"
        variables = {"name": "John"}  # Missing 'count'
        
        # Should return original template when variable is missing
        result = agent._render_template(template_str, variables)
        assert result == template_str
    
    def test_quiet_hours_detection(self, agent):
        """Test quiet hours detection"""
        # Test during quiet hours
        with patch('notification_agent.datetime') as mock_datetime:
            mock_datetime.now.return_value.time.return_value = datetime.strptime("23:30", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            assert agent._is_quiet_hours() == True
        
        # Test outside quiet hours
        with patch('notification_agent.datetime') as mock_datetime:
            mock_datetime.now.return_value.time.return_value = datetime.strptime("10:30", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            assert agent._is_quiet_hours() == False
    
    @pytest.mark.asyncio
    async def test_desktop_notification_macos(self, agent):
        """Test desktop notification on macOS"""
        with patch('notification_agent.platform.system', return_value='Darwin'):
            with patch('notification_agent.subprocess.run') as mock_run:
                mock_run.return_value = None
                
                result = await agent._send_desktop_notification("Test Subject", "Test Body", NotificationPriority.MEDIUM)
                
                assert result["success"] == True
                assert result["channel"] == "desktop"
                assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_desktop_notification_failure(self, agent):
        """Test desktop notification failure"""
        with patch('notification_agent.platform.system', return_value='Darwin'):
            with patch('notification_agent.subprocess.run', side_effect=Exception("Command failed")):
                
                result = await agent._send_desktop_notification("Test Subject", "Test Body", NotificationPriority.MEDIUM)
                
                assert result["success"] == False
                assert "Command failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_email_notification_success(self, agent):
        """Test email notification success"""
        with patch.dict(os.environ, {
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'EMAIL_USER': 'test@example.com',
            'EMAIL_PASSWORD': 'password'
        }):
            with patch('notification_agent.smtplib.SMTP') as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value = mock_server
                
                result = await agent._send_email_notification("Test Subject", "Test Body", NotificationPriority.HIGH)
                
                assert result["success"] == True
                assert result["channel"] == "email"
                assert mock_server.starttls.called
                assert mock_server.login.called
                assert mock_server.send_message.called
                assert mock_server.quit.called
    
    @pytest.mark.asyncio
    async def test_email_notification_no_config(self, agent):
        """Test email notification without configuration"""
        agent.config.parent_email = None
        
        result = await agent._send_email_notification("Test Subject", "Test Body", NotificationPriority.MEDIUM)
        
        assert result["success"] == False
        assert "No parent email configured" in result["error"]
    
    @pytest.mark.asyncio
    async def test_email_notification_no_credentials(self, agent):
        """Test email notification without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            result = await agent._send_email_notification("Test Subject", "Test Body", NotificationPriority.MEDIUM)
            
            assert result["success"] == False
            assert "Email credentials not configured" in result["error"]
    
    @pytest.mark.asyncio
    async def test_sms_notification_placeholder(self, agent):
        """Test SMS notification (placeholder implementation)"""
        result = await agent._send_sms_notification("Test Subject", "Test Body", NotificationPriority.EMERGENCY)
        
        assert result["success"] == True
        assert result["channel"] == "sms"
        assert "SMS service not implemented" in result["note"]
    
    @pytest.mark.asyncio
    async def test_sms_notification_no_phone(self, agent):
        """Test SMS notification without phone number"""
        agent.config.parent_phone = None
        
        result = await agent._send_sms_notification("Test Subject", "Test Body", NotificationPriority.EMERGENCY)
        
        assert result["success"] == False
        assert "No parent phone configured" in result["error"]
    
    @pytest.mark.asyncio
    async def test_in_app_notification(self, agent):
        """Test in-app notification"""
        result = await agent._send_in_app_notification("Test Subject", "Test Body", NotificationPriority.LOW)
        
        assert result["success"] == True
        assert result["channel"] == "in_app"
    
    @pytest.mark.asyncio
    async def test_child_notification_macos(self, agent):
        """Test child notification on macOS"""
        with patch('notification_agent.platform.system', return_value='Darwin'):
            with patch('notification_agent.subprocess.run') as mock_run:
                mock_run.return_value = None
                
                result = await agent._send_child_notification("Test message", NotificationPriority.MEDIUM)
                
                assert result["success"] == True
                assert result["channel"] == "child_desktop"
                assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, agent):
        """Test successful notification sending"""
        variables = {
            "child_name": "TestChild",
            "content_summary": "Test content",
            "category": "inappropriate",
            "reason": "Age inappropriate",
            "timestamp": "2024-01-01 12:00:00"
        }
        
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            with patch.object(agent, '_send_email_notification', return_value={"success": True, "channel": "email"}):
                
                result = await agent.send_notification("content_blocked", variables)
                
                assert result["status"] == "success"
                assert result["channels_successful"] == 2
                assert len(agent.notification_history) == 1
                assert agent.statistics["total_sent"] == 1
    
    @pytest.mark.asyncio
    async def test_send_notification_during_quiet_hours(self, agent):
        """Test notification sending during quiet hours"""
        variables = {"child_name": "TestChild", "content_summary": "Test", "category": "test", "reason": "test", "timestamp": "2024-01-01 12:00:00"}
        
        with patch.object(agent, '_is_quiet_hours', return_value=True):
            result = await agent.send_notification("content_blocked", variables)
            
            assert result["status"] == "delayed"
            assert result["reason"] == "quiet_hours"
            assert "scheduled_for" in result
    
    @pytest.mark.asyncio
    async def test_send_emergency_notification_ignores_quiet_hours(self, agent):
        """Test emergency notification ignores quiet hours"""
        variables = {"child_name": "TestChild", "content_summary": "Dangerous content", "threat_level": "high", "timestamp": "2024-01-01 12:00:00"}
        
        with patch.object(agent, '_is_quiet_hours', return_value=True):
            with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
                with patch.object(agent, '_send_email_notification', return_value={"success": True, "channel": "email"}):
                    
                    result = await agent.send_notification("emergency_alert", variables, priority_override="emergency")
                    
                    assert result["status"] == "success"
                    assert result["channels_successful"] > 0
    
    @pytest.mark.asyncio
    async def test_send_notification_invalid_template(self, agent):
        """Test sending notification with invalid template"""
        result = await agent.send_notification("invalid_template", {})
        
        assert result["status"] == "error"
        assert "Template 'invalid_template' not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_send_notification_all_channels_fail(self, agent):
        """Test notification when all channels fail"""
        variables = {"child_name": "TestChild", "content_summary": "Test", "category": "test", "reason": "test", "timestamp": "2024-01-01 12:00:00"}
        
        with patch.object(agent, '_send_desktop_notification', return_value={"success": False, "error": "Desktop failed"}):
            with patch.object(agent, '_send_email_notification', return_value={"success": False, "error": "Email failed"}):
                
                result = await agent.send_notification("content_blocked", variables)
                
                assert result["status"] == "failed"
                assert result["channels_successful"] == 0
                assert agent.statistics["failed_deliveries"] == 1
    
    @pytest.mark.asyncio
    async def test_send_emergency_notification(self, agent):
        """Test emergency notification sending"""
        with patch.object(agent, 'send_notification', return_value={"status": "success", "notification_id": "test123"}):
            
            result = await agent.send_emergency_notification("Dangerous content detected", "critical")
            
            assert result["status"] == "success"
            assert agent.statistics["emergency_count"] == 1
    
    def test_statistics_tracking(self, agent):
        """Test statistics tracking"""
        # Create mock notification record
        from notification_agent import NotificationRecord
        record = NotificationRecord(
            id="test123",
            timestamp=datetime.now(),
            priority=NotificationPriority.HIGH,
            channels=[NotificationChannel.DESKTOP, NotificationChannel.EMAIL],
            recipient="parent",
            subject="Test",
            body="Test body",
            status=NotificationStatus.SENT
        )
        
        agent._update_statistics(record, True)
        
        assert agent.statistics["total_sent"] == 1
        assert agent.statistics["by_priority"]["high"] == 1
        assert agent.statistics["by_channel"]["desktop"] == 1
        assert agent.statistics["by_channel"]["email"] == 1
        assert agent.statistics["by_status"]["sent"] == 1
    
    def test_get_notification_statistics(self, agent):
        """Test getting notification statistics"""
        # Add some mock history
        agent.statistics["total_sent"] = 10
        agent.statistics["failed_deliveries"] = 2
        
        stats = agent.get_notification_statistics()
        
        assert stats["total_statistics"]["total_sent"] == 10
        assert stats["success_rate"] == 80.0  # (10-2)/10 * 100
        assert "recent_count" in stats
        assert "average_daily_notifications" in stats
    
    def test_configure_notifications(self, agent):
        """Test notification configuration"""
        result = agent.configure_notifications(
            child_name="NewName",
            desktop_notifications=False,
            parent_email="new@example.com"
        )
        
        assert result["status"] == "success"
        assert agent.config.child_name == "NewName"
        assert agent.config.desktop_notifications == False
        assert agent.config.parent_email == "new@example.com"
    
    def test_get_notification_history(self, agent):
        """Test getting notification history"""
        # Add some mock history
        from notification_agent import NotificationRecord
        for i in range(3):
            record = NotificationRecord(
                id=f"test{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.DESKTOP],
                recipient="parent",
                subject=f"Test {i}",
                body=f"Test body {i}",
                status=NotificationStatus.SENT
            )
            agent.notification_history.append(record)
        
        history = agent.get_notification_history(limit=2)
        
        assert len(history) == 2
        assert history[0]["subject"] == "Test 0"  # Most recent first
        assert history[1]["subject"] == "Test 1"
    
    def test_get_notification_history_with_filter(self, agent):
        """Test getting notification history with priority filter"""
        # Add mock history with different priorities
        from notification_agent import NotificationRecord
        priorities = [NotificationPriority.LOW, NotificationPriority.HIGH, NotificationPriority.MEDIUM]
        
        for i, priority in enumerate(priorities):
            record = NotificationRecord(
                id=f"test{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                priority=priority,
                channels=[NotificationChannel.DESKTOP],
                recipient="parent",
                subject=f"Test {i}",
                body=f"Test body {i}",
                status=NotificationStatus.SENT
            )
            agent.notification_history.append(record)
        
        history = agent.get_notification_history(priority_filter="high")
        
        assert len(history) == 1
        assert history[0]["priority"] == "high"


class TestNotificationHelper:
    """Test the NotificationHelper class"""
    
    @pytest.fixture
    def helper(self):
        """Create test notification helper"""
        config = NotificationConfig(child_name="TestChild")
        return NotificationHelper(config)
    
    @pytest.mark.asyncio
    async def test_notify_content_blocked(self, helper):
        """Test content blocked notification helper"""
        with patch.object(helper.agent, 'send_notification', return_value={"status": "success"}) as mock_send:
            
            result = await helper.notify_content_blocked("Test content", "inappropriate", "Age inappropriate")
            
            assert result["status"] == "success"
            assert mock_send.called
            args, kwargs = mock_send.call_args
            assert args[0] == "content_blocked"
            assert "content_summary" in args[1]
            assert args[1]["content_summary"] == "Test content"
    
    @pytest.mark.asyncio
    async def test_notify_inappropriate_content(self, helper):
        """Test inappropriate content notification helper"""
        with patch.object(helper.agent, 'send_notification', return_value={"status": "success"}) as mock_send:
            
            result = await helper.notify_inappropriate_content("Test content", "social", 0.85)
            
            assert result["status"] == "success"
            assert mock_send.called
            args, kwargs = mock_send.call_args
            assert args[0] == "inappropriate_content"
            assert "85.0%" in args[1]["confidence"]
    
    @pytest.mark.asyncio
    async def test_emergency_alert(self, helper):
        """Test emergency alert helper"""
        with patch.object(helper.agent, 'send_emergency_notification', return_value={"status": "success"}) as mock_send:
            
            result = await helper.emergency_alert("Dangerous content", "critical")
            
            assert result["status"] == "success"
            assert mock_send.called
            args, kwargs = mock_send.call_args
            assert args[0] == "Dangerous content"
            assert args[1] == "critical"


class TestADKTools:
    """Test the ADK Function Tools"""
    
    def test_send_notification_tool_initialization(self):
        """Test send notification tool initialization"""
        assert send_notification_function_tool.func is not None
        assert send_notification_function_tool.func.__name__ == "send_notification_tool"
    
    @pytest.mark.asyncio
    async def test_send_notification_tool_call(self):
        """Test send notification tool call"""
        variables = {"child_name": "TestChild", "content_summary": "Test", "category": "test", "reason": "test", "timestamp": "2024-01-01 12:00:00"}
        
        # Mock the global agent
        with patch('notification_agent.get_global_notification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.send_notification = AsyncMock(return_value={"status": "success"})
            mock_get_agent.return_value = mock_agent
            
            result = await send_notification_function_tool.func("content_blocked", variables)
            
            assert result["status"] == "success"
            assert mock_agent.send_notification.called
    
    def test_emergency_notification_tool_initialization(self):
        """Test emergency notification tool initialization"""
        assert send_emergency_notification_function_tool.func is not None
        assert send_emergency_notification_function_tool.func.__name__ == "send_emergency_notification_tool"
    
    @pytest.mark.asyncio
    async def test_emergency_notification_tool_call(self):
        """Test emergency notification tool call"""
        with patch('notification_agent.get_global_notification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.send_emergency_notification = AsyncMock(return_value={"status": "success"})
            mock_get_agent.return_value = mock_agent
            
            result = await send_emergency_notification_function_tool.func("Dangerous content detected")
            
            assert result["status"] == "success"
            assert mock_agent.send_emergency_notification.called
    
    def test_statistics_tool_initialization(self):
        """Test statistics tool initialization"""
        assert get_notification_statistics_function_tool.func is not None
        assert get_notification_statistics_function_tool.func.__name__ == "get_notification_statistics_tool"
    
    def test_statistics_tool_call(self):
        """Test statistics tool call"""
        with patch('notification_agent.get_global_notification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.get_notification_statistics = Mock(return_value={"total_statistics": {}, "success_rate": 100.0})
            mock_get_agent.return_value = mock_agent
            
            result = get_notification_statistics_function_tool.func()
            
            assert "total_statistics" in result
            assert "success_rate" in result
    
    def test_configuration_tool_initialization(self):
        """Test configuration tool initialization"""
        assert configure_notifications_function_tool.func is not None
        assert configure_notifications_function_tool.func.__name__ == "configure_notifications_tool"
    
    def test_configuration_tool_call(self):
        """Test configuration tool call"""
        with patch('notification_agent.get_global_notification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.configure_notifications = Mock(return_value={"status": "success"})
            mock_get_agent.return_value = mock_agent
            
            result = configure_notifications_function_tool.func(child_name="NewName", desktop_notifications=False)
            
            assert result["status"] == "success"
            assert mock_agent.configure_notifications.called
    
    def test_history_tool_initialization(self):
        """Test history tool initialization"""
        assert get_notification_history_function_tool.func is not None
        assert get_notification_history_function_tool.func.__name__ == "get_notification_history_tool"
    
    def test_history_tool_call(self):
        """Test history tool call"""
        with patch('notification_agent.get_global_notification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.get_notification_history = Mock(return_value=[])
            mock_get_agent.return_value = mock_agent
            
            result = get_notification_history_function_tool.func(limit=10)
            
            assert isinstance(result, list)


class TestNotificationScenarios:
    """Test realistic notification scenarios"""
    
    @pytest.fixture
    def agent(self):
        """Create test notification agent"""
        config = NotificationConfig(
            parent_email="parent@example.com",
            child_name="Alice",
            desktop_notifications=True,
            email_notifications=True
        )
        return NotificationAgent(config)
    
    @pytest.mark.asyncio
    async def test_content_blocked_scenario(self, agent):
        """Test complete content blocked scenario"""
        # Mock successful delivery
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            with patch.object(agent, '_send_email_notification', return_value={"success": True, "channel": "email"}):
                with patch.object(agent, '_send_child_notification', return_value={"success": True, "channel": "child_desktop"}):
                    
                    variables = {
                        "child_name": "Alice",
                        "content_summary": "Adult content website",
                        "category": "inappropriate",
                        "reason": "Contains adult content not suitable for child's age",
                        "timestamp": "2024-01-01 15:30:00"
                    }
                    
                    result = await agent.send_notification("content_blocked", variables)
                    
                    assert result["status"] == "success"
                    assert result["channels_successful"] == 2
                    assert result["child_notification"]["success"] == True
                    assert len(agent.notification_history) == 1
                    
                    # Check notification record
                    record = agent.notification_history[0]
                    assert record.priority == NotificationPriority.HIGH
                    assert "Alice" in record.subject
                    assert "adult content" in record.body.lower()
    
    @pytest.mark.asyncio
    async def test_emergency_scenario(self, agent):
        """Test emergency notification scenario"""
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            with patch.object(agent, '_send_email_notification', return_value={"success": True, "channel": "email"}):
                
                result = await agent.send_emergency_notification(
                    "Child accessed self-harm related content",
                    "critical",
                    {"keywords": ["self-harm", "suicide"], "confidence": 0.95}
                )
                
                assert result["status"] == "success"
                assert result["channels_successful"] == 2
                assert agent.statistics["emergency_count"] == 1
                
                # Check that emergency notification was logged
                record = agent.notification_history[0]
                assert record.priority == NotificationPriority.EMERGENCY
                assert "EMERGENCY" in record.subject
                assert "self-harm" in record.body
    
    @pytest.mark.asyncio
    async def test_partial_delivery_failure(self, agent):
        """Test scenario where some delivery channels fail"""
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            with patch.object(agent, '_send_email_notification', return_value={"success": False, "error": "SMTP error"}):
                
                variables = {
                    "child_name": "Alice",
                    "content_summary": "Inappropriate video",
                    "category": "concerning",
                    "confidence": "75.0%",
                    "timestamp": "2024-01-01 16:00:00"
                }
                
                result = await agent.send_notification("inappropriate_content", variables)
                
                assert result["status"] == "success"  # At least one channel succeeded
                assert result["channels_successful"] == 1
                assert result["delivery_results"]["desktop"]["success"] == True
                assert result["delivery_results"]["email"]["success"] == False
    
    @pytest.mark.asyncio
    async def test_quiet_hours_emergency_override(self, agent):
        """Test that emergency notifications override quiet hours"""
        with patch.object(agent, '_is_quiet_hours', return_value=True):
            with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
                with patch.object(agent, '_send_email_notification', return_value={"success": True, "channel": "email"}):
                    
                    result = await agent.send_emergency_notification("Dangerous content", "high")
                    
                    assert result["status"] == "success"
                    assert result["channels_successful"] == 2
                    # Emergency should not be delayed despite quiet hours
    
    @pytest.mark.asyncio
    async def test_notification_history_tracking(self, agent):
        """Test that notification history is properly tracked"""
        # Send multiple notifications
        variables = {"child_name": "Alice", "content_summary": "Test", "category": "test", "reason": "test", "timestamp": "2024-01-01 12:00:00"}
        
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            
            for i in range(3):
                await agent.send_notification("content_blocked", variables)
        
        assert len(agent.notification_history) == 3
        assert agent.statistics["total_sent"] == 3
        assert agent.statistics["by_priority"]["high"] == 3
        
        # Test history retrieval
        history = agent.get_notification_history(limit=2)
        assert len(history) == 2
        
        # Test statistics
        stats = agent.get_notification_statistics()
        assert stats["total_statistics"]["total_sent"] == 3
        assert stats["success_rate"] == 100.0


class TestNotificationConfiguration:
    """Test notification configuration scenarios"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = NotificationConfig()
        
        assert config.child_name == "Child"
        assert config.parent_name == "Parent"
        assert config.desktop_notifications == True
        assert config.email_notifications == True
        assert config.sms_notifications == False
        assert config.quiet_hours_start == "22:00"
        assert config.quiet_hours_end == "07:00"
        assert "desktop" in config.emergency_channels
        assert "email" in config.emergency_channels
    
    def test_custom_configuration(self):
        """Test custom configuration"""
        config = NotificationConfig(
            parent_email="custom@example.com",
            child_name="CustomChild",
            desktop_notifications=False,
            emergency_channels=["email", "sms"]
        )
        
        assert config.parent_email == "custom@example.com"
        assert config.child_name == "CustomChild"
        assert config.desktop_notifications == False
        assert config.emergency_channels == ["email", "sms"]
    
    def test_configuration_update(self):
        """Test configuration updates"""
        agent = NotificationAgent()
        
        result = agent.configure_notifications(
            child_name="UpdatedChild",
            parent_email="updated@example.com",
            sms_notifications=True
        )
        
        assert result["status"] == "success"
        assert agent.config.child_name == "UpdatedChild"
        assert agent.config.parent_email == "updated@example.com"
        assert agent.config.sms_notifications == True
    
    def test_invalid_configuration_key(self):
        """Test configuration with invalid key"""
        agent = NotificationAgent()
        
        # Should not raise error, just ignore invalid key
        result = agent.configure_notifications(
            child_name="ValidChild",
            invalid_key="invalid_value"
        )
        
        assert result["status"] == "success"
        assert agent.config.child_name == "ValidChild"
        assert not hasattr(agent.config, 'invalid_key')


class TestNotificationPerformance:
    """Test notification performance scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_notifications_performance(self):
        """Test performance with multiple notifications"""
        import time
        
        agent = NotificationAgent()
        
        with patch.object(agent, '_send_desktop_notification', return_value={"success": True, "channel": "desktop"}):
            
            start_time = time.time()
            
            # Send 10 notifications
            tasks = []
            for i in range(10):
                variables = {
                    "child_name": "TestChild",
                    "content_summary": f"Test content {i}",
                    "category": "test",
                    "reason": "test",
                    "timestamp": "2024-01-01 12:00:00"
                }
                task = agent.send_notification("content_blocked", variables)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (< 2 seconds)
            assert duration < 2.0
            assert len(results) == 10
            assert all(r["status"] == "success" for r in results)
            assert agent.statistics["total_sent"] == 10
    
    def test_statistics_calculation_performance(self):
        """Test statistics calculation performance"""
        agent = NotificationAgent()
        
        # Add many mock notifications
        from notification_agent import NotificationRecord
        for i in range(1000):
            record = NotificationRecord(
                id=f"test{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.DESKTOP],
                recipient="parent",
                subject=f"Test {i}",
                body=f"Test body {i}",
                status=NotificationStatus.SENT
            )
            agent.notification_history.append(record)
        
        import time
        start_time = time.time()
        
        stats = agent.get_notification_statistics()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly even with many records
        assert duration < 0.1
        assert stats["recent_count"] <= 1000


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 