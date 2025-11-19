"""
Configuration Management API
Manage Suricata configurations for agents
"""

from flask import request, jsonify
from datetime import datetime
import hashlib
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.models import Agent, AgentConfig, AuditLog
from binary.dashboard.database import get_pg_session
import logging

logger = logging.getLogger(__name__)

@api.route('/configs/<int:agent_id>', methods=['GET'])
@require_auth
def get_config(agent_id):
    """Get current configuration for agent"""
    session = get_pg_session()

    config_type = request.args.get('config_type', 'suricata.yaml')
    version = request.args.get('version')

    query = session.query(AgentConfig).filter_by(
        agent_id=agent_id,
        config_type=config_type
    )

    if version:
        config = query.filter_by(version=int(version)).first()
    else:
        config = query.filter_by(is_active=True).first()

    if not config:
        return jsonify({'success': False, 'error': 'Config not found'}), 404

    return jsonify({
        'success': True,
        'config': config.to_dict()
    })

@api.route('/configs/<int:agent_id>/history', methods=['GET'])
@require_auth
def get_config_history(agent_id):
    """Get configuration version history"""
    session = get_pg_session()

    config_type = request.args.get('config_type', 'suricata.yaml')

    configs = session.query(AgentConfig).filter_by(
        agent_id=agent_id,
        config_type=config_type
    ).order_by(AgentConfig.version.desc()).all()

    return jsonify({
        'success': True,
        'history': [c.to_dict() for c in configs]
    })

@api.route('/configs/<int:agent_id>', methods=['POST'])
@require_auth
def create_config(agent_id):
    """Create new configuration version"""
    data = request.get_json()

    session = get_pg_session()

    # Verify agent exists
    agent = session.query(Agent).filter_by(id=agent_id).first()
    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    config_type = data.get('config_type', 'suricata.yaml')
    content = data.get('content', '')
    change_notes = data.get('change_notes', '')
    validate_only = data.get('validate_only', False)
    auto_apply = data.get('auto_apply', False)

    # Calculate content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Get next version number
    latest = session.query(AgentConfig).filter_by(
        agent_id=agent_id,
        config_type=config_type
    ).order_by(AgentConfig.version.desc()).first()

    next_version = (latest.version + 1) if latest else 1

    # TODO: Validate configuration
    is_valid = True
    validation_errors = None

    if validate_only:
        return jsonify({
            'success': True,
            'validation': {
                'is_valid': is_valid,
                'errors': validation_errors or []
            }
        })

    # Create new config
    config = AgentConfig(
        agent_id=agent_id,
        config_type=config_type,
        content=content,
        content_hash=content_hash,
        version=next_version,
        is_active=False,  # Not active until applied
        is_valid=is_valid,
        validation_errors=validation_errors,
        status='draft',
        changed_by=request.username,
        change_notes=change_notes
    )

    session.add(config)
    session.commit()

    # Audit log
    audit = AuditLog(
        user_id=request.user_id,
        username=request.username,
        agent_id=agent_id,
        action='config_created',
        resource_type='config',
        resource_id=config.id,
        details={'version': next_version, 'notes': change_notes},
        ip_address=request.remote_addr
    )
    session.add(audit)
    session.commit()

    logger.info(f"Config created: agent={agent_id}, type={config_type}, version={next_version}")

    return jsonify({
        'success': True,
        'config_id': config.id,
        'version': next_version,
        'validation': {
            'is_valid': is_valid,
            'errors': validation_errors or []
        },
        'message': 'Config saved as draft'
    }), 201

@api.route('/configs/<int:agent_id>/apply', methods=['POST'])
@require_auth
def apply_config(agent_id):
    """Apply configuration to agent"""
    data = request.get_json()

    session = get_pg_session()

    config_id = data.get('config_id')
    reload_method = data.get('reload_method', 'graceful')

    config = session.query(AgentConfig).filter_by(id=config_id, agent_id=agent_id).first()

    if not config:
        return jsonify({'success': False, 'error': 'Config not found'}), 404

    if not config.is_valid:
        return jsonify({'success': False, 'error': 'Config is invalid'}), 400

    # Deactivate old configs
    session.query(AgentConfig).filter_by(
        agent_id=agent_id,
        config_type=config.config_type,
        is_active=True
    ).update({'is_active': False})

    # Create command for agent
    from binary.dashboard.models import AgentCommand

    command = AgentCommand(
        agent_id=agent_id,
        command_type='apply_config',
        parameters={
            'config_id': config_id,
            'config_type': config.config_type,
            'content': config.content,
            'reload_method': reload_method
        },
        created_by=request.username,
        priority=1
    )

    session.add(command)
    session.commit()

    # Audit log
    audit = AuditLog(
        user_id=request.user_id,
        username=request.username,
        agent_id=agent_id,
        action='config_applied',
        resource_type='config',
        resource_id=config_id,
        details={'version': config.version},
        ip_address=request.remote_addr
    )
    session.add(audit)
    session.commit()

    logger.info(f"Config apply initiated: agent={agent_id}, config={config_id}")

    return jsonify({
        'success': True,
        'command_id': command.id,
        'message': 'Config deployment initiated'
    })

@api.route('/configs/<int:agent_id>/fetch', methods=['POST'])
@require_auth
def fetch_config_from_agent(agent_id):
    """Fetch current configuration FROM agent (real-time)"""
    data = request.get_json() or {}

    session = get_pg_session()

    # Verify agent exists
    agent = session.query(Agent).filter_by(id=agent_id).first()
    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    # Check if agent is online
    if agent.status != 'online':
        return jsonify({'success': False, 'error': 'Agent is offline'}), 503

    config_path = data.get('path', '/etc/suricata/suricata.yaml')

    # Create command to read config from agent
    from binary.dashboard.models import AgentCommand

    command = AgentCommand(
        agent_id=agent_id,
        command_type='read_config',
        parameters={'path': config_path},
        created_by=request.username,
        priority=2  # High priority for interactive requests
    )

    session.add(command)
    session.commit()

    logger.info(f"Config fetch initiated: agent={agent_id}, path={config_path}")

    # Return command ID so client can poll for result
    return jsonify({
        'success': True,
        'command_id': command.id,
        'status': 'pending',
        'message': 'Config fetch initiated. Poll command status to get result.'
    }), 202
