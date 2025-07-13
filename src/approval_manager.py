"""
Approval Manager for Parental Control System

This module manages approval requests and integrates with:
- Lock screen system
- WebSocket server for parent communication
- Monitoring system for content blocking
- Timeout handling and emergency procedures
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
import os
import fcntl  # For file locking

from lock_screen import show_system_lock, unlock_system, is_system_locked, update_lock_status
from websocket_server import get_websocket_server, send_approval_request_via_command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timing utilities
def get_precise_timestamp():
    return time.time()

def log_timing(event_name: str, timestamp: float, content: str = "", extra_info: str = ""):
    logger.info(f"⏱️ TIMING [{event_name}] {timestamp}s - {content[:20]}{'...' if len(content) > 20 else ''} {extra_info}")

# File paths for persistence
APPROVAL_REQUESTS_FILE = "temp/approval_requests.json"
APPROVAL_HISTORY_FILE = "temp/approval_history.json"

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ApprovalRequest:
    """Approval request data structure"""
    id: str
    reason: str
    timestamp: datetime
    content: str = ""
    application_name: str = "Unknown"
    blocked_url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    child_id: str = "child-001"
    parent_id: str = "parent-001"
    status: ApprovalStatus = ApprovalStatus.PENDING
    timeout_seconds: int = 300  # 5 minutes default
    response_time: Optional[datetime] = None
    response_data: Dict[str, Any] = field(default_factory=dict)

class ApprovalManager:
    """Manages approval requests and system locking"""
    
    def __init__(self):
        self.active_requests: Dict[str, ApprovalRequest] = {}
        self.request_history: List[ApprovalRequest] = []
        self.websocket_server = get_websocket_server()
        self.lock_thread = None
        self.is_system_locked = False
        self.current_request_id = None
        
        # Load existing requests from file
        self._load_requests()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'approved_requests': 0,
            'denied_requests': 0,
            'timeout_requests': 0,
            'average_response_time': 0.0
        }
        
        logger.info("Approval Manager initialized")
    
    def _load_requests(self):
        """Load approval requests from file"""
        try:
            if os.path.exists(APPROVAL_REQUESTS_FILE):
                with open(APPROVAL_REQUESTS_FILE, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                    data = json.load(f)
                    
                    # Convert back to ApprovalRequest objects
                    for request_data in data:
                        request = ApprovalRequest(
                            id=request_data['id'],
                            reason=request_data['reason'],
                            timestamp=datetime.fromisoformat(request_data['timestamp']),
                            content=request_data.get('content', ''),
                            application_name=request_data.get('application_name', 'Unknown'),
                            blocked_url=request_data.get('blocked_url'),
                            keywords=request_data.get('keywords', []),
                            confidence=request_data.get('confidence', 0.0),
                            child_id=request_data.get('child_id', 'child-001'),
                            parent_id=request_data.get('parent_id', 'parent-001'),
                            status=ApprovalStatus(request_data.get('status', 'pending')),
                            timeout_seconds=request_data.get('timeout_seconds', 300),
                            response_time=datetime.fromisoformat(request_data['response_time']) if request_data.get('response_time') else None,
                            response_data=request_data.get('response_data', {})
                        )
                        self.active_requests[request.id] = request
                    
                    logger.info(f"Loaded {len(self.active_requests)} active requests from file")
        except Exception as e:
            logger.error(f"Error loading requests: {e}")
    
    def _save_requests(self):
        """Save approval requests to file"""
        try:
            # Convert ApprovalRequest objects to dictionaries
            data = []
            for request in self.active_requests.values():
                request_dict = {
                    'id': request.id,
                    'reason': request.reason,
                    'timestamp': request.timestamp.isoformat(),
                    'content': request.content,
                    'application_name': request.application_name,
                    'blocked_url': request.blocked_url,
                    'keywords': request.keywords,
                    'confidence': request.confidence,
                    'child_id': request.child_id,
                    'parent_id': request.parent_id,
                    'status': request.status.value,
                    'timeout_seconds': request.timeout_seconds,
                    'response_time': request.response_time.isoformat() if request.response_time else None,
                    'response_data': request.response_data
                }
                data.append(request_dict)
            
            with open(APPROVAL_REQUESTS_FILE, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(data)} active requests to file")
        except Exception as e:
            logger.error(f"Error saving requests: {e}")
    
    def create_approval_request(self, reason: str, content: str = "", 
                              application_name: str = "Unknown",
                              blocked_url: str = None,
                              keywords: List[str] = None,
                              confidence: float = 0.0,
                              timeout_seconds: int = 300) -> str:
        """
        Create a new approval request
        
        Args:
            reason: Reason for the request
            content: Content that triggered the request
            application_name: Name of the application
            blocked_url: URL that was blocked (if applicable)
            keywords: Keywords that triggered the block
            confidence: AI confidence level
            timeout_seconds: Timeout in seconds
            
        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())
        
        request = ApprovalRequest(
            id=request_id,
            reason=reason,
            timestamp=datetime.now(),
            content=content,
            application_name=application_name,
            blocked_url=blocked_url,
            keywords=keywords or [],
            confidence=confidence,
            timeout_seconds=timeout_seconds
        )
        
        self.active_requests[request_id] = request
        self.stats['total_requests'] += 1
        
        # Save to file
        self._save_requests()
        
        logger.info(f"Created approval request: {request_id} - {reason}")
        
        return request_id
    
    def request_approval_with_lock(self, reason: str, content: str = "",
                                  application_name: str = "Unknown",
                                  blocked_url: str = None,
                                  keywords: List[str] = None,
                                  confidence: float = 0.0,
                                  timeout_seconds: int = 300) -> str:
        """
        Request approval and lock the system
        
        Args:
            reason: Reason for the request
            content: Content that triggered the request
            application_name: Name of the application
            blocked_url: URL that was blocked (if applicable)
            keywords: Keywords that triggered the block
            confidence: AI confidence level
            timeout_seconds: Timeout in seconds
            
        Returns:
            Request ID
        """
        # Create approval request
        request_id = self.create_approval_request(
            reason=reason,
            content=content,
            application_name=application_name,
            blocked_url=blocked_url,
            keywords=keywords,
            confidence=confidence,
            timeout_seconds=timeout_seconds
        )
        
        # Send approval request to parent dashboard
        self._send_approval_request_to_parent(request_id)
        
        # Lock the system
        self._lock_system_for_approval(request_id)
        
        return request_id
    
    def _send_approval_request_to_parent(self, request_id: str):
        """Send approval request to parent dashboard via WebSocket"""
        if request_id not in self.active_requests:
            logger.error(f"Request {request_id} not found")
            return
        
        request = self.active_requests[request_id]
        
        # Prepare approval request data
        approval_data = {
            "id": request.id,
            "reason": request.reason,
            "timestamp": request.timestamp.isoformat(),
            "applicationName": request.application_name,
            "blockedUrl": request.blocked_url,
            "keywords": request.keywords,
            "confidence": request.confidence,
            "childId": request.child_id
        }
        
        logger.info(f"Sending approval request to parent dashboard: {request_id}")
        logger.info(f"Approval request data: {approval_data}")
        
        # WebSocket timing - start
        timestamp_websocket_start = get_precise_timestamp()
        log_timing("WEBSOCKET_SEND_START", timestamp_websocket_start, request.content)
        
        # Try regular WebSocket first
        try:
            self.websocket_server.send_message_to_clients("APPROVAL_REQUEST", approval_data)
            
            # Check if message was actually sent (has clients)
            if len(self.websocket_server.clients) == 0:
                logger.warning("No clients connected to WebSocket server, trying command interface")
                
                # Try command interface as fallback
                success = send_approval_request_via_command(
                    request_id=request.id,
                    reason=request.reason,
                    applicationName=request.application_name,
                    blockedUrl=request.blocked_url,
                    keywords=request.keywords,
                    confidence=request.confidence,
                    childId=request.child_id
                )
                
                if success:
                    logger.info("Successfully sent approval request via command interface")
                else:
                    logger.error("Failed to send approval request via command interface")
            
            # WebSocket timing - end
            timestamp_websocket_end = get_precise_timestamp()
            log_timing("WEBSOCKET_SEND_END", timestamp_websocket_end, request.content, f"websocket_time={(timestamp_websocket_end-timestamp_websocket_start):.3f}s")
            
            logger.info(f"Successfully sent approval request to parent: {request_id}")
        except Exception as e:
            logger.error(f"Failed to send approval request to parent: {e}")
            logger.error(f"Request ID: {request_id}, Data: {approval_data}")
            raise
    
    def _lock_system_for_approval(self, request_id: str):
        """Lock the system and wait for approval"""
        if request_id not in self.active_requests:
            logger.error(f"Request {request_id} not found")
            return
        
        request = self.active_requests[request_id]
        
        # Set current request
        self.current_request_id = request_id
        self.is_system_locked = True
        
        # Create approval and timeout callbacks
        def on_approval():
            logger.info(f"Lock screen approved for request: {request_id}")
            # The actual approval will be handled by process_approval_response
        
        def on_timeout():
            logger.info(f"Lock screen timeout for request: {request_id}")
            self._handle_timeout(request_id)
        
        def on_emergency():
            logger.info(f"Emergency unlock for request: {request_id}")
            self._handle_emergency_unlock(request_id)
        
        # Show lock screen
        show_system_lock(
            reason=request.reason,
            timeout=request.timeout_seconds,
            approval_callback=on_approval,
            timeout_callback=on_timeout
        )
        
        # Start timeout monitoring in separate thread
        timeout_thread = threading.Thread(
            target=self._monitor_timeout,
            args=(request_id,),
            daemon=True
        )
        timeout_thread.start()
    
    def _monitor_timeout(self, request_id: str):
        """Monitor request timeout"""
        if request_id not in self.active_requests:
            return
        
        request = self.active_requests[request_id]
        start_time = request.timestamp
        
        while request.status == ApprovalStatus.PENDING:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed >= request.timeout_seconds:
                logger.info(f"Request {request_id} timed out after {elapsed} seconds")
                self._handle_timeout(request_id)
                break
            
            time.sleep(1)
    
    def process_approval_response(self, request_id: str, approved: bool, 
                                parent_id: str = "parent-001") -> bool:
        """
        Process approval response from parent
        
        Args:
            request_id: Request ID
            approved: Whether approved or denied
            parent_id: Parent ID who responded
            
        Returns:
            True if processed successfully
        """
        # Reload requests from file to get latest state
        self._load_requests()
        
        if request_id not in self.active_requests:
            logger.error(f"Request {request_id} not found in active requests")
            logger.info(f"Available requests: {list(self.active_requests.keys())}")
            return False
        
        request = self.active_requests[request_id]
        
        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"Request {request_id} is not pending (status: {request.status})")
            return False
        
        # Update request
        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
        request.response_time = datetime.now()
        request.response_data = {
            "parent_id": parent_id,
            "approved": approved,
            "response_time": request.response_time.isoformat()
        }
        
        # Update statistics
        if approved:
            self.stats['approved_requests'] += 1
        else:
            self.stats['denied_requests'] += 1
        
        # Calculate response time
        response_time = (request.response_time - request.timestamp).total_seconds()
        self._update_average_response_time(response_time)
        
        logger.info(f"Request {request_id} {'approved' if approved else 'denied'} by {parent_id}")
        
        # Handle the response
        if approved:
            self._handle_approval(request_id)
        else:
            self._handle_denial(request_id)
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # Save updated state to file
        self._save_requests()
        
        return True
    
    def _handle_approval(self, request_id: str):
        """Handle approval response"""
        logger.info(f"Handling approval for request: {request_id}")
        
        # Update lock screen status
        update_lock_status("Parent approved! Unlocking system...")
        
        # Send unlock notification to WebSocket clients via command interface
        try:
            unlock_message = {
                "type": "SYSTEM_UNLOCKED",
                "data": {
                    "requestId": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "Parent approved"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Try command interface first
            success = self._send_via_command_interface(unlock_message)
            
            if not success:
                # Fallback to regular WebSocket server
                self.websocket_server.send_message_to_clients("SYSTEM_UNLOCKED", {
                    "requestId": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "reason": "Parent approved"
                })
                
        except Exception as e:
            logger.error(f"Failed to send unlock notification: {e}")
        
        # Unlock system immediately
        self._unlock_system()
    
    def _handle_denial(self, request_id: str):
        """Handle denial response"""
        logger.info(f"Handling denial for request: {request_id}")
        
        # Update lock screen status
        update_lock_status("Parent denied request. System remains locked.")
        
        # Keep system locked - parent can approve later or use emergency unlock
        # The system will remain locked until manual intervention
    
    def _handle_timeout(self, request_id: str):
        """Handle request timeout"""
        if request_id not in self.active_requests:
            return
        
        request = self.active_requests[request_id]
        request.status = ApprovalStatus.TIMEOUT
        request.response_time = datetime.now()
        
        self.stats['timeout_requests'] += 1
        
        logger.info(f"Request {request_id} timed out")
        
        # Update lock screen
        update_lock_status("Request timed out. System remains locked.")
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # Keep system locked until manual intervention
    
    def _handle_emergency_unlock(self, request_id: str):
        """Handle emergency unlock"""
        if request_id not in self.active_requests:
            return
        
        request = self.active_requests[request_id]
        request.status = ApprovalStatus.CANCELLED
        request.response_time = datetime.now()
        request.response_data = {
            "emergency_unlock": True,
            "response_time": request.response_time.isoformat()
        }
        
        logger.info(f"Emergency unlock for request: {request_id}")
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # Unlock system
        self._unlock_system()
    
    def _unlock_system(self):
        """Unlock the system"""
        logger.info("Unlocking system")
        
        self.is_system_locked = False
        self.current_request_id = None
        
        # Unlock the lock screen
        unlock_system()
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time statistics"""
        total_responses = (self.stats['approved_requests'] + 
                          self.stats['denied_requests'])
        
        if total_responses > 0:
            current_avg = self.stats['average_response_time']
            self.stats['average_response_time'] = (
                (current_avg * (total_responses - 1) + response_time) / total_responses
            )
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request"""
        if request_id not in self.active_requests:
            logger.error(f"Request {request_id} not found")
            return False
        
        request = self.active_requests[request_id]
        request.status = ApprovalStatus.CANCELLED
        request.response_time = datetime.now()
        
        logger.info(f"Cancelled request: {request_id}")
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # If this was the current lock request, unlock
        if self.current_request_id == request_id:
            self._unlock_system()
        
        return True
    
    def get_active_requests(self) -> List[ApprovalRequest]:
        """Get list of active requests"""
        return list(self.active_requests.values())
    
    def get_request_history(self, limit: int = 50) -> List[ApprovalRequest]:
        """Get request history"""
        return self.request_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval statistics"""
        return {
            **self.stats,
            'active_requests': len(self.active_requests),
            'system_locked': self.is_system_locked,
            'current_request_id': self.current_request_id
        }
    
    def is_system_currently_locked(self) -> bool:
        """Check if system is currently locked"""
        return self.is_system_locked and is_system_locked()

    def _send_via_command_interface(self, message: dict) -> bool:
        """Send message via command interface"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("localhost", 8081))
                sock.send(json.dumps(message).encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                logger.info(f"Command interface response: {response}")
                return True
        except Exception as e:
            logger.error(f"Failed to send via command interface: {e}")
            return False

# Global approval manager instance
_approval_manager: Optional[ApprovalManager] = None

def get_approval_manager() -> ApprovalManager:
    """Get or create the global approval manager instance"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager

def request_approval(reason: str, content: str = "", **kwargs) -> str:
    """
    Request approval and lock system
    
    Args:
        reason: Reason for approval request
        content: Content that triggered the request
        **kwargs: Additional parameters
        
    Returns:
        Request ID
    """
    # Approval timing - entry point
    timestamp_approval_start = get_precise_timestamp()
    log_timing("APPROVAL_REQUEST_START", timestamp_approval_start, content)
    
    manager = get_approval_manager()
    request_id = manager.request_approval_with_lock(
        reason=reason,
        content=content,
        **kwargs
    )
    
    # Approval timing - completion
    timestamp_approval_end = get_precise_timestamp()
    log_timing("APPROVAL_REQUEST_END", timestamp_approval_end, content, f"approval_time={(timestamp_approval_end-timestamp_approval_start):.2f}s")
    
    return request_id

def process_parent_response(request_id: str, approved: bool, parent_id: str = "parent-001") -> bool:
    """
    Process parent approval response
    
    Args:
        request_id: Request ID
        approved: Whether approved or denied
        parent_id: Parent ID
        
    Returns:
        True if processed successfully
    """
    manager = get_approval_manager()
    return manager.process_approval_response(request_id, approved, parent_id)

def get_approval_statistics() -> Dict[str, Any]:
    """Get approval statistics"""
    manager = get_approval_manager()
    return manager.get_statistics()

if __name__ == "__main__":
    # Test the approval manager
    print("🔐 Testing Approval Manager...")
    
    manager = get_approval_manager()
    
    # Create test request
    request_id = manager.request_approval_with_lock(
        reason="Test inappropriate content detected",
        content="test content",
        application_name="Test Browser",
        confidence=0.85,
        timeout_seconds=30
    )
    
    print(f"📋 Created request: {request_id}")
    
    # Simulate parent approval after 10 seconds
    def simulate_approval():
        time.sleep(10)
        print("📱 Simulating parent approval...")
        manager.process_approval_response(request_id, True, "parent-001")
    
    approval_thread = threading.Thread(target=simulate_approval, daemon=True)
    approval_thread.start()
    
    # Keep main thread alive
    try:
        while manager.is_system_currently_locked():
            time.sleep(1)
        print("�� System unlocked")
        print("📊 Statistics:", manager.get_statistics())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        manager.cancel_request(request_id) 