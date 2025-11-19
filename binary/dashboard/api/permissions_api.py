"""
Permissions API
Endpoints for viewing and managing permissions
"""

from flask import request, jsonify
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.api.decorators import require_permission
from binary.dashboard.permissions import (
    get_all_permissions,
    get_role_list,
    get_role_permissions,
    ROLE_PERMISSIONS
)

@api.route('/permissions', methods=['GET'])
@require_auth
def list_permissions():
    """Get all available permissions"""
    return jsonify({
        'success': True,
        'permissions': get_all_permissions()
    })

@api.route('/permissions/roles', methods=['GET'])
@require_auth
def list_roles():
    """Get all available roles with their permissions"""
    roles = {}
    for role in get_role_list():
        roles[role] = get_role_permissions(role)

    return jsonify({
        'success': True,
        'roles': roles
    })

@api.route('/permissions/roles/<role>', methods=['GET'])
@require_auth
def get_role_info(role):
    """Get permissions for a specific role"""
    if role not in ROLE_PERMISSIONS:
        return jsonify({
            'success': False,
            'error': 'Invalid role'
        }), 404

    return jsonify({
        'success': True,
        'role': role,
        'permissions': get_role_permissions(role)
    })
