"""
System-Level Lock Screen for Parental Control

This module implements a full-screen lock screen that blocks all user interaction
when inappropriate content is detected. The lock screen:
- Covers all monitors with a full-screen overlay
- Blocks all keyboard and mouse input
- Displays blocking reason and approval status
- Integrates with WebSocket server for parent approval
- Automatically unlocks when approved by parent
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import json
import os
import sys
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import multiprocessing
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LockScreenConfig:
    """Configuration for lock screen"""
    timeout_seconds: int = 300  # 5 minutes default timeout
    show_countdown: bool = True
    show_reason: bool = True
    allow_emergency_unlock: bool = True
    emergency_password: str = "emergency123"
    background_color: str = "#1a1a1a"
    text_color: str = "#ffffff"
    accent_color: str = "#ff4444"
    font_family: str = "Arial"
    font_size_large: int = 24
    font_size_medium: int = 16
    font_size_small: int = 12

# Global lock screen request queue for thread-safe communication
_lock_screen_requests = []
_lock_screen_lock = threading.Lock()

class SystemLockScreen:
    """System-level lock screen implementation"""
    
    def __init__(self, config: Optional[LockScreenConfig] = None):
        self.config = config or LockScreenConfig()
        self.root = None
        self.windows = []
        self.is_locked = False
        self.lock_reason = "System locked by parental control"
        self.start_time = None
        self.approval_callback = None
        self.timeout_callback = None
        self.emergency_unlock_callback = None
        
        # Threading
        self.lock_thread = None
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # UI elements
        self.reason_label = None
        self.status_label = None
        self.countdown_label = None
        self.progress_bar = None
        
        logger.info("System lock screen initialized")
    
    def show_lock_screen(self, reason: str = None, timeout: int = None, 
                        approval_callback: Callable = None,
                        timeout_callback: Callable = None) -> None:
        """
        Show the lock screen with specified reason and timeout
        
        Args:
            reason: Reason for locking the screen
            timeout: Timeout in seconds (None for no timeout)
            approval_callback: Callback when parent approves
            timeout_callback: Callback when timeout occurs
        """
        if self.is_locked:
            logger.warning("Lock screen is already active")
            return
        
        self.lock_reason = reason or self.lock_reason
        self.approval_callback = approval_callback
        self.timeout_callback = timeout_callback
        
        if timeout:
            self.config.timeout_seconds = timeout
        
        logger.info(f"Showing lock screen: {self.lock_reason}")
        
        # Check if we're on the main thread
        if threading.current_thread() is threading.main_thread():
            # Already on main thread, run directly
            self._show_lock_screen_thread()
        else:
            # We're on a background thread - use subprocess approach for macOS compatibility
            logger.info("Running lock screen in subprocess for macOS compatibility")
            self._run_lock_screen_subprocess()
    
    def _run_lock_screen_subprocess(self):
        """Run lock screen in subprocess for macOS compatibility"""
        try:
            # Create a simple lock screen script that runs in its own process
            lock_script = f'''
import tkinter as tk
import threading
import time
from datetime import datetime

class SimpleLockScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Locked")
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#1a1a1a")
        self.root.overrideredirect(True)
        
        # Create UI
        main_frame = tk.Frame(self.root, bg="#1a1a1a")
        main_frame.pack(expand=True, fill='both')
        
        center_frame = tk.Frame(main_frame, bg="#1a1a1a")
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Lock icon
        lock_icon = tk.Label(center_frame, text="🔒", font=("Arial", 72), 
                           bg="#1a1a1a", fg="#ff4444")
        lock_icon.pack(pady=(0, 20))
        
        # Title
        title_label = tk.Label(center_frame, text="System Locked", 
                             font=("Arial", 24, 'bold'), bg="#1a1a1a", fg="#ffffff")
        title_label.pack(pady=(0, 20))
        
        # Reason
        reason_label = tk.Label(center_frame, text="{self.lock_reason}", 
                              font=("Arial", 16), bg="#1a1a1a", fg="#ffffff",
                              wraplength=600, justify='center')
        reason_label.pack(pady=(0, 30))
        
        # Status
        status_label = tk.Label(center_frame, text="Waiting for parent approval...", 
                              font=("Arial", 16), bg="#1a1a1a", fg="#ffffff")
        status_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = tk.Label(center_frame, 
                              text="A notification has been sent to your parent.\\nPlease wait for approval.",
                              font=("Arial", 12), bg="#1a1a1a", fg="#ffffff", justify='center')
        instructions.pack(pady=(0, 20))
        
        # Footer
        footer = tk.Label(main_frame, text="Safe Browser AI - Parental Control System",
                        font=("Arial", 12), bg="#1a1a1a", fg="#ffffff")
        footer.pack(side='bottom', pady=20)
        
        # Block input
        self.root.bind('<Key>', lambda e: 'break')
        self.root.bind('<Button>', lambda e: 'break')
        self.root.focus_set()
        self.root.grab_set()
        
        # Check for unlock signal file
        self.check_unlock()
        
    def check_unlock(self):
        import os
        if os.path.exists('/tmp/unlock_signal'):
            os.remove('/tmp/unlock_signal')
            self.root.quit()
            return
        self.root.after(1000, self.check_unlock)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    lock = SimpleLockScreen()
    lock.run()
'''
            
            # Write the lock script to a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(lock_script)
                script_path = f.name
            
            # Run the lock screen in a subprocess
            self.lock_process = subprocess.Popen([sys.executable, script_path])
            self.is_locked = True
            self.start_time = datetime.now()
            
            # Start monitoring thread
            self.update_thread = threading.Thread(target=self._monitor_subprocess, daemon=True)
            self.update_thread.start()
            
            logger.info("Lock screen subprocess started")
            
        except Exception as e:
            logger.error(f"Error starting lock screen subprocess: {e}")
            # Fallback to notification
            self._show_notification_fallback()
    
    def _monitor_subprocess(self):
        """Monitor the subprocess and handle timeout"""
        try:
            timeout_time = self.start_time + timedelta(seconds=self.config.timeout_seconds)
            
            while self.is_locked and datetime.now() < timeout_time:
                # Check if subprocess is still running
                if hasattr(self, 'lock_process') and self.lock_process.poll() is not None:
                    # Process ended
                    self.is_locked = False
                    break
                    
                time.sleep(1)
            
            # Handle timeout
            if self.is_locked and datetime.now() >= timeout_time:
                logger.info("Lock screen timeout")
                if self.timeout_callback:
                    self.timeout_callback()
                    
        except Exception as e:
            logger.error(f"Error monitoring subprocess: {e}")
    
    def _show_notification_fallback(self):
        """Fallback notification when lock screen fails"""
        try:
            subprocess.run([
                'osascript', '-e', 
                f'display notification "{self.lock_reason}" with title "System Locked"'
            ])
            logger.info("Fallback notification shown")
        except Exception as e:
            logger.error(f"Fallback notification failed: {e}")
    
    def _show_lock_screen_thread(self):
        """Thread function to show lock screen - only for main thread"""
        try:
            self.is_locked = True
            self.start_time = datetime.now()
            self.stop_event.clear()
            
            # Create main window
            self.root = tk.Tk()
            self.root.title("System Locked")
            
            # Configure window to be always on top and fullscreen
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
            self.root.configure(bg=self.config.background_color)
            
            # Disable window manager decorations
            self.root.overrideredirect(True)
            
            # Bind escape key for emergency unlock (if enabled)
            if self.config.allow_emergency_unlock:
                self.root.bind('<Control-Alt-e>', self._emergency_unlock_dialog)
            
            # Prevent window from being closed
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Create UI
            self._create_ui()
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_ui_thread, daemon=True)
            self.update_thread.start()
            
            # Block all input
            self._block_input()
            
            # Start the main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Error in lock screen thread: {e}")
            # Fallback to notification
            self._show_notification_fallback()
        finally:
            self.is_locked = False
            self.stop_event.set()
    
    def _create_ui(self):
        """Create the lock screen UI"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.config.background_color)
        main_frame.pack(expand=True, fill='both')
        
        # Center container
        center_frame = tk.Frame(main_frame, bg=self.config.background_color)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Lock icon (using text)
        lock_icon = tk.Label(
            center_frame,
            text="🔒",
            font=(self.config.font_family, 72),
            bg=self.config.background_color,
            fg=self.config.accent_color
        )
        lock_icon.pack(pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            center_frame,
            text="System Locked",
            font=(self.config.font_family, self.config.font_size_large, 'bold'),
            bg=self.config.background_color,
            fg=self.config.text_color
        )
        title_label.pack(pady=(0, 20))
        
        # Reason
        if self.config.show_reason:
            self.reason_label = tk.Label(
                center_frame,
                text=self.lock_reason,
                font=(self.config.font_family, self.config.font_size_medium),
                bg=self.config.background_color,
                fg=self.config.text_color,
                wraplength=600,
                justify='center'
            )
            self.reason_label.pack(pady=(0, 30))
        
        # Status
        self.status_label = tk.Label(
            center_frame,
            text="Waiting for parent approval...",
            font=(self.config.font_family, self.config.font_size_medium),
            bg=self.config.background_color,
            fg=self.config.text_color
        )
        self.status_label.pack(pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            center_frame,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 20))
        
        # Countdown
        if self.config.show_countdown:
            self.countdown_label = tk.Label(
                center_frame,
                text="",
                font=(self.config.font_family, self.config.font_size_small),
                bg=self.config.background_color,
                fg=self.config.text_color
            )
            self.countdown_label.pack(pady=(0, 30))
        
        # Instructions
        instructions = tk.Label(
            center_frame,
            text="A notification has been sent to your parent.\nPlease wait for approval.",
            font=(self.config.font_family, self.config.font_size_small),
            bg=self.config.background_color,
            fg=self.config.text_color,
            justify='center'
        )
        instructions.pack(pady=(0, 20))
        
        # Emergency unlock hint
        if self.config.allow_emergency_unlock:
            emergency_hint = tk.Label(
                center_frame,
                text="Emergency unlock: Ctrl+Alt+E",
                font=(self.config.font_family, self.config.font_size_small),
                bg=self.config.background_color,
                fg=self.config.text_color
            )
            emergency_hint.pack(pady=(0, 10))
        
        # Footer
        footer = tk.Label(
            main_frame,
            text="Safe Browser AI - Parental Control System",
            font=(self.config.font_family, self.config.font_size_small),
            bg=self.config.background_color,
            fg=self.config.text_color
        )
        footer.pack(side='bottom', pady=20)
    
    def _update_ui_thread(self):
        """Thread to update UI elements"""
        while not self.stop_event.is_set() and self.is_locked:
            try:
                if self.start_time:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    remaining = max(0, self.config.timeout_seconds - elapsed)
                    
                    # Update progress bar
                    if self.progress_bar:
                        progress = (elapsed / self.config.timeout_seconds) * 100
                        self.root.after(0, lambda: self.progress_bar.configure(value=min(100, progress)))
                    
                    # Update countdown
                    if self.countdown_label and self.config.show_countdown:
                        minutes = int(remaining // 60)
                        seconds = int(remaining % 60)
                        countdown_text = f"Timeout in: {minutes:02d}:{seconds:02d}"
                        self.root.after(0, lambda: self.countdown_label.configure(text=countdown_text))
                    
                    # Check timeout
                    if remaining <= 0:
                        self.root.after(0, self._handle_timeout)
                        break
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error updating UI: {e}")
                break
    
    def _block_input(self):
        """Block keyboard and mouse input"""
        # Bind all key events to prevent them
        self.root.bind('<Key>', lambda e: 'break')
        self.root.bind('<Button>', lambda e: 'break')
        self.root.bind('<Motion>', lambda e: 'break')
        
        # Focus on root window
        self.root.focus_set()
        self.root.grab_set()
    
    def _on_closing(self):
        """Handle window close attempts"""
        logger.info("Lock screen close attempt blocked")
        # Don't allow closing
        pass
    
    def _emergency_unlock_dialog(self, event=None):
        """Show emergency unlock dialog"""
        if not self.config.allow_emergency_unlock:
            return
        
        # Create password dialog
        password = tk.simpledialog.askstring(
            "Emergency Unlock",
            "Enter emergency password:",
            show='*'
        )
        
        if password == self.config.emergency_password:
            logger.info("Emergency unlock successful")
            if self.emergency_unlock_callback:
                self.emergency_unlock_callback()
            self.unlock_screen()
        else:
            messagebox.showerror("Error", "Invalid emergency password")
    
    def _handle_timeout(self):
        """Handle timeout expiration"""
        logger.info("Lock screen timeout expired")
        if self.timeout_callback:
            self.timeout_callback()
        
        # Update status
        if self.status_label:
            self.status_label.configure(text="Timeout expired. System remains locked.")
        
        # Optionally unlock or keep locked
        # For now, keep locked until parent approval
    
    def unlock_screen(self):
        """Unlock the screen"""
        if not self.is_locked:
            logger.info("Screen not locked in this process – sending global unlock signal")
            try:
                # Create unlock signal file so any subprocess lock screen can detect it
                with open('/tmp/unlock_signal', 'w') as f:
                    f.write('unlock')
                # Give the subprocess a moment to read the file
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to write global unlock signal: {e}")
            return

        logger.info("Unlocking screen")
        
        # Set stop event
        self.stop_event.set()
        
        # Handle subprocess unlock
        if hasattr(self, 'lock_process'):
            try:
                # Create unlock signal file
                with open('/tmp/unlock_signal', 'w') as f:
                    f.write('unlock')
                
                # Wait for process to end
                self.lock_process.wait(timeout=5)
                
                # Clean up signal file
                if os.path.exists('/tmp/unlock_signal'):
                    os.remove('/tmp/unlock_signal')
                    
            except Exception as e:
                logger.error(f"Error unlocking subprocess: {e}")
                # Force terminate if needed
                try:
                    self.lock_process.terminate()
                except:
                    pass
        
        # Close UI if running in main thread
        if self.root:
            self.root.after(0, self.root.quit)
            self.root.after(0, self.root.destroy)
        
        self.is_locked = False
        
        # Call approval callback
        if self.approval_callback:
            self.approval_callback()
    
    def update_status(self, status: str):
        """Update the status message"""
        if self.status_label and self.root:
            self.root.after(0, lambda: self.status_label.configure(text=status))
    
    def is_screen_locked(self) -> bool:
        """Check if screen is currently locked"""
        return self.is_locked
    
    def get_lock_duration(self) -> float:
        """Get current lock duration in seconds"""
        if not self.is_locked or not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

# Global lock screen instance
_lock_screen: Optional[SystemLockScreen] = None

def get_lock_screen() -> SystemLockScreen:
    """Get or create the global lock screen instance"""
    global _lock_screen
    if _lock_screen is None:
        _lock_screen = SystemLockScreen()
    return _lock_screen

def show_system_lock(reason: str, timeout: int = 300, 
                    approval_callback: Callable = None,
                    timeout_callback: Callable = None) -> None:
    """
    Show system lock screen
    
    Args:
        reason: Reason for locking
        timeout: Timeout in seconds
        approval_callback: Callback when approved
        timeout_callback: Callback when timeout occurs
    """
    lock_screen = get_lock_screen()
    lock_screen.show_lock_screen(
        reason=reason,
        timeout=timeout,
        approval_callback=approval_callback,
        timeout_callback=timeout_callback
    )

def unlock_system() -> None:
    """Unlock the system"""
    lock_screen = get_lock_screen()
    lock_screen.unlock_screen()

def is_system_locked() -> bool:
    """Check if the system is currently locked"""
    lock_screen = get_lock_screen()
    return lock_screen.is_locked

def update_lock_status(status: str) -> None:
    """Update lock screen status"""
    lock_screen = get_lock_screen()
    lock_screen.update_status(status)

if __name__ == "__main__":
    # Test the lock screen
    def on_approval():
        print("✅ Parent approved - unlocking")
        unlock_system()
    
    def on_timeout():
        print("⏰ Timeout occurred")
    
    def on_emergency():
        print("🚨 Emergency unlock used")
    
    print("🔒 Testing system lock screen...")
    
    lock_screen = get_lock_screen()
    lock_screen.emergency_unlock_callback = on_emergency
    
    show_system_lock(
        reason="Test lock - inappropriate content detected",
        timeout=30,  # 30 seconds for testing
        approval_callback=on_approval,
        timeout_callback=on_timeout
    )
    
    # Simulate approval after 10 seconds
    def simulate_approval():
        time.sleep(10)
        print("📱 Simulating parent approval...")
        update_lock_status("Parent approved! Unlocking...")
        time.sleep(2)
        unlock_system()
    
    approval_thread = threading.Thread(target=simulate_approval, daemon=True)
    approval_thread.start()
    
    # Keep main thread alive
    try:
        while is_system_locked():
            time.sleep(1)
        print("🔓 System unlocked")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted - unlocking system")
        unlock_system() 