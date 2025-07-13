"""
Session Manager for Parental Control System

This module handles session management, persistent state, and event coordination
for the monitoring system. It provides session tracking, state persistence,
and event history management.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import pickle
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Session information and metadata"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"
    total_events: int = 0
    total_inputs: int = 0
    total_screenshots: int = 0
    total_analyses: int = 0
    total_judgments: int = 0
    total_notifications: int = 0
    errors: int = 0
    configuration: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "total_events": self.total_events,
            "total_inputs": self.total_inputs,
            "total_screenshots": self.total_screenshots,
            "total_analyses": self.total_analyses,
            "total_judgments": self.total_judgments,
            "total_notifications": self.total_notifications,
            "errors": self.errors,
            "configuration": self.configuration or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """Create from dictionary"""
        return cls(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
            status=data["status"],
            total_events=data["total_events"],
            total_inputs=data["total_inputs"],
            total_screenshots=data["total_screenshots"],
            total_analyses=data["total_analyses"],
            total_judgments=data["total_judgments"],
            total_notifications=data["total_notifications"],
            errors=data["errors"],
            configuration=data.get("configuration", {})
        )

@dataclass
class EventRecord:
    """Persistent event record"""
    event_id: str
    session_id: str
    timestamp: datetime
    event_type: str
    input_text: str
    input_hash: str  # For privacy
    screenshot_path: Optional[str]
    analysis_category: Optional[str]
    analysis_confidence: Optional[float]
    judgment_action: Optional[str]
    judgment_confidence: Optional[float]
    notification_sent: bool
    processing_time: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "input_text": self.input_text[:100] + "..." if len(self.input_text) > 100 else self.input_text,
            "input_hash": self.input_hash,
            "screenshot_path": self.screenshot_path,
            "analysis_category": self.analysis_category,
            "analysis_confidence": self.analysis_confidence,
            "judgment_action": self.judgment_action,
            "judgment_confidence": self.judgment_confidence,
            "notification_sent": self.notification_sent,
            "processing_time": self.processing_time,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventRecord':
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            input_text=data["input_text"],
            input_hash=data["input_hash"],
            screenshot_path=data["screenshot_path"],
            analysis_category=data["analysis_category"],
            analysis_confidence=data["analysis_confidence"],
            judgment_action=data["judgment_action"],
            judgment_confidence=data["judgment_confidence"],
            notification_sent=data["notification_sent"],
            processing_time=data["processing_time"],
            error=data.get("error")
        )

class SessionManager:
    """
    Session Manager for Parental Control System
    
    Handles session tracking, state persistence, and event history management.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.sessions_file = self.data_dir / "sessions.json"
        self.events_dir = self.data_dir / "events"
        self.events_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[SessionInfo] = None
        self.sessions: Dict[str, SessionInfo] = {}
        self.event_cache: List[EventRecord] = []
        self.lock = threading.Lock()
        
        # Load existing sessions
        self._load_sessions()
        
        logger.info(f"Session Manager initialized with data directory: {self.data_dir}")
    
    def create_session(self, session_id: str, configuration: Dict[str, Any]) -> SessionInfo:
        """Create a new monitoring session"""
        with self.lock:
            if session_id in self.sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            session = SessionInfo(
                session_id=session_id,
                start_time=datetime.now(),
                configuration=configuration
            )
            
            self.sessions[session_id] = session
            self.current_session = session
            
            # Save session info
            self._save_sessions()
            
            logger.info(f"Created new session: {session_id}")
            return session
    
    def end_session(self, session_id: str) -> Optional[SessionInfo]:
        """End a monitoring session"""
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(f"Session {session_id} not found")
                return None
            
            session = self.sessions[session_id]
            session.end_time = datetime.now()
            session.status = "completed"
            
            # Save events for this session
            self._save_session_events(session_id)
            
            # Save session info
            self._save_sessions()
            
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
            
            logger.info(f"Ended session: {session_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information"""
        return self.sessions.get(session_id)
    
    def get_current_session(self) -> Optional[SessionInfo]:
        """Get current active session"""
        return self.current_session
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get all sessions"""
        return list(self.sessions.values())
    
    def record_event(self, event_data: Dict[str, Any]) -> EventRecord:
        """Record a monitoring event"""
        if not self.current_session:
            raise ValueError("No active session")
        
        # Generate event ID
        event_id = f"{self.current_session.session_id}_{int(time.time() * 1000)}"
        
        # Create input hash for privacy
        input_hash = hashlib.md5(event_data.get('input_text', '').encode()).hexdigest()
        
        # Create event record
        event = EventRecord(
            event_id=event_id,
            session_id=self.current_session.session_id,
            timestamp=datetime.now(),
            event_type=event_data.get('event_type', 'unknown'),
            input_text=event_data.get('input_text', ''),
            input_hash=input_hash,
            screenshot_path=event_data.get('screenshot_path'),
            analysis_category=event_data.get('analysis_category'),
            analysis_confidence=event_data.get('analysis_confidence'),
            judgment_action=event_data.get('judgment_action'),
            judgment_confidence=event_data.get('judgment_confidence'),
            notification_sent=event_data.get('notification_sent', False),
            processing_time=event_data.get('processing_time', 0.0),
            error=event_data.get('error')
        )
        
        with self.lock:
            # Add to cache
            self.event_cache.append(event)
            
            # Update session statistics
            self.current_session.total_events += 1
            if event_data.get('input_text'):
                self.current_session.total_inputs += 1
            if event_data.get('screenshot_path'):
                self.current_session.total_screenshots += 1
            if event_data.get('analysis_category'):
                self.current_session.total_analyses += 1
            if event_data.get('judgment_action'):
                self.current_session.total_judgments += 1
            if event_data.get('notification_sent'):
                self.current_session.total_notifications += 1
            if event_data.get('error'):
                self.current_session.errors += 1
            
            # Periodically save events
            if len(self.event_cache) >= 10:
                self._save_session_events(self.current_session.session_id)
        
        return event
    
    def get_session_events(self, session_id: str, limit: int = 100) -> List[EventRecord]:
        """Get events for a specific session"""
        # First check cache for current session
        if self.current_session and self.current_session.session_id == session_id:
            return sorted(self.event_cache, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        # Load from file
        events_file = self.events_dir / f"{session_id}.json"
        if not events_file.exists():
            return []
        
        try:
            with open(events_file, 'r') as f:
                events_data = json.load(f)
            
            events = [EventRecord.from_dict(data) for data in events_data]
            return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        except Exception as e:
            logger.error(f"Error loading events for session {session_id}: {e}")
            return []
    
    def get_recent_events(self, limit: int = 50) -> List[EventRecord]:
        """Get recent events across all sessions"""
        all_events = []
        
        # Add current session events
        if self.current_session:
            all_events.extend(self.event_cache)
        
        # Add events from recent sessions
        recent_sessions = sorted(
            self.sessions.values(),
            key=lambda x: x.start_time,
            reverse=True
        )[:5]  # Last 5 sessions
        
        for session in recent_sessions:
            if session.session_id != (self.current_session.session_id if self.current_session else None):
                events = self.get_session_events(session.session_id, limit)
                all_events.extend(events)
        
        # Sort by timestamp and limit
        return sorted(all_events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a session"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        events = self.get_session_events(session_id)
        
        # Calculate additional statistics
        categories = {}
        actions = {}
        processing_times = []
        
        for event in events:
            if event.analysis_category:
                categories[event.analysis_category] = categories.get(event.analysis_category, 0) + 1
            if event.judgment_action:
                actions[event.judgment_action] = actions.get(event.judgment_action, 0) + 1
            processing_times.append(event.processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "session_info": session.to_dict(),
            "event_count": len(events),
            "category_distribution": categories,
            "action_distribution": actions,
            "average_processing_time": avg_processing_time,
            "error_rate": session.errors / max(session.total_events, 1),
            "notification_rate": session.total_notifications / max(session.total_events, 1)
        }
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old session data"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with self.lock:
            sessions_to_remove = []
            
            for session_id, session in self.sessions.items():
                if session.end_time and session.end_time < cutoff_date:
                    sessions_to_remove.append(session_id)
                    
                    # Remove events file
                    events_file = self.events_dir / f"{session_id}.json"
                    if events_file.exists():
                        events_file.unlink()
            
            # Remove sessions
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
            
            # Save updated sessions
            self._save_sessions()
            
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
    
    def _load_sessions(self):
        """Load sessions from file"""
        if not self.sessions_file.exists():
            return
        
        try:
            with open(self.sessions_file, 'r') as f:
                sessions_data = json.load(f)
            
            for session_data in sessions_data:
                session = SessionInfo.from_dict(session_data)
                self.sessions[session.session_id] = session
                
                # Set current session if it's active
                if session.status == "active":
                    self.current_session = session
            
            logger.info(f"Loaded {len(self.sessions)} sessions")
        
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            sessions_data = [session.to_dict() for session in self.sessions.values()]
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _save_session_events(self, session_id: str):
        """Save events for a specific session"""
        if not self.event_cache:
            return
        
        events_file = self.events_dir / f"{session_id}.json"
        
        try:
            # Load existing events
            existing_events = []
            if events_file.exists():
                with open(events_file, 'r') as f:
                    existing_events = json.load(f)
            
            # Add new events
            session_events = [
                event for event in self.event_cache
                if event.session_id == session_id
            ]
            
            new_events_data = [event.to_dict() for event in session_events]
            all_events = existing_events + new_events_data
            
            # Save all events
            with open(events_file, 'w') as f:
                json.dump(all_events, f, indent=2)
            
            # Clear cache for this session
            self.event_cache = [
                event for event in self.event_cache
                if event.session_id != session_id
            ]
            
        except Exception as e:
            logger.error(f"Error saving events for session {session_id}: {e}")

# Global session manager instance
_global_session_manager = None

def get_global_session_manager() -> SessionManager:
    """Get or create global session manager instance"""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager

# Export main classes
__all__ = [
    "SessionManager",
    "SessionInfo",
    "EventRecord",
    "get_global_session_manager"
] 