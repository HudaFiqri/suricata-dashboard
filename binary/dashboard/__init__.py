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

    # Initialize database connections
    logger.info("Initializing database connections...")
    from binary.dashboard.database import init_postgresql, init_mongodb

    try:
        init_postgresql(app)
        logger.info("✓ PostgreSQL connection initialized")
    except Exception as e:
        logger.error(f"✗ PostgreSQL initialization failed: {e}")
        raise

    try:
        init_mongodb(app)
        logger.info("✓ MongoDB connection initialized")
    except Exception as e:
        logger.error(f"✗ MongoDB initialization failed: {e}")
        raise

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
