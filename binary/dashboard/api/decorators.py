"""
API Decorators
Authentication and permission decorators for API endpoints
"""

from functools import wraps
from flask import request, jsonify, g
from binary.dashboard.permissions import has_permission
import logging

logger = logging.getLogger(__name__)


def require_permission(permission):
    """
    Decorator to require specific permission for an endpoint

    Usage:
        @api.route('/agents', methods=['POST'])
        @require_auth
        @require_permission('agents.manage')
        def create_agent():
            pass

    Args:
        permission: Permission string (e.g., 'agents.manage')

    Returns:
        Decorator function that checks if user has required permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated (should be set by @require_auth)
            if not hasattr(g, 'user'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

            user = g.user
            user_role = user.get('role', 'viewer')
            custom_permissions = user.get('custom_permissions', None)

            # Check if user has permission
            if not has_permission(user_role, permission, custom_permissions):
                logger.warning(f"Permission denied: User {user.get('username')} attempted to access {permission}")
                return jsonify({
                    'success': False,
                    'error': f'Permission denied: {permission} required',
                    'required_permission': permission
                }), 403

            # User has permission, proceed
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_any_permission(*permissions):
    """
    Decorator to require ANY of the specified permissions

    Usage:
        @require_any_permission('users.view', 'users.manage')
        def view_user():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

            user = g.user
            user_role = user.get('role', 'viewer')
            custom_permissions = user.get('custom_permissions', None)

            # Check if user has ANY of the permissions
            has_any = False
            for permission in permissions:
                if has_permission(user_role, permission, custom_permissions):
                    has_any = True
                    break

            if not has_any:
                logger.warning(f"Permission denied: User {user.get('username')} needs one of {permissions}")
                return jsonify({
                    'success': False,
                    'error': f'Permission denied: One of {permissions} required',
                    'required_permissions': list(permissions)
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def require_all_permissions(*permissions):
    """
    Decorator to require ALL of the specified permissions

    Usage:
        @require_all_permissions('events.view', 'events.export')
        def export_events():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401

            user = g.user
            user_role = user.get('role', 'viewer')
            custom_permissions = user.get('custom_permissions', None)

            # Check if user has ALL of the permissions
            missing = []
            for permission in permissions:
                if not has_permission(user_role, permission, custom_permissions):
                    missing.append(permission)

            if missing:
                logger.warning(f"Permission denied: User {user.get('username')} missing {missing}")
                return jsonify({
                    'success': False,
                    'error': f'Permission denied: Missing {missing}',
                    'missing_permissions': missing
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator
