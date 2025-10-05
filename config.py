import os
from dotenv import load_dotenv

load_dotenv()


def _get_env_raw(*keys):
    for key in keys:
        value = os.getenv(key)
        if value is not None:
            return value
    return None


def _get_env(*keys, default=None):
    for key in keys:
        value = os.getenv(key)
        if value is not None and value != '':
            return value
    return default


def _normalize_db_type(value):
    if not value:
        return None

    normalized = value.strip().lower()
    mapping = {
        'postgres': 'postgresql',
        'postgresql': 'postgresql',
        'psql': 'postgresql',
        'mysql': 'mysql',
        'mariadb': 'mysql'
    }
    return mapping.get(normalized, normalized)


def _infer_db_type(port_value, user_value):
    port = None
    if port_value is not None:
        try:
            port = int(port_value)
        except ValueError:
            port = None

    if port in (5432, 6432):
        return 'postgresql'
    if port in (3306, 33060, 3307):
        return 'mysql'

    if user_value:
        lowered_user = user_value.strip().lower()
        if lowered_user == 'postgres':
            return 'postgresql'
        if lowered_user in ('root', 'mysql'):
            return 'mysql'

    return None


class Config:
    # Dashboard settings
    DASHBOARD_NAME = _get_env('SURICATA_DASHBOARD_NAME', default='Suricata Dashboard')
    TRAFFIC_AGGREGATION_INTERVAL = int(_get_env('TRAFFIC_AGGREGATION_INTERVAL', default='300'))  # 5 minutes
    DB_STORE_TIME = int(_get_env('DB_STORE_TIME', default='60'))  # Database store interval in seconds

    # Suricata paths
    SURICATA_BINARY_PATH = _get_env('SURICATA_BINARY_PATH', default='suricata')
    SURICATA_CONFIG_PATH = _get_env('SURICATA_CONFIG_PATH', default='/etc/suricata/suricata.yaml')
    SURICATA_RULES_DIR = _get_env('SURICATA_RULES_DIR', default='/etc/suricata/rules')
    SURICATA_LOG_DIR = _get_env('SURICATA_LOG_DIR', default='/var/log/suricata')

    # RRD settings
    RRD_DIR = _get_env('RRD_DIR', default='/var/lib/suricata/rrd')

    # Database settings
    _db_host_env = _get_env('DB_HOST', 'DATABASE_HOST')
    _db_port_env = _get_env('DB_PORT', 'DATABASE_PORT')
    _db_user_env = _get_env('DB_USER', 'DATABASE_USERNAME')

    _raw_db_type_env = _get_env_raw('DB_TYPE', 'DATABASE_TYPE')
    DB_TYPE = _normalize_db_type(_raw_db_type_env) or _infer_db_type(_db_port_env, _db_user_env) or 'postgresql'

    _supported_defaults = {
        'postgresql': {'port': '5432', 'user': 'postgres'},
        'mysql': {'port': '3306', 'user': 'root'}
    }

    if DB_TYPE not in _supported_defaults:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

    defaults_for_type = _supported_defaults[DB_TYPE]

    DB_HOST = _db_host_env or 'localhost'
    DB_PORT = int(_db_port_env or defaults_for_type['port'])
    DB_USER = _db_user_env or defaults_for_type['user']
    DB_PASSWORD = _get_env('DB_PASSWORD', 'DATABASE_PASSWORD', default='')
    DB_NAME = _get_env('DB_NAME', 'DATABASE_NAME', default='suricata')

    _retention_raw = _get_env('DB_RETENTION_DAYS', default='30')
    try:
        DB_RETENTION_DAYS = max(int(_retention_raw), 0)
    except ValueError:
        DB_RETENTION_DAYS = 30

    # Application storage paths
    APP_DATA_DIR = _get_env('APP_DATA_DIR', default='/opt/suricata_monitoring/data')
    APP_LOG_DIR = _get_env('APP_LOG_DIR', default='/opt/suricata_monitoring/log')

    # Flask settings
    FLASK_HOST = _get_env('FLASK_HOST', default='0.0.0.0')
    FLASK_PORT = int(_get_env('FLASK_PORT', default='5000'))
    FLASK_DEBUG = _get_env('FLASK_DEBUG', default='True').strip().lower() == 'true'

    # Dashboard settings
    AUTO_REFRESH_INTERVAL = int(_get_env('AUTO_REFRESH_INTERVAL', default='5000'))
    LOG_LINES_LIMIT = int(_get_env('LOG_LINES_LIMIT', default='100'))
    MAX_RULE_FILE_SIZE = int(_get_env('MAX_RULE_FILE_SIZE', default='1048576'))

    # Auto-restart settings
    AUTO_RESTART_ENABLED = _get_env('AUTO_RESTART_ENABLED', default='False').strip().lower() == 'true'
    AUTO_RESTART_MAX_RETRIES = int(_get_env('AUTO_RESTART_MAX_RETRIES', default='3'))
    AUTO_RESTART_CHECK_INTERVAL = int(_get_env('AUTO_RESTART_CHECK_INTERVAL', default='30'))  # seconds

    # SSL/TLS settings
    USE_HTTPS = _get_env('USE_HTTPS', default='False').strip().lower() == 'true'
    SSL_CERT_PATH = _get_env('SSL_CERT_PATH', default='binary/certificates/cert.pem')
    SSL_KEY_PATH = _get_env('SSL_KEY_PATH', default='binary/certificates/key.pem')

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

