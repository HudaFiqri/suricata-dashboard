"""
Custom Roles API
Endpoints for managing custom roles
"""

from flask import request, jsonify
from datetime import datetime
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.api.decorators import require_permission
from binary.dashboard.database import get_pg_session, get_mongo_db
from binary.dashboard.permissions import get_all_permissions, ROLE_PERMISSIONS
import logging

logger = logging.getLogger(__name__)

@api.route('/roles', methods=['GET'])
@require_auth
@require_permission('users.view')
def get_all_roles():
    """List all roles (system + custom)"""
    roles = []

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import CustomRole

        db_roles = session.query(CustomRole).all()
        for role in db_roles:
            roles.append(role.to_dict())

        return jsonify({
            'success': True,
            'roles': roles,
            'db_type': 'postgresql'
        })

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        mongo_roles = db.custom_roles.find()

        for role in mongo_roles:
            roles.append({
                'id': str(role['_id']),
                'name': role['name'],
                'display_name': role.get('display_name'),
                'description': role.get('description'),
                'permissions': role.get('permissions', []),
                'is_system': role.get('is_system', False),
                'created_at': role.get('created_at').isoformat() if role.get('created_at') else None,
                'updated_at': role.get('updated_at').isoformat() if role.get('updated_at') else None
            })

        return jsonify({
            'success': True,
            'roles': roles,
            'db_type': 'mongodb'
        })

    except RuntimeError:
        pass

    # If both failed, return hardcoded system roles
    system_roles = []
    for role_name, perms in ROLE_PERMISSIONS.items():
        system_roles.append({
            'name': role_name,
            'display_name': role_name.capitalize(),
            'permissions': perms,
            'is_system': True
        })

    return jsonify({
        'success': True,
        'roles': system_roles,
        'db_type': 'fallback'
    })


@api.route('/roles', methods=['POST'])
@require_auth
@require_permission('users.manage')
def create_role():
    """Create a new custom role"""
    data = request.get_json()

    name = data.get('name')
    display_name = data.get('display_name')
    description = data.get('description')
    permissions = data.get('permissions', [])

    if not name:
        return jsonify({
            'success': False,
            'error': 'Role name is required'
        }), 400

    # Validate name format (alphanumeric + underscore only)
    if not name.replace('_', '').isalnum():
        return jsonify({
            'success': False,
            'error': 'Role name must be alphanumeric (underscore allowed)'
        }), 400

    # Check if it's a system role name
    if name in ROLE_PERMISSIONS:
        return jsonify({
            'success': False,
            'error': 'Cannot create role with system role name'
        }), 400

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import CustomRole

        # Check if role exists
        existing = session.query(CustomRole).filter_by(name=name).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Role already exists'
            }), 409

        new_role = CustomRole(
            name=name,
            display_name=display_name or name.replace('_', ' ').title(),
            description=description,
            permissions=permissions,
            is_system=False
        )

        session.add(new_role)
        session.commit()

        logger.info(f"Custom role created in PostgreSQL: {name} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Role created successfully',
            'role': new_role.to_dict()
        }), 201

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()

        # Check if role exists
        existing = db.custom_roles.find_one({'name': name})
        if existing:
            return jsonify({
                'success': False,
                'error': 'Role already exists'
            }), 409

        role_doc = {
            'name': name,
            'display_name': display_name or name.replace('_', ' ').title(),
            'description': description,
            'permissions': permissions,
            'is_system': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.custom_roles.insert_one(role_doc)

        logger.info(f"Custom role created in MongoDB: {name} by {request.username}")

        role_doc['id'] = str(result.inserted_id)
        role_doc.pop('_id', None)

        return jsonify({
            'success': True,
            'message': 'Role created successfully',
            'role': role_doc
        }), 201

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503


@api.route('/roles/<role_id>', methods=['PUT'])
@require_auth
@require_permission('users.manage')
def update_role(role_id):
    """Update a custom role"""
    data = request.get_json()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import CustomRole

        role = session.query(CustomRole).filter_by(id=role_id).first()
        if not role:
            return jsonify({
                'success': False,
                'error': 'Role not found'
            }), 404

        # Don't allow editing system roles
        if role.is_system:
            return jsonify({
                'success': False,
                'error': 'Cannot modify system roles'
            }), 403

        # Update fields
        if 'display_name' in data:
            role.display_name = data['display_name']
        if 'description' in data:
            role.description = data['description']
        if 'permissions' in data:
            role.permissions = data['permissions']

        role.updated_at = datetime.utcnow()
        session.commit()

        logger.info(f"Custom role updated in PostgreSQL: {role.name} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Role updated successfully',
            'role': role.to_dict()
        })

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        from bson.objectid import ObjectId

        role = db.custom_roles.find_one({'_id': ObjectId(role_id)})
        if not role:
            return jsonify({
                'success': False,
                'error': 'Role not found'
            }), 404

        # Don't allow editing system roles
        if role.get('is_system', False):
            return jsonify({
                'success': False,
                'error': 'Cannot modify system roles'
            }), 403

        update_data = {
            'updated_at': datetime.utcnow()
        }

        if 'display_name' in data:
            update_data['display_name'] = data['display_name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'permissions' in data:
            update_data['permissions'] = data['permissions']

        db.custom_roles.update_one(
            {'_id': ObjectId(role_id)},
            {'$set': update_data}
        )

        logger.info(f"Custom role updated in MongoDB: {role['name']} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Role updated successfully'
        })

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503


@api.route('/roles/<role_id>', methods=['DELETE'])
@require_auth
@require_permission('users.manage')
def delete_role(role_id):
    """Delete a custom role"""
    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import CustomRole

        role = session.query(CustomRole).filter_by(id=role_id).first()
        if not role:
            return jsonify({
                'success': False,
                'error': 'Role not found'
            }), 404

        # Don't allow deleting system roles
        if role.is_system:
            return jsonify({
                'success': False,
                'error': 'Cannot delete system roles'
            }), 403

        role_name = role.name
        session.delete(role)
        session.commit()

        logger.info(f"Custom role deleted from PostgreSQL: {role_name} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Role deleted successfully'
        })

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        from bson.objectid import ObjectId

        role = db.custom_roles.find_one({'_id': ObjectId(role_id)})
        if not role:
            return jsonify({
                'success': False,
                'error': 'Role not found'
            }), 404

        # Don't allow deleting system roles
        if role.get('is_system', False):
            return jsonify({
                'success': False,
                'error': 'Cannot delete system roles'
            }), 403

        db.custom_roles.delete_one({'_id': ObjectId(role_id)})

        logger.info(f"Custom role deleted from MongoDB: {role['name']} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'Role deleted successfully'
        })

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503
