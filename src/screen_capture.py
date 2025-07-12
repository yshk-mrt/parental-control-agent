import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import io
import base64
import os
import tempfile
from pathlib import Path

import mss
from PIL import Image
from google.adk.tools import FunctionTool, ToolContext
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ScreenCaptureConfig:
    """Configuration for screen capture"""
    # Image optimization settings
    max_width: int = 1920
    max_height: int = 1080
    quality: int = 85
    format: str = "JPEG"
    
    # AI analysis optimization
    optimize_for_ai: bool = True
    preserve_aspect_ratio: bool = True
    
    # Security settings
    secure_temp_storage: bool = True
    auto_cleanup: bool = True
    temp_dir: Optional[str] = None
    
    # Performance settings
    compression_level: int = 6  # 0-9, higher = better compression, slower

class ScreenCaptureManager:
    """High-performance screen capture manager using MSS"""
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        self.config = config or ScreenCaptureConfig()
        self.mss_instance = mss.mss()
        self.temp_files = []
        self._lock = threading.Lock()
        
        # Setup temp directory
        if self.config.secure_temp_storage:
            self.temp_dir = tempfile.mkdtemp(prefix="parental_control_")
        else:
            self.temp_dir = self.config.temp_dir or tempfile.gettempdir()
    
    def capture_screen(self, monitor: int = 0) -> Dict[str, Any]:
        """
        Capture screen with high performance using MSS, fallback to screencapture on macOS
        
        Args:
            monitor: Monitor index (0 = all monitors, 1+ = specific monitor)
        
        Returns:
            dict: Capture result with image data and metadata
        """
        try:
            with self._lock:
                start_time = time.time()
                
                # Try MSS first
                try:
                    # Get monitor info
                    if monitor == 0:
                        # Capture all monitors
                        monitor_info = self.mss_instance.monitors[0]
                    else:
                        # Capture specific monitor
                        if monitor > len(self.mss_instance.monitors) - 1:
                            monitor = 1  # Default to first monitor
                        monitor_info = self.mss_instance.monitors[monitor]
                    
                    # Check if monitor info is valid
                    if monitor_info.get("width", 0) > 0 and monitor_info.get("height", 0) > 0:
                        # Capture screenshot
                        screenshot = self.mss_instance.grab(monitor_info)
                        
                        # Convert to PIL Image
                        image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "BGRX")
                        
                        capture_time = time.time() - start_time
                        
                        # Get image info
                        original_size = image.size
                        file_size_estimate = len(screenshot.bgra)
                        
                        return {
                            "status": "success",
                            "image": image,
                            "metadata": {
                                "timestamp": datetime.now().isoformat(),
                                "monitor": monitor,
                                "original_size": original_size,
                                "capture_time_ms": round(capture_time * 1000, 2),
                                "file_size_estimate": file_size_estimate,
                                "method": "mss",
                                "monitor_info": {
                                    "left": monitor_info["left"],
                                    "top": monitor_info["top"],
                                    "width": monitor_info["width"],
                                    "height": monitor_info["height"]
                                }
                            }
                        }
                    else:
                        raise Exception("Invalid monitor dimensions")
                        
                except Exception as mss_error:
                    # MSS failed, try macOS screencapture as fallback
                    return self._capture_screen_macos_fallback(start_time)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Screen capture failed: {str(e)}",
                "image": None,
                "metadata": None
            }
    
    def _capture_screen_macos_fallback(self, start_time: float) -> Dict[str, Any]:
        """
        Fallback screen capture using macOS screencapture command
        
        Args:
            start_time: Start time for performance measurement
            
        Returns:
            dict: Capture result with image data and metadata
        """
        import subprocess
        import tempfile
        
        try:
            # Create temporary file for screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Use screencapture command
            result = subprocess.run([
                'screencapture', 
                '-t', 'png',  # PNG format
                '-x',  # No sound
                temp_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                raise Exception(f"screencapture command failed: {result.stderr}")
            
            # Load image
            image = Image.open(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            capture_time = time.time() - start_time
            
            return {
                "status": "success",
                "image": image,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "monitor": 0,
                    "original_size": image.size,
                    "capture_time_ms": round(capture_time * 1000, 2),
                    "file_size_estimate": image.size[0] * image.size[1] * 3,  # Estimate
                    "method": "screencapture",
                    "monitor_info": {
                        "left": 0,
                        "top": 0,
                        "width": image.size[0],
                        "height": image.size[1]
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"macOS screencapture fallback failed: {str(e)}",
                "image": None,
                "metadata": None
            }
    
    def optimize_for_ai_analysis(self, image: Image.Image) -> Dict[str, Any]:
        """
        Optimize image for AI analysis
        
        Args:
            image: PIL Image to optimize
            
        Returns:
            dict: Optimization result with optimized image
        """
        try:
            start_time = time.time()
            original_size = image.size
            
            # Convert RGBA to RGB if needed
            if image.mode in ("RGBA", "LA"):
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(image)
                image = background
            
            # Resize if too large
            if (image.width > self.config.max_width or 
                image.height > self.config.max_height):
                
                if self.config.preserve_aspect_ratio:
                    # Calculate aspect ratio preserving resize
                    ratio = min(
                        self.config.max_width / image.width,
                        self.config.max_height / image.height
                    )
                    new_size = (
                        int(image.width * ratio),
                        int(image.height * ratio)
                    )
                else:
                    new_size = (self.config.max_width, self.config.max_height)
                
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Optimize for AI analysis
            if self.config.optimize_for_ai:
                # Enhance contrast slightly for better AI recognition
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)
                
                # Slight sharpening for text recognition
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.05)
            
            optimization_time = time.time() - start_time
            
            return {
                "status": "success",
                "image": image,
                "optimization_info": {
                    "original_size": original_size,
                    "optimized_size": image.size,
                    "size_reduction": f"{(1 - (image.size[0] * image.size[1]) / (original_size[0] * original_size[1])) * 100:.1f}%",
                    "optimization_time_ms": round(optimization_time * 1000, 2)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Image optimization failed: {str(e)}",
                "image": image,  # Return original on error
                "optimization_info": None
            }
    
    def save_to_temp_file(self, image: Image.Image, prefix: str = "screenshot") -> Dict[str, Any]:
        """
        Save image to secure temporary file
        
        Args:
            image: PIL Image to save
            prefix: Filename prefix
            
        Returns:
            dict: Save result with file path
        """
        try:
            # Generate secure temporary filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{prefix}_{timestamp}.{self.config.format.lower()}"
            filepath = Path(self.temp_dir) / filename
            
            # Convert RGBA to RGB if saving as JPEG
            if self.config.format.upper() == "JPEG" and image.mode in ("RGBA", "LA"):
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(image)
                image = background
            
            # Save image
            save_kwargs = {
                "format": self.config.format,
                "optimize": True
            }
            
            if self.config.format.upper() == "JPEG":
                save_kwargs["quality"] = self.config.quality
            elif self.config.format.upper() == "PNG":
                save_kwargs["compress_level"] = self.config.compression_level
            
            image.save(filepath, **save_kwargs)
            
            # Track temp file for cleanup
            if self.config.auto_cleanup:
                self.temp_files.append(filepath)
            
            # Get file info
            file_size = filepath.stat().st_size
            
            return {
                "status": "success",
                "filepath": str(filepath),
                "filename": filename,
                "file_size": file_size,
                "format": self.config.format,
                "temp_dir": self.temp_dir
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save temp file: {str(e)}",
                "filepath": None
            }
    
    def image_to_base64(self, image: Image.Image) -> Dict[str, Any]:
        """
        Convert image to base64 string for API transmission
        
        Args:
            image: PIL Image to convert
            
        Returns:
            dict: Conversion result with base64 data
        """
        try:
            # Convert RGBA to RGB if saving as JPEG
            if self.config.format.upper() == "JPEG" and image.mode in ("RGBA", "LA"):
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(image)
                image = background
            
            # Convert to bytes
            buffer = io.BytesIO()
            save_kwargs = {
                "format": self.config.format,
                "optimize": True
            }
            
            if self.config.format.upper() == "JPEG":
                save_kwargs["quality"] = self.config.quality
            elif self.config.format.upper() == "PNG":
                save_kwargs["compress_level"] = self.config.compression_level
            
            image.save(buffer, **save_kwargs)
            image_bytes = buffer.getvalue()
            
            # Convert to base64
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            return {
                "status": "success",
                "base64_data": base64_string,
                "mime_type": f"image/{self.config.format.lower()}",
                "size_bytes": len(image_bytes),
                "base64_length": len(base64_string)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Base64 conversion failed: {str(e)}",
                "base64_data": None
            }
    
    def get_monitor_info(self) -> Dict[str, Any]:
        """Get information about available monitors"""
        try:
            monitors = []
            
            # Try MSS first
            try:
                mss_monitors = self.mss_instance.monitors
                if len(mss_monitors) > 1:  # MSS working properly
                    for i, monitor in enumerate(mss_monitors):
                        monitors.append({
                            "index": i,
                            "left": monitor["left"],
                            "top": monitor["top"],
                            "width": monitor["width"],
                            "height": monitor["height"],
                            "is_primary": i == 1  # First monitor (index 1) is usually primary
                        })
                    
                    return {
                        "status": "success",
                        "monitor_count": len(monitors) - 1,  # Exclude index 0 (all monitors)
                        "monitors": monitors[1:],  # Exclude index 0
                        "all_monitors_info": monitors[0],  # Index 0 = all monitors combined
                        "method": "mss"
                    }
                else:
                    raise Exception("MSS not detecting monitors properly")
                    
            except Exception:
                # MSS failed, use macOS fallback
                return self._get_monitor_info_macos_fallback()
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get monitor info: {str(e)}",
                "monitors": []
            }
    
    def _get_monitor_info_macos_fallback(self) -> Dict[str, Any]:
        """Get monitor info using macOS system_profiler as fallback"""
        try:
            import subprocess
            
            # Get display info using system_profiler
            result = subprocess.run([
                'system_profiler', 'SPDisplaysDataType', '-json'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Parse display information
                displays = data.get('SPDisplaysDataType', [])
                monitors = []
                
                # Add combined monitor info (index 0)
                monitors.append({
                    "index": 0,
                    "left": 0,
                    "top": 0,
                    "width": 0,  # Will be determined by actual screenshot
                    "height": 0,
                    "is_primary": False
                })
                
                # Add individual displays
                for i, display in enumerate(displays):
                    # Extract resolution if available
                    resolution = display.get('_spdisplays_resolution', 'Unknown')
                    if 'x' in str(resolution):
                        try:
                            width, height = map(int, str(resolution).split(' x '))
                        except:
                            width, height = 1920, 1080  # Default
                    else:
                        width, height = 1920, 1080  # Default
                    
                    monitors.append({
                        "index": i + 1,
                        "left": 0,
                        "top": 0,
                        "width": width,
                        "height": height,
                        "is_primary": i == 0
                    })
                
                return {
                    "status": "success",
                    "monitor_count": len(monitors) - 1,
                    "monitors": monitors[1:],
                    "all_monitors_info": monitors[0],
                    "method": "system_profiler"
                }
            else:
                # Ultimate fallback - assume single monitor
                return {
                    "status": "success",
                    "monitor_count": 1,
                    "monitors": [{
                        "index": 1,
                        "left": 0,
                        "top": 0,
                        "width": 1920,
                        "height": 1080,
                        "is_primary": True
                    }],
                    "all_monitors_info": {
                        "index": 0,
                        "left": 0,
                        "top": 0,
                        "width": 1920,
                        "height": 1080,
                        "is_primary": False
                    },
                    "method": "fallback"
                }
                
        except Exception as e:
            # Ultimate fallback
            return {
                "status": "success",
                "monitor_count": 1,
                "monitors": [{
                    "index": 1,
                    "left": 0,
                    "top": 0,
                    "width": 1920,
                    "height": 1080,
                    "is_primary": True
                }],
                "all_monitors_info": {
                    "index": 0,
                    "left": 0,
                    "top": 0,
                    "width": 1920,
                    "height": 1080,
                    "is_primary": False
                },
                "method": "fallback",
                "fallback_reason": str(e)
            }
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files"""
        try:
            cleaned_count = 0
            errors = []
            
            for filepath in self.temp_files:
                try:
                    if filepath.exists():
                        filepath.unlink()
                        cleaned_count += 1
                except Exception as e:
                    errors.append(f"{filepath}: {str(e)}")
            
            self.temp_files.clear()
            
            # Also cleanup temp directory if empty and we created it
            if self.config.secure_temp_storage:
                try:
                    temp_path = Path(self.temp_dir)
                    if temp_path.exists() and not any(temp_path.iterdir()):
                        temp_path.rmdir()
                except:
                    pass  # Ignore cleanup errors
            
            return {
                "status": "success",
                "cleaned_files": cleaned_count,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Cleanup failed: {str(e)}"
            }
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'config') and self.config.auto_cleanup:
            self.cleanup_temp_files()

# Global screen capture manager instance
_capture_manager = None

def get_capture_manager() -> ScreenCaptureManager:
    """Get or create the global screen capture manager"""
    global _capture_manager
    if _capture_manager is None:
        _capture_manager = ScreenCaptureManager()
    return _capture_manager

# ADK Function Tools

def capture_screen_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Capture screen using high-performance MSS library.
    
    Use this tool to take a screenshot of the current screen for AI analysis.
    The image is automatically optimized for AI processing.
    
    Returns:
        dict: Screen capture result with image data and metadata.
        Success: {'status': 'success', 'image_data': '...', 'metadata': {...}}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        manager = get_capture_manager()
        
        # Capture screen
        capture_result = manager.capture_screen(monitor=0)  # All monitors
        
        if capture_result["status"] != "success":
            return capture_result
        
        image = capture_result["image"]
        metadata = capture_result["metadata"]
        
        # Optimize for AI analysis
        optimization_result = manager.optimize_for_ai_analysis(image)
        
        if optimization_result["status"] != "success":
            return optimization_result
        
        optimized_image = optimization_result["image"]
        
        # Convert to base64 for API transmission
        base64_result = manager.image_to_base64(optimized_image)
        
        if base64_result["status"] != "success":
            return base64_result
        
        # Also save to temp file for backup
        temp_file_result = manager.save_to_temp_file(optimized_image, "ai_analysis")
        
        # Update session state
        tool_context.state["last_screenshot"] = {
            "timestamp": metadata["timestamp"],
            "file_path": temp_file_result.get("filepath"),
            "image_size": optimized_image.size,
            "optimization_applied": True
        }
        
        return {
            "status": "success",
            "image_data": base64_result["base64_data"],
            "mime_type": base64_result["mime_type"],
            "metadata": {
                **metadata,
                "optimization_info": optimization_result["optimization_info"],
                "base64_info": {
                    "size_bytes": base64_result["size_bytes"],
                    "base64_length": base64_result["base64_length"]
                },
                "temp_file": temp_file_result.get("filepath")
            },
            "ai_ready": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Screen capture failed: {str(e)}",
            "ai_ready": False
        }

def get_monitor_info_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get information about available monitors.
    
    Use this tool to understand the display setup before capturing screens.
    
    Returns:
        dict: Monitor information with details about available displays.
        Success: {'status': 'success', 'monitors': [...], 'monitor_count': N}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        manager = get_capture_manager()
        monitor_info = manager.get_monitor_info()
        
        # Update session state
        tool_context.state["monitor_info"] = monitor_info
        tool_context.state["monitor_check_time"] = datetime.now().isoformat()
        
        return monitor_info
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get monitor info: {str(e)}"
        }

def cleanup_temp_files_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Clean up temporary screenshot files.
    
    Use this tool to clean up temporary files after AI analysis is complete.
    This helps maintain privacy and free up disk space.
    
    Returns:
        dict: Cleanup result with number of files cleaned.
        Success: {'status': 'success', 'cleaned_files': N}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        manager = get_capture_manager()
        cleanup_result = manager.cleanup_temp_files()
        
        # Update session state
        tool_context.state["last_cleanup"] = {
            "timestamp": datetime.now().isoformat(),
            "cleaned_files": cleanup_result.get("cleaned_files", 0)
        }
        
        return cleanup_result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cleanup failed: {str(e)}"
        }

def capture_on_input_complete_tool(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Capture screen when input is complete (triggered by keylogger).
    
    Use this tool as a callback when the keylogger detects input completion.
    This creates the screen context for AI analysis.
    
    Returns:
        dict: Combined capture result with timing information.
        Success: {'status': 'success', 'capture_triggered': True, 'image_data': '...'}
        Error: {'status': 'error', 'message': 'Error details'}
    """
    try:
        # Get input completion trigger time
        trigger_time = datetime.now()
        
        # Small delay to ensure screen is stable after input
        time.sleep(0.1)
        
        # Capture screen
        capture_result = capture_screen_tool(tool_context)
        
        if capture_result["status"] != "success":
            return capture_result
        
        # Add trigger context
        capture_result["trigger_info"] = {
            "trigger_time": trigger_time.isoformat(),
            "trigger_type": "input_completion",
            "delay_ms": 100  # 100ms delay
        }
        capture_result["capture_triggered"] = True
        
        return capture_result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Triggered capture failed: {str(e)}",
            "capture_triggered": False
        }

# Create ADK Function Tools
capture_screen_function_tool = FunctionTool(func=capture_screen_tool)
get_monitor_info_function_tool = FunctionTool(func=get_monitor_info_tool)
cleanup_temp_files_function_tool = FunctionTool(func=cleanup_temp_files_tool)
capture_on_input_complete_function_tool = FunctionTool(func=capture_on_input_complete_tool)

# Example monitoring agent with screen capture
def create_screen_capture_agent() -> Agent:
    """Create a screen capture agent with all capture tools"""
    
    return Agent(
        name="ScreenCaptureAgent",
        model="gemini-2.0-flash",
        description="A screen capture agent that provides high-performance screenshot capabilities for AI analysis",
        instruction="""
        You are a screen capture agent responsible for taking screenshots and optimizing them for AI analysis.
        
        Your capabilities include:
        1. capture_screen: Take high-performance screenshots using MSS
        2. get_monitor_info: Get information about available displays
        3. cleanup_temp_files: Clean up temporary files for privacy
        4. capture_on_input_complete: Triggered capture when input is complete
        
        All captured images are automatically optimized for AI analysis:
        - Resized to optimal dimensions (max 1920x1080)
        - Enhanced contrast and sharpness for better recognition
        - Compressed for efficient API transmission
        - Saved securely with automatic cleanup
        
        Always provide clear status updates and handle errors gracefully.
        Maintain privacy by cleaning up temporary files after use.
        """,
        tools=[
            capture_screen_function_tool,
            get_monitor_info_function_tool,
            cleanup_temp_files_function_tool,
            capture_on_input_complete_function_tool
        ]
    )

# Direct execution mode (for testing)
if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    
    # Test screen capture
    console.print("[bold green]Screen Capture Tool Test[/]")
    
    manager = get_capture_manager()
    
    # Test monitor info
    console.print("\n[bold blue]Monitor Information:[/]")
    monitor_info = manager.get_monitor_info()
    console.print(monitor_info)
    
    # Test screen capture
    console.print("\n[bold blue]Capturing Screen...[/]")
    capture_result = manager.capture_screen()
    
    if capture_result["status"] == "success":
        console.print(f"✅ Capture successful!")
        console.print(f"Size: {capture_result['metadata']['original_size']}")
        console.print(f"Capture time: {capture_result['metadata']['capture_time_ms']}ms")
        
        # Test optimization
        console.print("\n[bold blue]Optimizing for AI...[/]")
        optimization_result = manager.optimize_for_ai_analysis(capture_result["image"])
        
        if optimization_result["status"] == "success":
            console.print(f"✅ Optimization successful!")
            console.print(f"Size reduction: {optimization_result['optimization_info']['size_reduction']}")
            
            # Test temp file save
            console.print("\n[bold blue]Saving to temp file...[/]")
            temp_result = manager.save_to_temp_file(optimization_result["image"], "test")
            
            if temp_result["status"] == "success":
                console.print(f"✅ Temp file saved: {temp_result['filepath']}")
                console.print(f"File size: {temp_result['file_size']} bytes")
                
                # Test cleanup
                console.print("\n[bold blue]Cleaning up...[/]")
                cleanup_result = manager.cleanup_temp_files()
                console.print(f"✅ Cleaned up {cleanup_result['cleaned_files']} files")
            else:
                console.print(f"❌ Temp file save failed: {temp_result['message']}")
        else:
            console.print(f"❌ Optimization failed: {optimization_result['message']}")
    else:
        console.print(f"❌ Capture failed: {capture_result['message']}") 