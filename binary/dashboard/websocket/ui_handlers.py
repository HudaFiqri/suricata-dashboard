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

# Track active UI connections
active_ui_clients = {}  # {session_id: {user_id, username, connected_at}}

@socketio.on('connect', namespace='/ws/v1/ui')
def handle_ui_connect():
    """Web UI client connects"""
    session_id = request.sid
    logger.info(f"UI client connecting: {session_id}")

    emit('connected', {
        'session_id': session_id,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('auth', namespace='/ws/v1/ui')
def handle_ui_auth(data):
    """Authenticate UI client with JWT token"""
    session_id = request.sid
    token = data.get('token')

    if not token:
        emit('auth_response', {
            'success': False,
            'error': 'No token provided'
        })
        disconnect()
        return

    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        user_id = payload.get('user_id')
        username = payload.get('username')

        # Verify user exists
        db = get_pg_session()
        user = db.query(User).filter_by(id=user_id, is_active=True).first()

        if not user:
            emit('auth_response', {
                'success': False,
                'error': 'User not found'
            })
            disconnect()
            return

        # Store in active clients
        active_ui_clients[session_id] = {
            'user_id': user_id,
            'username': username,
            'role': user.role,
            'connected_at': datetime.utcnow()
        }

        logger.info(f"UI client authenticated: {username}")

        emit('auth_response', {
            'success': True,
            'user': {
                'username': username,
                'role': user.role
            }
        })

    except jwt.ExpiredSignatureError:
        emit('auth_response', {
            'success': False,
            'error': 'Token expired'
        })
        disconnect()

    except jwt.InvalidTokenError:
        emit('auth_response', {
            'success': False,
            'error': 'Invalid token'
        })
        disconnect()

    except Exception as e:
        logger.error(f"UI auth failed: {e}")
        emit('auth_response', {
            'success': False,
            'error': 'Authentication failed'
        })
        disconnect()

@socketio.on('subscribe', namespace='/ws/v1/ui')
def handle_subscribe(data):
    """Subscribe to specific data streams"""
    session_id = request.sid

    if session_id not in active_ui_clients:
        emit('error', {'message': 'Not authenticated'})
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

    if session_id not in active_ui_clients:
        emit('error', {'message': 'Not authenticated'})
        return

    user_info = active_ui_clients[session_id]

    # Check permissions
    if user_info['role'] not in ['admin', 'operator']:
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

    if session_id not in active_ui_clients:
        emit('error', {'message': 'Not authenticated'})
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
