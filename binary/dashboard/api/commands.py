"""
Command Management API
Send and track commands to agents
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth, require_agent_auth
from binary.dashboard.models import AgentCommand, AuditLog
from binary.dashboard.database import get_pg_session, get_mongo_db
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

@api.route('/commands/<int:agent_id>', methods=['POST'])
@require_auth
def send_command(agent_id):
    """Send command to agent"""
    data = request.get_json()

    session = get_pg_session()

    command_type = data.get('command_type')
    parameters = data.get('parameters', {})
    timeout_seconds = data.get('timeout_seconds', 300)

    if not command_type:
        return jsonify({'success': False, 'error': 'command_type required'}), 400

    # Create command
    command = AgentCommand(
        agent_id=agent_id,
        command_type=command_type,
        parameters=parameters,
        status='pending',
        timeout_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
        created_by=request.username,
        priority=data.get('priority', 5)
    )

    session.add(command)
    session.commit()

    # Audit log
    audit = AuditLog(
        user_id=request.user_id,
        username=request.username,
        agent_id=agent_id,
        action='command_sent',
        resource_type='command',
        resource_id=command.id,
        details={'command_type': command_type},
        ip_address=request.remote_addr
    )
    session.add(audit)
    session.commit()

    logger.info(f"Command sent: {command_type} to agent {agent_id} (ID: {command.id})")

    return jsonify({
        'success': True,
        'command_id': command.id,
        'status': 'pending',
        'timeout_at': command.timeout_at.isoformat()
    }), 201

@api.route('/commands/<int:command_id>', methods=['GET'])
@require_auth
def get_command(command_id):
    """Get command status"""
    session = get_pg_session()

    command = session.query(AgentCommand).filter_by(id=command_id).first()

    if not command:
        return jsonify({'success': False, 'error': 'Command not found'}), 404

    return jsonify({
        'success': True,
        'command': command.to_dict()
    })

@api.route('/commands', methods=['GET'])
@require_auth
def list_commands():
    """List commands with filtering"""
    session = get_pg_session()

    agent_id = request.args.get('agent_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    query = session.query(AgentCommand)

    if agent_id:
        query = query.filter_by(agent_id=int(agent_id))

    if status:
        query = query.filter_by(status=status)

    total = query.count()
    commands = query.order_by(AgentCommand.created_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        'success': True,
        'total': total,
        'commands': [cmd.to_dict() for cmd in commands]
    })

@api.route('/commands/<int:command_id>/result', methods=['POST'])
@require_agent_auth
def receive_command_result(command_id):
    """Receive command execution result from agent (PostgreSQL version)"""
    data = request.get_json()

    session = get_pg_session()

    command = session.query(AgentCommand).filter_by(id=command_id).first()

    if not command:
        return jsonify({'success': False, 'error': 'Command not found'}), 404

    # Update command
    command.status = data.get('status', 'completed')
    command.result = data.get('result', {})
    command.error_message = data.get('error_message')
    command.completed_at = datetime.utcnow()

    session.commit()

    logger.info(f"Command result received: {command_id} - {command.status}")

    return jsonify({'success': True})


@api.route('/commands/<command_id>/result', methods=['POST'])
@require_agent_auth
def receive_command_result_mongo(command_id):
    """Receive command execution result from agent (MongoDB version)"""
    data = request.get_json()

    try:
        db = get_mongo_db()
    except Exception as e:
        logger.error(f"MongoDB error: {e}")
        return jsonify({'success': False, 'error': 'Database not available'}), 500

    try:
        # Convert string ID to ObjectId
        obj_id = ObjectId(command_id)
    except Exception as e:
        logger.error(f"Invalid ObjectId: {command_id}")
        return jsonify({'success': False, 'error': 'Invalid command ID'}), 400

    # Find command
    command = db.agent_commands.find_one({'_id': obj_id})

    if not command:
        return jsonify({'success': False, 'error': 'Command not found'}), 404

    # Update command
    update_data = {
        'status': data.get('status', 'completed'),
        'result': data.get('result', {}),
        'error_message': data.get('error_message'),
        'completed_at': datetime.utcnow()
    }

    db.agent_commands.update_one(
        {'_id': obj_id},
        {'$set': update_data}
    )

    logger.info(f"Command result received (MongoDB): {command_id} - {update_data['status']}")

    return jsonify({'success': True})
