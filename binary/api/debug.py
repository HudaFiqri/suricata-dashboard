"""
Debug API - Handles debug endpoints
"""
from flask import jsonify


class DebugAPI:
    """API for debug operations"""

    def __init__(self, monitor_api):
        self.monitor_api = monitor_api

    def debug_eve(self):
        """Debug endpoint to check eve.json"""
        return jsonify(self.monitor_api.get_debug_info())
