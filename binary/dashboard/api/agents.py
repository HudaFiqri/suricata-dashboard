"""
Agent Management API
Endpoints for agent registration, status, and management
"""

from flask import request, jsonify
from datetime import datetime
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth, require_agent_auth
from binary.dashboard.models import Agent, AuditLog
from binary.dashboard.database import get_pg_session
import logging

logger = logging.getLogger(__name__)

@api.route('/agents/register', methods=['POST'])
def register_agent():
    """
    Register new agent
    Called by agent during installation
    """
    data = request.get_json()

    # Validate required fields
    required = ['name', 'hostname']
    for field in required:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400

    # Generate token (same for both PostgreSQL and MongoDB)
    import secrets
    import hashlib
    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
    encryption_key = secrets.token_urlsafe(32)

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Check if agent already exists
        existing = session.query(Agent).filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Agent with name {data["name"]} already exists'
            }), 409

        # Create new agent
        agent = Agent(
            name=data['name'],
            hostname=data['hostname'],
            ip_address=data.get('ip_address'),
            tags=data.get('tags', []),
            version=data.get('agent_version'),
            suricata_version=data.get('suricata_version'),
            system_info=data.get('system_info', {}),
            status='online',
            last_seen=datetime.utcnow(),
            token_hash=token_hash,
            encryption_key=encryption_key
        )

        session.add(agent)
        session.commit()

        agent_id = agent.id
        logger.info(f"Agent registered in PostgreSQL: {agent.name} (ID: {agent_id})")

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            db = get_mongo_db()

            # Check if agent already exists
            existing = db.agents.find_one({'name': data['name']})
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'Agent with name {data["name"]} already exists'
                }), 409

            # Create new agent document
            agent_doc = {
                'name': data['name'],
                'hostname': data['hostname'],
                'ip_address': data.get('ip_address'),
                'tags': data.get('tags', []),
                'version': data.get('agent_version'),
                'suricata_version': data.get('suricata_version'),
                'system_info': data.get('system_info', {}),
                'status': 'online',
                'last_seen': datetime.utcnow(),
                'token_hash': token_hash,
                'encryption_key': encryption_key,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            result = db.agents.insert_one(agent_doc)
            agent_id = str(result.inserted_id)

            logger.info(f"Agent registered in MongoDB: {data['name']} (ID: {agent_id})")

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503

    # Return response with config and token
    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'token': plain_token,  # Return plain token for installer
        'message': 'Agent registered successfully',
        'config': {
            'heartbeat_interval': 30,
            'batch_size': 100,
            'batch_timeout': 5
        }
    }), 201

@api.route('/agents', methods=['GET'])
@require_auth
def list_agents():
    """List all agents with optional filtering"""
    try:
        session = get_pg_session()
    except RuntimeError:
        # PostgreSQL not available
        return jsonify({
            'success': False,
            'error': 'Database not available',
            'agents': []
        }), 503

    # Query parameters
    status = request.args.get('status')
    tags = request.args.get('tags')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    # Build query
    query = session.query(Agent)

    if status:
        query = query.filter_by(status=status)

    if tags:
        # Filter by tags (JSONB contains)
        tag_list = tags.split(',')
        for tag in tag_list:
            query = query.filter(Agent.tags.contains([tag]))

    # Count total
    total = query.count()

    # Apply pagination
    agents = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        'success': True,
        'total': total,
        'agents': [agent.to_dict() for agent in agents]
    })

@api.route('/agents/<int:agent_id>', methods=['GET'])
@require_auth
def get_agent(agent_id):
    """Get single agent details"""
    session = get_pg_session()
    agent = session.query(Agent).filter_by(id=agent_id).first()

    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    return jsonify({
        'success': True,
        'agent': agent.to_dict()
    })

@api.route('/agents/<int:agent_id>', methods=['PUT'])
@require_auth
def update_agent(agent_id):
    """Update agent metadata"""
    session = get_pg_session()
    agent = session.query(Agent).filter_by(id=agent_id).first()

    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    data = request.get_json()

    # Update allowed fields
    if 'tags' in data:
        agent.tags = data['tags']

    if 'name' in data:
        # Check name uniqueness
        existing = session.query(Agent).filter(
            Agent.name == data['name'],
            Agent.id != agent_id
        ).first()

        if existing:
            return jsonify({'success': False, 'error': 'Name already exists'}), 409

        agent.name = data['name']

    session.commit()

    # Audit log
    audit = AuditLog(
        user_id=request.user_id,
        username=request.username,
        agent_id=agent_id,
        action='agent_updated',
        resource_type='agent',
        resource_id=agent_id,
        details=data,
        ip_address=request.remote_addr
    )
    session.add(audit)
    session.commit()

    return jsonify({
        'success': True,
        'message': 'Agent updated successfully'
    })

@api.route('/agents/<int:agent_id>', methods=['DELETE'])
@require_auth
def delete_agent(agent_id):
    """Delete agent"""
    confirm = request.args.get('confirm')
    if confirm != 'true':
        return jsonify({
            'success': False,
            'error': 'Confirmation required (add ?confirm=true)'
        }), 400

    session = get_pg_session()
    agent = session.query(Agent).filter_by(id=agent_id).first()

    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    agent_name = agent.name

    # Audit log before deletion
    audit = AuditLog(
        user_id=request.user_id,
        username=request.username,
        agent_id=agent_id,
        action='agent_deleted',
        resource_type='agent',
        resource_id=agent_id,
        details={'name': agent_name},
        ip_address=request.remote_addr
    )
    session.add(audit)

    # Delete agent (cascade will delete related configs, commands, etc.)
    session.delete(agent)
    session.commit()

    logger.info(f"Agent deleted: {agent_name} (ID: {agent_id}) by {request.username}")

    return jsonify({
        'success': True,
        'message': 'Agent deleted successfully'
    })

@api.route('/agents/<int:agent_id>/heartbeat', methods=['POST'])
@require_agent_auth
def agent_heartbeat(agent_id):
    """
    Agent heartbeat endpoint
    Called periodically by agent to update status and get pending commands
    """
    data = request.get_json()

    session = get_pg_session()
    agent = session.query(Agent).filter_by(id=agent_id).first()

    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    # Update agent status
    agent.status = 'online'
    agent.last_seen = datetime.utcnow()

    # Update health metrics
    if 'health' in data:
        agent.health_metrics = data['health']

    # Update Suricata info
    if 'suricata' in data:
        suricata = data['suricata']
        if 'pid' in suricata:
            agent.suricata_pid = suricata['pid']

    session.commit()

    # Get pending commands
    from binary.dashboard.models import AgentCommand
    pending_commands = session.query(AgentCommand).filter_by(
        agent_id=agent_id,
        status='pending'
    ).order_by(AgentCommand.priority.asc()).limit(10).all()

    commands = []
    for cmd in pending_commands:
        commands.append({
            'command_id': cmd.id,
            'command_type': cmd.command_type,
            'parameters': cmd.parameters
        })

        # Mark as sent
        cmd.status = 'sent'
        cmd.sent_at = datetime.utcnow()

    session.commit()

    return jsonify({
        'success': True,
        'pending_commands': commands
    })
