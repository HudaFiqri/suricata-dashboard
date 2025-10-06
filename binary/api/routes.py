"""
API Routes - Centralized API endpoint definitions
"""
from flask import request, jsonify, send_file


class APIRoutes:
    """Centralized API routes handler"""

    def __init__(self, app, controller, rrd_manager, monitor_api, alerts_api, database_api, integration_manager):
        self.app = app
        self.controller = controller
        self.rrd_manager = rrd_manager
        self.monitor_api = monitor_api
        self.alerts_api = alerts_api
        self.database_api = database_api
        self.integration_manager = integration_manager
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""
        # Status & Control APIs
        self.app.add_url_rule('/api/status', 'api_status', self.get_status)
        self.app.add_url_rule('/api/start', 'api_start', self.start_suricata, methods=['POST'])
        self.app.add_url_rule('/api/stop', 'api_stop', self.stop_suricata, methods=['POST'])
        self.app.add_url_rule('/api/restart', 'api_restart', self.restart_suricata, methods=['POST'])
        self.app.add_url_rule('/api/reload-rules', 'api_reload_rules', self.reload_rules, methods=['POST'])

        # Logs API
        self.app.add_url_rule('/api/logs', 'api_logs', self.get_logs)

        # Rules API
        self.app.add_url_rule('/api/rules', 'api_rules', self.get_rules)

        # Config API
        self.app.add_url_rule('/api/config', 'api_config_get', self.get_config, methods=['GET'])
        self.app.add_url_rule('/api/config', 'api_config_post', self.save_config, methods=['POST'])

        # Integration APIs
        self.app.add_url_rule('/api/integration', 'api_integration_get_all', self.get_integrations, methods=['GET'])
        self.app.add_url_rule('/api/integration/<integration_name>', 'api_integration_get', self.get_integration, methods=['GET'])
        self.app.add_url_rule('/api/integration/<integration_name>', 'api_integration_save', self.save_integration, methods=['POST'])
        self.app.add_url_rule('/api/integration/<integration_name>/test', 'api_integration_test', self.test_integration, methods=['POST'])
        self.app.add_url_rule('/api/integration/<integration_name>/template', 'api_integration_template', self.save_template, methods=['POST'])

        # Suricata Config APIs
        self.app.add_url_rule('/api/suricata-config/app-layer', 'api_config_app_layer_get', self.get_app_layer_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/app-layer', 'api_config_app_layer_update', self.update_app_layer_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/outputs', 'api_config_outputs_get', self.get_outputs_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/outputs', 'api_config_outputs_update', self.update_outputs_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/af-packet', 'api_config_af_packet_get', self.get_af_packet_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/af-packet', 'api_config_af_packet_update', self.update_af_packet_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/stream', 'api_config_stream_get', self.get_stream_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/stream', 'api_config_stream_update', self.update_stream_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/vars', 'api_config_vars_get', self.get_vars_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/vars', 'api_config_vars_update', self.update_vars_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/logging', 'api_config_logging_get', self.get_logging_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/logging', 'api_config_logging_update', self.update_logging_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/detection', 'api_config_detection_get', self.get_detection_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/detection', 'api_config_detection_update', self.update_detection_config, methods=['POST'])
        self.app.add_url_rule('/api/suricata-config/host', 'api_config_host_get', self.get_host_config, methods=['GET'])
        self.app.add_url_rule('/api/suricata-config/host', 'api_config_host_update', self.update_host_config, methods=['POST'])

        # Monitor APIs
        self.app.add_url_rule('/api/monitor/data', 'api_monitor_data', self.get_monitor_data)
        self.app.add_url_rule('/api/monitor/graph/<metric>/<timespan>', 'api_monitor_graph', self.get_monitor_graph)

        # Database APIs
        self.app.add_url_rule('/api/database/info', 'api_database_info', self.get_database_info)
        self.app.add_url_rule('/api/database/alerts', 'api_database_alerts', self.get_database_alerts)
        self.app.add_url_rule('/api/database/stats', 'api_database_stats', self.get_database_stats)
        self.app.add_url_rule('/api/database/check', 'api_database_check', self.check_database)
        self.app.add_url_rule('/api/database/traffic/latest', 'api_traffic_latest', self.get_latest_traffic)
        self.app.add_url_rule('/api/database/traffic/recent', 'api_traffic_recent', self.get_recent_traffic)
        self.app.add_url_rule('/api/database/reset-counter', 'api_reset_counter', self.reset_counter, methods=['POST'])

        # Debug APIs
        self.app.add_url_rule('/api/debug/eve', 'api_debug_eve', self.debug_eve)

    # ==================== Status & Control ====================
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

    # ==================== Logs ====================
    def get_logs(self):
        """Get Suricata logs"""
        try:
            eve_logs = self.controller.log_manager.get_eve_log(100)

            if eve_logs:
                formatted_logs = self._format_logs(eve_logs)
                return jsonify({'logs': formatted_logs})
            else:
                return jsonify({'logs': []})

        except Exception as e:
            return jsonify({'error': str(e), 'logs': []})

    def _format_logs(self, logs):
        """Format eve.json logs for display"""
        formatted = []
        for log in logs:
            event_type = log.get('event_type', 'unknown')
            timestamp = log.get('timestamp', '')

            if event_type == 'alert':
                alert = log.get('alert', {})
                formatted.append(
                    f"[ALERT] {timestamp} - {alert.get('signature', 'Unknown')} | "
                    f"{log.get('src_ip', '')} -> {log.get('dest_ip', '')} "
                    f"[{log.get('proto', '')}] (Severity: {alert.get('severity', 0)})"
                )
            elif event_type == 'stats':
                formatted.append(f"[STATS] {timestamp} - Statistics Update")
            elif event_type == 'flow':
                src = f"{log.get('src_ip', '')}:{log.get('src_port', '')}"
                dest = f"{log.get('dest_ip', '')}:{log.get('dest_port', '')}"
                service = self._detect_service(log.get('src_port'), log.get('dest_port'))
                formatted.append(f"[FLOW] {timestamp} - {src} -> {dest} [{log.get('proto', '')}]{service}")
            elif event_type == 'http':
                http = log.get('http', {})
                formatted.append(f"[HTTP] {timestamp} - {http.get('hostname', '')}{http.get('url', '')}")
            elif event_type == 'dns':
                dns = log.get('dns', {})
                formatted.append(f"[DNS] {timestamp} - Query: {dns.get('rrname', '')}")
            elif event_type == 'ssh':
                formatted.append(f"[SSH] {timestamp} - {log.get('src_ip', '')} -> {log.get('dest_ip', '')}")
            elif event_type == 'tls':
                tls = log.get('tls', {})
                formatted.append(f"[TLS] {timestamp} - SNI: {tls.get('sni', '')}")
            else:
                formatted.append(f"[{event_type.upper()}] {timestamp}")

        return formatted

    def _detect_service(self, src_port, dest_port):
        """Detect service by port number"""
        services = {
            22: 'SSH', 80: 'HTTP', 443: 'HTTPS', 53: 'DNS',
            67: 'DHCP', 68: 'DHCP', 21: 'FTP', 25: 'SMTP'
        }
        for port in [src_port, dest_port]:
            if port in services:
                return f" ({services[port]})"
        return ''

    # ==================== Rules ====================
    def get_rules(self):
        """Get Suricata rules"""
        try:
            rules = self.controller.rule_manager.get_rule_files()
            return jsonify({'rules': rules})
        except Exception as e:
            return jsonify({'error': str(e)})

    # ==================== Config ====================
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

    # ==================== Integrations ====================
    def get_integrations(self):
        """Get all integration settings"""
        try:
            settings = self.integration_manager.get_settings()
            hashes = self.integration_manager.get_hashes()
            response = {'success': True, 'settings': settings}
            if hashes:
                response['hashes'] = hashes
            return jsonify(response)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_integration(self, integration_name):
        """Get single integration settings"""
        try:
            settings = self.integration_manager.get_integration(integration_name)
            hash_info = self.integration_manager.get_hash(integration_name)
            response = {'success': True, 'settings': settings, 'integration': integration_name.lower()}
            if hash_info:
                response['hash'] = hash_info
            return jsonify(response)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def save_integration(self, integration_name):
        """Save integration configuration"""
        try:
            payload = request.get_json(silent=True) or {}
            settings = self.integration_manager.update_integration(integration_name, payload)
            hash_info = self.integration_manager.get_hash(integration_name)
            response = {'success': True, 'settings': settings, 'integration': integration_name.lower()}
            if hash_info:
                response['hash'] = hash_info
            return jsonify(response)
        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def test_integration(self, integration_name):
        """Send test message to integration"""
        try:
            from binary.integrations.notification_sender import NotificationSender

            payload = request.get_json(silent=True) or {}
            custom_message = payload.get('message', '')

            # Get integration settings
            settings = self.integration_manager.get_integration(integration_name)

            # Create sample alert data for testing
            sample_alert = {
                'alert': {
                    'signature': 'ET SCAN Potential SSH Brute Force Attack',
                    'category': 'Attempted Administrator Privilege Gain',
                    'severity': 2
                },
                'src_ip': '192.168.1.100',
                'src_port': '54321',
                'dest_ip': '10.0.0.50',
                'dest_port': '22',
                'proto': 'TCP',
                'timestamp': '2024-01-15T10:30:45.123456+0000'
            }

            if integration_name.lower() == 'telegram':
                bot_token = settings.get('bot_token', '')
                chat_id = settings.get('chat_id', '')
                template = settings.get('message_template', '')

                if not bot_token or not chat_id:
                    return jsonify({
                        'success': False,
                        'message': 'Please configure Bot Token and Chat ID first'
                    })

                # Use custom message from request, or template from settings, or default
                if custom_message:
                    message = NotificationSender.format_alert_message(sample_alert, custom_message)
                elif template:
                    message = NotificationSender.format_alert_message(sample_alert, template)
                else:
                    message = "🧪 <b>Test Message from Suricata Dashboard</b>\n\nThis is a test notification to verify your Telegram integration is working correctly."

                result = NotificationSender.send_telegram(bot_token, chat_id, message)
                return jsonify(result)

            elif integration_name.lower() == 'discord':
                webhook_url = settings.get('webhook_url', '')
                template = settings.get('message_template', '')

                if not webhook_url:
                    return jsonify({
                        'success': False,
                        'message': 'Please configure Webhook URL first'
                    })

                # Use custom message from request, or template from settings, or default
                if custom_message:
                    message = NotificationSender.format_alert_message(sample_alert, custom_message)
                    title = "🧪 Test Alert Message"
                elif template:
                    message = NotificationSender.format_alert_message(sample_alert, template)
                    title = "🧪 Test Alert Message"
                else:
                    message = "This is a test notification to verify your Discord integration is working correctly."
                    title = "🧪 Test Message from Suricata Dashboard"

                result = NotificationSender.send_discord(webhook_url, message, title)
                return jsonify(result)

            else:
                return jsonify({
                    'success': False,
                    'message': f'Integration {integration_name} not supported for testing'
                }), 404

        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def save_template(self, integration_name):
        """Save custom message template for integration"""
        try:
            payload = request.get_json(silent=True) or {}
            template = payload.get('template', '')

            if not template:
                return jsonify({
                    'success': False,
                    'message': 'Template cannot be empty'
                })

            # Update integration with template
            update_payload = {'message_template': template}
            settings = self.integration_manager.update_integration(integration_name, update_payload)

            return jsonify({
                'success': True,
                'message': 'Message template saved successfully',
                'settings': settings
            })

        except ValueError as exc:
            return jsonify({'success': False, 'message': str(exc)}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ==================== Monitor ====================
    def get_monitor_data(self):
        """Get monitoring data from eve.json"""
        timespan = request.args.get('timespan', '1h')
        return jsonify(self.monitor_api.get_monitor_data(timespan))

    def get_monitor_graph(self, metric, timespan):
        """Generate monitoring graph"""
        result = self.rrd_manager.generate_graph(metric, timespan)
        if result.get('success'):
            return send_file(result['graph_path'], mimetype='image/png')
        else:
            return jsonify(result), 400

    # ==================== Database ====================
    def get_database_info(self):
        """Get database information"""
        return jsonify(self.database_api.get_info())

    def get_database_alerts(self):
        """Get all events from eve.json"""
        limit = request.args.get('limit', 100, type=int)
        category = request.args.get('category', None)
        protocol = request.args.get('protocol', None)
        return jsonify(self.alerts_api.get_all_events(limit, category, protocol))

    def get_database_stats(self):
        """Get latest statistics"""
        return jsonify(self.database_api.get_stats())

    def check_database(self):
        """Check database connection status"""
        return jsonify(self.database_api.check_connection())

    def get_latest_traffic(self):
        """Get latest traffic statistics from database"""
        try:
            # Access db_manager through database_api
            stats = self.database_api.db_manager.get_latest_traffic_stats()
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
        try:
            from datetime import datetime, timedelta

            limit = request.args.get('limit', 20, type=int)
            protocol = request.args.get('protocol', None)
            hours = request.args.get('hours', 24, type=int)

            start_time = datetime.utcnow() - timedelta(hours=hours)

            # Access db_manager through database_api
            stats = self.database_api.db_manager.get_traffic_stats(
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
        """Reset traffic counter"""
        return jsonify(self.database_api.reset_counter())

    # ==================== Debug ====================
    def debug_eve(self):
        """Debug endpoint to check eve.json"""
        return jsonify(self.monitor_api.get_debug_info())

    # ==================== Suricata Config ====================
    def get_app_layer_config(self):
        """Get app-layer protocols configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            # Check if config file exists
            if not os.path.exists(config_path):
                # Return default protocols if config doesn't exist
                default_protocols = {
                    'http': {'enabled': 'yes'},
                    'tls': {'enabled': 'yes'},
                    'dns': {'enabled': 'yes'},
                    'ssh': {'enabled': 'yes'},
                    'smtp': {'enabled': 'yes'},
                    'ftp': {'enabled': 'no'},
                    'smb': {'enabled': 'no'},
                    'dcerpc': {'enabled': 'no'},
                    'dhcp': {'enabled': 'yes'},
                    'nfs': {'enabled': 'no'},
                    'tftp': {'enabled': 'no'},
                    'ikev2': {'enabled': 'no'},
                    'krb5': {'enabled': 'no'},
                    'ntp': {'enabled': 'no'},
                    'snmp': {'enabled': 'no'},
                    'sip': {'enabled': 'no'},
                    'rdp': {'enabled': 'no'},
                    'rfb': {'enabled': 'no'},
                    'mqtt': {'enabled': 'no'},
                    'modbus': {'enabled': 'no'}
                }
                return jsonify({
                    'success': True,
                    'protocols': default_protocols,
                    'warning': f'Config file not found at {config_path}. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            protocols = yaml_manager.get_app_layer_protocols()

            return jsonify({
                'success': True,
                'protocols': protocols
            })

        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'message': f'Config file not found: {str(e)}'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading config: {str(e)}'
            }), 500

    def update_app_layer_config(self):
        """Update app-layer protocols configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            updates = payload.get('protocols', {})

            if not updates:
                return jsonify({
                    'success': False,
                    'message': 'No protocol updates provided'
                }), 400

            config_path = self.controller.config.config_path

            # Check if config file exists
            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Suricata config file not found at {config_path}. Cannot save changes.'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            # Update each protocol
            for protocol, settings in updates.items():
                enabled = settings.get('enabled', False)
                # Remove 'enabled' from settings dict to pass other configs
                protocol_settings = {k: v for k, v in settings.items() if k != 'enabled'}

                yaml_manager.update_app_layer_protocol(
                    protocol,
                    enabled,
                    protocol_settings if protocol_settings else None
                )

            return jsonify({
                'success': True,
                'message': 'App-layer configuration updated successfully. Reload Suricata to apply changes.'
            })

        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'message': f'Config file not found: {str(e)}'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating config: {str(e)}'
            }), 500

    def get_outputs_config(self):
        """Get outputs configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            # Check if config file exists
            if not os.path.exists(config_path):
                # Return default outputs if config doesn't exist
                default_outputs = {
                    'eve-log': {'enabled': 'yes', 'filetype': 'regular'},
                    'unified2-alert': {'enabled': 'no'},
                    'fast': {'enabled': 'yes', 'append': 'yes'},
                    'stats': {'enabled': 'yes'},
                    'http-log': {'enabled': 'no'},
                    'tls-log': {'enabled': 'no'},
                    'dns-log': {'enabled': 'no'},
                    'pcap-log': {'enabled': 'no'}
                }
                return jsonify({
                    'success': True,
                    'outputs': default_outputs,
                    'warning': f'Config file not found at {config_path}. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            outputs = yaml_manager.get_outputs()

            return jsonify({
                'success': True,
                'outputs': outputs
            })

        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'message': f'Config file not found: {str(e)}'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading outputs config: {str(e)}'
            }), 500

    def update_outputs_config(self):
        """Update outputs configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            updates = payload.get('outputs', {})

            if not updates:
                return jsonify({
                    'success': False,
                    'message': 'No output updates provided'
                }), 400

            config_path = self.controller.config.config_path

            # Check if config file exists
            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Suricata config file not found at {config_path}. Cannot save changes.'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            # Update each output
            for output_name, settings in updates.items():
                enabled = settings.get('enabled', False)
                # Remove 'enabled' from settings dict to pass other configs
                output_settings = {k: v for k, v in settings.items() if k != 'enabled'}

                yaml_manager.update_output(
                    output_name,
                    enabled,
                    output_settings if output_settings else None
                )

            return jsonify({
                'success': True,
                'message': 'Outputs configuration updated successfully. Reload Suricata to apply changes.'
            })

        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'message': f'Config file not found: {str(e)}'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating outputs config: {str(e)}'
            }), 500


    def get_af_packet_config(self):
        """Get AF-Packet configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_af_packet = {
                    'interface': 'eth0',
                    'threads': 'auto',
                    'cluster-id': 99,
                    'cluster-type': 'cluster_flow',
                    'defrag': True,
                    'use-mmap': True,
                    'tpacket-v3': True,
                    'promisc': True
                }
                return jsonify({
                    'success': True,
                    'af_packet': default_af_packet,
                    'warning': 'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            af_packet_config = yaml_manager.get_af_packet_config()

            return jsonify({
                'success': True,
                'af_packet': af_packet_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading AF-Packet config: {str(e)}'
            }), 500

    def update_af_packet_config(self):
        """Update AF-Packet configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            settings = payload.get('af_packet') or {}

            if not isinstance(settings, dict) or not settings:
                return jsonify({
                    'success': False,
                    'message': 'No AF-Packet settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            if not yaml_manager.update_af_packet_config(settings):
                return jsonify({
                    'success': False,
                    'message': 'Failed to update AF-Packet configuration'
                }), 500

            return jsonify({
                'success': True,
                'message': 'AF-Packet configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating AF-Packet config: {str(e)}'
            }), 500

    def get_stream_config(self):
        """Get stream configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_stream = {
                    'memcap': '32mb',
                    'checksum-validation': 'auto',
                    'inline': 'auto',
                    'prealloc-sessions': 4096,
                    'reassembly': {
                        'memcap': '64mb',
                        'depth': '1mb',
                        'toserver-chunk-size': 2560,
                        'toclient-chunk-size': 2560
                    }
                }
                return jsonify({
                    'success': True,
                    'stream': default_stream,
                    'warning': 'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            stream_config = yaml_manager.get_stream()

            return jsonify({
                'success': True,
                'stream': stream_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading stream config: {str(e)}'
            }), 500

    def update_stream_config(self):
        """Update stream configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            settings = payload.get('stream') or {}

            if not isinstance(settings, dict) or not settings:
                return jsonify({
                    'success': False,
                    'message': 'No stream settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            if not yaml_manager.update_stream(settings):
                return jsonify({
                    'success': False,
                    'message': 'Failed to update stream configuration'
                }), 500

            return jsonify({
                'success': True,
                'message': 'Stream configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating stream config: {str(e)}'
            }), 500

    def get_vars_config(self):
        """Get Suricata variables configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_vars = {}
                return jsonify({
                    'success': True,
                    'vars': default_vars,
                    'warning': 'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            vars_config = yaml_manager.get_vars()

            return jsonify({
                'success': True,
                'vars': vars_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading vars config: {str(e)}'
            }), 500

    def update_vars_config(self):
        """Update Suricata variables configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            vars_settings = payload.get('vars')

            if not isinstance(vars_settings, dict):
                return jsonify({
                    'success': False,
                    'message': 'No vars settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            if not yaml_manager.update_vars(vars_settings):
                return jsonify({
                    'success': False,
                    'message': 'Failed to update vars configuration'
                }), 500

            return jsonify({
                'success': True,
                'message': 'Variables configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating vars config: {str(e)}'
            }), 500

    def get_logging_config(self):
        """Get logging configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_logging = {
                    'default-log-level': 'notice',
                    'default-output-filter': None,
                    'outputs': [
                        {'console': {'enabled': 'yes'}},
                        {'file': {'enabled': 'yes', 'level': 'info', 'filename': '/var/log/suricata/suricata.log'}},
                        {'syslog': {'enabled': 'no'}}
                    ]
                }
                return jsonify({
                    'success': True,
                    'logging': default_logging,
                    'warning': f'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            logging_config = yaml_manager.get_logging()

            return jsonify({
                'success': True,
                'logging': logging_config
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading logging config: {str(e)}'
            }), 500

    def update_logging_config(self):
        """Update logging configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            logging_settings = payload.get('logging', {})

            if not logging_settings:
                return jsonify({
                    'success': False,
                    'message': 'No logging settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)
            yaml_manager.update_logging(logging_settings)

            return jsonify({
                'success': True,
                'message': 'Logging configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating logging config: {str(e)}'
            }), 500

    def get_detection_config(self):
        """Get detection engine configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_detection = {
                    'detect': {
                        'profile': 'medium',
                        'custom-values': {
                            'toclient-groups': 3,
                            'toserver-groups': 25
                        }
                    },
                    'mpm-algo': 'auto',
                    'sgh-mpm-context': 'auto',
                    'threading': {
                        'set-cpu-affinity': 'no',
                        'detect-thread-ratio': 1.0
                    },
                    'profiling': {
                        'rules': {'enabled': 'no'},
                        'keywords': {'enabled': 'no'},
                        'prefilter': {'enabled': 'no'},
                        'rulegroups': {'enabled': 'no'},
                        'packets': {'enabled': 'no'}
                    }
                }
                return jsonify({
                    'success': True,
                    'detection': default_detection,
                    'warning': f'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            detection_config = yaml_manager.get_detection()

            return jsonify({
                'success': True,
                'detection': detection_config
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading detection config: {str(e)}'
            }), 500

    def update_detection_config(self):
        """Update detection engine configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            detection_settings = payload.get('detection', {})

            if not detection_settings:
                return jsonify({
                    'success': False,
                    'message': 'No detection settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)
            yaml_manager.update_detection(detection_settings)

            return jsonify({
                'success': True,
                'message': 'Detection configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating detection config: {str(e)}'
            }), 500

    def get_host_config(self):
        """Get host configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_host = {
                    'hash-size': 4096,
                    'prealloc': 1000,
                    'memcap': '32mb'
                }
                return jsonify({
                    'success': True,
                    'host': default_host,
                    'warning': f'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            host_config = yaml_manager.get_host()

            return jsonify({
                'success': True,
                'host': host_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading host config: {str(e)}'
            }), 500

    def update_host_config(self):
        """Update host configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager
            import os

            payload = request.get_json(silent=True) or {}
            host_settings = payload.get('host', {})

            if not host_settings:
                return jsonify({
                    'success': False,
                    'message': 'No host settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)
            yaml_manager.update_host(host_settings)

            return jsonify({
                'success': True,
                'message': 'Host configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating host config: {str(e)}'
            }), 500

