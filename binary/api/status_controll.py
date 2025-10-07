"""
Status Control API - Handles Suricata service control
"""
from flask import jsonify


class StatusControlAPI:
    """API for controlling Suricata service status"""

    def __init__(self, controller):
        self.controller = controller

    def get_status(self):
        """Get Suricata status"""
        return jsonify(self.controller.get_status())

    def start_suricata(self):
        """Start Suricata"""
        return jsonify(self.controller.start())

    def stop_suricata(self):
        """Stop Suricata"""
        return jsonify(self.controller.stop())

    def restart_suricata(self):
        """Restart Suricata"""
        return jsonify(self.controller.restart())

    def reload_rules(self):
        """Reload Suricata rules"""
        return jsonify(self.controller.reload_rules())
