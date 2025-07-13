#!/usr/bin/env python3
"""
Continuous Parental Control Monitoring Script

This script runs the MonitoringAgent continuously to monitor keyboard input
and screen activity for parental control purposes.

Usage:
    python src/continuous_monitoring.py

Features:
- Real-time keyboard monitoring
- Screen capture integration
- Content analysis and judgment
- Notification system
- Session management
- Performance monitoring
"""

import asyncio
import signal
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from monitoring_agent import MonitoringAgent, MonitoringConfig
from session_manager import SessionManager
from analysis_agent import AnalysisAgent
from judgment_engine import JudgmentEngine
from notification_agent import NotificationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContinuousMonitor:
    """Continuous monitoring coordinator"""
    
    def __init__(self):
        self.running = False
        self.agent = None
        self.session_id = None
        
    async def start(self):
        """Start continuous monitoring"""
        try:
            print("🚀 Starting Continuous Parental Control Monitoring")
            print("=" * 60)
            
            # Configuration
            config = MonitoringConfig(
                age_group="elementary",
                strictness_level="moderate",
                enable_notifications=True,
                screenshot_on_input=True,
                cache_enabled=False  # Disable cache for fresh results
            )
            
            print("⚙️  Configuration:")
            print(f"   Age Group: {config.age_group}")
            print(f"   Strictness: {config.strictness_level}")
            print(f"   Notifications: {'Enabled' if config.enable_notifications else 'Disabled'}")
            print(f"   Screenshots: {'Enabled' if config.screenshot_on_input else 'Disabled'}")
            print(f"   Cache: {'Disabled' if not config.cache_enabled else 'Enabled'}")
            print("=" * 60)
            
            # Create monitoring agent with configuration
            self.agent = MonitoringAgent(config=config)
            
            # Start monitoring
            start_result = await self.agent.start_monitoring()
            if start_result.get('status') != 'success':
                print(f"❌ Failed to start monitoring: {start_result.get('error', 'Unknown error')}")
                return
            
            self.session_id = start_result.get('session_id')
            
            print("✅ Monitoring started successfully!")
            print(f"📊 Session ID: {self.session_id}")
            print(f"🕐 Started at: {datetime.now().isoformat()}")
            print()
            print("🔍 Monitoring keyboard input... (Press Ctrl+C to stop)")
            print("=" * 60)
            
            self.running = True
            
            # Status update loop
            while self.running:
                await asyncio.sleep(30)  # Status update every 30 seconds
                if self.running:
                    await self._print_status()
                    
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            await self.stop()
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop continuous monitoring"""
        self.running = False
        if self.agent:
            await self.agent.stop_monitoring()
            
            # Print final statistics
            stats = self.agent.get_monitoring_status()
            print("\n📈 Final Statistics:")
            print(f"   Total Events: {stats.get('total_events', 0)}")
            print(f"   Inputs Processed: {stats.get('inputs_processed', 0)}")
            print(f"   Notifications Sent: {stats.get('notifications_sent', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
            print(f"   Session Duration: {stats.get('uptime', 'Unknown')}")
            
        print("👋 Monitoring stopped successfully!")
    
    async def _print_status(self):
        """Print current status"""
        if not self.agent:
            return
            
        try:
            stats = self.agent.get_monitoring_status()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n📊 Status Update [{current_time}]:")
            print(f"   Status: {stats.get('status', 'unknown')}")
            print(f"   Events: {stats.get('total_events', 0)}")
            print(f"   Inputs: {stats.get('inputs_processed', 0)}")
            print(f"   Errors: {stats.get('errors', 0)}")
            print(f"   Avg Time: {stats.get('avg_processing_time', 0):.3f}s")
            
            # Show recent events
            recent_events = stats.get('recent_events', [])
            if recent_events:
                print("   Recent Events:")
                for event in recent_events[-3:]:  # Show last 3 events
                    input_preview = event.get('input_preview', '...')
                    category = event.get('category', 'unknown')
                    action = event.get('action', 'unknown')
                    print(f"     • {input_preview} → {category} → {action}")
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start monitor
    monitor = ContinuousMonitor()
    await monitor.start()

if __name__ == "__main__":
    asyncio.run(main()) 