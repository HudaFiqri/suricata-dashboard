"""
Web UI Blueprint
HTML pages for dashboard interface
"""

from flask import Blueprint

# Create web blueprint
web = Blueprint('web', __name__,
                template_folder='templates',
                static_folder='static')

# Import routes
from binary.dashboard.web import routes

__all__ = ['web']
