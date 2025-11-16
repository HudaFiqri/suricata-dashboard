"""
Database API - Handles database connection checks and traffic statistics
"""
from flask import jsonify, request
from datetime import datetime, timedelta
import hashlib


class DatabaseAPI:
    """API for database operations"""

    def __init__(self, db_manager, alerts_api):
        self.db_manager = db_manager
        self.alerts_api = alerts_api

    def _is_db_available(self):
        """Check if database is available and connected"""
        if not self.db_manager:
            return False
        return not getattr(self.db_manager, 'connection_failed', False)

    def check_connection(self):
        """Check database connection status"""
        try:
            if not self.db_manager:
                return jsonify({
                    'success': False,
                    'connected': False,
                    'message': 'Database manager not initialized'
                })

            db_info = self.db_manager.get_db_info()
            is_connected = db_info.get('connected', False) and self._is_db_available()

            raw_type = db_info.get('type')
            hashed_type = hashlib.md5(raw_type.encode()).hexdigest() if raw_type else None

            return jsonify({
                'success': True,
                'connected': is_connected,
                'database_type': hashed_type,
                'database_url': db_info.get('url'),
                'message': 'Database connected successfully' if is_connected else 'Database connection failed',
                'error': getattr(self.db_manager, 'connection_error', None) if not is_connected else None
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'connected': False,
                'message': f'Database check error: {str(e)}'
            })

    def get_info(self):
        """Get database information"""
        return jsonify(self.db_manager.get_db_info())

    def get_alerts(self):
        """Get all events from eve.json"""
        limit = request.args.get('limit', 100, type=int)
        category = request.args.get('category', None)
        protocol = request.args.get('protocol', None)
        return jsonify(self.alerts_api.get_all_events(limit, category, protocol))

    def get_stats(self):
        """Get latest statistics from database"""
        if not self._is_db_available():
            return jsonify({
                'success': False,
                'error': 'Database not available',
                'message': 'Database connection is not available. Statistics cannot be retrieved.'
            })
        try:
            return jsonify(self.db_manager.get_latest_stats())
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    def get_latest_traffic(self):
        """Get latest traffic statistics from database"""
        if not self._is_db_available():
            return jsonify({
                'success': False,
                'error': 'Database not available',
                'message': 'Database connection is not available. Traffic statistics cannot be retrieved.'
            })
        try:
            stats = self.db_manager.get_latest_traffic_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    def get_recent_traffic(self):
        """Get recent traffic statistics from database"""
        if not self._is_db_available():
            return jsonify({
                'success': False,
                'error': 'Database not available',
                'message': 'Database connection is not available. Traffic statistics cannot be retrieved.'
            })
        try:
            limit = request.args.get('limit', 20, type=int)
            protocol = request.args.get('protocol', None)
            hours = request.args.get('hours', 24, type=int)

            start_time = datetime.utcnow() - timedelta(hours=hours)

            stats = self.db_manager.get_traffic_stats(
                protocol=protocol,
                start_time=start_time,
                limit=limit
            )

            return jsonify({
                'success': True,
                'stats': [stat.to_dict() for stat in stats]
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    def reset_counter(self):
        """Reset traffic counter - delete all traffic statistics"""
        if not self._is_db_available():
            return jsonify({
                'success': False,
                'error': 'Database not available',
                'message': 'Database connection is not available. Cannot reset counter.'
            })
        try:
            result = self.db_manager.reset_traffic_stats()
            return jsonify({
                'success': True,
                'message': f'Successfully reset traffic counter. Deleted {result} records.'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to reset counter: {str(e)}'
            })
