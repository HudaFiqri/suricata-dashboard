"""
WebSocket Handlers for UI Connections
Handle web UI namespace (/ws/v1/ui)
"""

from flask import request
from flask_socketio import emit, disconnect, join_room, leave_room
from datetime import datetime
from binary.dashboard.websocket import socketio
from binary.dashboard.models import User, AgentCommand
from binary.dashboard.database import get_pg_session
import jwt
import os
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'False').lower() == 'true'

# Track active UI connections
active_ui_clients = {}  # {session_id: {user_id, username, connected_at}}

@socketio.on('connect', namespace='/ws/v1/ui')
def handle_ui_connect():
    """Web UI client connects"""
    session_id = request.sid

    if not ENABLE_AUTH:
        # PUBLIC ACCESS MODE
        logger.info(f"UI client connecting (public mode): {session_id}")
        active_ui_clients[session_id] = {
            'user_id': 'public',
            'username': 'public',
            'role': 'admin',
            'connected_at': datetime.utcnow()
        }

        emit('connected', {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'auth_required': False
        })
    else:
        # AUTH ENABLED - Wait for auth message
        logger.info(f"UI client connecting (auth required): {session_id}")
        emit('connected', {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'auth_required': True
        })

@socketio.on('auth', namespace='/ws/v1/ui')
def handle_ui_auth(data):
    """WebSocket authentication handler"""
    session_id = request.sid

    if not ENABLE_AUTH:
        # Public mode - auto success
        emit('auth_response', {
            'success': True,
            'user': {
                'username': 'public',
                'role': 'admin'
            }
        })
        return

    # Auth enabled - validate JWT token
    token = data.get('token')
    if not token:
        emit('auth_response', {
            'success': False,
            'error': 'Token required'
        })
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # Register authenticated client
        active_ui_clients[session_id] = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload.get('role', 'viewer'),
            'connected_at': datetime.utcnow()
        }

        emit('auth_response', {
            'success': True,
            'user': {
                'username': payload['username'],
                'role': payload.get('role', 'viewer')
            }
        })

        logger.info(f"UI client authenticated: {payload['username']}")

    except jwt.ExpiredSignatureError:
        emit('auth_response', {
            'success': False,
            'error': 'Token expired'
        })
    except jwt.InvalidTokenError:
        emit('auth_response', {
            'success': False,
            'error': 'Invalid token'
        })

@socketio.on('subscribe', namespace='/ws/v1/ui')
def handle_subscribe(data):
    """Subscribe to specific data streams"""
    session_id = request.sid

    # Check if client is registered
    if session_id not in active_ui_clients:
        if not ENABLE_AUTH:
            # Public mode - auto-register
            active_ui_clients[session_id] = {
                'user_id': 'public',
                'username': 'public',
                'role': 'admin',
                'connected_at': datetime.utcnow()
            }
        else:
            # Auth mode - client must authenticate first
            emit('error', {'message': 'Authentication required'})
            return

    channel = data.get('channel')

    # Valid channels:
    # - 'events' - All events
    # - 'logs' - All logs
    # - 'agent_123' - Specific agent updates
    # - 'alerts' - Only alert events

    valid_channels = ['events', 'logs', 'alerts']

    if channel.startswith('agent_'):
        # Agent-specific channel
        join_room(channel)
    elif channel in valid_channels:
        join_room(channel)
    else:
        emit('error', {'message': f'Invalid channel: {channel}'})
        return

    logger.debug(f"Client {session_id} subscribed to {channel}")

    emit('subscribed', {'channel': channel})

@socketio.on('unsubscribe', namespace='/ws/v1/ui')
def handle_unsubscribe(data):
    """Unsubscribe from data stream"""
    session_id = request.sid

    if session_id not in active_ui_clients:
        return

    channel = data.get('channel')

    leave_room(channel)
    logger.debug(f"Client {session_id} unsubscribed from {channel}")

    emit('unsubscribed', {'channel': channel})

@socketio.on('send_command', namespace='/ws/v1/ui')
def handle_send_command(data):
    """UI sends command to agent"""
    session_id = request.sid

    # Check if client is registered
    if session_id not in active_ui_clients:
        if not ENABLE_AUTH:
            # Public mode - auto-register
            active_ui_clients[session_id] = {
                'user_id': 'public',
                'username': 'public',
                'role': 'admin',
                'connected_at': datetime.utcnow()
            }
        else:
            # Auth mode - must be authenticated
            emit('error', {'message': 'Authentication required'})
            return

    user_info = active_ui_clients[session_id]

    # Check permissions (only admins can send commands in auth mode)
    if ENABLE_AUTH and user_info.get('role') != 'admin':
        emit('error', {'message': 'Insufficient permissions'})
        return

    agent_id = data.get('agent_id')
    command_type = data.get('command_type')
    parameters = data.get('parameters', {})

    if not agent_id or not command_type:
        emit('error', {'message': 'agent_id and command_type required'})
        return

    # Create command in database
    db = get_pg_session()

    command = AgentCommand(
        agent_id=agent_id,
        command_type=command_type,
        parameters=parameters,
        created_by=user_info['username'],
        status='pending'
    )

    db.add(command)
    db.commit()

    logger.info(f"Command created: {command_type} for agent {agent_id} by {user_info['username']}")

    # If agent is connected via WebSocket, send immediately
    from binary.dashboard.websocket.agent_handlers import active_agents

    agent_session = None
    for sid, info in active_agents.items():
        if info['agent_id'] == agent_id:
            agent_session = sid
            break

    if agent_session:
        # Send to agent directly
        if socketio:
            socketio.emit('command', {
                'command_id': command.id,
                'command_type': command_type,
                'parameters': parameters
            }, namespace='/ws/v1/agent', room=agent_session)

    emit('command_sent', {
        'command_id': command.id,
        'status': 'pending'
    })

@socketio.on('get_active_agents', namespace='/ws/v1/ui')
def handle_get_active_agents():
    """Get list of currently connected agents"""
    session_id = request.sid

    # Check if authenticated (in auth mode)
    if ENABLE_AUTH and session_id not in active_ui_clients:
        emit('error', {'message': 'Authentication required'})
        return

    from binary.dashboard.websocket.agent_handlers import active_agents

    agents = []
    for sid, info in active_agents.items():
        agents.append({
            'agent_id': info['agent_id'],
            'agent_name': info['agent_name'],
            'connected_at': info['connected_at'].isoformat()
        })

    emit('active_agents', {
        'count': len(agents),
        'agents': agents
    })

@socketio.on('disconnect', namespace='/ws/v1/ui')
def handle_ui_disconnect():
    """UI client disconnects"""
    session_id = request.sid

    if session_id in active_ui_clients:
        user_info = active_ui_clients[session_id]
        logger.info(f"UI client disconnected: {user_info['username']}")
        del active_ui_clients[session_id]
