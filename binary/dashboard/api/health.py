"""
Health Check API
System health and status monitoring
"""

from flask import jsonify
from binary.dashboard.api import api
from binary.dashboard.database import health_check, get_pg_session, get_mongo_db
from binary.dashboard.websocket.sessions import session_manager
import logging

logger = logging.getLogger(__name__)

@api.route('/health', methods=['GET'])
def health():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'suricata-dashboard'
    })

@api.route('/health/db', methods=['GET'])
def health_db():
    """Database health check"""
    db_health = health_check()

    status = 'healthy' if all(db_health.values()) else 'degraded'

    return jsonify({
        'status': status,
        'databases': db_health
    }), 200 if status == 'healthy' else 503

@api.route('/health/websocket', methods=['GET'])
def health_websocket():
    """WebSocket health check"""
    try:
        stats = session_manager.get_stats()

        return jsonify({
            'status': 'healthy',
            'connections': {
                'total': stats['total_connections'],
                'agents': stats['agent_connections'],
                'ui': stats['ui_connections']
            },
            'active_agents': len(stats['active_agents']),
            'active_ui_clients': len(stats['active_ui_clients'])
        })
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api.route('/health/full', methods=['GET'])
def health_full():
    """Complete health check"""
    db_health = health_check()
    ws_stats = session_manager.get_stats()

    # Check database
    db_status = 'healthy' if all(db_health.values()) else 'degraded'

    # Overall status
    overall_status = 'healthy' if db_status == 'healthy' else 'degraded'

    return jsonify({
        'status': overall_status,
        'components': {
            'database': {
                'status': db_status,
                'postgresql': db_health['postgresql'],
                'mongodb': db_health['mongodb']
            },
            'websocket': {
                'status': 'healthy',
                'total_connections': ws_stats['total_connections'],
                'agent_connections': ws_stats['agent_connections'],
                'ui_connections': ws_stats['ui_connections']
            }
        }
    }), 200 if overall_status == 'healthy' else 503
