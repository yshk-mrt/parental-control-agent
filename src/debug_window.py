#!/usr/bin/env python3
"""
Debug Window for Parental Control System

This module provides a semi-transparent debug window that displays real-time
analysis results and system status information.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class DebugWindow:
    """
    Semi-transparent debug window for real-time monitoring
    """
    
    def __init__(self):
        self.root = None
        self.text_widget = None
        self.status_label = None
        self.debug_queue = queue.Queue()
        self.running = False
        self.max_entries = 10
        self.entries = []
        
        # Colors for different categories and actions
        self.colors = {
            'input': '#FFFF99',      # Yellow
            'processing': '#FFA500',  # Orange
            'incomplete': '#808080',  # Gray
            'complete': '#90EE90',    # Light Green
            'error': '#FF6B6B',       # Red
            'safe': '#90EE90',        # Light Green
            'educational': '#87CEEB', # Sky Blue
            'concerning': '#FFA500',  # Orange
            'inappropriate': '#FF6B6B', # Red
            'allow': '#90EE90',       # Light Green
            'monitor': '#FFFF99',     # Yellow
            'restrict': '#FFA500',    # Orange
            'block': '#FF6B6B'        # Red
        }
    
    def create_window(self):
        """Create the debug window (must be called from main thread)"""
        self.root = tk.Tk()
        self.root.title("Parental Control Debug")
        self.root.geometry("500x600")
        
        # Make window semi-transparent
        self.root.attributes('-alpha', 0.85)
        
        # Always on top
        self.root.attributes('-topmost', True)
        
        # Position in top-right corner
        self.root.geometry("+{}+{}".format(
            self.root.winfo_screenwidth() - 520, 50
        ))
        
        # Dark theme
        self.root.configure(bg='#2b2b2b')
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🔍 Parental Control Debug", 
            font=('Arial', 14, 'bold'),
            bg='#2b2b2b', 
            fg='white'
        )
        title_label.pack(pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Status: Initializing...",
            font=('Arial', 10),
            bg='#2b2b2b',
            fg='#90EE90'
        )
        self.status_label.pack(pady=(0, 5))
        
        # Control buttons frame
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_entries,
            bg='#404040',
            fg='white',
            font=('Arial', 9)
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Hide button
        hide_btn = tk.Button(
            button_frame,
            text="Hide",
            command=self.toggle_visibility,
            bg='#404040',
            fg='white',
            font=('Arial', 9)
        )
        hide_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.close_window,
            bg='#404040',
            fg='white',
            font=('Arial', 9)
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Scrolled text widget for debug output
        self.text_widget = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=60,
            height=25,
            bg='#1e1e1e',
            fg='white',
            font=('Courier', 9),
            insertbackground='white'
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colors
        for color_name, color_value in self.colors.items():
            self.text_widget.tag_configure(color_name, foreground=color_value)
        
        # Start processing queue
        self.running = True
        self.process_queue()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Initial message
        self.add_initial_message()
    
    def add_initial_message(self):
        """Add initial instructions to the debug window"""
        initial_msg = """🔍 Debug Window Controls:
   - Clear: Clear all debug entries
   - Hide: Hide/show the debug window
   - Close: Close the debug window

📊 Debug Window Information:
   - Yellow text: Current input being typed
   - Gray status: Incomplete input (waiting for more)
   - Orange status: Processing input
   - Green status: Complete analysis
   - Red status: Error occurred

🎯 Categories:
   - Green: Safe content
   - Blue: Educational content
   - Orange: Concerning content
   - Red: Blocked content

⚡ Actions:
   - Green: Allow
   - Yellow: Monitor
   - Orange: Restrict
   - Red: Block

========================================
"""
        self.text_widget.insert(tk.END, initial_msg)
        self.text_widget.see(tk.END)
    
    def log_debug_entry(self, input_text: str, status: str, category: str = "unknown", 
                       action: str = "unknown", confidence: float = 0.0, error: str = None):
        """Thread-safe method to log debug entries"""
        entry = {
            'timestamp': datetime.now(),
            'input_text': input_text,
            'status': status,
            'category': category,
            'action': action,
            'confidence': confidence,
            'error': error
        }
        
        try:
            self.debug_queue.put(entry, timeout=1)
        except queue.Full:
            pass  # Skip if queue is full
    
    def process_queue(self):
        """Process debug entries from queue (runs in main thread)"""
        if not self.running:
            return
        
        try:
            while True:
                entry = self.debug_queue.get_nowait()
                self.add_debug_entry(entry)
        except queue.Empty:
            pass
        
        # Schedule next processing
        if self.root:
            self.root.after(100, self.process_queue)
    
    def add_debug_entry(self, entry: Dict[str, Any]):
        """Add a debug entry to the display"""
        if not self.text_widget:
            return
        
        # Add to entries list
        self.entries.append(entry)
        
        # Keep only last max_entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        # Clear and redraw all entries
        self.redraw_entries()
    
    def redraw_entries(self):
        """Redraw all debug entries"""
        if not self.text_widget:
            return
        
        # Clear current content (except initial message)
        content = self.text_widget.get(1.0, tk.END)
        separator_pos = content.find("========================================")
        if separator_pos != -1:
            # Keep initial message
            initial_content = content[:separator_pos + 40]
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, initial_content)
        else:
            # Clear everything if separator not found
            self.text_widget.delete(1.0, tk.END)
            self.add_initial_message()
        
        # Add all entries
        for entry in self.entries:
            self.format_and_insert_entry(entry)
        
        # Scroll to bottom
        self.text_widget.see(tk.END)
    
    def format_and_insert_entry(self, entry: Dict[str, Any]):
        """Format and insert a single entry"""
        timestamp = entry['timestamp'].strftime("%H:%M:%S")
        input_text = entry['input_text'][:50] + "..." if len(entry['input_text']) > 50 else entry['input_text']
        
        # Insert timestamp
        self.text_widget.insert(tk.END, f"\n[{timestamp}] ")
        
        # Insert input text with color
        self.text_widget.insert(tk.END, f'Input: "{input_text}"\n', 'input')
        
        # Insert status with color
        status_color = self.colors.get(entry['status'], 'white')
        self.text_widget.insert(tk.END, f"Status: {entry['status']}\n", entry['status'])
        
        # Insert category and action if available
        if entry['category'] != "unknown":
            self.text_widget.insert(tk.END, f"Category: {entry['category']}\n", entry['category'])
        
        if entry['action'] != "unknown":
            self.text_widget.insert(tk.END, f"Action: {entry['action']}\n", entry['action'])
        
        # Insert confidence if available
        if entry['confidence'] > 0:
            self.text_widget.insert(tk.END, f"Confidence: {entry['confidence']:.2f}\n")
        
        # Insert error if available
        if entry['error']:
            self.text_widget.insert(tk.END, f"Error: {entry['error']}\n", 'error')
        
        self.text_widget.insert(tk.END, "\n")
    
    def clear_entries(self):
        """Clear all debug entries"""
        self.entries = []
        if self.text_widget:
            self.text_widget.delete(1.0, tk.END)
            self.add_initial_message()
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.root:
            if self.root.winfo_viewable():
                self.root.withdraw()
            else:
                self.root.deiconify()
    
    def close_window(self):
        """Close the debug window"""
        self.running = False
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def update_status(self, status: str):
        """Update the status label"""
        if self.status_label:
            self.status_label.config(text=f"Status: {status}")
    
    def run(self):
        """Run the debug window (must be called from main thread)"""
        self.create_window()
        self.root.mainloop()

# Global debug window instance
_debug_window = None

def get_debug_window() -> Optional[DebugWindow]:
    """Get the global debug window instance"""
    global _debug_window
    return _debug_window

def create_debug_window() -> DebugWindow:
    """Create and return a new debug window instance"""
    global _debug_window
    _debug_window = DebugWindow()
    return _debug_window

if __name__ == "__main__":
    # Test the debug window
    debug_window = create_debug_window()
    
    # Add some test entries
    debug_window.log_debug_entry("Hello world", "complete", "safe", "allow", 0.95)
    debug_window.log_debug_entry("I w", "incomplete", "unknown", "unknown", 0.0)
    debug_window.log_debug_entry("Test input", "processing", "unknown", "unknown", 0.0)
    
    # Run the window
    debug_window.run() 