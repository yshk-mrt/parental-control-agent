"""
Notification Agent for Parental Control System

This agent handles all notification functionality including:
- Parent notifications (desktop, email, SMS)
- Child notifications (age-appropriate messaging)
- Emergency notifications (immediate alerts)
- Notification templates and customization
- Delivery tracking and logging
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal, Union
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import platform
import weave
from google.adk.tools import FunctionTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"

class NotificationChannel(Enum):
    """Available notification channels"""
    DESKTOP = "desktop"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

@dataclass
class NotificationConfig:
    """Configuration for notification preferences"""
    parent_email: Optional[str] = None
    parent_phone: Optional[str] = None
    child_name: str = "Child"
    parent_name: str = "Parent"
    desktop_notifications: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    emergency_channels: List[str] = None
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    
    def __post_init__(self):
        if self.emergency_channels is None:
            self.emergency_channels = ["desktop", "email"]

@dataclass
class NotificationTemplate:
    """Template for notification messages"""
    id: str
    name: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    subject_template: str
    body_template: str
    child_message_template: Optional[str] = None
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []

@dataclass
class NotificationRecord:
    """Record of sent notification"""
    id: str
    timestamp: datetime
    priority: NotificationPriority
    channels: List[NotificationChannel]
    recipient: str
    subject: str
    body: str
    status: NotificationStatus
    template_id: Optional[str] = None
    judgment_id: Optional[str] = None
    delivery_attempts: int = 0
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None

class NotificationAgent(weave.Model):
    """
    Notification Agent for Parental Control System
    
    Handles all notification functionality including parent/child notifications,
    emergency alerts, and delivery tracking with Weave integration.
    """
    
    # Define model configuration to allow extra fields
    model_config = {"extra": "allow"}
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        super().__init__()
        
        # Use object.__setattr__ to set attributes on Pydantic model
        object.__setattr__(self, 'config', config or NotificationConfig())
        object.__setattr__(self, 'notification_history', [])
        object.__setattr__(self, 'templates', self._load_default_templates())
        object.__setattr__(self, 'statistics', {
            "total_sent": 0,
            "by_priority": {p.value: 0 for p in NotificationPriority},
            "by_channel": {c.value: 0 for c in NotificationChannel},
            "by_status": {s.value: 0 for s in NotificationStatus},
            "emergency_count": 0,
            "failed_deliveries": 0
        })
        
        # Initialize Weave tracking
        try:
            weave.init("parental-control-notifications")
            logger.info("Weave tracking initialized for notifications")
        except Exception as e:
            logger.warning(f"Weave initialization failed: {e}")
    
    def _load_default_templates(self) -> Dict[str, NotificationTemplate]:
        """Load default notification templates"""
        templates = {
            "content_blocked": NotificationTemplate(
                id="content_blocked",
                name="Content Blocked",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.DESKTOP, NotificationChannel.EMAIL],
                subject_template="Content Blocked - {child_name}",
                body_template="Your child {child_name} attempted to access blocked content:\n\nContent: {content_summary}\nCategory: {category}\nReason: {reason}\nTime: {timestamp}",
                child_message_template="This content has been blocked as it's not appropriate for your age group.",
                variables=["child_name", "content_summary", "category", "reason", "timestamp"]
            ),
            "inappropriate_content": NotificationTemplate(
                id="inappropriate_content",
                name="Inappropriate Content Warning",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.DESKTOP, NotificationChannel.EMAIL],
                subject_template="Inappropriate Content Alert - {child_name}",
                body_template="Your child {child_name} accessed content that may need attention:\n\nContent: {content_summary}\nCategory: {category}\nConfidence: {confidence}\nTime: {timestamp}",
                child_message_template="Please be mindful of the content you're viewing. Consider discussing this with your parents.",
                variables=["child_name", "content_summary", "category", "confidence", "timestamp"]
            ),
            "emergency_alert": NotificationTemplate(
                id="emergency_alert",
                name="Emergency Alert",
                priority=NotificationPriority.EMERGENCY,
                channels=[NotificationChannel.DESKTOP, NotificationChannel.EMAIL, NotificationChannel.SMS],
                subject_template="EMERGENCY ALERT - {child_name}",
                body_template="IMMEDIATE ATTENTION REQUIRED\n\nYour child {child_name} has encountered potentially dangerous content:\n\nContent: {content_summary}\nThreat Level: {threat_level}\nTime: {timestamp}\n\nPlease check on your child immediately.",
                child_message_template="This content contains serious safety concerns. Please speak with your parents immediately.",
                variables=["child_name", "content_summary", "threat_level", "timestamp"]
            ),
            "monitoring_alert": NotificationTemplate(
                id="monitoring_alert",
                name="Monitoring Alert",
                priority=NotificationPriority.LOW,
                channels=[NotificationChannel.EMAIL],
                subject_template="Activity Summary - {child_name}",
                body_template="Daily activity summary for {child_name}:\n\nTotal time: {total_time}\nWebsites visited: {website_count}\nContent categories: {categories}\nConcerns: {concern_count}\n\nDetailed report attached.",
                variables=["child_name", "total_time", "website_count", "categories", "concern_count"]
            ),
            "system_status": NotificationTemplate(
                id="system_status",
                name="System Status",
                priority=NotificationPriority.LOW,
                channels=[NotificationChannel.DESKTOP],
                subject_template="Parental Control System Status",
                body_template="System status update:\n\nStatus: {status}\nUptime: {uptime}\nLast check: {last_check}\n\n{details}",
                variables=["status", "uptime", "last_check", "details"]
            )
        }
        return templates
    
    @weave.op()
    async def send_notification(self, 
                               template_id: str,
                               variables: Dict[str, Any],
                               recipient: str = "parent",
                               channels: Optional[List[str]] = None,
                               priority_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification using specified template
        
        Args:
            template_id: ID of the notification template to use
            variables: Variables to substitute in template
            recipient: Target recipient (parent/child)
            channels: Override channels for delivery
            priority_override: Override template priority
            
        Returns:
            Dictionary with notification status and details
        """
        try:
            # Get template
            if template_id not in self.templates:
                raise ValueError(f"Template '{template_id}' not found")
            
            template = self.templates[template_id]
            
            # Override priority if specified
            priority = NotificationPriority(priority_override) if priority_override else template.priority
            
            # Override channels if specified
            notification_channels = []
            if channels:
                notification_channels = [NotificationChannel(c) for c in channels]
            else:
                notification_channels = template.channels
            
            # Check quiet hours for non-emergency notifications
            if priority != NotificationPriority.EMERGENCY and self._is_quiet_hours():
                logger.info(f"Delaying notification due to quiet hours: {template_id}")
                return {
                    "status": "delayed",
                    "reason": "quiet_hours",
                    "template_id": template_id,
                    "scheduled_for": self._get_next_active_time()
                }
            
            # Render message content
            subject = self._render_template(template.subject_template, variables)
            body = self._render_template(template.body_template, variables)
            
            # Create notification record
            notification_id = f"not_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{template_id}"
            record = NotificationRecord(
                id=notification_id,
                timestamp=datetime.now(),
                priority=priority,
                channels=notification_channels,
                recipient=recipient,
                subject=subject,
                body=body,
                status=NotificationStatus.PENDING,
                template_id=template_id,
                judgment_id=variables.get("judgment_id")
            )
            
            # Send through each channel
            delivery_results = {}
            for channel in notification_channels:
                try:
                    if channel == NotificationChannel.DESKTOP:
                        result = await self._send_desktop_notification(subject, body, priority)
                    elif channel == NotificationChannel.EMAIL:
                        result = await self._send_email_notification(subject, body, priority)
                    elif channel == NotificationChannel.SMS:
                        result = await self._send_sms_notification(subject, body, priority)
                    elif channel == NotificationChannel.IN_APP:
                        result = await self._send_in_app_notification(subject, body, priority)
                    else:
                        result = {"success": False, "error": f"Unknown channel: {channel}"}
                    
                    delivery_results[channel.value] = result
                    
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel.value}: {e}")
                    delivery_results[channel.value] = {"success": False, "error": str(e)}
            
            # Update record status
            successful_deliveries = sum(1 for r in delivery_results.values() if r.get("success"))
            if successful_deliveries > 0:
                record.status = NotificationStatus.SENT
                record.delivered_at = datetime.now()
            else:
                record.status = NotificationStatus.FAILED
                record.error_message = "All delivery channels failed"
            
            # Store record and update statistics
            new_history = list(self.notification_history)
            new_history.append(record)
            object.__setattr__(self, 'notification_history', new_history)
            self._update_statistics(record, successful_deliveries > 0)
            
            # Send child notification if applicable
            child_result = None
            if recipient == "parent" and template.child_message_template:
                child_message = self._render_template(template.child_message_template, variables)
                child_result = await self._send_child_notification(child_message, priority)
            
            return {
                "status": "success" if successful_deliveries > 0 else "failed",
                "notification_id": notification_id,
                "delivery_results": delivery_results,
                "child_notification": child_result,
                "timestamp": record.timestamp.isoformat(),
                "channels_attempted": len(notification_channels),
                "channels_successful": successful_deliveries
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "status": "error",
                "error": str(e),
                "template_id": template_id,
                "timestamp": datetime.now().isoformat()
            }
    
    @weave.op()
    async def send_emergency_notification(self, 
                                        content_summary: str,
                                        threat_level: str,
                                        additional_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send emergency notification with immediate delivery
        
        Args:
            content_summary: Summary of dangerous content
            threat_level: Level of threat (high/critical)
            additional_details: Additional context information
            
        Returns:
            Dictionary with emergency notification status
        """
        try:
            variables = {
                "child_name": self.config.child_name,
                "content_summary": content_summary,
                "threat_level": threat_level,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if additional_details:
                variables.update(additional_details)
            
            # Force all emergency channels
            emergency_channels = ["desktop", "email"]
            if self.config.sms_notifications and self.config.parent_phone:
                emergency_channels.append("sms")
            
            result = await self.send_notification(
                template_id="emergency_alert",
                variables=variables,
                recipient="parent",
                channels=emergency_channels,
                priority_override="emergency"
            )
            
            # Update emergency statistics
            new_stats = dict(self.statistics)
            new_stats["emergency_count"] += 1
            object.__setattr__(self, 'statistics', new_stats)
            
            logger.warning(f"Emergency notification sent: {content_summary}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending emergency notification: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _send_desktop_notification(self, subject: str, body: str, priority: NotificationPriority) -> Dict[str, Any]:
        """Send desktop notification"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Use osascript for macOS notifications
                script = f'''
                display notification "{body}" with title "{subject}" sound name "Glass"
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                
            elif platform.system() == "Linux":
                # Use notify-send for Linux
                subprocess.run(["notify-send", subject, body], check=True)
                
            elif platform.system() == "Windows":
                # Use Windows toast notifications
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(subject, body, duration=10)
                except ImportError:
                    logger.warning("win10toast not available, using fallback")
                    return {"success": False, "error": "Windows notifications not available"}
            
            return {"success": True, "channel": "desktop", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Desktop notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_email_notification(self, subject: str, body: str, priority: NotificationPriority) -> Dict[str, Any]:
        """Send email notification"""
        try:
            if not self.config.parent_email:
                return {"success": False, "error": "No parent email configured"}
            
            # Use environment variables for email configuration
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            
            if not email_user or not email_password:
                return {"success": False, "error": "Email credentials not configured"}
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = self.config.parent_email
            msg['Subject'] = f"[Parental Control] {subject}"
            
            # Add priority header for emergency notifications
            if priority == NotificationPriority.EMERGENCY:
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            return {"success": True, "channel": "email", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms_notification(self, subject: str, body: str, priority: NotificationPriority) -> Dict[str, Any]:
        """Send SMS notification (placeholder for SMS service integration)"""
        try:
            if not self.config.parent_phone:
                return {"success": False, "error": "No parent phone configured"}
            
            # This would integrate with SMS service (Twilio, AWS SNS, etc.)
            # For now, return placeholder
            logger.info(f"SMS notification would be sent to {self.config.parent_phone}: {subject}")
            
            return {"success": True, "channel": "sms", "timestamp": datetime.now().isoformat(), "note": "SMS service not implemented"}
            
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_in_app_notification(self, subject: str, body: str, priority: NotificationPriority) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # Store in-app notification for dashboard/UI
            notification_data = {
                "subject": subject,
                "body": body,
                "priority": priority.value,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            # This would typically store in a database or message queue
            # For now, just log it
            logger.info(f"In-app notification: {subject}")
            
            return {"success": True, "channel": "in_app", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_child_notification(self, message: str, priority: NotificationPriority) -> Dict[str, Any]:
        """Send age-appropriate notification to child"""
        try:
            # Send desktop notification to child
            if platform.system() == "Darwin":  # macOS
                script = f'''
                display notification "{message}" with title "Digital Safety Reminder" sound name "Ping"
                '''
                subprocess.run(["osascript", "-e", script], check=True)
            
            return {"success": True, "channel": "child_desktop", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Child notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(self.config.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(self.config.quiet_hours_end, "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Quiet hours cross midnight
                return now >= start_time or now <= end_time
        except Exception:
            return False
    
    def _get_next_active_time(self) -> str:
        """Get next time when notifications can be sent"""
        try:
            now = datetime.now()
            end_time = datetime.strptime(self.config.quiet_hours_end, "%H:%M").time()
            next_active = datetime.combine(now.date(), end_time)
            
            if next_active <= now:
                next_active += timedelta(days=1)
            
            return next_active.isoformat()
        except Exception:
            return (datetime.now() + timedelta(hours=1)).isoformat()
    
    def _update_statistics(self, record: NotificationRecord, success: bool):
        """Update notification statistics"""
        # Create a new statistics dict to avoid Pydantic tracking issues
        new_stats = dict(self.statistics)
        new_stats["total_sent"] += 1
        new_stats["by_priority"][record.priority.value] += 1
        new_stats["by_status"][record.status.value] += 1
        
        for channel in record.channels:
            new_stats["by_channel"][channel.value] += 1
        
        if not success:
            new_stats["failed_deliveries"] += 1
        
        # Update statistics using object.__setattr__
        object.__setattr__(self, 'statistics', new_stats)
    
    @weave.op()
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification statistics and analytics"""
        recent_notifications = [
            n for n in self.notification_history 
            if n.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_statistics": self.statistics,
            "recent_count": len(recent_notifications),
            "recent_emergency_count": len([n for n in recent_notifications if n.priority == NotificationPriority.EMERGENCY]),
            "average_daily_notifications": len(recent_notifications) / 7 if recent_notifications else 0,
            "success_rate": ((self.statistics["total_sent"] - self.statistics["failed_deliveries"]) / max(self.statistics["total_sent"], 1)) * 100,
            "last_notification": self.notification_history[-1].timestamp.isoformat() if self.notification_history else None
        }
    
    @weave.op()
    def configure_notifications(self, **config_updates) -> Dict[str, Any]:
        """Update notification configuration"""
        try:
            # Create a new config object to avoid Pydantic issues
            new_config = self.config
            for key, value in config_updates.items():
                if hasattr(new_config, key):
                    setattr(new_config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            return {
                "status": "success",
                "updated_config": asdict(new_config),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @weave.op()
    def get_notification_history(self, limit: int = 50, priority_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notification history with optional filtering"""
        try:
            history = self.notification_history
            
            if priority_filter:
                priority_enum = NotificationPriority(priority_filter)
                history = [n for n in history if n.priority == priority_enum]
            
            # Sort by timestamp (newest first) and limit
            history = sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return [
                {
                    "id": n.id,
                    "timestamp": n.timestamp.isoformat(),
                    "priority": n.priority.value,
                    "channels": [c.value for c in n.channels],
                    "recipient": n.recipient,
                    "subject": n.subject,
                    "status": n.status.value,
                    "template_id": n.template_id,
                    "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
                    "error_message": n.error_message
                }
                for n in history
            ]
        except Exception as e:
            logger.error(f"Error retrieving notification history: {e}")
            return []
    
    def predict(self, **kwargs) -> Dict[str, Any]:
        """Weave Model compatibility method"""
        return self.get_notification_statistics()


class NotificationHelper:
    """Helper class for easy notification agent usage"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.agent = NotificationAgent(config)
    
    async def notify_content_blocked(self, content_summary: str, category: str, reason: str, child_name: str = None) -> Dict[str, Any]:
        """Quick method to send content blocked notification"""
        variables = {
            "child_name": child_name or self.agent.config.child_name,
            "content_summary": content_summary,
            "category": category,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return await self.agent.send_notification("content_blocked", variables)
    
    async def notify_inappropriate_content(self, content_summary: str, category: str, confidence: float, child_name: str = None) -> Dict[str, Any]:
        """Quick method to send inappropriate content notification"""
        variables = {
            "child_name": child_name or self.agent.config.child_name,
            "content_summary": content_summary,
            "category": category,
            "confidence": f"{confidence:.1%}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return await self.agent.send_notification("inappropriate_content", variables)
    
    async def emergency_alert(self, content_summary: str, threat_level: str = "high") -> Dict[str, Any]:
        """Quick method to send emergency alert"""
        return await self.agent.send_emergency_notification(content_summary, threat_level)


# ADK Function Tools

@weave.op()
async def send_notification_tool(template_id: str, variables: Dict[str, Any], 
                               recipient: str = "parent", channels: Optional[List[str]] = None, 
                               priority_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a notification using a template
    
    Args:
        template_id: ID of the notification template to use
        variables: Variables to substitute in the template
        recipient: Target recipient (parent/child)
        channels: Override delivery channels
        priority_override: Override template priority
        
    Returns:
        Dictionary with notification status and details
    """
    agent = get_global_notification_agent()
    return await agent.send_notification(template_id, variables, recipient, channels, priority_override)


@weave.op()
async def send_emergency_notification_tool(content_summary: str, threat_level: str = "high", 
                                         additional_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Send an emergency notification with immediate delivery
    
    Args:
        content_summary: Summary of the dangerous content
        threat_level: Level of threat (high/critical)
        additional_details: Additional context information
        
    Returns:
        Dictionary with emergency notification status
    """
    agent = get_global_notification_agent()
    return await agent.send_emergency_notification(content_summary, threat_level, additional_details)


@weave.op()
def get_notification_statistics_tool() -> Dict[str, Any]:
    """
    Get notification statistics and analytics
    
    Returns:
        Dictionary with notification statistics
    """
    agent = get_global_notification_agent()
    return agent.get_notification_statistics()


@weave.op()
def configure_notifications_tool(**config_updates) -> Dict[str, Any]:
    """
    Update notification configuration
    
    Args:
        **config_updates: Configuration updates
        
    Returns:
        Dictionary with update status
    """
    agent = get_global_notification_agent()
    return agent.configure_notifications(**config_updates)


@weave.op()
def get_notification_history_tool(limit: int = 50, priority_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get notification history with optional filtering
    
    Args:
        limit: Maximum number of notifications to return
        priority_filter: Filter by priority level
        
    Returns:
        List of notification records
    """
    agent = get_global_notification_agent()
    return agent.get_notification_history(limit, priority_filter)


# Create ADK Function Tools
send_notification_function_tool = FunctionTool(func=send_notification_tool)
send_emergency_notification_function_tool = FunctionTool(func=send_emergency_notification_tool)
get_notification_statistics_function_tool = FunctionTool(func=get_notification_statistics_tool)
configure_notifications_function_tool = FunctionTool(func=configure_notifications_tool)
get_notification_history_function_tool = FunctionTool(func=get_notification_history_tool)

# Global notification agent instance
_global_notification_agent = None

def get_global_notification_agent() -> NotificationAgent:
    """Get or create global notification agent instance"""
    global _global_notification_agent
    if _global_notification_agent is None:
        _global_notification_agent = NotificationAgent()
    return _global_notification_agent


# Export main classes
__all__ = [
    "NotificationAgent",
    "NotificationHelper", 
    "NotificationConfig",
    "NotificationPriority",
    "NotificationChannel",
    "NotificationStatus",
    "send_notification_function_tool",
    "send_emergency_notification_function_tool",
    "get_notification_statistics_function_tool",
    "configure_notifications_function_tool",
    "get_notification_history_function_tool",
    "get_global_notification_agent"
] 