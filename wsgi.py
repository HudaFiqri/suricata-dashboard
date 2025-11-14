#!/usr/bin/env python3
"""
WSGI Entry Point for Production
Use with gunicorn or other WSGI servers
"""

from binary.dashboard import create_app

# Create application
app, socketio = create_app()

if __name__ == "__main__":
    # For development with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False
    )
