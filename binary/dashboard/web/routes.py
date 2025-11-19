"""
Web UI Routes
Dashboard pages for multi-agent management
"""

from flask import render_template, redirect, url_for, session, request
from binary.dashboard.web import web
import logging
import os

logger = logging.getLogger(__name__)

ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'False').lower() == 'true'

@web.route('/')
def index():
    """Dashboard home - agent overview"""
    return render_template('dashboard.html', enable_auth=ENABLE_AUTH)

@web.route('/agents')
def agents():
    """Agent management page"""
    return render_template('agents.html')

@web.route('/agents/<agent_id>')
def agent_detail(agent_id):
    """Single agent detail page"""
    return render_template('agent_detail.html', agent_id=agent_id)

@web.route('/events')
def events():
    """Events viewer - all agents"""
    return render_template('events.html')

@web.route('/events/<agent_id>')
def agent_events(agent_id):
    """Events for specific agent"""
    return render_template('events.html', agent_id=agent_id)

@web.route('/alerts')
def alerts():
    """Alerts dashboard"""
    return render_template('alerts.html')

@web.route('/logs')
def logs():
    """Logs viewer"""
    return render_template('logs.html')

@web.route('/statistics')
def statistics():
    """Statistics and analytics"""
    return render_template('statistics.html')

@web.route('/configs')
def configs():
    """Configuration management"""
    return render_template('configs.html', enable_auth=ENABLE_AUTH)

@web.route('/configs/<agent_id>')
def agent_config(agent_id):
    """Agent configuration editor"""
    return render_template('config_editor.html', agent_id=agent_id)

@web.route('/users')
def users():
    """User management page"""
    return render_template('users.html')

@web.route('/login')
def login():
    """Login page"""
    if not ENABLE_AUTH:
        # Auth disabled, redirect to dashboard
        return redirect(url_for('web.index'))
    return render_template('login.html')

@web.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('web.index'))
