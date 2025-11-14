"""
Agent Configuration Loader
Loads and validates agent configuration from YAML file
"""

import yaml
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'agent': {
        'name': None,  # Will use hostname if not provided
        'token': None,  # Required
        'tags': []
    },
    'dashboard': {
        'url': 'http://localhost:5000',
        'api_version': 'v1',
        'verify_ssl': True,
        'connection': {
            'transport': 'websocket',  # websocket or http
            'websocket_url': None,  # Auto-generated if not provided
            'fallback_to_http': True,
            'reconnect_interval': 5,
            'max_reconnect_delay': 300
        },
        'heartbeat_interval': 30
    },
    'suricata': {
        'eve_log': '/var/log/suricata/eve.json',
        'suricata_log': '/var/log/suricata/suricata.log',
        'fast_log': '/var/log/suricata/fast.log',
        'config_file': '/etc/suricata/suricata.yaml',
        'pid_file': '/var/run/suricata.pid',
        'control_socket': '/var/run/suricata/suricata-command.socket'
    },
    'streaming': {
        'batch_size': 100,
        'batch_timeout': 5,
        'compression': True
    },
    'buffer': {
        'database': '/var/lib/suricata-agent/buffer.db',
        'max_events': 100000,
        'max_size_mb': 500
    },
    'logging': {
        'level': 'INFO',
        'file': '/var/log/suricata-agent/agent.log',
        'max_size_mb': 100,
        'backup_count': 5
    }
}

class Config:
    """Agent configuration manager"""

    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()

        if config_path:
            self.load_from_file(config_path)

        self.validate()

    def load_from_file(self, path):
        """Load configuration from YAML file"""
        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f)

            # Deep merge with defaults
            self._merge_config(self.config, user_config)

            logger.info(f"Configuration loaded from {path}")

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            sys.exit(1)

    def _merge_config(self, base, override):
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base:
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def validate(self):
        """Validate configuration"""
        errors = []

        # Required fields
        if not self.config['agent'].get('token'):
            errors.append("agent.token is required")

        if not self.config['dashboard'].get('url'):
            errors.append("dashboard.url is required")

        # Auto-generate websocket URL if not provided
        if not self.config['dashboard']['connection'].get('websocket_url'):
            dashboard_url = self.config['dashboard']['url']
            ws_url = dashboard_url.replace('https://', 'wss://').replace('http://', 'ws://')
            self.config['dashboard']['connection']['websocket_url'] = f"{ws_url}/ws/v1/agent"

        # Auto-generate agent name if not provided
        if not self.config['agent'].get('name'):
            import socket
            self.config['agent']['name'] = socket.gethostname()

        # Check file paths exist
        eve_log = self.config['suricata']['eve_log']
        if not os.path.exists(eve_log):
            logger.warning(f"eve.json not found at {eve_log}")

        # Create buffer directory if it doesn't exist
        buffer_db = self.config['buffer']['database']
        buffer_dir = os.path.dirname(buffer_db)
        if buffer_dir and not os.path.exists(buffer_dir):
            try:
                os.makedirs(buffer_dir, mode=0o755)
                logger.info(f"Created buffer directory: {buffer_dir}")
            except OSError as e:
                errors.append(f"Cannot create buffer directory {buffer_dir}: {e}")

        # Create log directory if it doesn't exist
        log_file = self.config['logging']['file']
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, mode=0o755)
                logger.info(f"Created log directory: {log_dir}")
            except OSError as e:
                errors.append(f"Cannot create log directory {log_dir}: {e}")

        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            sys.exit(1)

        logger.info("Configuration validated successfully")

    def get(self, key_path, default=None):
        """Get configuration value by dot-separated path"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key_path, value):
        """Set configuration value by dot-separated path"""
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def to_dict(self):
        """Get full configuration as dictionary"""
        return self.config.copy()

    def save(self, path=None):
        """Save configuration to file"""
        save_path = path or self.config_path

        if not save_path:
            raise ValueError("No config path specified")

        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)

        logger.info(f"Configuration saved to {save_path}")
