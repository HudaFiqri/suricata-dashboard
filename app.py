"""
Suricata Dashboard - Main Application Entry Point

A lightweight, modular web dashboard for Suricata IDS monitoring.
All core logic is separated into binary/app and binary/api modules.
"""
import logging
from flask import Flask
from config import Config
from binary.app import AppEngine, BackgroundTasks, WebRoutes

# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Initialize Flask
app = Flask(__name__)

# Initialize application engine
engine = AppEngine(Config)

# Register web routes (HTML pages)
web_routes = WebRoutes(app, engine.controller, Config)

# Register API routes
api_routes = engine.register_routes(app)

# Start background tasks
background_tasks = BackgroundTasks(engine, Config)
background_tasks.start_all()

# Run application
if __name__ == '__main__':
    app.run(
        debug=Config.FLASK_DEBUG,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        use_debugger=False,
        use_reloader=True
    )
