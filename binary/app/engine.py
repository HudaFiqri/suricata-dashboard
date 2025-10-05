"""
Application Engine - Core initialization and setup
"""
import os
from binary import SuricataFrontendController, SuricataRRDManager, DatabaseManager, IntegrationManager
from binary.api import MonitorAPI, AlertsAPI, DatabaseAPI, APIRoutes


def _is_reloader_process():
    """Check if running in Flask reloader child process"""
    return os.environ.get('WERKZEUG_RUN_MAIN') == 'true'


class AppEngine:
    """Core application engine for Suricata Dashboard"""

    def __init__(self, config):
        self.config = config
        self.controller = None
        self.rrd_manager = None
        self.db_manager = None
        self.integration_manager = None
        self.monitor_api = None
        self.alerts_api = None
        self.database_api = None
        self.api_routes = None

        self._init_directories()
        self._init_components()
        self._init_apis()

    def _init_directories(self):
        """Ensure application directories exist"""
        try:
            os.makedirs(self.config.APP_DATA_DIR, exist_ok=True)
            os.makedirs(self.config.APP_LOG_DIR, exist_ok=True)
            if not _is_reloader_process():
                print(f"[APP] Directories initialized: data={self.config.APP_DATA_DIR}, logs={self.config.APP_LOG_DIR}")
        except Exception as e:
            if not _is_reloader_process():
                print(f"[APP] Warning: Could not create directories: {e}")

    def _init_components(self):
        """Initialize core components"""
        # Suricata Frontend Controller
        self.controller = SuricataFrontendController(
            binary_path=self.config.SURICATA_BINARY_PATH,
            config_path=self.config.SURICATA_CONFIG_PATH,
            rules_directory=self.config.SURICATA_RULES_DIR,
            log_directory=self.config.SURICATA_LOG_DIR
        )

        # Database Manager
        db_config = self._get_db_config()
        self.db_manager = DatabaseManager(
            db_type=self.config.DB_TYPE,
            db_config=db_config
        )

        # Integration manager
        self.integration_manager = IntegrationManager(self.config.APP_DATA_DIR, db_manager=self.db_manager)

        # RRD Manager (with database integration)
        self.rrd_manager = SuricataRRDManager(
            rrd_directory=self.config.RRD_DIR,
            log_directory=self.config.SURICATA_LOG_DIR,
            db_manager=self.db_manager
        )

    def _get_db_config(self):
        """Get database configuration"""
        if self.config.DB_TYPE == 'mysql':
            return {
                'host': self.config.DB_HOST,
                'port': self.config.DB_PORT,
                'user': self.config.DB_USER,
                'password': self.config.DB_PASSWORD,
                'database': self.config.DB_NAME,
            }
        elif self.config.DB_TYPE == 'postgresql':
            return {
                'host': self.config.DB_HOST,
                'port': self.config.DB_PORT,
                'user': self.config.DB_USER,
                'password': self.config.DB_PASSWORD,
                'database': self.config.DB_NAME,
            }
        else:
            raise ValueError(f"Unsupported database type: {self.config.DB_TYPE}")

    def _init_apis(self):
        """Initialize API modules"""
        self.monitor_api = MonitorAPI(self.config)
        self.alerts_api = AlertsAPI(self.config)
        self.database_api = DatabaseAPI(self.db_manager)

    def register_routes(self, app):
        """Register API routes to Flask app"""
        self.api_routes = APIRoutes(
            app,
            self.controller,
            self.rrd_manager,
            self.monitor_api,
            self.alerts_api,
            self.database_api,
            self.integration_manager
        )
        return self.api_routes

