"""
User Management API
Endpoints for user CRUD operations
"""

from flask import request, jsonify
from datetime import datetime
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.database import get_pg_session, get_mongo_db
import bcrypt
import logging
import os

logger = logging.getLogger(__name__)

def get_all_users():
    """Get all users from PostgreSQL or MongoDB"""
    users = []

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import User

        pg_users = session.query(User).all()
        for user in pg_users:
            users.append(user.to_dict())
        return users, 'postgresql'
    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        mongo_users = db.users.find()
        for user in mongo_users:
            users.append({
                'id': str(user['_id']),
                'username': user['username'],
                'email': user.get('email'),
                'role': user.get('role', 'viewer'),
                'is_active': user.get('is_active', True),
                'last_login': user.get('last_login').isoformat() if user.get('last_login') else None,
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
                'updated_at': user.get('updated_at').isoformat() if user.get('updated_at') else None
            })
        return users, 'mongodb'
    except RuntimeError:
        pass

    return None, None

@api.route('/users', methods=['GET'])
@require_auth
def list_users():
    """List all users"""
    # Check if user is admin
    if request.user_role != 'admin':
        return jsonify({
            'success': False,
            'error': 'Admin access required'
        }), 403

    users, db_type = get_all_users()

    if users is None:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 503

    return jsonify({
        'success': True,
        'users': users,
        'db_type': db_type
    })

@api.route('/users', methods=['POST'])
@require_auth
def create_user():
    """Create new user"""
    # Check if user is admin
    if request.user_role != 'admin':
        return jsonify({
            'success': False,
            'error': 'Admin access required'
        }), 403

    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password are required'
        }), 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import User

        # Check if username exists
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 409

        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True
        )

        session.add(new_user)
        session.commit()

        logger.info(f"User created in PostgreSQL: {username} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()

        # Check if username exists
        existing = db.users.find_one({'username': username})
        if existing:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 409

        user_doc = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.users.insert_one(user_doc)

        logger.info(f"User created in MongoDB: {username} by {request.username}")

        user_doc['id'] = str(result.inserted_id)
        user_doc.pop('_id', None)

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': user_doc
        }), 201

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503

@api.route('/users/<user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user"""
    # Check if user is admin
    if request.user_role != 'admin':
        return jsonify({
            'success': False,
            'error': 'Admin access required'
        }), 403

    data = request.get_json()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import User

        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Update fields
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'password' in data and data['password']:
            user.password_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()

        user.updated_at = datetime.utcnow()
        session.commit()

        logger.info(f"User updated in PostgreSQL: {user.username} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        from bson.objectid import ObjectId

        update_data = {
            'updated_at': datetime.utcnow()
        }

        if 'email' in data:
            update_data['email'] = data['email']
        if 'role' in data:
            update_data['role'] = data['role']
        if 'is_active' in data:
            update_data['is_active'] = data['is_active']
        if 'password' in data and data['password']:
            update_data['password_hash'] = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()

        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        logger.info(f"User updated in MongoDB: {user_id} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503

@api.route('/users/<user_id>', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    """Delete user"""
    # Check if user is admin
    if request.user_role != 'admin':
        return jsonify({
            'success': False,
            'error': 'Admin access required'
        }), 403

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        from binary.dashboard.models import User

        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Don't allow deleting admin user
        if user.username == 'admin':
            return jsonify({
                'success': False,
                'error': 'Cannot delete default admin user'
            }), 403

        username = user.username
        session.delete(user)
        session.commit()

        logger.info(f"User deleted from PostgreSQL: {username} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })

    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        from bson.objectid import ObjectId

        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Don't allow deleting admin user
        if user.get('username') == 'admin':
            return jsonify({
                'success': False,
                'error': 'Cannot delete default admin user'
            }), 403

        db.users.delete_one({'_id': ObjectId(user_id)})

        logger.info(f"User deleted from MongoDB: {user.get('username')} by {request.username}")

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })

    except RuntimeError:
        pass

    return jsonify({
        'success': False,
        'error': 'Database not available'
    }), 503
