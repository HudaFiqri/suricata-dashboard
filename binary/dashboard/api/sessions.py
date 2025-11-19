"""
Session Management API
Manage user sessions, view active sessions, force logout
"""

from flask import request, jsonify
from datetime import datetime, timedelta
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth
from binary.dashboard.models import UserSession, User
from binary.dashboard.database import get_pg_session, get_mongo_db
from user_agents import parse
import hashlib


def create_session(user_id, token, ip_address=None, user_agent_string=None):
    """Create a new session record"""
    # Hash the token for storage
    session_token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Parse user agent
    device_type = None
    browser = None
    os = None

    if user_agent_string:
        try:
            ua = parse(user_agent_string)
            device_type = 'mobile' if ua.is_mobile else ('tablet' if ua.is_tablet else 'desktop')
            browser = f"{ua.browser.family} {ua.browser.version_string}"
            os = f"{ua.os.family} {ua.os.version_string}"
        except:
            pass

    # Expiration (24 hours from now)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        user_session = UserSession(
            user_id=user_id,
            session_token=session_token_hash,
            ip_address=ip_address,
            user_agent=user_agent_string,
            device_type=device_type,
            browser=browser,
            os=os,
            is_active=True,
            expires_at=expires_at
        )
        session.add(user_session)
        session.commit()
        return user_session.id
    except RuntimeError:
        pass
    except Exception as e:
        print(f"PostgreSQL session creation failed: {e}")
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        session_doc = {
            'user_id': user_id,
            'session_token': session_token_hash,
            'ip_address': ip_address,
            'user_agent': user_agent_string,
            'device_type': device_type,
            'browser': browser,
            'os': os,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'expires_at': expires_at,
            'logged_out_at': None
        }
        result = db.user_sessions.insert_one(session_doc)
        return str(result.inserted_id)
    except:
        pass

    return None


def update_session_activity(token):
    """Update last activity timestamp for a session"""
    session_token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Try PostgreSQL
    try:
        session = get_pg_session()
        user_session = session.query(UserSession).filter_by(
            session_token=session_token_hash,
            is_active=True
        ).first()
        if user_session:
            user_session.last_activity = datetime.utcnow()
            session.commit()
            return
    except:
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        db.user_sessions.update_one(
            {'session_token': session_token_hash, 'is_active': True},
            {'$set': {'last_activity': datetime.utcnow()}}
        )
    except:
        pass


@api.route('/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Get all active sessions for current user"""
    user_id = request.user_id

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        sessions = session.query(UserSession).filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(UserSession.last_activity.desc()).all()

        return jsonify({
            'success': True,
            'sessions': [s.to_dict() for s in sessions]
        })
    except RuntimeError:
        pass
    except Exception as e:
        print(f"PostgreSQL get sessions failed: {e}")
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        sessions = list(db.user_sessions.find({
            'user_id': user_id,
            'is_active': True
        }).sort('last_activity', -1))

        # Convert MongoDB documents to dict
        result = []
        for s in sessions:
            result.append({
                'id': str(s['_id']),
                'user_id': s['user_id'],
                'ip_address': s.get('ip_address'),
                'user_agent': s.get('user_agent'),
                'device_type': s.get('device_type'),
                'browser': s.get('browser'),
                'os': s.get('os'),
                'is_active': s.get('is_active'),
                'created_at': s['created_at'].isoformat() if s.get('created_at') else None,
                'last_activity': s['last_activity'].isoformat() if s.get('last_activity') else None,
                'expires_at': s['expires_at'].isoformat() if s.get('expires_at') else None,
                'logged_out_at': s['logged_out_at'].isoformat() if s.get('logged_out_at') else None
            })

        return jsonify({
            'success': True,
            'sessions': result
        })
    except Exception as e:
        print(f"MongoDB get sessions failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/sessions/<int:session_id>', methods=['DELETE'])
@require_auth
def logout_session(session_id):
    """Force logout a specific session"""
    user_id = request.user_id

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        user_session = session.query(UserSession).filter_by(
            id=session_id,
            user_id=user_id
        ).first()

        if not user_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        user_session.is_active = False
        user_session.logged_out_at = datetime.utcnow()
        session.commit()

        return jsonify({
            'success': True,
            'message': 'Session logged out successfully'
        })
    except RuntimeError:
        pass
    except Exception as e:
        print(f"PostgreSQL logout session failed: {e}")
        pass

    # Fallback to MongoDB
    try:
        from bson.objectid import ObjectId
        db = get_mongo_db()

        result = db.user_sessions.update_one(
            {'_id': ObjectId(session_id), 'user_id': user_id},
            {'$set': {
                'is_active': False,
                'logged_out_at': datetime.utcnow()
            }}
        )

        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Session logged out successfully'
        })
    except Exception as e:
        print(f"MongoDB logout session failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/sessions/logout-all', methods=['POST'])
@require_auth
def logout_all_sessions():
    """Force logout all sessions except current one"""
    user_id = request.user_id

    # Get current session token from request
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    current_session_hash = hashlib.sha256(token.encode()).hexdigest()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        sessions = session.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.session_token != current_session_hash
        ).all()

        count = 0
        for s in sessions:
            s.is_active = False
            s.logged_out_at = datetime.utcnow()
            count += 1

        session.commit()

        return jsonify({
            'success': True,
            'message': f'Logged out {count} sessions'
        })
    except RuntimeError:
        pass
    except Exception as e:
        print(f"PostgreSQL logout all sessions failed: {e}")
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        result = db.user_sessions.update_many(
            {
                'user_id': user_id,
                'is_active': True,
                'session_token': {'$ne': current_session_hash}
            },
            {'$set': {
                'is_active': False,
                'logged_out_at': datetime.utcnow()
            }}
        )

        return jsonify({
            'success': True,
            'message': f'Logged out {result.modified_count} sessions'
        })
    except Exception as e:
        print(f"MongoDB logout all sessions failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/sessions/cleanup', methods=['POST'])
@require_auth
def cleanup_expired_sessions():
    """Cleanup expired sessions (admin only)"""
    if request.user_role != 'admin':
        return jsonify({
            'success': False,
            'error': 'Admin access required'
        }), 403

    now = datetime.utcnow()

    # Try PostgreSQL first
    try:
        session = get_pg_session()
        expired_sessions = session.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at < now
        ).all()

        count = 0
        for s in expired_sessions:
            s.is_active = False
            s.logged_out_at = now
            count += 1

        session.commit()

        return jsonify({
            'success': True,
            'message': f'Cleaned up {count} expired sessions'
        })
    except RuntimeError:
        pass
    except Exception as e:
        print(f"PostgreSQL cleanup failed: {e}")
        pass

    # Fallback to MongoDB
    try:
        db = get_mongo_db()
        result = db.user_sessions.update_many(
            {
                'is_active': True,
                'expires_at': {'$lt': now}
            },
            {'$set': {
                'is_active': False,
                'logged_out_at': now
            }}
        )

        return jsonify({
            'success': True,
            'message': f'Cleaned up {result.modified_count} expired sessions'
        })
    except Exception as e:
        print(f"MongoDB cleanup failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
