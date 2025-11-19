"""
Role-Based Access Control (RBAC) System
Permission definitions and role mappings
"""

# Permission definitions
PERMISSIONS = {
    # Agent permissions
    'agents.view': 'View agents',
    'agents.manage': 'Add, edit, delete agents',

    # Event permissions
    'events.view': 'View events and alerts',
    'events.export': 'Export events data',

    # Configuration permissions
    'configs.view': 'View configurations',
    'configs.edit': 'Edit configurations',

    # User management permissions
    'users.view': 'View users',
    'users.manage': 'Add, edit, delete users',

    # Session management permissions
    'sessions.view': 'View active sessions',
    'sessions.manage': 'Manage and logout sessions',

    # Statistics permissions
    'stats.view': 'View statistics and analytics',

    # Logs permissions
    'logs.view': 'View logs',
}

# Role definitions with their permissions
ROLE_PERMISSIONS = {
    'admin': [
        # Full access to everything
        'agents.view',
        'agents.manage',
        'events.view',
        'events.export',
        'configs.view',
        'configs.edit',
        'users.view',
        'users.manage',
        'sessions.view',
        'sessions.manage',
        'stats.view',
        'logs.view',
    ],

    'operator': [
        # Can manage agents and configs, but NOT users
        'agents.view',
        'agents.manage',
        'events.view',
        'events.export',
        'configs.view',
        'configs.edit',
        'stats.view',
        'logs.view',
    ],

    'analyst': [
        # Read-only + export capabilities
        'agents.view',
        'events.view',
        'events.export',
        'configs.view',
        'stats.view',
        'logs.view',
    ],

    'viewer': [
        # Read-only access
        'agents.view',
        'events.view',
        'stats.view',
        'logs.view',
    ],
}


def get_role_permissions(role: str) -> list:
    """Get permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(user_role: str, permission: str, custom_permissions: list = None) -> bool:
    """
    Check if a user has a specific permission

    Args:
        user_role: User's role (admin, operator, analyst, viewer)
        permission: Permission to check (e.g., 'agents.manage')
        custom_permissions: Optional custom permissions list for user

    Returns:
        bool: True if user has permission
    """
    # Custom permissions override role permissions
    if custom_permissions:
        return permission in custom_permissions

    # Check role-based permissions
    role_perms = get_role_permissions(user_role)
    return permission in role_perms


def get_all_permissions() -> dict:
    """Get all available permissions"""
    return PERMISSIONS


def get_role_list() -> list:
    """Get list of available roles"""
    return list(ROLE_PERMISSIONS.keys())
