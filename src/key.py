import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pynput import keyboard
from rich.console import Console
from google.adk.tools import FunctionTool, ToolContext
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

@dataclass
class InputBuffer:
    """Manages input buffer for the keylogger"""
    text: str = ""
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    enter_pressed: bool = False
    substantial_input_threshold: int = 10  # Minimum characters for substantial input
    
    def add_char(self, char: str) -> None:
        """Add character to buffer"""
        if not self.start_time:
            self.start_time = datetime.now()
        
        self.text += char
        self.last_activity = datetime.now()
        
        # Reset enter flag when new content is added
        if char != '\n':
            self.enter_pressed = False
    
    def mark_enter_pressed(self) -> None:
        """Mark that Enter key was pressed"""
        self.enter_pressed = True
        self.last_activity = datetime.now()
    
    def is_substantial_input(self) -> bool:
        """Check if input is substantial enough"""
        return len(self.text.strip()) >= self.substantial_input_threshold
    
    def is_input_complete(self) -> bool:
        """Determine if input is complete based on Enter press or substantial input"""
        return self.enter_pressed or self.is_substantial_input()
    
    def clear(self) -> None:
        """Clear the buffer"""
        self.text = ""
        self.start_time = None
        self.last_activity = None
        self.enter_pressed = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current buffer state"""
        return {
            "text": self.text,
            "length": len(self.text),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "enter_pressed": self.enter_pressed,
            "is_substantial": self.is_substantial_input(),
            "is_complete": self.is_input_complete()
        }

class EnhancedKeylogger:
    """Enhanced keylogger with ADK integration"""
    
    def __init__(self):
        self.buffer = InputBuffer()
        self.listener = None
        self.is_running = False
        self.logfile = None
        self.completion_callbacks = []
        self._lock = threading.Lock()
        
        # Open log file
        self.logfile = open("keystrokes.log", "a", encoding="utf-8")
        
    def add_completion_callback(self, callback):
        """Add callback to be called when input is complete"""
        self.completion_callbacks.append(callback)
    
    def _log_keystroke(self, key_info: str) -> None:
        """Log keystroke to file and console"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{ts}\t{key_info}"
        console.print(line, style="cyan")
        if self.logfile:
            self.logfile.write(line + "\n")
            self.logfile.flush()
    
    def _on_press(self, key) -> None:
        """Handle key press events"""
        with self._lock:
            try:
                if key == keyboard.Key.enter:
                    self._log_keystroke("Key.enter")
                    self.buffer.add_char('\n')
                    self.buffer.mark_enter_pressed()
                    self._check_completion()
                elif key == keyboard.Key.space:
                    self._log_keystroke("Key.space")
                    self.buffer.add_char(' ')
                elif key == keyboard.Key.backspace:
                    self._log_keystroke("Key.backspace")
                    # Handle backspace by removing last character
                    if self.buffer.text:
                        self.buffer.text = self.buffer.text[:-1]
                        self.buffer.last_activity = datetime.now()
                elif key == keyboard.Key.esc:
                    self._log_keystroke("Key.esc")
                    console.print("[bold red]ESC pressed - stopping keylogger[/]")
                    self.stop()
                    return False
                elif hasattr(key, 'char') and key.char:
                    # Regular character
                    self._log_keystroke(key.char)
                    self.buffer.add_char(key.char)
                    self._check_completion()
                else:
                    # Special keys
                    key_name = str(key)
                    self._log_keystroke(key_name)
                    
            except Exception as e:
                console.print(f"[bold red]Error in key handler: {e}[/]")
    
    def _check_completion(self) -> None:
        """Check if input is complete and trigger callbacks"""
        if self.buffer.is_input_complete():
            # Trigger completion callbacks
            for callback in self.completion_callbacks:
                try:
                    callback(self.buffer.get_summary())
                except Exception as e:
                    console.print(f"[bold red]Error in completion callback: {e}[/]")
    
    def start(self) -> None:
        """Start the keylogger"""
        if self.is_running:
            return
        
        self.is_running = True
        console.print("[bold green]Enhanced Keylogger starting... Press ESC to stop[/]")
        
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
    
    def stop(self) -> None:
        """Stop the keylogger"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.listener:
            self.listener.stop()
        
        if self.logfile:
            self.logfile.close()
        
        console.print("[bold red]Enhanced Keylogger stopped[/]")
    
    def get_buffered_input(self) -> Dict[str, Any]:
        """Get current buffered input"""
        with self._lock:
            return self.buffer.get_summary()
    
    def clear_buffer(self) -> None:
        """Clear the input buffer"""
        with self._lock:
            self.buffer.clear()
    
    def is_input_complete(self) -> bool:
        """Check if input is complete"""
        with self._lock:
            return self.buffer.is_input_complete()

# Global keylogger instance
_keylogger_instance = None

def get_keylogger_instance() -> EnhancedKeylogger:
    """Get or create the global keylogger instance"""
    global _keylogger_instance
    if _keylogger_instance is None:
        _keylogger_instance = EnhancedKeylogger()
    return _keylogger_instance

# ADK Function Tools

def start_keylogger(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Starts the enhanced keylogger with input buffer management.
    
    Use this tool to begin monitoring keyboard input. The keylogger will
    detect Enter key presses and substantial input completion automatically.
    
    Returns:
        dict: Status of the keylogger startup with monitoring capabilities.
        Success: {'status': 'success', 'message': 'Keylogger started', 'monitoring': True}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        keylogger = get_keylogger_instance()
        
        if keylogger.is_running:
            return {
                "status": "already_running",
                "message": "Keylogger is already running",
                "monitoring": True
            }
        
        keylogger.start()
        
        # Store keylogger state in session
        tool_context.state["keylogger_active"] = True
        tool_context.state["keylogger_start_time"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Enhanced keylogger started successfully",
            "monitoring": True,
            "features": [
                "Enter key detection",
                "Input buffer management",
                "Substantial input detection",
                "Real-time logging"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to start keylogger: {str(e)}"
        }

def stop_keylogger(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Stops the enhanced keylogger and returns final buffer state.
    
    Use this tool to stop keyboard monitoring and get the final input buffer.
    
    Returns:
        dict: Status of keylogger shutdown with final buffer contents.
        Success: {'status': 'success', 'final_buffer': {...}, 'monitoring': False}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        keylogger = get_keylogger_instance()
        
        if not keylogger.is_running:
            return {
                "status": "not_running",
                "message": "Keylogger is not currently running",
                "monitoring": False
            }
        
        # Get final buffer state before stopping
        final_buffer = keylogger.get_buffered_input()
        
        keylogger.stop()
        
        # Update session state
        tool_context.state["keylogger_active"] = False
        tool_context.state["keylogger_stop_time"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Keylogger stopped successfully",
            "final_buffer": final_buffer,
            "monitoring": False
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to stop keylogger: {str(e)}"
        }

def get_current_input(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gets the current input buffer state and completion status.
    
    Use this tool to check the current keyboard input buffer, whether Enter
    has been pressed, and if the input is considered complete for analysis.
    
    Returns:
        dict: Current buffer state with completion analysis.
        Success: {'status': 'success', 'buffer': {...}, 'input_complete': bool}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        keylogger = get_keylogger_instance()
        
        if not keylogger.is_running:
            return {
                "status": "not_running",
                "message": "Keylogger is not currently running",
                "buffer": None,
                "input_complete": False
            }
        
        buffer_state = keylogger.get_buffered_input()
        
        # Update session state with current buffer
        tool_context.state["last_buffer_check"] = datetime.now().isoformat()
        tool_context.state["current_input_length"] = buffer_state["length"]
        
        return {
            "status": "success",
            "buffer": buffer_state,
            "input_complete": buffer_state["is_complete"],
            "monitoring": True,
            "analysis": {
                "has_content": buffer_state["length"] > 0,
                "is_substantial": buffer_state["is_substantial"],
                "enter_detected": buffer_state["enter_pressed"],
                "ready_for_analysis": buffer_state["is_complete"]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get current input: {str(e)}"
        }

def clear_input_buffer(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Clears the current input buffer and resets completion state.
    
    Use this tool after processing input to prepare for the next input session.
    This is typically called after screen capture and AI analysis are complete.
    
    Returns:
        dict: Status of buffer clearing operation.
        Success: {'status': 'success', 'message': 'Buffer cleared', 'ready_for_input': True}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        keylogger = get_keylogger_instance()
        
        if not keylogger.is_running:
            return {
                "status": "not_running",
                "message": "Keylogger is not currently running",
                "ready_for_input": False
            }
        
        # Get buffer state before clearing for logging
        buffer_before = keylogger.get_buffered_input()
        
        keylogger.clear_buffer()
        
        # Update session state
        tool_context.state["last_buffer_clear"] = datetime.now().isoformat()
        tool_context.state["cleared_input_length"] = buffer_before["length"]
        
        return {
            "status": "success",
            "message": "Input buffer cleared successfully",
            "ready_for_input": True,
            "cleared_content": {
                "length": buffer_before["length"],
                "was_complete": buffer_before["is_complete"]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear input buffer: {str(e)}"
        }

# Create ADK Function Tools
start_keylogger_tool = FunctionTool(func=start_keylogger)
stop_keylogger_tool = FunctionTool(func=stop_keylogger)
get_current_input_tool = FunctionTool(func=get_current_input)
clear_input_buffer_tool = FunctionTool(func=clear_input_buffer)

# Example monitoring agent
def create_monitoring_agent() -> Agent:
    """Create a monitoring agent with keylogger tools"""
    
    return Agent(
        name="MonitoringAgent",
        model="gemini-2.0-flash",
        description="A monitoring agent that manages keyboard input capture and analysis",
        instruction="""
        You are a monitoring agent responsible for keyboard input capture and analysis.
        
        Your capabilities include:
        1. start_keylogger: Begin monitoring keyboard input
        2. get_current_input: Check current input buffer and completion status
        3. clear_input_buffer: Clear buffer after processing
        4. stop_keylogger: Stop monitoring when done
        
        When input is complete (Enter pressed or substantial input detected), 
        you should prepare it for analysis by other agents.
        
        Always provide clear status updates and handle errors gracefully.
        """,
        tools=[
            start_keylogger_tool,
            stop_keylogger_tool,
            get_current_input_tool,
            clear_input_buffer_tool
        ]
    )

# Direct execution mode (for testing)
if __name__ == "__main__":
    # Test the enhanced keylogger directly
    def on_completion(buffer_info):
        console.print(f"[bold yellow]Input Complete![/] {buffer_info}")
    
    keylogger = get_keylogger_instance()
    keylogger.add_completion_callback(on_completion)
    
    try:
        keylogger.start()
        console.print("[bold green]Enhanced Keylogger Test Mode[/]")
        console.print("Type something and press Enter, or type substantial text...")
        console.print("Press ESC to exit")
        
        # Keep the main thread alive
        keylogger.listener.join()
        
    except KeyboardInterrupt:
        console.print("[bold red]Interrupted by user[/]")
    finally:
        keylogger.stop()