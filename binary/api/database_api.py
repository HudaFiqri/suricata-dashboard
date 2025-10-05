"""
Database API - Handles database connection checks and info
"""
from flask import jsonify


class DatabaseAPI:
    """API for database operations"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def check_connection(self):
        """Check database connection status"""
        try:
            db_info = self.db_manager.get_db_info()
            is_connected = db_info.get('connected', False)

            return {
                'success': True,
                'connected': is_connected,
                'database_type': db_info.get('type'),
                'database_url': db_info.get('url'),
                'message': 'Database connected successfully' if is_connected else 'Database connection failed'
            }
        except Exception as e:
            return {
                'success': False,
                'connected': False,
                'message': f'Database check error: {str(e)}'
            }

    def get_info(self):
        """Get database information"""
        return self.db_manager.get_db_info()

    def get_stats(self):
        """Get latest statistics from database"""
        return self.db_manager.get_latest_stats()
