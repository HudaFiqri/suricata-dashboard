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
    """Web UI client connects - PUBLIC ACCESS MODE"""
    session_id = request.sid
    logger.info(f"UI client connecting (public mode): {session_id}")

    # Auto-register as public user
    active_ui_clients[session_id] = {
        'user_id': 'public',
        'username': 'public',
        'role': 'admin',  # Grant admin role in public mode
        'connected_at': datetime.utcnow()
    }

    emit('connected', {
        'session_id': session_id,
        'timestamp': datetime.utcnow().isoformat(),
        'public_mode': True
    })

@socketio.on('auth', namespace='/ws/v1/ui')
def handle_ui_auth(data):
    """Auth handler - disabled in public access mode"""
    session_id = request.sid

    # Always return success in public mode
    emit('auth_response', {
        'success': True,
        'public_mode': True,
        'user': {
            'username': 'public',
            'role': 'admin'
        }
    })

@socketio.on('subscribe', namespace='/ws/v1/ui')
def handle_subscribe(data):
    """Subscribe to specific data streams - PUBLIC ACCESS MODE"""
    session_id = request.sid

    # Public mode - no auth check needed
    # Auto-register if not exists
    if session_id not in active_ui_clients:
        active_ui_clients[session_id] = {
            'user_id': 'public',
            'username': 'public',
            'role': 'admin',
            'connected_at': datetime.utcnow()
        }

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
    """UI sends command to agent - PUBLIC ACCESS MODE"""
    session_id = request.sid

    # Public mode - auto-register if needed
    if session_id not in active_ui_clients:
        active_ui_clients[session_id] = {
            'user_id': 'public',
            'username': 'public',
            'role': 'admin',
            'connected_at': datetime.utcnow()
        }

    user_info = active_ui_clients[session_id]

    # Public mode - no permission check (everyone is admin)

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
    """Get list of currently connected agents - PUBLIC ACCESS MODE"""
    session_id = request.sid

    # Public mode - no auth check needed

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
