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
    from cryptography.fernet import Fernet

    plain_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

    # Generate proper Fernet key (32 bytes base64-encoded)
    encryption_key = Fernet.generate_key().decode('utf-8')

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
            status='pending',  # Will change to 'online' when agent sends first heartbeat
            last_seen=None,
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
                'status': 'pending',  # Will change to 'online' when agent sends first heartbeat
                'last_seen': None,
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

    # Return response with config, token, and encryption key
    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'token': plain_token,  # Return plain token for installer
        'encryption_key': encryption_key,  # Return encryption key for installer
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

    # Query parameters
    status = request.args.get('status')
    tags = request.args.get('tags')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    # Try PostgreSQL first
    try:
        session = get_pg_session()

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

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            db = get_mongo_db()

            # Build MongoDB query
            mongo_query = {}
            if status:
                mongo_query['status'] = status
            if tags:
                tag_list = tags.split(',')
                mongo_query['tags'] = {'$all': tag_list}

            # Count total
            total = db.agents.count_documents(mongo_query)

            # Query with pagination
            cursor = db.agents.find(mongo_query).sort('created_at', -1).skip(offset).limit(limit)
            agents_list = []

            for agent_doc in cursor:
                # Convert MongoDB document to dict
                agent_dict = {
                    'id': str(agent_doc.get('_id')),
                    'name': agent_doc.get('name'),
                    'hostname': agent_doc.get('hostname'),
                    'ip_address': agent_doc.get('ip_address'),
                    'tags': agent_doc.get('tags', []),
                    'version': agent_doc.get('version'),
                    'suricata_version': agent_doc.get('suricata_version'),
                    'system_info': agent_doc.get('system_info', {}),
                    'status': agent_doc.get('status', 'offline'),
                    'last_seen': agent_doc.get('last_seen'),
                    'created_at': agent_doc.get('created_at'),
                    'updated_at': agent_doc.get('updated_at')
                }
                agents_list.append(agent_dict)

            return jsonify({
                'success': True,
                'total': total,
                'agents': agents_list
            })

        except RuntimeError:
            # Both databases unavailable
            return jsonify({
                'success': False,
                'error': 'Database not available',
                'agents': []
            }), 503

@api.route('/agents/self', methods=['GET'])
def get_self_agent():
    """
    Get agent's own info using token authentication
    Used by agent to fetch its encryption key during auto-fix
    """
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'success': False,
            'error': 'Missing or invalid Authorization header'
        }), 401

    token = auth_header.replace('Bearer ', '')

    # Hash the token to match against database
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        agent = session.query(Agent).filter_by(token_hash=token_hash).first()

        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        return jsonify({
            'success': True,
            'agent_id': agent.id,
            'name': agent.name,
            'encryption_key': agent.encryption_key,
            'tags': agent.tags,
            'status': agent.status
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            db = get_mongo_db()

            agent = db.agents.find_one({'token_hash': token_hash})

            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            return jsonify({
                'success': True,
                'agent_id': str(agent.get('_id')),
                'name': agent.get('name'),
                'encryption_key': agent.get('encryption_key'),
                'tags': agent.get('tags', []),
                'status': agent.get('status')
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503

@api.route('/agents/<agent_id>', methods=['GET'])
@require_auth
def get_agent(agent_id):
    """Get single agent details (supports both int and string IDs)"""

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Convert to int for PostgreSQL
        try:
            pg_agent_id = int(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid agent ID'}), 400

        agent = session.query(Agent).filter_by(id=pg_agent_id).first()

        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        return jsonify({
            'success': True,
            'agent': agent.to_dict()
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            from bson import ObjectId
            db = get_mongo_db()

            # Convert to ObjectId
            try:
                mongo_agent_id = ObjectId(agent_id)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid agent ID format'}), 400

            agent = db.agents.find_one({'_id': mongo_agent_id})

            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            # Convert to dict
            agent_dict = {
                'id': str(agent.get('_id')),
                'name': agent.get('name'),
                'hostname': agent.get('hostname'),
                'ip_address': agent.get('ip_address'),
                'tags': agent.get('tags', []),
                'version': agent.get('version'),
                'suricata_version': agent.get('suricata_version'),
                'system_info': agent.get('system_info', {}),
                'status': agent.get('status', 'offline'),
                'last_seen': agent.get('last_seen'),
                'created_at': agent.get('created_at'),
                'updated_at': agent.get('updated_at')
            }

            return jsonify({
                'success': True,
                'agent': agent_dict
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503

@api.route('/agents/<agent_id>', methods=['PUT'])
@require_auth
def update_agent(agent_id):
    """Update agent metadata (supports both int and string IDs)"""
    data = request.get_json()

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Convert to int for PostgreSQL
        try:
            pg_agent_id = int(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid agent ID'}), 400

        agent = session.query(Agent).filter_by(id=pg_agent_id).first()

        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        # Update allowed fields
        if 'tags' in data:
            agent.tags = data['tags']

        if 'name' in data:
            # Check name uniqueness
            existing = session.query(Agent).filter(
                Agent.name == data['name'],
                Agent.id != pg_agent_id
            ).first()

            if existing:
                return jsonify({'success': False, 'error': 'Name already exists'}), 409

            agent.name = data['name']

        session.commit()

        # Audit log
        audit = AuditLog(
            user_id=request.user_id,
            username=request.username,
            agent_id=pg_agent_id,
            action='agent_updated',
            resource_type='agent',
            resource_id=pg_agent_id,
            details=data,
            ip_address=request.remote_addr
        )
        session.add(audit)
        session.commit()

        return jsonify({
            'success': True,
            'message': 'Agent updated successfully'
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            from bson import ObjectId
            from datetime import datetime
            db = get_mongo_db()

            # Convert to ObjectId
            try:
                mongo_agent_id = ObjectId(agent_id)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid agent ID format'}), 400

            # Find agent
            agent = db.agents.find_one({'_id': mongo_agent_id})
            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            # Build update document
            update_doc = {'updated_at': datetime.utcnow()}

            if 'tags' in data:
                update_doc['tags'] = data['tags']

            if 'name' in data:
                # Check name uniqueness
                existing = db.agents.find_one({
                    'name': data['name'],
                    '_id': {'$ne': mongo_agent_id}
                })
                if existing:
                    return jsonify({'success': False, 'error': 'Name already exists'}), 409

                update_doc['name'] = data['name']

            # Update agent
            db.agents.update_one(
                {'_id': mongo_agent_id},
                {'$set': update_doc}
            )

            return jsonify({
                'success': True,
                'message': 'Agent updated successfully'
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503

@api.route('/agents/<agent_id>', methods=['DELETE'])
@require_auth
def delete_agent(agent_id):
    """Delete agent (supports both int and string IDs for PostgreSQL/MongoDB)"""
    confirm = request.args.get('confirm')
    if confirm != 'true':
        return jsonify({
            'success': False,
            'error': 'Confirmation required (add ?confirm=true)'
        }), 400

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Convert agent_id to int for PostgreSQL
        try:
            pg_agent_id = int(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid agent ID for PostgreSQL'}), 400

        agent = session.query(Agent).filter_by(id=pg_agent_id).first()

        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        agent_name = agent.name

        # Audit log before deletion
        audit = AuditLog(
            user_id=request.user_id,
            username=request.username,
            agent_id=pg_agent_id,
            action='agent_deleted',
            resource_type='agent',
            resource_id=pg_agent_id,
            details={'name': agent_name},
            ip_address=request.remote_addr
        )
        session.add(audit)

        # Delete agent (cascade will delete related configs, commands, etc.)
        session.delete(agent)
        session.commit()

        logger.info(f"Agent deleted from PostgreSQL: {agent_name} (ID: {pg_agent_id})")

        return jsonify({
            'success': True,
            'message': 'Agent deleted successfully'
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            from bson import ObjectId
            db = get_mongo_db()

            # Convert string ID to ObjectId
            try:
                mongo_agent_id = ObjectId(agent_id)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid agent ID format'}), 400

            # Find agent
            agent = db.agents.find_one({'_id': mongo_agent_id})
            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            agent_name = agent.get('name', 'Unknown')

            # Delete agent
            result = db.agents.delete_one({'_id': mongo_agent_id})

            if result.deleted_count == 0:
                return jsonify({'success': False, 'error': 'Failed to delete agent'}), 500

            logger.info(f"Agent deleted from MongoDB: {agent_name} (ID: {agent_id})")

            return jsonify({
                'success': True,
                'message': 'Agent deleted successfully'
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503

@api.route('/agents/<agent_id>/heartbeat', methods=['POST'])
@require_agent_auth
def agent_heartbeat(agent_id):
    """
    Agent heartbeat endpoint (encrypted)
    Called periodically by agent to update status and get pending commands

    Expects encrypted payload:
    {
        "encrypted": "base64_encoded_encrypted_data"
    }

    Decrypted payload contains health metrics
    """
    data = request.get_json()

    # Decrypt payload
    try:
        # Get agent from request (set by require_agent_auth)
        agent = request.agent

        # Import decrypt function from events.py
        from binary.dashboard.api.events import decrypt_agent_payload

        # Decrypt health data
        if 'encrypted' in data:
            health_data = decrypt_agent_payload(agent, data['encrypted'])
        else:
            # Fallback for non-encrypted (backward compat during migration)
            health_data = data

    except Exception as e:
        logger.error(f"Failed to decrypt heartbeat: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to decrypt heartbeat data'
        }), 400

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Convert to int for PostgreSQL
        try:
            pg_agent_id = int(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid agent ID'}), 400

        agent_obj = session.query(Agent).filter_by(id=pg_agent_id).first()

        if not agent_obj:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        # Update agent status
        agent_obj.status = 'online'
        agent_obj.last_seen = datetime.utcnow()

        # Update health metrics (store decrypted health data)
        agent_obj.health_metrics = health_data

        # Update Suricata info
        if 'suricata' in health_data:
            suricata = health_data['suricata']
            if 'pid' in suricata:
                agent_obj.suricata_pid = suricata['pid']

        session.commit()

        # Get pending commands (TODO: implement command queue)
        commands = []

        return jsonify({
            'success': True,
            'pending_commands': commands
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            from bson import ObjectId
            db = get_mongo_db()

            # Convert to ObjectId
            try:
                mongo_agent_id = ObjectId(agent_id)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid agent ID'}), 400

            # Update agent
            result = db.agents.update_one(
                {'_id': mongo_agent_id},
                {'$set': {
                    'status': 'online',
                    'last_seen': datetime.utcnow(),
                    'health_metrics': health_data,
                    'updated_at': datetime.utcnow()
                }}
            )

            if result.matched_count == 0:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            # TODO: Get pending commands from MongoDB

            return jsonify({
                'success': True,
                'pending_commands': []
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503



@api.route('/agents/<agent_id>/rotate-key', methods=['POST'])
@require_auth
def rotate_encryption_key(agent_id):
    """
    Rotate agent encryption key
    Generates new encryption key for the agent

    Returns new key that needs to be updated in agent config
    """

    # Generate new encryption key (proper Fernet format)
    from cryptography.fernet import Fernet
    new_encryption_key = Fernet.generate_key().decode('utf-8')

    # Try PostgreSQL first
    try:
        session = get_pg_session()

        # Convert to int for PostgreSQL
        try:
            pg_agent_id = int(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid agent ID'}), 400

        agent = session.query(Agent).filter_by(id=pg_agent_id).first()

        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        agent_name = agent.name
        old_key = agent.encryption_key[:8] + '...'  # Show first 8 chars for audit

        # Update encryption key
        agent.encryption_key = new_encryption_key
        agent.updated_at = datetime.utcnow()
        session.commit()

        # Audit log
        audit = AuditLog(
            user_id=request.user_id,
            username=request.username,
            agent_id=pg_agent_id,
            action='encryption_key_rotated',
            resource_type='agent',
            resource_id=pg_agent_id,
            details={'agent_name': agent_name, 'old_key_prefix': old_key},
            ip_address=request.remote_addr
        )
        session.add(audit)
        session.commit()

        logger.info(f"Encryption key rotated for agent {agent_name} (ID: {pg_agent_id}) by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Encryption key rotated successfully',
            'encryption_key': new_encryption_key,
            'agent_name': agent_name
        })

    except RuntimeError:
        # Fallback to MongoDB
        try:
            from binary.dashboard.database import get_mongo_db
            from bson import ObjectId
            db = get_mongo_db()

            # Convert to ObjectId
            try:
                mongo_agent_id = ObjectId(agent_id)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid agent ID format'}), 400

            # Find agent
            agent = db.agents.find_one({'_id': mongo_agent_id})
            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 404

            agent_name = agent.get('name', 'Unknown')

            # Update encryption key
            result = db.agents.update_one(
                {'_id': mongo_agent_id},
                {'$set': {
                    'encryption_key': new_encryption_key,
                    'updated_at': datetime.utcnow()
                }}
            )

            if result.matched_count == 0:
                return jsonify({'success': False, 'error': 'Failed to update agent'}), 500

            logger.info(f"Encryption key rotated for agent {agent_name} (ID: {agent_id})")

            return jsonify({
                'success': True,
                'message': 'Encryption key rotated successfully',
                'encryption_key': new_encryption_key,
                'agent_name': agent_name
            })

        except RuntimeError:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 503
