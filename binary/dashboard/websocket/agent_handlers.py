"""
WebSocket Handlers for Agent Connections
Handle agent namespace (/ws/v1/agent)
"""

from flask import request
from flask_socketio import emit, disconnect, join_room
from datetime import datetime, timedelta
from binary.dashboard.websocket import socketio
from binary.dashboard.models import Agent, AgentCommand
from binary.dashboard.database import get_pg_session, get_mongo_db
import logging

logger = logging.getLogger(__name__)

# Track active agent connections
active_agents = {}  # {session_id: {agent_id, agent_name, connected_at}}

@socketio.on('connect', namespace='/ws/v1/agent')
def handle_agent_connect():
    """Agent establishes connection"""
    session_id = request.sid
    logger.info(f"Agent connecting: {session_id}")

    emit('connected', {
        'session_id': session_id,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('auth', namespace='/ws/v1/agent')
def handle_agent_auth(data):
    """Authenticate agent"""
    session_id = request.sid
    agent_id = data.get('agent_id')
    encrypted_token = data.get('token')

    logger.info(f"Agent auth attempt: agent_id={agent_id}")

    # TODO: Validate encrypted token
    # For now, simple check

    db = get_pg_session()
    agent = db.query(Agent).filter_by(id=agent_id).first()

    if not agent:
        logger.warning(f"Agent not found: {agent_id}")
        emit('auth_response', {
            'success': False,
            'error': 'Agent not found'
        })
        disconnect()
        return

    # Store in active connections
    active_agents[session_id] = {
        'agent_id': agent_id,
        'agent_name': agent.name,
        'connected_at': datetime.utcnow()
    }

    # Join room for this agent
    join_room(f'agent_{agent_id}')

    # Update agent status
    agent.status = 'online'
    agent.last_seen = datetime.utcnow()
    db.commit()

    # Broadcast to UI clients
    if socketio:
        socketio.emit('agent_status', {
            'agent_id': agent_id,
            'status': 'online'
        }, namespace='/ws/v1/ui')

    logger.info(f"Agent authenticated: {agent.name} (ID: {agent_id})")

    emit('auth_response', {
        'success': True,
        'config': {
            'heartbeat_interval': 30,
            'batch_size': 100,
            'compression': True
        }
    })

@socketio.on('event', namespace='/ws/v1/agent')
def handle_single_event(data):
    """Receive single event from agent"""
    session_id = request.sid

    if session_id not in active_agents:
        logger.warning(f"Unauthenticated event from {session_id}")
        return

    agent_info = active_agents[session_id]
    agent_id = agent_info['agent_id']

    # Store in MongoDB
    mongo_db = get_mongo_db()

    try:
        event_doc = {
            'agent_id': agent_id,
            'agent_name': agent_info['agent_name'],
            'event_type': data.get('event_type'),
            'timestamp': datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            'raw_event': data.get('data', {}),
            'indexed': data.get('data', {}).get('indexed', {}),
            'received_at': datetime.utcnow(),
            'expire_at': datetime.utcnow() + timedelta(days=90)
        }

        result = mongo_db.events.insert_one(event_doc)

        # Acknowledge
        sequence = data.get('sequence')
        if sequence:
            emit('event_ack', {'sequence': sequence})

        # Broadcast to UI
        if socketio:
            socketio.emit('new_event', {
                'agent_id': agent_id,
                'agent_name': agent_info['agent_name'],
                'event': data
            }, namespace='/ws/v1/ui', room='events')

    except Exception as e:
        logger.error(f"Failed to store event: {e}")

@socketio.on('event_batch', namespace='/ws/v1/agent')
def handle_event_batch(data):
    """Receive batch of events"""
    session_id = request.sid

    if session_id not in active_agents:
        return

    agent_info = active_agents[session_id]
    agent_id = agent_info['agent_id']

    events = data.get('events', [])
    logger.debug(f"Received {len(events)} events from agent {agent_id}")

    # Store in MongoDB
    mongo_db = get_mongo_db()

    event_docs = []
    for event in events:
        try:
            event_docs.append({
                'agent_id': agent_id,
                'agent_name': agent_info['agent_name'],
                'event_type': event.get('event_type'),
                'timestamp': datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')),
                'raw_event': event.get('data', {}),
                'indexed': event.get('data', {}).get('indexed', {}),
                'received_at': datetime.utcnow(),
                'expire_at': datetime.utcnow() + timedelta(days=90)
            })
        except Exception as e:
            logger.error(f"Failed to process event: {e}")

    if event_docs:
        try:
            result = mongo_db.events.insert_many(event_docs, ordered=False)
            processed = len(result.inserted_ids)
        except Exception as e:
            logger.error(f"MongoDB insert failed: {e}")
            processed = 0
    else:
        processed = 0

    # Acknowledge
    emit('event_batch_ack', {
        'sequence': data.get('sequence'),
        'processed': processed,
        'failed': len(events) - processed
    })

    # Broadcast summary to UI
    if socketio:
        socketio.emit('event_batch_received', {
            'agent_id': agent_id,
            'count': len(events)
        }, namespace='/ws/v1/ui')

@socketio.on('log', namespace='/ws/v1/agent')
def handle_log(data):
    """Receive log entry"""
    session_id = request.sid

    if session_id not in active_agents:
        return

    agent_info = active_agents[session_id]
    agent_id = agent_info['agent_id']

    # Store in MongoDB
    mongo_db = get_mongo_db()

    try:
        log_doc = {
            'agent_id': agent_id,
            'agent_name': agent_info['agent_name'],
            'timestamp': datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            'level': data['level'],
            'message': data['message'],
            'raw_line': data.get('raw_line', ''),
            'received_at': datetime.utcnow(),
            'expire_at': datetime.utcnow() + timedelta(days=30)
        }

        mongo_db.logs.insert_one(log_doc)

        # Broadcast to UI
        if socketio:
            socketio.emit('new_log', {
                'agent_id': agent_id,
                'agent_name': agent_info['agent_name'],
                'log': data
            }, namespace='/ws/v1/ui', room='logs')

    except Exception as e:
        logger.error(f"Failed to store log: {e}")

@socketio.on('heartbeat', namespace='/ws/v1/agent')
def handle_heartbeat(data):
    """Agent heartbeat"""
    session_id = request.sid

    if session_id not in active_agents:
        return

    agent_info = active_agents[session_id]
    agent_id = agent_info['agent_id']

    # Update agent
    db = get_pg_session()
    agent = db.query(Agent).filter_by(id=agent_id).first()

    if agent:
        agent.last_seen = datetime.utcnow()
        agent.health_metrics = data.get('health', {})
        db.commit()

    # Get pending commands
    pending_commands = db.query(AgentCommand).filter_by(
        agent_id=agent_id,
        status='pending'
    ).limit(10).all()

    commands = []
    for cmd in pending_commands:
        commands.append({
            'command_id': cmd.id,
            'command_type': cmd.command_type,
            'parameters': cmd.parameters
        })
        cmd.status = 'sent'
        cmd.sent_at = datetime.utcnow()

    db.commit()

    emit('heartbeat_ack', {
        'pending_commands': commands
    })

@socketio.on('command_result', namespace='/ws/v1/agent')
def handle_command_result(data):
    """Agent reports command result"""
    session_id = request.sid

    if session_id not in active_agents:
        return

    command_id = data.get('command_id')
    status = data.get('status')
    result = data.get('result', {})

    # Update command
    db = get_pg_session()
    cmd = db.query(AgentCommand).filter_by(id=command_id).first()

    if cmd:
        cmd.status = status
        cmd.result = result
        cmd.completed_at = datetime.utcnow()
        db.commit()

        # Notify UI
        if socketio:
            socketio.emit('command_completed', {
                'command_id': command_id,
                'status': status,
                'result': result
            }, namespace='/ws/v1/ui', room=f'agent_{cmd.agent_id}')

@socketio.on('disconnect', namespace='/ws/v1/agent')
def handle_agent_disconnect():
    """Agent disconnects"""
    session_id = request.sid

    if session_id in active_agents:
        agent_info = active_agents[session_id]
        agent_id = agent_info['agent_id']

        # Update status
        db = get_pg_session()
        agent = db.query(Agent).filter_by(id=agent_id).first()

        if agent:
            agent.status = 'offline'
            db.commit()

        # Broadcast to UI
        if socketio:
            socketio.emit('agent_status', {
                'agent_id': agent_id,
                'status': 'offline'
            }, namespace='/ws/v1/ui')

        logger.info(f"Agent disconnected: {agent_info['agent_name']}")
        del active_agents[session_id]
