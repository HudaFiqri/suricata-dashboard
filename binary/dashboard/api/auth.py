"""
Authentication API
JWT token generation and validation
"""

from flask import request, jsonify
from functools import wraps
import jwt
import bcrypt
import hashlib
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.models import User, Agent
from binary.dashboard.database import get_pg_session
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
JWT_EXPIRATION_HOURS = 24

def generate_jwt(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def validate_jwt(token):
    """Validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'success': False, 'error': 'No authorization header'}), 401

        try:
            # Bearer token format
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = validate_jwt(token)

            if not payload:
                return jsonify({'success': False, 'error': 'Invalid token'}), 401

            # Attach user info to request
            request.user_id = payload['user_id']
            request.username = payload['username']
            request.user_role = payload['role']

        except Exception as e:
            return jsonify({'success': False, 'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)

    return decorated_function

def require_agent_auth(f):
    """Decorator to require agent authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        encrypted_token = request.headers.get('X-Agent-Token')
        agent_id = request.headers.get('X-Agent-ID')

        if not encrypted_token or not agent_id:
            return jsonify({'success': False, 'error': 'Missing agent credentials'}), 401

        try:
            session = get_pg_session()
            agent = session.query(Agent).filter_by(id=int(agent_id)).first()

            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 401

            # TODO: Decrypt and validate token
            # For now, basic validation

            # Attach agent info to request
            request.agent_id = agent.id
            request.agent = agent

        except Exception as e:
            return jsonify({'success': False, 'error': 'Agent authentication failed'}), 401

        return f(*args, **kwargs)

    return decorated_function

@api.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password required'
        }), 400

    session = get_pg_session()
    user = session.query(User).filter_by(username=username, is_active=True).first()

    if not user:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    # Verify password
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    # Update last login
    user.last_login = datetime.utcnow()
    session.commit()

    # Generate token
    token = generate_jwt(user)

    return jsonify({
        'success': True,
        'token': token,
        'expires_in': JWT_EXPIRATION_HOURS * 3600,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@api.route('/auth/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """Refresh JWT token"""
    session = get_pg_session()
    user = session.query(User).filter_by(id=request.user_id).first()

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Generate new token
    token = generate_jwt(user)

    return jsonify({
        'success': True,
        'token': token,
        'expires_in': JWT_EXPIRATION_HOURS * 3600
    })

@api.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    session = get_pg_session()
    user = session.query(User).filter_by(id=request.user_id).first()

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from binary.dashboard.database import health_check as db_health_check

    db_health = db_health_check()

    return jsonify({
        'success': True,
        'status': 'healthy' if all(db_health.values()) else 'degraded',
        'databases': db_health,
        'timestamp': datetime.utcnow().isoformat()
    })
