"""
Web UI Blueprint
HTML pages for dashboard interface
"""

from flask import Blueprint
import os

# Create web blueprint
web = Blueprint('web', __name__,
                template_folder='templates',
                static_folder='static')

# Context processor to inject variables into all templates
@web.app_context_processor
def inject_config():
    return {
        'enable_auth': os.getenv('ENABLE_AUTH', 'False').lower() == 'true'
    }

# Import routes
from binary.dashboard.web import routes

__all__ = ['web']
