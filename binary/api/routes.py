"""
API Routes - Centralized API endpoint definitions
"""


class APIRoutes:
    """Centralized API routes handler"""

    def __init__(self, app, controller, rrd_manager, config, db_manager, integration_manager):
        """
        Initialize API Routes

        Args:
            app: Flask application instance
            controller: Suricata controller instance
            rrd_manager: RRD manager for graphs
            config: Configuration object
            db_manager: Database manager instance
            integration_manager: Integration manager instance
        """
        from binary.api.status_controll import StatusControlAPI
        from binary.api.logging import LoggingAPI
        from binary.api.rules import RulesAPI
        from binary.api.config import ConfigAPI
        from binary.api.integrations import IntegrationsAPI
        from binary.api.suricata import SuricataConfigAPI
        from binary.api.monitor import MonitorAPI
        from binary.api.database import DatabaseAPI
        from binary.api.debug import DebugAPI
        from binary.api.alerts import AlertsAPI

        self.app = app
        self.controller = controller
        self.rrd_manager = rrd_manager
        self.config = config
        self.db_manager = db_manager
        self.integration_manager = integration_manager

        # Initialize all API modules
        self.alerts_api = AlertsAPI(config)
        self.status_api = StatusControlAPI(controller)
        self.logging_api = LoggingAPI(controller)
        self.rules_api = RulesAPI(controller)
        self.config_api = ConfigAPI(controller)
        self.integrations_api = IntegrationsAPI(integration_manager)
        self.suricata_config_api = SuricataConfigAPI(controller)
        self.monitor_api = MonitorAPI(config, rrd_manager)
        self.database_api = DatabaseAPI(db_manager, self.alerts_api)
        self.debug_api = DebugAPI(self.monitor_api)

        # Register all routes
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""
        # Status & Control APIs
        self.app.add_url_rule('/api/status', 'api_status', self.status_api.get_status)
        self.app.add_url_rule('/api/start', 'api_start', self.status_api.start_suricata, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'api_stop', self.status_api.stop_suricata, methods=['POST'])
        self.app.add_url_rule('/api/restart', 'api_restart', self.status_api.restart_suricata, methods=['POST'])
        self.app.add_url_rule('/api/reload-rules', 'api_reload_rules', self.status_api.reload_rules, methods=['POST'])

        # Logs API
        self.app.add_url_rule('/api/logs', 'api_logs', self.logging_api.get_logs)

        # Rules API
        self.app.add_url_rule('/api/rules', 'api_rules', self.rules_api.get_rules)

        # Config API
        self.app.add_url_rule('/api/config', 'api_config_get', self.config_api.get_config, methods=['GET'])
        self.app.add_url_rule('/api/config', 'api_config_post', self.config_api.save_config, methods=['POST'])

        # Integration APIs
        self.app.add_url_rule('/api/integration', 'api_integration_get_all', self.integrations_api.get_integrations, methods=['GET'])
        self.app.add_url_rule('/api/integration/<integration_name>', 'api_integration_get', self.integrations_api.get_integration, methods=['GET'])
        self.app.add_url_rule('/api/integration/<integration_name>', 'api_integration_save', self.integrations_api.save_integration, methods=['POST'])
        self.app.add_url_rule('/api/integration/<integration_name>/test', 'api_integration_test', self.integrations_api.test_integration, methods=['POST'])
        self.app.add_url_rule('/api/integration/<integration_name>/template', 'api_integration_template', self.integrations_api.save_template, methods=['POST'])

        # Suricata Config APIs (Advanced Configuration)
        self.app.add_url_rule('/api/suricata-config/app-layer', 'api_config_app_layer_get', self.suricata_config_api.get_app_layer_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/app-layer', 'api_config_app_layer_update', self.suricata_config_api.update_app_layer_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/outputs', 'api_config_outputs_get', self.suricata_config_api.get_outputs_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/outputs', 'api_config_outputs_update', self.suricata_config_api.update_outputs_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/af-packet', 'api_config_af_packet_get', self.suricata_config_api.get_af_packet_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/af-packet', 'api_config_af_packet_update', self.suricata_config_api.update_af_packet_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/stream', 'api_config_stream_get', self.suricata_config_api.get_stream_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/stream', 'api_config_stream_update', self.suricata_config_api.update_stream_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/vars', 'api_config_vars_get', self.suricata_config_api.get_vars_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/vars', 'api_config_vars_update', self.suricata_config_api.update_vars_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/logging', 'api_config_logging_get', self.suricata_config_api.get_logging_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/logging', 'api_config_logging_update', self.suricata_config_api.update_logging_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/detection', 'api_config_detection_get', self.suricata_config_api.get_detection_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/detection', 'api_config_detection_update', self.suricata_config_api.update_detection_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/host', 'api_config_host_get', self.suricata_config_api.get_host_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/host', 'api_config_host_update', self.suricata_config_api.update_host_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/ips', 'api_config_ips_get', self.suricata_config_api.get_ips_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/ips', 'api_config_ips_update', self.suricata_config_api.update_ips_config, methods=['POST'])
        self.app.add_url_rule('/api/system/interfaces', 'api_system_interfaces', self.suricata_config_api.get_system_interfaces, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/interfaces', 'api_config_interfaces_get', self.suricata_config_api.get_interfaces_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/interfaces', 'api_config_interfaces_update', self.suricata_config_api.update_interfaces_config, methods=['POST'])

        # Monitor APIs
        self.app.add_url_rule('/api/monitor/data', 'api_monitor_data', self.monitor_api.get_monitor_data)
        self.app.add_url_rule('/api/monitor/graph/<metric>/<timespan>', 'api_monitor_graph', self.monitor_api.get_monitor_graph)

        # Database APIs
        self.app.add_url_rule('/api/database/info', 'api_database_info', self.database_api.get_info)
        self.app.add_url_rule('/api/database/alerts', 'api_database_alerts', self.database_api.get_alerts)
        self.app.add_url_rule('/api/database/stats', 'api_database_stats', self.database_api.get_stats)
        self.app.add_url_rule('/api/database/check', 'api_database_check', self.database_api.check_connection)
        self.app.add_url_rule('/api/database/traffic/latest', 'api_traffic_latest', self.database_api.get_latest_traffic)
        self.app.add_url_rule('/api/database/traffic/recent', 'api_traffic_recent', self.database_api.get_recent_traffic)
        self.app.add_url_rule('/api/database/reset-counter', 'api_reset_counter', self.database_api.reset_counter, methods=['POST'])

        # Debug APIs
        self.app.add_url_rule('/api/debug/eve', 'api_debug_eve', self.debug_api.debug_eve)
