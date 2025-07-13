"""
Monitoring Agent for Parental Control System

This is the main orchestrating agent that coordinates all components:
- Enhanced keylogger for input monitoring
- Screen capture for context analysis
- Gemini multimodal analysis
- Judgment engine for decision making
- Notification system for alerts

The agent provides a unified interface for the complete parental control workflow.
"""

import asyncio
import json
import logging
import time
import weave
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading
import queue
import os

from google.adk import Agent, Runner
from google.adk.tools import FunctionTool

# Import all component tools
from key import (
    start_keylogger_tool,
    stop_keylogger_tool,
    get_current_input_tool,
    clear_input_buffer_tool,
    create_monitoring_agent as create_keylogger_agent
)
from screen_capture import (
    capture_screen_tool,
    get_monitor_info_tool,
    cleanup_temp_files_tool,
    capture_on_input_complete_tool,
    create_screen_capture_agent
)
from analysis_agent import (
    AnalysisAgent,
    AnalysisResult,
    create_analysis_agent
)
from judgment_engine import (
    JudgmentEngine,
    JudgmentResult,
    JudgmentAction,
    create_judgment_agent
)
from notification_agent import (
    NotificationAgent,
    NotificationHelper,
    NotificationConfig
)
from session_manager import (
    SessionManager,
    SessionInfo,
    EventRecord,
    get_global_session_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitoring_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Weave for tracking
try:
    weave.init("parental-control-monitoring")
    #logger.info("Weave initialized for Monitoring Agent")
except Exception as e:
    logger.warning(f"Weave initialization failed: {e}. Continuing without Weave tracking.")

class MonitoringStatus(Enum):
    """Monitoring system status"""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class MonitoringEvent:
    """Event data structure for monitoring workflow"""
    timestamp: datetime
    event_type: str
    input_text: str
    screenshot_path: Optional[str]
    analysis_result: Optional[AnalysisResult]
    judgment_result: Optional[JudgmentResult]
    notification_sent: bool
    processing_time: float
    error: Optional[str] = None

@dataclass
class MonitoringConfig:
    """Configuration for monitoring agent"""
    age_group: str = "elementary"
    strictness_level: str = "moderate"
    enable_notifications: bool = True
    enable_emergency_alerts: bool = True
    screenshot_on_input: bool = True
    cache_enabled: bool = True
    monitoring_interval: float = 0.5  # seconds
    input_completion_threshold: int = 10  # characters
    notification_config: Optional[NotificationConfig] = None
    
    def __post_init__(self):
        if self.notification_config is None:
            self.notification_config = NotificationConfig()

class MonitoringAgent(weave.Model):
    """
    Main Monitoring Agent for Parental Control System
    
    This agent orchestrates all components:
    1. Monitors keyboard input continuously
    2. Captures screen context when input is complete
    3. Analyzes content using Gemini multimodal AI
    4. Applies judgment rules to determine actions
    5. Sends notifications as needed
    6. Tracks all activities and performance
    """
    
    # Define model configuration to allow extra fields
    model_config = {"extra": "allow"}
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        super().__init__()
        
        # Use object.__setattr__ to set attributes on Pydantic model
        object.__setattr__(self, 'config', config or MonitoringConfig())
        object.__setattr__(self, 'status', MonitoringStatus.STOPPED)
        object.__setattr__(self, 'event_history', [])
        object.__setattr__(self, 'session_id', None)
        object.__setattr__(self, 'monitoring_thread', None)
        object.__setattr__(self, 'stop_event', threading.Event())
        object.__setattr__(self, 'event_queue', queue.Queue())
        object.__setattr__(self, 'session_manager', get_global_session_manager())
        
        # Initialize component agents
        object.__setattr__(self, 'analysis_agent', AnalysisAgent(
            age_group=self.config.age_group,
            strictness_level=self.config.strictness_level,
            cache_enabled=self.config.cache_enabled
        ))
        
        from judgment_engine import JudgmentConfig, AgeGroup, StrictnessLevel
        
        # Create judgment config
        age_group_enum = AgeGroup(self.config.age_group)
        strictness_enum = StrictnessLevel(self.config.strictness_level)
        judgment_config = JudgmentConfig(
            age_group=age_group_enum,
            strictness_level=strictness_enum
        )
        
        object.__setattr__(self, 'judgment_engine', JudgmentEngine(config=judgment_config))
        
        object.__setattr__(self, 'notification_agent', NotificationAgent(
            config=self.config.notification_config
        ))
        
        # Statistics tracking
        object.__setattr__(self, 'statistics', {
            'total_events': 0,
            'inputs_processed': 0,
            'screenshots_taken': 0,
            'analyses_completed': 0,
            'judgments_made': 0,
            'notifications_sent': 0,
            'errors': 0,
            'average_processing_time': 0.0,
            'session_start_time': None,
            'uptime': 0.0
        })
        
        logger.info(f"Monitoring Agent initialized for {self.config.age_group} with {self.config.strictness_level} strictness")
    
    @weave.op()
    async def start_monitoring(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start the monitoring system
        
        Args:
            session_id: Optional session identifier for tracking
            
        Returns:
            Dictionary with startup status and session information
        """
        try:
            if self.status == MonitoringStatus.ACTIVE:
                return {
                    "status": "already_active",
                    "session_id": self.session_id,
                    "message": "Monitoring is already active"
                }
            
            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{int(time.time())}"
            
            object.__setattr__(self, 'session_id', session_id)
            object.__setattr__(self, 'status', MonitoringStatus.STARTING)
            
            # Create session in session manager
            session_config = {
                "age_group": self.config.age_group,
                "strictness_level": self.config.strictness_level,
                "enable_notifications": self.config.enable_notifications,
                "screenshot_on_input": self.config.screenshot_on_input,
                "cache_enabled": self.config.cache_enabled
            }
            
            try:
                self.session_manager.create_session(session_id, session_config)
            except ValueError as e:
                # Session already exists, end it first
                self.session_manager.end_session(session_id)
                self.session_manager.create_session(session_id, session_config)
            
            # Start keylogger
            class MockToolContext:
                def __init__(self):
                    self.state = {}
            
            context = MockToolContext()
            keylogger_result = start_keylogger_tool.func(context)
            
            if keylogger_result.get('status') != 'success':
                object.__setattr__(self, 'status', MonitoringStatus.ERROR)
                return {
                    "status": "error",
                    "error": "Failed to start keylogger",
                    "details": keylogger_result
                }
            
            # Reset stop event and start monitoring thread
            self.stop_event.clear()
            object.__setattr__(self, 'monitoring_thread', threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            ))
            self.monitoring_thread.start()
            
            # Update statistics
            new_stats = dict(self.statistics)
            new_stats['session_start_time'] = datetime.now()
            object.__setattr__(self, 'statistics', new_stats)
            
            object.__setattr__(self, 'status', MonitoringStatus.ACTIVE)
            
            logger.info(f"Monitoring started for session: {session_id}")
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Monitoring started successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            object.__setattr__(self, 'status', MonitoringStatus.ERROR)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @weave.op()
    async def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop the monitoring system
        
        Returns:
            Dictionary with shutdown status and session summary
        """
        try:
            if self.status == MonitoringStatus.STOPPED:
                return {
                    "status": "already_stopped",
                    "message": "Monitoring is already stopped"
                }
            
            # Signal stop to monitoring thread
            self.stop_event.set()
            
            # Wait for thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            # Stop keylogger
            class MockToolContext:
                def __init__(self):
                    self.state = {}
            
            context = MockToolContext()
            stop_keylogger_tool.func(context)
            
            # Clean up temporary files
            cleanup_temp_files_tool.func(context)
            
            # End session in session manager
            if self.session_id:
                self.session_manager.end_session(self.session_id)
            
            # Update statistics
            new_stats = dict(self.statistics)
            if new_stats['session_start_time']:
                new_stats['uptime'] = (datetime.now() - new_stats['session_start_time']).total_seconds()
            object.__setattr__(self, 'statistics', new_stats)
            
            object.__setattr__(self, 'status', MonitoringStatus.STOPPED)
            
            session_summary = {
                "session_id": self.session_id,
                "total_events": self.statistics['total_events'],
                "inputs_processed": self.statistics['inputs_processed'],
                "uptime": self.statistics['uptime']
            }
            
            logger.info(f"Monitoring stopped for session: {self.session_id}")
            
            return {
                "status": "success",
                "message": "Monitoring stopped successfully",
                "session_summary": session_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        logger.info("Monitoring loop started")
        
        while not self.stop_event.is_set():
            try:
                # Check for input completion
                context = type('MockToolContext', (), {'state': {}})()
                input_status = get_current_input_tool.func(context)
                
                if input_status.get('input_complete', False):
                    # Process the completed input
                    asyncio.run(self._process_input_event(input_status))
                
                # Wait before next check
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Update error statistics
                new_stats = dict(self.statistics)
                new_stats['errors'] += 1
                object.__setattr__(self, 'statistics', new_stats)
                
                # Continue monitoring despite errors
                time.sleep(self.config.monitoring_interval)
        
        logger.info("Monitoring loop stopped")
    
    async def _process_input_event(self, input_status: Dict[str, Any]):
        """Process a completed input event through the full workflow"""
        start_time = time.time()
        
        # Extract text from buffer structure
        input_text = ""
        enter_pressed = False
        if input_status.get('buffer') and isinstance(input_status['buffer'], dict):
            input_text = input_status['buffer'].get('text', '')
            enter_pressed = input_status['buffer'].get('enter_pressed', False)
        
        # Skip processing if input is only whitespace/newlines
        if not input_text or not input_text.strip():
            logger.debug("Skipping empty or whitespace-only input")
            # Clear input buffer to prevent loops
            try:
                context = type('MockToolContext', (), {'state': {}})()
                clear_input_buffer_tool.func(context)
            except Exception as e:
                logger.error(f"Error clearing input buffer: {e}")
            return
        
        event = MonitoringEvent(
            timestamp=datetime.now(),
            event_type="input_complete",
            input_text=input_text,
            screenshot_path=None,
            analysis_result=None,
            judgment_result=None,
            notification_sent=False,
            processing_time=0.0
        )
        
        try:
            # Step 1: Capture screen if enabled
            screenshot_path = None
            if self.config.screenshot_on_input:
                context = type('MockToolContext', (), {'state': {}})()
                screenshot_result = capture_screen_tool(context)
                if screenshot_result.get('success', False):
                    screenshot_path = screenshot_result.get('screenshot_path')
                    event.screenshot_path = screenshot_path
                    
                    # Update statistics
                    new_stats = dict(self.statistics)
                    new_stats['screenshots_taken'] += 1
                    object.__setattr__(self, 'statistics', new_stats)
            
            # Step 2: Analyze content
            # Force analysis if Enter was pressed, otherwise let completeness check decide
            analysis_result = await self.analysis_agent.analyze_input_context(
                event.input_text, 
                screenshot_path,
                force_analysis=enter_pressed
            )
            
            # If analysis returns None, input is incomplete - keep buffer and wait
            if analysis_result is None:
                logger.debug(f"Input incomplete, keeping buffer: '{input_text[:50]}...'")
                return  # Don't clear buffer, let input continue accumulating
            
            event.analysis_result = analysis_result
            
            # Update statistics
            new_stats = dict(self.statistics)
            new_stats['analyses_completed'] += 1
            object.__setattr__(self, 'statistics', new_stats)
            
            # Step 3: Apply judgment
            judgment_result = await self.judgment_engine.judge_content({
                'input_text': event.input_text,
                'category': analysis_result.category,
                'confidence': analysis_result.confidence,
                'age_appropriateness': analysis_result.age_appropriateness,
                'safety_concerns': analysis_result.safety_concerns,
                'educational_value': analysis_result.educational_value,
                'parental_action': analysis_result.parental_action,
                'context_summary': analysis_result.context_summary
            })
            event.judgment_result = judgment_result
            
            # Update statistics
            new_stats = dict(self.statistics)
            new_stats['judgments_made'] += 1
            object.__setattr__(self, 'statistics', new_stats)
            
            # Step 4: Send notifications if needed
            if self.config.enable_notifications and judgment_result.action != JudgmentAction.ALLOW:
                await self._send_appropriate_notification(analysis_result, judgment_result)
                event.notification_sent = True
                
                # Update statistics
                new_stats = dict(self.statistics)
                new_stats['notifications_sent'] += 1
                object.__setattr__(self, 'statistics', new_stats)
            
            # Step 5: Clear input buffer only after successful analysis
            context = type('MockToolContext', (), {'state': {}})()
            clear_input_buffer_tool.func(context)
            
            # Calculate processing time
            event.processing_time = time.time() - start_time
            
            # Update statistics
            new_stats = dict(self.statistics)
            new_stats['total_events'] += 1
            new_stats['inputs_processed'] += 1
            new_stats['average_processing_time'] = (
                (new_stats['average_processing_time'] * (new_stats['total_events'] - 1) + event.processing_time) /
                new_stats['total_events']
            )
            object.__setattr__(self, 'statistics', new_stats)
            
            logger.info(f"Processed input event: {analysis_result.category} -> {judgment_result.action.value} ({event.processing_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"Error processing input event: {e}")
            event.error = str(e)
            
            # Always clear input buffer on error to prevent loops
            try:
                context = type('MockToolContext', (), {'state': {}})()
                clear_input_buffer_tool.func(context)
            except Exception as clear_error:
                logger.error(f"Error clearing input buffer after error: {clear_error}")
            
            # Update error statistics
            new_stats = dict(self.statistics)
            new_stats['errors'] += 1
            object.__setattr__(self, 'statistics', new_stats)
        
        # Record event in session manager only if analysis was completed
        if event.analysis_result is not None:
            try:
                event_data = {
                    'event_type': event.event_type,
                    'input_text': event.input_text,
                    'screenshot_path': event.screenshot_path,
                    'analysis_category': event.analysis_result.category if event.analysis_result else None,
                    'analysis_confidence': event.analysis_result.confidence if event.analysis_result else None,
                    'judgment_action': event.judgment_result.action.value if event.judgment_result else None,
                    'judgment_confidence': event.judgment_result.confidence if event.judgment_result else None,
                    'notification_sent': event.notification_sent,
                    'processing_time': event.processing_time,
                    'error': event.error
                }
                self.session_manager.record_event(event_data)
            except Exception as e:
                logger.error(f"Error recording event: {e}")
            
            # Add event to history only if analysis was completed
            new_history = list(self.event_history)
            new_history.append(event)
            # Keep only last 100 events
            if len(new_history) > 100:
                new_history = new_history[-100:]
            object.__setattr__(self, 'event_history', new_history)
    
    async def _send_appropriate_notification(self, analysis_result: AnalysisResult, judgment_result: JudgmentResult):
        """Send appropriate notification based on analysis and judgment"""
        try:
            if judgment_result.action == JudgmentAction.BLOCK:
                if any(concern in ['violence', 'adult_content', 'dangerous_activities'] 
                       for concern in analysis_result.safety_concerns):
                    # Emergency notification
                    await self.notification_agent.send_emergency_notification(
                        content_summary=analysis_result.context_summary,
                        threat_level="high",
                        additional_details={
                            "category": analysis_result.category,
                            "confidence": analysis_result.confidence,
                            "safety_concerns": analysis_result.safety_concerns
                        }
                    )
                else:
                    # Content blocked notification
                    await self.notification_agent.send_notification(
                        template_id="content_blocked",
                        variables={
                            "child_name": self.config.notification_config.child_name,
                            "content_summary": analysis_result.context_summary,
                            "category": analysis_result.category,
                            "reason": judgment_result.reasoning,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
            
            elif judgment_result.action == JudgmentAction.RESTRICT:
                # Inappropriate content notification
                await self.notification_agent.send_notification(
                    template_id="inappropriate_content",
                    variables={
                        "child_name": self.config.notification_config.child_name,
                        "content_summary": analysis_result.context_summary,
                        "category": analysis_result.category,
                        "confidence": f"{analysis_result.confidence:.1%}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    @weave.op()
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics"""
        return {
            "status": self.status.value,
            "session_id": self.session_id,
            "statistics": self.statistics,
            "config": {
                "age_group": self.config.age_group,
                "strictness_level": self.config.strictness_level,
                "enable_notifications": self.config.enable_notifications,
                "screenshot_on_input": self.config.screenshot_on_input,
                "cache_enabled": self.config.cache_enabled
            },
            "recent_events": len(self.event_history),
            "timestamp": datetime.now().isoformat()
        }
    
    @weave.op()
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent monitoring events"""
        # Get events from session manager for better persistence
        if self.session_id:
            try:
                events = self.session_manager.get_recent_events(limit)
                return [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type,
                        "input_text": event.input_text[:100] + "..." if len(event.input_text) > 100 else event.input_text,
                        "category": event.analysis_category,
                        "action": event.judgment_action,
                        "notification_sent": event.notification_sent,
                        "processing_time": event.processing_time,
                        "error": event.error
                    }
                    for event in events
                ]
            except Exception as e:
                logger.error(f"Error getting events from session manager: {e}")
        
        # Fallback to local event history
        events = sorted(self.event_history, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "input_text": event.input_text[:100] + "..." if len(event.input_text) > 100 else event.input_text,
                "category": event.analysis_result.category if event.analysis_result else None,
                "action": event.judgment_result.action.value if event.judgment_result else None,
                "notification_sent": event.notification_sent,
                "processing_time": event.processing_time,
                "error": event.error
            }
            for event in events
        ]
    
    @weave.op()
    def configure_monitoring(self, **config_updates) -> Dict[str, Any]:
        """Update monitoring configuration"""
        try:
            # Update configuration
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    
                    # Update component configurations
                    if key in ['age_group', 'strictness_level']:
                        self.analysis_agent.configure_settings(
                            self.config.age_group,
                            self.config.strictness_level
                        )
                        self.judgment_engine.configure_judgment_settings(
                            age_group=self.config.age_group,
                            strictness_level=self.config.strictness_level
                        )
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            return {
                "status": "success",
                "updated_config": {
                    "age_group": self.config.age_group,
                    "strictness_level": self.config.strictness_level,
                    "enable_notifications": self.config.enable_notifications,
                    "screenshot_on_input": self.config.screenshot_on_input,
                    "cache_enabled": self.config.cache_enabled
                },
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
    async def process_manual_input(self, input_text: str, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Manually process input through the full workflow (for testing)
        
        Args:
            input_text: Text input to analyze
            screenshot_path: Optional path to screenshot
            
        Returns:
            Dictionary with complete workflow results
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze content (force analysis for manual input)
            analysis_result = await self.analysis_agent.analyze_input_context(
                input_text, 
                screenshot_path,
                force_analysis=True  # Always force analysis for manual input
            )
            
            # Step 2: Apply judgment
            judgment_result = await self.judgment_engine.judge_content({
                'input_text': input_text,
                'category': analysis_result.category,
                'confidence': analysis_result.confidence,
                'age_appropriateness': analysis_result.age_appropriateness,
                'safety_concerns': analysis_result.safety_concerns,
                'educational_value': analysis_result.educational_value,
                'parental_action': analysis_result.parental_action,
                'context_summary': analysis_result.context_summary
            })
            
            # Step 3: Send notification if needed
            notification_result = None
            if self.config.enable_notifications and judgment_result.action != JudgmentAction.ALLOW:
                await self._send_appropriate_notification(analysis_result, judgment_result)
                notification_result = {"status": "sent", "action": judgment_result.action.value}
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "input_text": input_text,
                "analysis": {
                    "category": analysis_result.category,
                    "confidence": analysis_result.confidence,
                    "safety_concerns": analysis_result.safety_concerns,
                    "educational_value": analysis_result.educational_value,
                    "context_summary": analysis_result.context_summary
                },
                "judgment": {
                    "action": judgment_result.action.value,
                    "confidence": judgment_result.confidence,
                    "reasoning": judgment_result.reasoning
                },
                "notification": notification_result,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual processing: {e}")
            return {
                "status": "error",
                "error": str(e),
                "input_text": input_text,
                "timestamp": datetime.now().isoformat()
            }
    
    def predict(self, **kwargs) -> Dict[str, Any]:
        """Weave Model compatibility method"""
        return self.get_monitoring_status()


# ADK Function Tool implementations
async def start_monitoring_tool(context) -> Dict[str, Any]:
    """ADK tool to start monitoring"""
    agent = get_global_monitoring_agent()
    return await agent.start_monitoring()

async def stop_monitoring_tool(context) -> Dict[str, Any]:
    """ADK tool to stop monitoring"""
    agent = get_global_monitoring_agent()
    return await agent.stop_monitoring()

def get_monitoring_status_tool(context) -> Dict[str, Any]:
    """ADK tool to get monitoring status"""
    agent = get_global_monitoring_agent()
    return agent.get_monitoring_status()

def get_recent_events_tool(context) -> List[Dict[str, Any]]:
    """ADK tool to get recent events"""
    agent = get_global_monitoring_agent()
    limit = getattr(context, 'limit', 10)
    return agent.get_recent_events(limit)

def configure_monitoring_tool(context) -> Dict[str, Any]:
    """ADK tool to configure monitoring"""
    agent = get_global_monitoring_agent()
    config_updates = getattr(context, 'config_updates', {})
    return agent.configure_monitoring(**config_updates)

async def process_manual_input_tool(context) -> Dict[str, Any]:
    """ADK tool to manually process input"""
    agent = get_global_monitoring_agent()
    input_text = getattr(context, 'input_text', '')
    screenshot_path = getattr(context, 'screenshot_path', None)
    return await agent.process_manual_input(input_text, screenshot_path)

# Create ADK Function Tools
start_monitoring_function_tool = FunctionTool(func=start_monitoring_tool)
stop_monitoring_function_tool = FunctionTool(func=stop_monitoring_tool)
get_monitoring_status_function_tool = FunctionTool(func=get_monitoring_status_tool)
get_recent_events_function_tool = FunctionTool(func=get_recent_events_tool)
configure_monitoring_function_tool = FunctionTool(func=configure_monitoring_tool)
process_manual_input_function_tool = FunctionTool(func=process_manual_input_tool)

# Global monitoring agent instance
_global_monitoring_agent = None

def get_global_monitoring_agent() -> MonitoringAgent:
    """Get or create global monitoring agent instance"""
    global _global_monitoring_agent
    if _global_monitoring_agent is None:
        _global_monitoring_agent = MonitoringAgent()
    return _global_monitoring_agent

# Create complete monitoring agent for ADK
def create_monitoring_agent() -> Agent:
    """Create a complete Monitoring Agent for parental control system"""
    
    return Agent(
        name="MonitoringAgent",
        model="gemini-1.5-flash",
        description="A comprehensive monitoring agent that orchestrates all parental control components",
        instruction="""
        You are the main orchestrating agent for a comprehensive parental control system.
        
        Your capabilities include:
        1. start_monitoring: Start the complete monitoring system
        2. stop_monitoring: Stop monitoring and get session summary
        3. get_monitoring_status: Get current status and statistics
        4. get_recent_events: Get recent monitoring events and their outcomes
        5. configure_monitoring: Update monitoring configuration
        6. process_manual_input: Manually process input for testing
        
        Your system orchestrates:
        - Enhanced keylogger for input monitoring
        - Screen capture for context analysis
        - Gemini multimodal AI for content analysis
        - Judgment engine for decision making
        - Notification system for parent/child alerts
        
        You provide:
        - Real-time monitoring of all keyboard input
        - Context-aware analysis using screen captures
        - Age-appropriate content filtering
        - Intelligent judgment and action recommendations
        - Multi-channel notification system
        - Comprehensive logging and analytics
        
        Your workflow:
        1. Monitor keyboard input continuously
        2. Capture screen when input is complete
        3. Analyze content using multimodal AI
        4. Apply judgment rules based on age/strictness
        5. Send appropriate notifications
        6. Log all activities for review
        
        Always prioritize child safety while maintaining age-appropriate freedom.
        Provide clear status updates and handle errors gracefully.
        """,
        tools=[
            start_monitoring_function_tool,
            stop_monitoring_function_tool,
            get_monitoring_status_function_tool,
            get_recent_events_function_tool,
            configure_monitoring_function_tool,
            process_manual_input_function_tool
        ]
    )

# Export main classes
__all__ = [
    "MonitoringAgent",
    "MonitoringConfig",
    "MonitoringStatus",
    "MonitoringEvent",
    "start_monitoring_function_tool",
    "stop_monitoring_function_tool",
    "get_monitoring_status_function_tool",
    "get_recent_events_function_tool",
    "configure_monitoring_function_tool",
    "process_manual_input_function_tool",
    "create_monitoring_agent",
    "get_global_monitoring_agent"
] 