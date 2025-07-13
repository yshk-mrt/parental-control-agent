#!/usr/bin/env python3
"""
Continuous Monitoring with Debug Window

This script runs the parental control monitoring system with a real-time debug window
that shows analysis results and system status.
"""

import sys
import os
import threading
import asyncio
import time
import signal
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitoring_agent import MonitoringAgent, MonitoringConfig
from debug_window import create_debug_window, get_debug_window

class MonitoringWithDebug:
    """
    Wrapper class that runs monitoring agent with debug window
    """
    
    def __init__(self):
        self.monitoring_agent = None
        self.debug_window = None
        self.monitoring_thread = None
        self.running = False
        
    def setup_monitoring_agent(self):
        """Setup the monitoring agent with debug window integration"""
        
        # Create monitoring configuration
        config = MonitoringConfig(
            age_group="elementary",
            strictness_level="moderate",
            enable_notifications=True,
            screenshot_on_input=True,
            cache_enabled=True,
            monitoring_interval=1.0  # Check every second
        )
        
        # Create monitoring agent with debug window
        self.monitoring_agent = MonitoringAgent(config, debug_window=self.debug_window)
        
        print("✅ Monitoring agent configured")
    
    def monitoring_loop(self):
        """Run the monitoring loop in a separate thread"""
        async def async_monitoring_loop():
            try:
                print("🚀 Starting monitoring loop...")
                
                # Start monitoring
                result = await self.monitoring_agent.start_monitoring()
                print(f"✅ Monitoring started: {result}")
                
                # Update debug window status
                if self.debug_window:
                    self.debug_window.update_status("Monitoring Active")
                
                # Keep running until stopped
                while self.running:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                if self.debug_window:
                    self.debug_window.log_debug_entry("System Error", "error", error=str(e))
                    self.debug_window.update_status("Error")
            finally:
                print("🛑 Monitoring loop stopped")
        
        # Run the async loop
        asyncio.run(async_monitoring_loop())
    
    def start_monitoring_thread(self):
        """Start the monitoring in a background thread"""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("✅ Monitoring thread started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        print("🛑 Stopping monitoring system...")
        self.running = False
        
        if self.monitoring_agent:
            try:
                asyncio.run(self.monitoring_agent.stop_monitoring())
            except Exception as e:
                print(f"Error stopping monitoring agent: {e}")
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        print("✅ Monitoring system stopped")
    
    def run(self):
        """Run the complete system with debug window"""
        try:
            print("🔍 Debug Window Controls:")
            print("   - Clear: Clear all debug entries")
            print("   - Hide: Hide/show the debug window")
            print("   - Close: Close the debug window")
            
            print("\n📊 Debug Window Information:")
            print("   - Yellow text: Current input being typed")
            print("   - Gray status: Incomplete input (waiting for more)")
            print("   - Orange status: Processing input")
            print("   - Green status: Complete analysis")
            print("   - Red status: Error occurred")
            
            print("\n🎯 Categories:")
            print("   - Green: Safe content")
            print("   - Blue: Educational content")
            print("   - Orange: Concerning content")
            print("   - Red: Blocked content")
            
            print("\n⚡ Actions:")
            print("   - Green: Allow")
            print("   - Yellow: Monitor")
            print("   - Orange: Restrict")
            print("   - Red: Block")
            
            print("\n🚀 Starting Continuous Parental Control Monitoring with Debug Window")
            print("=" * 70)
            
            # Create debug window (must be done in main thread)
            print("🔍 Starting debug window...")
            self.debug_window = create_debug_window()
            
            # Setup monitoring agent
            self.setup_monitoring_agent()
            
            # Start monitoring in background thread
            self.start_monitoring_thread()
            
            # Run debug window in main thread (this blocks until window is closed)
            self.debug_window.run()
            
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        except Exception as e:
            print(f"❌ Error running system: {e}")
        finally:
            self.stop_monitoring()

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print(f"\n🛑 Received signal {signum}")
    sys.exit(0)

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run the monitoring system
    monitoring_system = MonitoringWithDebug()
    monitoring_system.run()

if __name__ == "__main__":
    main() 