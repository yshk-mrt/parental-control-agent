#!/usr/bin/env python3
"""
Complete MCP Server for Parental Control Unlock
Includes all required handlers for Claude Desktop compatibility
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Initialize server
server = Server("parental-control-unlock")

@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="unlock_screen",
            description="Unlock the parental control lock screen",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def unlock_screen(name: str, arguments: dict) -> list[TextContent]:
    """Unlock the parental control lock screen"""
    try:
        # Import and use the unlock function
        from lock_screen import unlock_system
        unlock_system()
        
        return [TextContent(
            type="text", 
            text="🔓 Screen unlocked successfully!"
        )]
    except ImportError:
        return [TextContent(
            type="text", 
            text="❌ Lock screen module not available"
        )]
    except Exception as e:
        return [TextContent(
            type="text", 
            text=f"❌ Error: {str(e)}"
        )]

@server.list_resources()
async def list_resources():
    """List available resources (empty for this server)"""
    return []

@server.list_prompts()
async def list_prompts():
    """List available prompts (empty for this server)"""
    return []

async def main():
    """Main function"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 