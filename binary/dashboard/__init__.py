"""
Suricata Dashboard Application
Flask app initialization and configuration
"""

from flask import Flask
from flask_cors import CORS
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduce werkzeug logging noise
logging.getLogger('werkzeug').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def create_app(config=None):
    """Create and configure Flask application"""

    app = Flask(__name__)

    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        # Load from environment
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

        # PostgreSQL
        app.config['POSTGRESQL_HOST'] = os.getenv('POSTGRESQL_HOST', 'localhost')
        app.config['POSTGRESQL_PORT'] = int(os.getenv('POSTGRESQL_PORT', 5432))
        app.config['POSTGRESQL_DB'] = os.getenv('POSTGRESQL_DB', 'suricata_dashboard')
        app.config['POSTGRESQL_USER'] = os.getenv('POSTGRESQL_USER', 'suricata')
        app.config['POSTGRESQL_PASSWORD'] = os.getenv('POSTGRESQL_PASSWORD', 'suricata123')

        # MongoDB
        app.config['MONGODB_HOST'] = os.getenv('MONGODB_HOST', 'localhost')
        app.config['MONGODB_PORT'] = int(os.getenv('MONGODB_PORT', 27017))
        app.config['MONGODB_DB'] = os.getenv('MONGODB_DB', 'suricata_events')
        app.config['MONGODB_USER'] = os.getenv('MONGODB_USER', '')
        app.config['MONGODB_PASSWORD'] = os.getenv('MONGODB_PASSWORD', '')

        # JWT
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
        app.config['JWT_EXPIRATION_HOURS'] = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database connections with auto-detection
    logger.info("Initializing database connections...")
    from binary.dashboard.database import init_postgresql, init_mongodb

    db_initialized = False
    pg_available = False
    mongo_available = False

    # Try PostgreSQL first
    pg_engine, pg_session = init_postgresql(app, raise_on_error=False)
    if pg_engine is not None and pg_session is not None:
        logger.info("✓ PostgreSQL connection initialized")
        pg_available = True
        db_initialized = True
    else:
        logger.warning("⚠ PostgreSQL not available - some features will be limited")

    # Try MongoDB
    mongo_client, mongo_db = init_mongodb(app, raise_on_error=False)
    if mongo_client is not None and mongo_db is not None:
        logger.info("✓ MongoDB connection initialized")
        mongo_available = True
        db_initialized = True
    else:
        logger.warning("⚠ MongoDB not available - some features will be limited")

    # Show status summary
    if not db_initialized:
        logger.warning("=" * 60)
        logger.warning("⚠ WARNING: No database connections available!")
        logger.warning("=" * 60)
        logger.warning("Application will run with LIMITED functionality:")
        logger.warning("  ✓ Real-time monitoring (from log files)")
        logger.warning("  ✗ Alert history (requires PostgreSQL)")
        logger.warning("  ✗ Traffic statistics (requires PostgreSQL)")
        logger.warning("  ✗ Time-series events (requires MongoDB)")
        logger.warning("")
        logger.warning("To enable database features:")
        logger.warning("  1. Install PostgreSQL and/or MongoDB")
        logger.warning("  2. Update credentials in .env file")
        logger.warning("  3. Restart the application")
        logger.warning("=" * 60)
    else:
        logger.info("Database status:")
        logger.info(f"  PostgreSQL: {'✓ Connected' if pg_available else '✗ Not available'}")
        logger.info(f"  MongoDB:    {'✓ Connected' if mongo_available else '✗ Not available'}")

    # Store database status in app config
    app.config['DB_POSTGRESQL_AVAILABLE'] = pg_available
    app.config['DB_MONGODB_AVAILABLE'] = mongo_available

    # Initialize WebSocket
    logger.info("Initializing WebSocket server...")
    from binary.dashboard.websocket import init_socketio
    socketio = init_socketio(app)
    logger.info("✓ WebSocket server initialized")

    # Register API blueprints
    logger.info("Registering API blueprints...")
    from binary.dashboard.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    logger.info("✓ API blueprints registered")

    # Register web UI blueprints (if exists)
    try:
        from binary.dashboard.web import web as web_blueprint
        app.register_blueprint(web_blueprint)
        logger.info("✓ Web UI blueprints registered")
    except ImportError:
        logger.warning("⚠ Web UI blueprints not found - API only mode")

    # Create database tables if needed
    with app.app_context():
        from binary.dashboard.database import create_tables
        create_tables()
        logger.info("✓ Database tables verified")

    logger.info("=" * 60)
    logger.info("Suricata Dashboard initialized successfully")
    logger.info("=" * 60)

    # Store socketio instance in app for access
    app.socketio = socketio

    return app, socketio

__all__ = ['create_app']
