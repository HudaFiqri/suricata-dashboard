#!/usr/bin/env python3
"""
Suricata Dashboard Agent
Main entry point for the agent daemon
"""

import sys
import os
import argparse
import signal
import logging
import time
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from heartbeat import HeartbeatManager
from watcher import EventWatcher
from api_client import DashboardClient

# Version
__version__ = "1.0.0"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SuricataAgent:
    """Main agent class"""

    def __init__(self, config_path):
        """Initialize agent"""
        self.config = Config(config_path)
        self.running = False
        self.client = None
        self.heartbeat_manager = None
        self.event_watcher = None

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """Start the agent"""
        logger.info("=" * 60)
        logger.info(f"Suricata Dashboard Agent v{__version__}")
        logger.info("=" * 60)
        logger.info(f"Agent Name: {self.config.agent_name}")
        logger.info(f"Dashboard URL: {self.config.dashboard_url}")
        logger.info(f"Eve Log: {self.config.eve_log_path}")
        logger.info("=" * 60)

        # Initialize dashboard client
        logger.info("Initializing dashboard client...")
        self.client = DashboardClient(
            dashboard_url=self.config.dashboard_url,
            token=self.config.token,
            encryption_key=self.config.encryption_key,
            verify_ssl=self.config.verify_ssl
        )

        # Test connection
        if not self.client.test_connection():
            logger.error("Failed to connect to dashboard. Exiting.")
            return False

        logger.info("Successfully connected to dashboard")

        # Start heartbeat manager
        logger.info("Starting heartbeat manager...")
        self.heartbeat_manager = HeartbeatManager(
            client=self.client,
            agent_name=self.config.agent_name,
            interval=self.config.heartbeat_interval
        )
        self.heartbeat_manager.start()

        # Start event watcher
        logger.info("Starting event watcher...")
        self.event_watcher = EventWatcher(
            client=self.client,
            eve_log_path=self.config.eve_log_path,
            batch_size=self.config.batch_size,
            batch_timeout=self.config.batch_timeout
        )
        self.event_watcher.start()

        logger.info("Agent started successfully")
        self.running = True

        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the agent"""
        if not self.running:
            return

        logger.info("Stopping agent...")
        self.running = False

        # Stop components
        if self.event_watcher:
            self.event_watcher.stop()

        if self.heartbeat_manager:
            self.heartbeat_manager.stop()

        logger.info("Agent stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Suricata Dashboard Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--config', '-c',
        default='/etc/suricata-agent/config.yaml',
        help='Path to configuration file (default: /etc/suricata-agent/config.yaml)'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'Suricata Dashboard Agent v{__version__}'
    )

    args = parser.parse_args()

    # Check config file exists
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)

    # Create and start agent
    agent = SuricataAgent(args.config)
    success = agent.start()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
