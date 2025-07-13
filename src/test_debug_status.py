#!/usr/bin/env python3
"""
Test script to verify debug window status updates work correctly
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from debug_window import create_debug_window

def test_status_updates():
    """Test status updates from background thread"""
    debug_window = create_debug_window()
    
    def update_status_thread():
        """Update status from background thread"""
        time.sleep(2)
        debug_window.update_status("Connecting...")
        
        time.sleep(2)
        debug_window.update_status("Monitoring Active")
        
        time.sleep(2)
        debug_window.log_debug_entry("Test input", "processing", "unknown", "unknown", 0.0)
        
        time.sleep(2)
        debug_window.log_debug_entry("Test input", "complete", "safe", "allow", 0.95)
        
        time.sleep(2)
        debug_window.update_status("Processing Complete")
    
    # Start background thread
    thread = threading.Thread(target=update_status_thread, daemon=True)
    thread.start()
    
    # Run debug window (this blocks)
    debug_window.run()

if __name__ == "__main__":
    test_status_updates() 