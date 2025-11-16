"""
Application Engine - Core initialization and setup
"""
import os
from binary import SuricataFrontendController, SuricataRRDManager, DatabaseManager, IntegrationManager
from binary.api.routes import APIRoutes


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
        self.api_routes = None

        self._init_directories()
        self._init_components()

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

        # Database Manager with auto-detection
        self.db_manager = self._init_database_with_fallback()

        # Integration manager
        self.integration_manager = IntegrationManager(self.config.APP_DATA_DIR, db_manager=self.db_manager)

        # RRD Manager (with database integration)
        self.rrd_manager = SuricataRRDManager(
            rrd_directory=self.config.RRD_DIR,
            log_directory=self.config.SURICATA_LOG_DIR,
            db_manager=self.db_manager
        )

    def _get_db_config(self, db_type=None):
        """Get database configuration for specified type"""
        db_type = db_type or self.config.DB_TYPE

        if db_type == 'mysql':
            return {
                'host': self.config.DB_HOST,
                'port': self.config.DB_PORT,
                'user': self.config.DB_USER,
                'password': self.config.DB_PASSWORD,
                'database': self.config.DB_NAME,
            }
        elif db_type == 'postgresql':
            return {
                'host': self.config.DB_HOST,
                'port': self.config.DB_PORT,
                'user': self.config.DB_USER,
                'password': self.config.DB_PASSWORD,
                'database': self.config.DB_NAME,
            }
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _init_database_with_fallback(self):
        """Initialize database with auto-detection and fallback"""
        import os

        # Get available database configs from environment
        databases_to_try = []

        # Primary database from config
        databases_to_try.append({
            'type': self.config.DB_TYPE,
            'config': self._get_db_config(self.config.DB_TYPE)
        })

        # Check for alternate PostgreSQL config
        if os.getenv('POSTGRES_HOST') and self.config.DB_TYPE != 'postgresql':
            try:
                databases_to_try.append({
                    'type': 'postgresql',
                    'config': {
                        'host': os.getenv('POSTGRES_HOST', 'localhost'),
                        'port': int(os.getenv('POSTGRES_PORT', '5432')),
                        'user': os.getenv('POSTGRES_USER', 'postgres'),
                        'password': os.getenv('POSTGRES_PASSWORD', ''),
                        'database': os.getenv('POSTGRES_DB', 'suricata_dashboard'),
                    }
                })
            except Exception:
                pass

        # Try each database configuration
        for db_attempt in databases_to_try:
            if not _is_reloader_process():
                print(f"[DATABASE] Attempting connection to {db_attempt['type'].upper()}...")

            try:
                db_manager = DatabaseManager(
                    db_type=db_attempt['type'],
                    db_config=db_attempt['config'],
                    auto_detect=True
                )

                if not db_manager.connection_failed:
                    return db_manager

            except Exception as e:
                if not _is_reloader_process():
                    print(f"[DATABASE] Failed to connect to {db_attempt['type'].upper()}: {e}")
                continue

        # If all attempts failed, show helpful error
        if not _is_reloader_process():
            print("\n" + "="*60)
            print("[DATABASE] ⚠ WARNING: No database connection available!")
            print("="*60)
            print("Tried the following databases:")
            for db_attempt in databases_to_try:
                cfg = db_attempt['config']
                print(f"  - {db_attempt['type'].upper()}: {cfg.get('host')}:{cfg.get('port')}/{cfg.get('database')}")
            print("\nApplication will run with LIMITED functionality:")
            print("  ✓ Suricata monitoring (live stats from logs)")
            print("  ✗ Alert history (requires database)")
            print("  ✗ Traffic statistics (requires database)")
            print("\nTo enable full features, please:")
            print("  1. Install and start PostgreSQL or MySQL")
            print("  2. Update database credentials in .env file")
            print("="*60 + "\n")

        # Return the last attempted manager (with connection_failed flag set)
        # This allows the app to run but API calls will handle gracefully
        try:
            db_manager = DatabaseManager(
                db_type=databases_to_try[0]['type'],
                db_config=databases_to_try[0]['config'],
                auto_detect=True
            )
            return db_manager
        except Exception:
            return None

    def register_routes(self, app):
        """Register API routes to Flask app"""
        self.api_routes = APIRoutes(
            app,
            self.controller,
            self.rrd_manager,
            self.config,
            self.db_manager,
            self.integration_manager
        )
        return self.api_routes

