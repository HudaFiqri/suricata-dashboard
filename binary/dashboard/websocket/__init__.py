"""
WebSocket Server Module
Real-time bidirectional communication via Socket.IO
"""

from flask_socketio import SocketIO

# Will be initialized in main app
socketio = None

def init_socketio(app):
    """Initialize Socket.IO with Flask app"""
    global socketio

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='gevent',
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25
    )

    # Register handlers
    from . import agent_handlers
    from . import ui_handlers

    return socketio

__all__ = ['socketio', 'init_socketio']
