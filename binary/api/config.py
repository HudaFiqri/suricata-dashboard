"""
Config API - Handles Suricata configuration
"""
from flask import jsonify, request


class ConfigAPI:
    """API for managing Suricata configuration"""

    def __init__(self, controller):
        self.controller = controller

    def get_config(self):
        """Get Suricata configuration"""
        try:
            import yaml
            config_data = self.controller.config.load()
            config_string = yaml.dump(config_data, default_flow_style=False, indent=2)
            return jsonify({'config': config_string})
        except Exception as e:
            return jsonify({'error': str(e)})

    def save_config(self):
        """Save Suricata configuration"""
        try:
            import yaml
            config_content = request.json.get('config', '')
            config_data = yaml.safe_load(config_content)
            self.controller.config.save(config_data)
            return jsonify({'success': True, 'message': 'Configuration saved successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
