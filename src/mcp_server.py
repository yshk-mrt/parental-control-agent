#!/usr/bin/env python3
"""
MCP Server for Parental Control Agent System

This MCP server provides tools for AI assistants to interact with the 
parental control system, including monitoring, analysis, and approval management.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"MCP not available: {e}", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("mcp-parental-control")

class ParentalControlMCPServer:
    """MCP Server for Parental Control Agent System"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            raise ImportError("MCP library not available")
            
        self.server = Server("parental-control-agent")
        self.monitoring_agent = None
        self.session_manager = None
        self.approval_manager = None
        self.websocket_server = None
        
        # Initialize components (with error handling)
        self._initialize_components()
        
        # Register tools
        self._register_tools()
        
        logger.info("Parental Control MCP Server initialized successfully")
    
    def _initialize_components(self):
        """Initialize parental control components with error handling"""
        try:
            # Try to import and initialize components
            try:
                from session_manager import get_global_session_manager
                self.session_manager = get_global_session_manager()
                logger.info("Session manager initialized")
            except ImportError as e:
                logger.warning(f"Session manager not available: {e}")
            
            try:
                from approval_manager import get_approval_manager
                self.approval_manager = get_approval_manager()
                logger.info("Approval manager initialized")
            except ImportError as e:
                logger.warning(f"Approval manager not available: {e}")
            
            try:
                from websocket_server import get_websocket_server
                self.websocket_server = get_websocket_server()
                logger.info("WebSocket server initialized")
            except ImportError as e:
                logger.warning(f"WebSocket server not available: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize some components: {e}")
            # Continue with limited functionality
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        # System info tool
        @self.server.call_tool()
        async def get_system_info(arguments: Dict[str, Any]) -> List[TextContent]:
            """Get system information and component status"""
            try:
                info = {
                    "server_status": "running",
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "session_manager": self.session_manager is not None,
                        "approval_manager": self.approval_manager is not None,
                        "websocket_server": self.websocket_server is not None,
                        "monitoring_agent": self.monitoring_agent is not None
                    },
                    "python_version": sys.version,
                    "working_directory": os.getcwd()
                }
                
                return [TextContent(
                    type="text",
                    text=f"🖥️ Parental Control System Info\n"
                         f"Status: {info['server_status']}\n"
                         f"Time: {info['timestamp']}\n"
                         f"Components Available:\n"
                         f"  - Session Manager: {'✅' if info['components']['session_manager'] else '❌'}\n"
                         f"  - Approval Manager: {'✅' if info['components']['approval_manager'] else '❌'}\n"
                         f"  - WebSocket Server: {'✅' if info['components']['websocket_server'] else '❌'}\n"
                         f"  - Monitoring Agent: {'✅' if info['components']['monitoring_agent'] else '❌'}\n"
                         f"Python: {info['python_version']}\n"
                         f"Directory: {info['working_directory']}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to get system info: {str(e)}"
                )]
        
        # Test tool
        @self.server.call_tool()
        async def test_connection(arguments: Dict[str, Any]) -> List[TextContent]:
            """Test the MCP server connection"""
            try:
                test_message = arguments.get("message", "Hello from Parental Control MCP Server!")
                
                return [TextContent(
                    type="text",
                    text=f"✅ Connection test successful!\n"
                         f"Message: {test_message}\n"
                         f"Server time: {datetime.now().isoformat()}\n"
                         f"Python version: {sys.version.split()[0]}\n"
                         f"Working directory: {os.getcwd()}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Connection test failed: {str(e)}"
                )]
        
        # Monitoring tools
        @self.server.call_tool()
        async def start_monitoring(arguments: Dict[str, Any]) -> List[TextContent]:
            """Start the parental control monitoring system"""
            try:
                age_group = arguments.get("age_group", "elementary")
                strictness_level = arguments.get("strictness_level", "moderate")
                
                # Try to import and create monitoring agent
                try:
                    from monitoring_agent import MonitoringAgent, MonitoringConfig
                    
                    config = MonitoringConfig(
                        age_group=age_group,
                        strictness_level=strictness_level
                    )
                    
                    self.monitoring_agent = MonitoringAgent(config=config)
                    await self.monitoring_agent.start_monitoring()
                    
                    return [TextContent(
                        type="text",
                        text=f"✅ Monitoring started successfully\n"
                             f"Age Group: {age_group}\n"
                             f"Strictness: {strictness_level}\n"
                             f"Status: Active"
                    )]
                except ImportError as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Monitoring components not available: {str(e)}\n"
                             f"Please ensure all dependencies are installed."
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to start monitoring: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def stop_monitoring(arguments: Dict[str, Any]) -> List[TextContent]:
            """Stop the parental control monitoring system"""
            try:
                if self.monitoring_agent:
                    summary = await self.monitoring_agent.stop_monitoring()
                    self.monitoring_agent = None
                    return [TextContent(
                        type="text",
                        text=f"✅ Monitoring stopped successfully\n"
                             f"Session Summary: {json.dumps(summary, indent=2)}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="ℹ️ Monitoring was not running"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to stop monitoring: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def get_monitoring_status(arguments: Dict[str, Any]) -> List[TextContent]:
            """Get current monitoring status and statistics"""
            try:
                if self.monitoring_agent:
                    status = await self.monitoring_agent.get_monitoring_status()
                    return [TextContent(
                        type="text",
                        text=f"📊 Monitoring Status\n"
                             f"Status: {status.get('status', 'Unknown')}\n"
                             f"Uptime: {status.get('uptime', 'Unknown')}\n"
                             f"Events Processed: {status.get('events_processed', 0)}\n"
                             f"Blocked Content: {status.get('blocked_content', 0)}\n"
                             f"Notifications Sent: {status.get('notifications_sent', 0)}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="ℹ️ Monitoring is not currently running"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to get status: {str(e)}"
                )]
        
        # Lock screen tools
        @self.server.call_tool()
        async def show_lock_screen(arguments: Dict[str, Any]) -> List[TextContent]:
            """Show the system lock screen"""
            try:
                reason = arguments.get("reason", "Content blocked by parental control")
                timeout = arguments.get("timeout", 300)
                
                # Try to import lock screen
                try:
                    from lock_screen import show_system_lock
                    
                    show_system_lock(
                        reason=reason,
                        timeout=timeout
                    )
                    
                    return [TextContent(
                        type="text",
                        text=f"🔒 Lock screen displayed\n"
                             f"Reason: {reason}\n"
                             f"Timeout: {timeout} seconds"
                    )]
                except ImportError as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Lock screen not available: {str(e)}"
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to show lock screen: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def unlock_screen(arguments: Dict[str, Any]) -> List[TextContent]:
            """Unlock the system screen"""
            try:
                try:
                    from lock_screen import unlock_system
                    unlock_system()
                    return [TextContent(
                        type="text",
                        text="🔓 System unlocked successfully"
                    )]
                except ImportError as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Lock screen not available: {str(e)}"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to unlock system: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def check_lock_status(arguments: Dict[str, Any]) -> List[TextContent]:
            """Check if the system is currently locked"""
            try:
                try:
                    from lock_screen import is_system_locked
                    locked = is_system_locked()
                    status = "🔒 Locked" if locked else "🔓 Unlocked"
                    return [TextContent(
                        type="text",
                        text=f"System Status: {status}"
                    )]
                except ImportError as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Lock screen not available: {str(e)}"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to check lock status: {str(e)}"
                )]
    
    @property
    def tools(self) -> List[Tool]:
        """Return list of available tools"""
        return [
            Tool(
                name="get_system_info",
                description="Get system information and component status",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="test_connection",
                description="Test the MCP server connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Test message to echo back"
                        }
                    }
                }
            ),
            Tool(
                name="start_monitoring",
                description="Start the parental control monitoring system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "age_group": {
                            "type": "string",
                            "enum": ["elementary", "middle_school", "high_school"],
                            "description": "Age group for filtering"
                        },
                        "strictness_level": {
                            "type": "string",
                            "enum": ["strict", "moderate", "permissive"],
                            "description": "Strictness level for content filtering"
                        }
                    }
                }
            ),
            Tool(
                name="stop_monitoring",
                description="Stop the parental control monitoring system",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="get_monitoring_status",
                description="Get current monitoring status and statistics",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="show_lock_screen",
                description="Show the system lock screen",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for locking the screen"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds"
                        }
                    }
                }
            ),
            Tool(
                name="unlock_screen",
                description="Unlock the system screen",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="check_lock_status",
                description="Check if the system is currently locked",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting MCP server...")
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            logger.info("Tools requested")
            return ListToolsResult(tools=self.tools)
        
        try:
            # Use a simpler approach to stdio server
            from mcp.server.stdio import stdio_server
            
            async with stdio_server() as streams:
                read_stream, write_stream = streams
                logger.info("MCP server connected via stdio")
                
                # Initialize the server
                init_options = InitializationOptions(
                    server_name="parental-control-agent",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    ),
                )
                
                # Run the server
                await self.server.run(read_stream, write_stream, init_options)
                
        except Exception as e:
            logger.error(f"MCP server error: {e}")
            import traceback
            traceback.print_exc()
            raise

async def main():
    """Main entry point"""
    try:
        logger.info("Initializing Parental Control MCP Server...")
        server = ParentalControlMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 