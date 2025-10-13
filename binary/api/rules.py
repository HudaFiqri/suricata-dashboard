"""
Rules API - Handles Suricata rules management
"""
from flask import jsonify


class RulesAPI:
    """API for managing Suricata rules"""

    def __init__(self, controller):
        self.controller = controller

    def get_rules(self):
        """Get Suricata rules"""
        try:
            rules = self.controller.rule_manager.get_rule_files()
            return jsonify({'rules': rules})
        except Exception as e:
            return jsonify({'error': str(e)})
