"""
Authentication API
JWT token generation and validation
"""

from flask import request, jsonify, g
from functools import wraps
import jwt
import bcrypt
import hashlib
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.models import User, Agent
from binary.dashboard.database import get_pg_session, get_mongo_db
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key')
JWT_EXPIRATION_HOURS = 24
ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'False').lower() == 'true'

def get_user_from_db(username):
    """Get user from PostgreSQL or MongoDB (fallback)"""
    # Try PostgreSQL first
    try:
        session = get_pg_session()
        user = session.query(User).filter_by(username=username, is_active=True).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role,
                'is_active': user.is_active
            }, session
    except RuntimeError:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        user = db.users.find_one({'username': username, 'is_active': True})
        if user:
            return {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user.get('email'),
                'password_hash': user['password_hash'],
                'role': user.get('role', 'viewer'),
                'is_active': user.get('is_active', True)
            }, None
    except RuntimeError:
        pass

    return None, None

def update_last_login(user_id, session=None):
    """Update last login timestamp"""
    if session:
        # PostgreSQL
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        except:
            pass
    else:
        # MongoDB
        try:
            db = get_mongo_db()
            from bson.objectid import ObjectId
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
        except:
            pass

def generate_jwt(user):
    """Generate JWT token for user (accepts dict or User object)"""
    if isinstance(user, dict):
        user_id = user['id']
        username = user['username']
        role = user.get('role', 'viewer')
        custom_permissions = user.get('permissions', {})
    else:
        user_id = user.id
        username = user.username
        role = user.role
        custom_permissions = user.permissions if hasattr(user, 'permissions') else {}

    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'custom_permissions': custom_permissions,
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
        if not ENABLE_AUTH:
            # PUBLIC ACCESS MODE - No authentication required
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'
            # Set g.user for permission checks
            g.user = {
                'id': 'public',
                'username': 'public',
                'role': 'admin',
                'custom_permissions': None
            }
            return f(*args, **kwargs)

        # AUTH ENABLED - Check for JWT token
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'success': False, 'error': 'No authorization token'}), 401

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        payload = validate_jwt(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401

        # Attach user info to request (legacy)
        request.user_id = payload['user_id']
        request.username = payload['username']
        request.user_role = payload.get('role', 'viewer')

        # Set g.user for permission checks (new)
        g.user = {
            'id': payload['user_id'],
            'username': payload['username'],
            'role': payload.get('role', 'viewer'),
            'custom_permissions': payload.get('custom_permissions', None)
        }

        return f(*args, **kwargs)

    return decorated_function

def require_agent_auth(f):
    """Decorator to require agent authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support both old format (X-Agent-Token + X-Agent-ID) and new format (Bearer token)
        encrypted_token = request.headers.get('X-Agent-Token')
        agent_id = request.headers.get('X-Agent-ID')

        # New format: Authorization Bearer token
        auth_header = request.headers.get('Authorization')

        if not encrypted_token and auth_header and auth_header.startswith('Bearer '):
            # Extract token from Authorization header
            plain_token = auth_header.replace('Bearer ', '')

            # Hash token to find agent
            token_hash = hashlib.sha256(plain_token.encode()).hexdigest()

            agent = None

            # Try PostgreSQL first
            try:
                session = get_pg_session()
                agent = session.query(Agent).filter_by(token_hash=token_hash).first()
            except RuntimeError:
                # PostgreSQL not available, try MongoDB
                pass
            except Exception as e:
                # Other error, log but continue to MongoDB
                pass

            # Try MongoDB fallback if PostgreSQL failed or agent not found
            if not agent:
                try:
                    db = get_mongo_db()
                    agent_doc = db.agents.find_one({'token_hash': token_hash})
                    if agent_doc:
                        # Convert MongoDB doc to agent-like object
                        class AgentObj:
                            def __init__(self, doc):
                                self.id = str(doc['_id'])
                                self.name = doc.get('name')
                                self.encryption_key = doc.get('encryption_key')
                        agent = AgentObj(agent_doc)
                except RuntimeError:
                    # MongoDB not available either
                    pass
                except Exception:
                    pass

            if not agent:
                return jsonify({'success': False, 'error': 'Agent not found'}), 401

            # Attach agent info to request
            request.agent_id = agent.id
            request.agent = agent

            return f(*args, **kwargs)

        # Old format: X-Agent-Token + X-Agent-ID
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
    # If auth is disabled, reject login attempts
    if not ENABLE_AUTH:
        return jsonify({
            'success': False,
            'error': 'Authentication is disabled'
        }), 400

    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Username and password required'
        }), 400

    # Get user from database (PostgreSQL or MongoDB)
    user, session = get_user_from_db(username)

    if not user:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    # Verify password
    if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    # Update last login
    update_last_login(user['id'], session)

    # Generate token
    token = generate_jwt(user)

    # Create session record
    try:
        from binary.dashboard.api.sessions import create_session
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        create_session(user['id'], token, ip_address, user_agent)
    except Exception as e:
        print(f"Failed to create session record: {e}")
        # Continue even if session creation fails

    return jsonify({
        'success': True,
        'token': token,
        'expires_in': JWT_EXPIRATION_HOURS * 3600,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user.get('email'),
            'role': user['role']
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
