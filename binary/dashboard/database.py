"""
Database Connection Manager
Handles PostgreSQL (SQLAlchemy) and MongoDB (PyMongo) connections
"""

import os
import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

# Suppress pymongo threading warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pymongo")

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Global connection objects
pg_engine = None
pg_session = None
mongo_client = None
mongo_db = None

def get_postgres_uri():
    """Build PostgreSQL connection URI from environment"""
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', '5432') or '5432')
    database = os.getenv('POSTGRES_DB', 'suricata_dashboard')
    user = os.getenv('POSTGRES_USER', 'suricata')
    password = os.getenv('POSTGRES_PASSWORD', 'password')

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_mongodb_uri():
    """Build MongoDB connection URI from environment"""
    host = os.getenv('MONGO_HOST', 'localhost')
    port = int(os.getenv('MONGO_PORT', '27017') or '27017')
    user = os.getenv('MONGO_USER', '')  # Default empty string
    password = os.getenv('MONGO_PASSWORD', '')  # Default empty string
    auth_source = os.getenv('MONGO_AUTH_SOURCE', 'admin')

    # Only use authentication if both user and password are provided
    if user and password:
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource={auth_source}"
    else:
        # No authentication (for development)
        return f"mongodb://{host}:{port}/"

def init_postgresql(app=None, raise_on_error=False):
    """Initialize PostgreSQL connection

    Args:
        app: Flask app instance
        raise_on_error: If True, raise exception on connection failure. If False, log warning and continue.

    Returns:
        Tuple of (engine, session) or (None, None) if connection fails
    """
    global pg_engine, pg_session

    # Skip if PostgreSQL host is not configured
    if not os.getenv('POSTGRES_HOST'):
        logger.warning("PostgreSQL not configured (POSTGRES_HOST not set)")
        return None, None

    uri = get_postgres_uri()

    try:
        # Create engine with connection pooling
        pg_engine = create_engine(
            uri,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False
        )

        # Create session factory
        session_factory = sessionmaker(bind=pg_engine)
        pg_session = scoped_session(session_factory)

        # Test connection
        with pg_engine.connect() as conn:
            conn.execute("SELECT 1")

        logger.info("✓ PostgreSQL connection established")

        # If Flask app provided, add teardown handler
        if app:
            @app.teardown_appcontext
            def shutdown_session(exception=None):
                if pg_session:
                    pg_session.remove()

        return pg_engine, pg_session

    except Exception as e:
        logger.error(f"✗ Failed to connect to PostgreSQL: {e}")
        pg_engine = None
        pg_session = None
        if raise_on_error:
            raise
        return None, None

def init_mongodb(app=None, raise_on_error=False):
    """Initialize MongoDB connection

    Args:
        app: Flask app instance
        raise_on_error: If True, raise exception on connection failure. If False, log warning and continue.

    Returns:
        Tuple of (client, db) or (None, None) if connection fails
    """
    global mongo_client, mongo_db

    uri = get_mongodb_uri()
    database_name = os.getenv('MONGO_DB', 'suricata')

    try:
        # Create MongoDB client
        mongo_client = MongoClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )

        # Test connection
        mongo_client.admin.command('ping')

        # Get database
        mongo_db = mongo_client[database_name]

        logger.info(f"✓ MongoDB connection established (database: {database_name})")

        # Don't close MongoDB connection on teardown
        # MongoDB client manages its own connection pool and should stay alive
        # Closing it on every request causes "Cannot use MongoClient after close" errors

        return mongo_client, mongo_db

    except (ConnectionFailure, Exception) as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        mongo_client = None
        mongo_db = None
        if raise_on_error:
            raise
        return None, None

def init_databases(app):
    """Initialize both PostgreSQL and MongoDB"""
    logger.info("Initializing databases...")

    # Initialize PostgreSQL
    init_postgresql(app)

    # Initialize MongoDB
    init_mongodb(app)

    logger.info("All databases initialized")

def get_pg_session():
    """Get PostgreSQL session"""
    if pg_session is None:
        logger.warning("PostgreSQL not available")
        raise RuntimeError("PostgreSQL not initialized. Call init_postgresql() first.")
    return pg_session

def get_mongo_db():
    """Get MongoDB database"""
    if mongo_db is None:
        logger.warning("MongoDB not available")
        raise RuntimeError("MongoDB not initialized. Call init_mongodb() first.")
    return mongo_db

def create_tables():
    """Create database tables if they don't exist"""
    try:
        from binary.dashboard.models import Base

        if pg_engine:
            Base.metadata.create_all(pg_engine)
            logger.info("✓ Database tables created/verified")
        else:
            logger.warning("⚠ PostgreSQL engine not initialized, skipping table creation")
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        # Don't raise - let app continue without tables

def health_check():
    """Check health of all database connections"""
    health = {
        'postgresql': False,
        'mongodb': False
    }

    # Check PostgreSQL
    try:
        if pg_engine:
            with pg_engine.connect() as conn:
                conn.execute("SELECT 1")
            health['postgresql'] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")

    # Check MongoDB
    try:
        if mongo_client:
            mongo_client.admin.command('ping')
            health['mongodb'] = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")

    return health

# Export for easy imports
__all__ = [
    'Base',
    'init_postgresql',
    'init_mongodb',
    'init_databases',
    'get_pg_session',
    'get_mongo_db',
    'create_tables',
    'health_check',
    'pg_engine',
    'pg_session',
    'mongo_client',
    'mongo_db'
]
