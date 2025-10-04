import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Suricata paths
    SURICATA_BINARY_PATH = os.getenv('SURICATA_BINARY_PATH', 'suricata')
    SURICATA_CONFIG_PATH = os.getenv('SURICATA_CONFIG_PATH', '/etc/suricata/suricata.yaml')
    SURICATA_RULES_DIR = os.getenv('SURICATA_RULES_DIR', '/etc/suricata/rules')
    SURICATA_LOG_DIR = os.getenv('SURICATA_LOG_DIR', '/var/log/suricata')

    # RRD settings
    RRD_DIR = os.getenv('RRD_DIR', '/var/lib/suricata/rrd')

    # Database settings
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # sqlite, mysql, postgresql
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))  # MySQL default
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'suricata')
    DB_PATH = os.getenv('DB_PATH', 'suricata.db')  # For SQLite

    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Dashboard settings
    AUTO_REFRESH_INTERVAL = int(os.getenv('AUTO_REFRESH_INTERVAL', 5000))
    LOG_LINES_LIMIT = int(os.getenv('LOG_LINES_LIMIT', 100))
    MAX_RULE_FILE_SIZE = int(os.getenv('MAX_RULE_FILE_SIZE', 1048576))
    
    @classmethod
    def get_platform_defaults(cls):
        if os.name == 'nt':  # Windows
            return {
                'binary_path': 'C:\\Program Files\\Suricata\\suricata.exe',
                'config_path': 'C:\\Program Files\\Suricata\\suricata.yaml',
                'rules_dir': 'C:\\Program Files\\Suricata\\rules',
                'log_dir': 'C:\\Program Files\\Suricata\\log'
            }
        else:  # Linux/Unix
            return {
                'binary_path': 'suricata',
                'config_path': '/etc/suricata/suricata.yaml',
                'rules_dir': '/etc/suricata/rules',
                'log_dir': '/var/log/suricata'
            }