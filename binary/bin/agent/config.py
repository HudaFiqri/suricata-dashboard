"""
Configuration loader for Suricata Dashboard Agent
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)


class Config:
    """Agent configuration"""

    def __init__(self, config_path):
        """Load configuration from YAML file"""
        self.config_path = config_path
        self._load_config()

    def _load_config(self):
        """Load and parse configuration file"""
        logger.info(f"Loading configuration from {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

        # Agent settings
        agent_config = config.get('agent', {})
        self.agent_name = agent_config.get('name', os.uname().nodename)
        self.token = agent_config.get('token')
        self.tags = agent_config.get('tags', [])

        if not self.token:
            raise ValueError("Agent token not configured")

        # Dashboard settings
        dashboard_config = config.get('dashboard', {})
        self.dashboard_url = dashboard_config.get('url')
        self.api_version = dashboard_config.get('api_version', 'v1')
        self.verify_ssl = dashboard_config.get('verify_ssl', True)

        if not self.dashboard_url:
            raise ValueError("Dashboard URL not configured")

        # Construct API base URL
        self.api_base_url = f"{self.dashboard_url.rstrip('/')}/api/{self.api_version}"

        # Suricata settings
        suricata_config = config.get('suricata', {})
        self.eve_log_path = suricata_config.get('eve_log', '/var/log/suricata/eve.json')
        self.suricata_log_path = suricata_config.get('suricata_log', '/var/log/suricata/suricata.log')
        self.suricata_config_path = suricata_config.get('config_file', '/etc/suricata/suricata.yaml')

        # Buffer settings
        buffer_config = config.get('buffer', {})
        self.buffer_db_path = buffer_config.get('database', '/var/lib/suricata-agent/buffer.db')
        self.max_buffer_events = buffer_config.get('max_events', 100000)

        # Performance settings
        self.heartbeat_interval = agent_config.get('heartbeat_interval', 30)
        self.batch_size = config.get('batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 5)

        # Logging settings
        logging_config = config.get('logging', {})
        self.log_level = logging_config.get('level', 'INFO')
        self.log_file = logging_config.get('file', '/var/log/suricata-agent/agent.log')

        logger.info("Configuration loaded successfully")

    def reload(self):
        """Reload configuration from file"""
        logger.info("Reloading configuration")
        self._load_config()
