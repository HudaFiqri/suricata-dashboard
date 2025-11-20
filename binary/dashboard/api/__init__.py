"""
Dashboard API Module
RESTful API endpoints for agent communication and web UI
"""

from flask import Blueprint

# Create API blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1')

# Import all API modules to register routes
from . import auth
from . import agents
from . import events
from . import logs
from . import configs
from . import commands
from . import stats
from . import query
from . import installer
from . import health
from . import users
from . import sessions
from . import permissions_api
from . import roles
from . import suricata_config

__all__ = [
    'api',
    'auth',
    'agents',
    'events',
    'logs',
    'configs',
    'commands',
    'stats',
    'query',
    'installer',
    'health',
    'users',
    'sessions',
    'permissions_api',
    'roles',
    'suricata_config'
]
