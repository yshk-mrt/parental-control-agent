# Parental Control Agent System

A comprehensive AI-powered parental control system that monitors children's computer usage in real-time using multi-agent architecture and multimodal AI analysis.

## Overview

This system provides intelligent monitoring and control of children's computer activities by:

- **Continuous Monitoring**: Real-time keylogging and screen capture
- **AI Analysis**: Gemini multimodal AI analyzes both text input and screen content
- **Intelligent Decision Making**: Age-appropriate content filtering with customizable strictness levels
- **Lock Screen Protection**: Native macOS Cocoa overlay for complete system blocking
- **Parent Dashboard**: Real-time React dashboard for monitoring and approval
- **Multi-channel Notifications**: Email, desktop, and SMS notifications

## System Architecture

### Multi-Agent System
- **Monitoring Agent**: Orchestrates all components and continuous monitoring
- **Analysis Agent**: Coordinates AI content analysis using Gemini multimodal
- **Judgment Engine**: Makes decisions based on age-appropriate rules
- **Notification Agent**: Handles all notification channels
- **Approval Manager**: Manages approval requests and system locking

### Key Components
- **Enhanced Keylogger**: Monitors all keyboard input with context awareness
- **Screen Capture**: Automatic screenshots when input is complete
- **Lock Screen System**: Full-screen native macOS overlay blocking
- **WebSocket Server**: Real-time communication with parent dashboard
- **Session Manager**: Tracks activities and maintains state

## Features

### For Parents
- **Real-time Dashboard**: Monitor child's activities in real-time
- **Approval System**: Approve/deny blocked content requests
- **Activity History**: Complete log of all monitored activities
- **Customizable Settings**: Adjust age group and strictness levels
- **Multiple Notifications**: Email, desktop, and SMS alerts

### For Children
- **Age-appropriate Filtering**: Content filtering based on age group
- **Educational Focus**: Promotes safe learning environments
- **Clear Communication**: Child-friendly lock screen messages
- **Emergency Unlock**: Safety mechanisms for urgent situations

### Technical Features
- **Multimodal AI**: Simultaneous text and image analysis
- **Performance Optimized**: Caching and efficient processing
- **macOS Native**: Full Cocoa framework integration
- **Thread-safe**: Robust multi-threading architecture
- **Comprehensive Logging**: Detailed analytics and performance tracking

## MCP (Model Context Protocol) Integration

This system includes a Model Context Protocol server that enables integration with AI assistants like Claude Desktop, providing remote control capabilities for the parental control system.

### MCP Server Features

- **Remote Unlock**: Unlock the parental control lock screen remotely
- **System Monitoring** (Planning): Get real-time system status and information
- **Monitoring Control** (Planning): Start and stop monitoring remotely
- **Lock Screen Control** (Planning): Display lock screen with custom messages
- **Standard Compliance**: Full MCP protocol compliance for Claude Desktop

### MCP Server Setup

#### 1. Configure Claude Desktop

Add the following to your Claude Desktop MCP configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "parental-control-agent": {
      "type": "stdio",
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/parental-control-agent/parental_control_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/parental-control-agent/src"
      }
    }
  },
  "toolPermissions": {
    "parental-control-agent": true
  }
}
```

#### 2. Available MCP Tools

- **`unlock_screen`**: Unlock the parental control lock screen
- **`get_system_info`** (Planning): Get system information and component status
- **`start_monitoring`** (Planning): Start the parental control monitoring system
- **`stop_monitoring`** (Planning): Stop the monitoring system
- **`show_lock_screen`** (Planning): Display lock screen with custom message
- **`test_connection`** (Planning): Test MCP server connection

#### 3. Usage Examples

In Claude Desktop, you can use commands like:
- "Unlock the parental control screen"
- "Show me the system status" (Planning)
- "Start monitoring with moderate strictness" (Planning)
- "Display a lock screen saying 'Take a break'" (Planning)

### MCP Server Files

- **`parental_control_mcp_server.py`**: Full-featured MCP server with all tools

## Installation

### Prerequisites

```bash
# Python 3.8 or higher
python --version

# Install required dependencies
pip install -r requirements.txt
```

### macOS Permissions Setup

#### 1. Input Monitoring
1. **System Settings** → **Privacy & Security** → **Input Monitoring**
2. Click the **+** button
3. Add **Terminal** or **Python executable**
4. Enable the checkbox

#### 2. Accessibility
1. **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Add **Terminal** or **Python executable**
4. Enable the checkbox

#### 3. Screen Recording (for screen capture)
1. **System Settings** → **Privacy & Security** → **Screen Recording**
2. Click the **+** button
3. Add **Terminal** or **Python executable**
4. Enable the checkbox

**Important**: Completely restart Terminal after configuring permissions.

### Environment Setup

Create a `.env` file in the project root:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Email Notifications (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Parent Contact Information
PARENT_EMAIL=parent@example.com
PARENT_PHONE=+1234567890
CHILD_NAME=Child Name
```

## Usage

### Starting the System

#### 1. Start the WebSocket Server
```bash
cd src
python websocket_server.py
```

#### 2. Start the Monitoring Agent
```bash
cd src
python monitoring_agent.py
```

#### 3. Start the Parent Dashboard
```bash
cd frontend
npm install
npm start
```

### Configuration

#### Age Groups
- `elementary`: Ages 6-10 (strict filtering)
- `middle_school`: Ages 11-13 (moderate filtering)
- `high_school`: Ages 14-17 (balanced filtering)

#### Strictness Levels
- `strict`: Maximum protection, blocks most content
- `moderate`: Balanced approach (default)
- `permissive`: Minimal filtering, monitoring focus

### Testing

#### Test Individual Components
```bash
# Test keylogger
python test/test_enhanced_keylogger.py

# Test screen capture
python test/test_screen_capture.py

# Test Gemini analysis
python test/test_gemini_multimodal.py

# Test lock screen
python test_lock_integration.py
```

#### Test Complete Workflow
```bash
python test/test_complete_workflow.py
```

## System Workflow

1. **Input Detection**: Keylogger detects keyboard input
2. **Context Capture**: Screen capture when input is complete
3. **AI Analysis**: Gemini analyzes text and image content
4. **Judgment**: Age-appropriate decision making
5. **Action**: Allow, monitor, or block content
6. **Lock Screen**: Full-screen overlay if blocked
7. **Parent Notification**: Real-time dashboard and notifications
8. **Approval Process**: Parent approves/denies via dashboard
9. **System Unlock**: Automatic unlock on approval

## File Structure

```
parental-control-agent/
├── src/
│   ├── monitoring_agent.py       # Main orchestrating agent
│   ├── analysis_agent.py         # AI analysis coordination
│   ├── judgment_engine.py        # Decision making engine
│   ├── notification_agent.py     # Notification system
│   ├── approval_manager.py       # Approval and locking
│   ├── lock_screen.py            # Lock screen system
│   ├── cocoa_lock_screen.py      # Native macOS overlay
│   ├── websocket_server.py       # Real-time communication
│   ├── key.py                    # Enhanced keylogger
│   ├── screen_capture.py         # Screen capture tools
│   ├── gemini_multimodal.py      # AI analysis tools
│   └── session_manager.py        # Session management
├── parental_control_mcp_server.py # MCP server for Claude Desktop
├── frontend/                     # React parent dashboard
├── test/                         # Comprehensive test suite
├── doc/                          # Documentation
└── requirements.txt              # Python dependencies
```

## API Reference

### Monitoring Agent
```python
from monitoring_agent import MonitoringAgent

agent = MonitoringAgent(config={
    'age_group': 'elementary',
    'strictness_level': 'moderate'
})

# Start monitoring
agent.start_monitoring()

# Get status
status = agent.get_monitoring_status()

# Stop monitoring
summary = agent.stop_monitoring()
```

### Lock Screen System
```python
from lock_screen import show_system_lock, unlock_system

# Show lock screen
show_system_lock(
    reason="Inappropriate content detected",
    timeout=300,
    approval_callback=on_approval,
    timeout_callback=on_timeout
)

# Unlock system
unlock_system()
```

### MCP Server Integration
```python
# Start MCP server for Claude Desktop integration
python parental_control_mcp_server.py
```

#### Available MCP Tools via Claude Desktop
```
# Unlock the parental control screen
unlock_screen

# Get system status (Planning)
get_system_info

# Start monitoring (Planning)
start_monitoring(age_group="middle_school", strictness_level="moderate")

# Stop monitoring (Planning)
stop_monitoring

# Show custom lock screen (Planning)
show_lock_screen(reason="Custom message", timeout=60)

# Test connection (Planning)
test_connection(message="Hello from Claude")
```

## Troubleshooting

### Common Issues

#### Lock Screen Not Displaying
- Ensure all macOS permissions are granted
- Restart Terminal completely after permission changes
- Check that Cocoa dependencies are installed: `pip install pyobjc-framework-Cocoa`

#### WebSocket Connection Failed
- Verify port 8080 is available
- Check firewall settings
- Ensure WebSocket server is running

#### AI Analysis Errors
- Verify Gemini API key is correct
- Check internet connection
- Ensure sufficient API quota

#### MCP Server Issues
- Ensure Python virtual environment path is correct in Claude Desktop config
- Verify `PYTHONPATH` includes the `src` directory
- Check that MCP dependencies are installed: `pip install mcp`
- Restart Claude Desktop after configuration changes
- Check Claude Desktop logs for connection errors

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
python monitoring_agent.py
```

## Security Considerations

- **Data Privacy**: All analysis is done locally except Gemini API calls
- **Secure Communication**: WebSocket connections use secure protocols
- **Access Control**: Parent dashboard requires authentication
- **Emergency Override**: Built-in safety mechanisms for urgent situations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is designed for legitimate parental control purposes only. Users are responsible for:
- Obtaining proper consent before monitoring
- Complying with local privacy laws
- Using the system ethically and responsibly
- Ensuring child safety and well-being

## Support

For issues and questions:
- Check the troubleshooting section
- Review the documentation in the `doc/` directory
- Submit issues on the project repository 