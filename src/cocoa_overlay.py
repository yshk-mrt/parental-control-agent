"""
Native macOS Cocoa Overlay for Parental Control Lock Screen

This module implements a native macOS overlay using PyObjC that provides
perfect full-screen coverage without the limitations of Tkinter:
- Covers entire screen including menu bar
- Prevents all user interaction
- Cannot be minimized, closed, or moved
- Uses CGShieldingWindowLevel for maximum priority
"""

import logging
import threading
import time
from typing import Callable, Optional
from datetime import datetime
import os
import sys

logger = logging.getLogger(__name__)

# Try to import Cocoa dependencies
try:
    from Cocoa import (
        NSApplication, NSWindow, NSScreen, NSColor, NSView, NSTextField, NSFont,
        NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
        NSApplicationActivationPolicyRegular, NSRunningApplication, NSBundle,
        NSImageView, NSImage, NSAttributedString, NSForegroundColorAttributeName,
        NSFontAttributeName, NSParagraphStyleAttributeName, NSMutableParagraphStyle,
        NSTextAlignmentCenter
    )
    from Quartz import CGShieldingWindowLevel
    from Foundation import NSMakeRect, NSTimer, NSRunLoop, NSDefaultRunLoopMode
    
    COCOA_AVAILABLE = True
    logger.info("Cocoa dependencies available")
except ImportError as e:
    COCOA_AVAILABLE = False
    logger.warning(f"Cocoa dependencies not available: {e}")
    logger.info("Install with: pip install PyObjC-framework-Cocoa PyObjC-framework-Quartz")

class ParentalControlOverlayView(NSView):
    """Custom NSView for the parental control overlay content"""
    
    def initWithFrame_reason_status_(self, frame, reason, status):
        self = self.initWithFrame_(frame)
        if self:
            self.reason = reason
            self.status = status
            self.setup_ui()
        return self
    
    def setup_ui(self):
        """Setup the UI elements"""
        # Background color
        self.setWantsLayer_(True)
        self.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.1, 0.1, 0.1, 0.95).CGColor())
        
        # Lock icon (using Unicode emoji)
        lock_icon = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        lock_icon.setStringValue_("🔒")
        lock_icon.setFont_(NSFont.systemFontOfSize_(72))
        lock_icon.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 0.27, 0.27, 1.0))
        lock_icon.setBackgroundColor_(NSColor.clearColor())
        lock_icon.setBordered_(False)
        lock_icon.setEditable_(False)
        lock_icon.setSelectable_(False)
        lock_icon.setAlignment_(NSTextAlignmentCenter)
        
        # Position lock icon at center top
        screen_frame = self.frame()
        lock_x = (screen_frame.size.width - 100) / 2
        lock_y = screen_frame.size.height * 0.6
        lock_icon.setFrame_(NSMakeRect(lock_x, lock_y, 100, 100))
        self.addSubview_(lock_icon)
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 40))
        title.setStringValue_("System Locked")
        title.setFont_(NSFont.boldSystemFontOfSize_(24))
        title.setTextColor_(NSColor.whiteColor())
        title.setBackgroundColor_(NSColor.clearColor())
        title.setBordered_(False)
        title.setEditable_(False)
        title.setSelectable_(False)
        title.setAlignment_(NSTextAlignmentCenter)
        
        # Position title
        title_x = (screen_frame.size.width - 600) / 2
        title_y = lock_y - 60
        title.setFrame_(NSMakeRect(title_x, title_y, 600, 40))
        self.addSubview_(title)
        
        # Reason text
        reason_text = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 800, 60))
        reason_text.setStringValue_(self.reason)
        reason_text.setFont_(NSFont.systemFontOfSize_(16))
        reason_text.setTextColor_(NSColor.whiteColor())
        reason_text.setBackgroundColor_(NSColor.clearColor())
        reason_text.setBordered_(False)
        reason_text.setEditable_(False)
        reason_text.setSelectable_(False)
        reason_text.setAlignment_(NSTextAlignmentCenter)
        
        # Position reason
        reason_x = (screen_frame.size.width - 800) / 2
        reason_y = title_y - 80
        reason_text.setFrame_(NSMakeRect(reason_x, reason_y, 800, 60))
        self.addSubview_(reason_text)
        
        # Status text
        status_text = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 30))
        status_text.setStringValue_(self.status)
        status_text.setFont_(NSFont.systemFontOfSize_(16))
        status_text.setTextColor_(NSColor.whiteColor())
        status_text.setBackgroundColor_(NSColor.clearColor())
        status_text.setBordered_(False)
        status_text.setEditable_(False)
        status_text.setSelectable_(False)
        status_text.setAlignment_(NSTextAlignmentCenter)
        
        # Position status
        status_x = (screen_frame.size.width - 600) / 2
        status_y = reason_y - 50
        status_text.setFrame_(NSMakeRect(status_x, status_y, 600, 30))
        self.addSubview_(status_text)
        
        # Instructions
        instructions = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 40))
        instructions.setStringValue_("A notification has been sent to your parent.\nPlease wait for approval.")
        instructions.setFont_(NSFont.systemFontOfSize_(12))
        instructions.setTextColor_(NSColor.whiteColor())
        instructions.setBackgroundColor_(NSColor.clearColor())
        instructions.setBordered_(False)
        instructions.setEditable_(False)
        instructions.setSelectable_(False)
        instructions.setAlignment_(NSTextAlignmentCenter)
        
        # Position instructions
        instr_x = (screen_frame.size.width - 600) / 2
        instr_y = status_y - 60
        instructions.setFrame_(NSMakeRect(instr_x, instr_y, 600, 40))
        self.addSubview_(instructions)
        
        # Footer
        footer = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 20))
        footer.setStringValue_("Safe Browser AI - Parental Control System")
        footer.setFont_(NSFont.systemFontOfSize_(12))
        footer.setTextColor_(NSColor.whiteColor())
        footer.setBackgroundColor_(NSColor.clearColor())
        footer.setBordered_(False)
        footer.setEditable_(False)
        footer.setSelectable_(False)
        footer.setAlignment_(NSTextAlignmentCenter)
        
        # Position footer at bottom
        footer_x = (screen_frame.size.width - 600) / 2
        footer_y = 40
        footer.setFrame_(NSMakeRect(footer_x, footer_y, 600, 20))
        self.addSubview_(footer)
        
        # Store references for updates
        self.status_label = status_text
        self.reason_label = reason_text
    
    def update_status(self, new_status):
        """Update the status text"""
        if hasattr(self, 'status_label'):
            self.status_label.setStringValue_(new_status)
    
    def update_reason(self, new_reason):
        """Update the reason text"""
        if hasattr(self, 'reason_label'):
            self.reason_label.setStringValue_(new_reason)

class CocoaOverlay:
    """Native macOS Cocoa overlay implementation"""
    
    def __init__(self):
        self.window = None
        self.view = None
        self.app = None
        self.is_showing = False
        self.unlock_predicate = None
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
    def show_overlay(self, reason: str, unlock_predicate: Callable[[], bool]) -> None:
        """
        Show the overlay with the specified reason
        
        Args:
            reason: Reason for showing the overlay
            unlock_predicate: Function that returns True when overlay should be dismissed
        """
        if not COCOA_AVAILABLE:
            logger.error("Cocoa not available, cannot show overlay")
            return
        
        if self.is_showing:
            logger.warning("Overlay already showing, hiding previous overlay first")
            self.hide_overlay()
            time.sleep(0.1)  # Brief pause to ensure cleanup
        
        self.unlock_predicate = unlock_predicate
        self.is_showing = True
        
        logger.info(f"Showing Cocoa overlay: {reason}")
        
        # Run overlay in main thread
        if threading.current_thread() is threading.main_thread():
            self._show_overlay_main_thread(reason)
        else:
            # Schedule on main thread using NSObject performSelectorOnMainThread
            logger.info("Scheduling Cocoa overlay on main thread from background thread")
            self._schedule_on_main_thread(reason)
    
    def _schedule_on_main_thread(self, reason: str):
        """Schedule overlay display on main thread using independent Cocoa app"""
        try:
            import subprocess
            import sys
            import os
            
            # Use the independent Cocoa lock screen app
            script_path = os.path.join(os.path.dirname(__file__), 'cocoa_lock_screen.py')
            
            logger.info("Using independent Cocoa application for display")
            
            # Run the independent Cocoa app
            self.overlay_process = subprocess.Popen([
                sys.executable, script_path,
                '--reason', reason,
                '--timeout', str(self.config.timeout_seconds if hasattr(self, 'config') else 300)
            ])
            
            self.is_showing = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_unlock, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Independent Cocoa application started successfully")
            
        except Exception as e:
            logger.error(f"Error starting independent Cocoa application: {e}")
            # Fallback to subprocess approach
            self._show_overlay_subprocess(reason)
    
    def _show_overlay_subprocess(self, reason: str):
        """Show overlay using subprocess approach for main thread safety"""
        try:
            import subprocess
            import tempfile
            import sys
            
            # Create a simple overlay script that runs in its own process
            overlay_script = f'''
import sys
import time
import os
import threading
sys.path.append('{os.path.dirname(__file__)}')

try:
    from cocoa_overlay import CocoaOverlay
    
    # Create overlay instance
    overlay = CocoaOverlay()
    
    # Define unlock predicate
    def unlock_predicate():
        # Check for unlock signal file
        if os.path.exists('/tmp/cocoa_overlay_unlock'):
            return True
        return False
    
    # Show overlay
    overlay.show_overlay("{reason}", unlock_predicate)
    
    # Keep process alive
    while overlay.is_showing:
        time.sleep(0.1)
        
except Exception as e:
    print(f"Error in overlay subprocess: {{e}}")
    import traceback
    traceback.print_exc()
'''
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(overlay_script)
                script_path = f.name
            
            # Run overlay in subprocess
            self.overlay_process = subprocess.Popen([sys.executable, script_path])
            self.is_showing = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_unlock, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Cocoa overlay subprocess started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Cocoa overlay subprocess: {e}")
            self.is_showing = False
    
    def _show_overlay_main_thread(self, reason: str):
        """Show overlay on main thread"""
        try:
            # Get the main screen
            screen = NSScreen.mainScreen()
            screen_frame = screen.frame()
            
            # Create application if needed
            self.app = NSApplication.sharedApplication()
            self.app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
            
            # Activate the application to bring it to foreground
            self.app.activateIgnoringOtherApps_(True)
            
            # Create window
            self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                screen_frame,
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False
            )
            
            # Configure window
            self.window.setLevel_(CGShieldingWindowLevel())
            self.window.setOpaque_(False)
            self.window.setBackgroundColor_(NSColor.clearColor())
            self.window.setIgnoresMouseEvents_(False)
            self.window.setAcceptsMouseMovedEvents_(False)
            # Note: setCanBecomeKeyWindow_ and setCanBecomeMainWindow_ are not available in newer PyObjC
            # The window will automatically become key/main when shown
            
            # Create and set content view
            self.view = ParentalControlOverlayView.alloc().initWithFrame_reason_status_(
                screen_frame, reason, "Waiting for parent approval..."
            )
            self.window.setContentView_(self.view)
            
            # Show window
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()
            
            # Make window key (but not main, as borderless windows can't be main)
            self.window.makeKeyWindow()
            
            # Ensure application is active
            self.app.activateIgnoringOtherApps_(True)
            
            # Set showing flag
            self.is_showing = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_unlock, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Cocoa overlay displayed successfully")
            
        except Exception as e:
            logger.error(f"Error showing Cocoa overlay: {e}")
            self.is_showing = False
    
    def _monitor_unlock(self):
        """Monitor for unlock condition"""
        while self.is_showing and not self.stop_event.is_set():
            try:
                if self.unlock_predicate and self.unlock_predicate():
                    logger.info("Unlock condition met, hiding overlay")
                    self.hide_overlay()
                    break
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in unlock monitoring: {e}")
                time.sleep(1)
    
    def hide_overlay(self):
        """Hide the overlay"""
        if not self.is_showing:
            return
        
        logger.info("Hiding Cocoa overlay")
        
        try:
            # If using subprocess, signal it to stop
            if hasattr(self, 'overlay_process') and self.overlay_process:
                # Create unlock signal file for independent Cocoa app
                try:
                    with open('/tmp/cocoa_lock_unlock', 'w') as f:
                        f.write('unlock')
                    
                    # Wait for process to terminate
                    self.overlay_process.wait(timeout=5)
                    
                    # Clean up signal file
                    if os.path.exists('/tmp/cocoa_lock_unlock'):
                        os.remove('/tmp/cocoa_lock_unlock')
                        
                except Exception as e:
                    logger.error(f"Error terminating overlay subprocess: {e}")
                    try:
                        self.overlay_process.terminate()
                    except:
                        pass
                
                self.overlay_process = None
            
            # If using direct window, close it
            if self.window:
                self.window.orderOut_(None)
                self.window.close()
                self.window = None
            
            self.view = None
            self.is_showing = False
            self.stop_event.set()
            
            logger.info("Cocoa overlay hidden successfully")
            
        except Exception as e:
            logger.error(f"Error hiding Cocoa overlay: {e}")
    
    def update_status(self, status: str):
        """Update the status text"""
        if self.view:
            self.view.update_status(status)
    
    def update_reason(self, reason: str):
        """Update the reason text"""
        if self.view:
            self.view.update_reason(reason)

# Global overlay instance
_overlay_instance = None

def show_overlay(reason: str, unlock_predicate: Callable[[], bool]) -> None:
    """
    Show the Cocoa overlay
    
    Args:
        reason: Reason for showing the overlay
        unlock_predicate: Function that returns True when overlay should be dismissed
    """
    global _overlay_instance
    
    if not COCOA_AVAILABLE:
        logger.error("Cocoa overlay not available on this system")
        return
    
    if _overlay_instance is None:
        _overlay_instance = CocoaOverlay()
    
    _overlay_instance.show_overlay(reason, unlock_predicate)

def hide_overlay() -> None:
    """Hide the Cocoa overlay"""
    global _overlay_instance
    
    if _overlay_instance:
        _overlay_instance.hide_overlay()

def update_overlay_status(status: str) -> None:
    """Update the overlay status text"""
    global _overlay_instance
    
    if _overlay_instance:
        _overlay_instance.update_status(status)

def update_overlay_reason(reason: str) -> None:
    """Update the overlay reason text"""
    global _overlay_instance
    
    if _overlay_instance:
        _overlay_instance.update_reason(reason)

def is_overlay_available() -> bool:
    """Check if Cocoa overlay is available"""
    return COCOA_AVAILABLE

# Test function
def test_overlay():
    """Test the Cocoa overlay"""
    if not COCOA_AVAILABLE:
        print("Cocoa overlay not available")
        return
    
    print("Testing Cocoa overlay...")
    
    # Test unlock predicate (unlock after 10 seconds)
    start_time = time.time()
    def unlock_after_10_seconds():
        return time.time() - start_time > 10
    
    show_overlay("Testing Cocoa overlay - will unlock in 10 seconds", unlock_after_10_seconds)
    
    # Keep main thread alive
    try:
        while _overlay_instance and _overlay_instance.is_showing:
            time.sleep(0.1)
    except KeyboardInterrupt:
        hide_overlay()
    
    print("Test completed")

if __name__ == "__main__":
    test_overlay() 