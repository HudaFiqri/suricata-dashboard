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
from crypto import AgentCrypto

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

    def _validate_and_fix_encryption_key(self):
        """
        Validate encryption key and auto-fix if invalid
        Returns True if key is valid or was fixed, False otherwise
        """
        encryption_key = self.config.encryption_key

        # Check if encryption key exists and is valid
        if encryption_key and AgentCrypto.is_valid_fernet_key(encryption_key):
            logger.info("Encryption key validated successfully")
            return True

        if not encryption_key:
            logger.warning("Encryption key is missing from config!")
        else:
            logger.warning("Invalid encryption key format detected!")

        logger.info("Attempting to fetch valid encryption key from dashboard...")

        try:
            # Try to fetch the correct encryption key from dashboard
            import requests
            import yaml

            # Make API call to get agent info (which includes encryption_key)
            response = requests.get(
                f"{self.config.dashboard_url}/api/v1/agents/self",
                headers={'Authorization': f'Bearer {self.config.token}'},
                verify=self.config.verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                agent_data = response.json()
                new_encryption_key = agent_data.get('encryption_key')

                if new_encryption_key and AgentCrypto.is_valid_fernet_key(new_encryption_key):
                    logger.info("Valid encryption key fetched from dashboard")

                    # Update config in memory
                    self.config.encryption_key = new_encryption_key

                    # Update config file
                    logger.info(f"Updating config file: {self.config.config_path}")
                    with open(self.config.config_path, 'r') as f:
                        config_data = yaml.safe_load(f)

                    config_data['agent']['encryption_key'] = new_encryption_key

                    with open(self.config.config_path, 'w') as f:
                        yaml.dump(config_data, f, default_flow_style=False, indent=2)

                    logger.info("Encryption key auto-fixed successfully!")
                    return True
                else:
                    logger.error("Fetched encryption key is also invalid")
                    return False
            else:
                logger.error(f"Failed to fetch encryption key from dashboard: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to auto-fix encryption key: {e}")
            logger.error("Please contact your dashboard administrator to get the correct encryption key")
            return False

    def start(self):
        """Start the agent"""
        logger.info("=" * 60)
        logger.info(f"Suricata Dashboard Agent v{__version__}")
        logger.info("=" * 60)
        logger.info(f"Agent Name: {self.config.agent_name}")
        logger.info(f"Dashboard URL: {self.config.dashboard_url}")
        logger.info(f"Eve Log: {self.config.eve_log_path}")
        logger.info("=" * 60)

        # Validate and auto-fix encryption key if needed
        if not self._validate_and_fix_encryption_key():
            logger.error("Cannot start agent with invalid encryption key. Exiting.")
            return False

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
