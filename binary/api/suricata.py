"""
Suricata Config API - Handles Suricata advanced configuration (app-layer, outputs, stream, etc.)
"""
from flask import jsonify, request
import os


class SuricataConfigAPI:
    """API for managing advanced Suricata configuration"""

    def __init__(self, controller):
        self.controller = controller

    # ==================== App Layer Protocols ====================
    def get_app_layer_config(self):
        """Get app-layer protocols configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
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

            payload = request.get_json(silent=True) or {}
            updates = payload.get('protocols', {})

            if not updates:
                return jsonify({
                    'success': False,
                    'message': 'No protocol updates provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Suricata config file not found at {config_path}. Cannot save changes.'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            for protocol, settings in updates.items():
                enabled = settings.get('enabled', False)
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

    # ==================== Outputs ====================
    def get_outputs_config(self):
        """Get outputs configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
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

            payload = request.get_json(silent=True) or {}
            updates = payload.get('outputs', {})

            if not updates:
                return jsonify({
                    'success': False,
                    'message': 'No output updates provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Suricata config file not found at {config_path}. Cannot save changes.'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            for output_name, settings in updates.items():
                enabled = settings.get('enabled', False)
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

    # ==================== Packet Capture (Unified) ====================
    def get_packet_capture_config(self, capture_type):
        """Get Packet Capture configuration for any capture type"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            config_path = self.controller.config.config_path

            # Define defaults for each capture type
            defaults = {
                'af-packet': {
                    'interface': 'eth0',
                    'threads': 'auto',
                    'cluster-id': 99,
                    'cluster-type': 'cluster_flow',
                    'defrag': True,
                    'use-mmap': True,
                    'tpacket-v3': True,
                    'promisc': True
                },
                'af-xdp': {
                    'interface': 'eth0',
                    'threads': 'auto',
                    'enable-busy-poll': True,
                    'busy-poll-time': 20,
                    'busy-poll-budget': 64,
                },
                'dpdk': {
                    'eal-params': {
                        'proc-type': 'primary',
                    },
                    'interfaces': []
                },
                'pcap': {
                    'interface': 'eth0'
                }
            }

            if not os.path.exists(config_path):
                return jsonify({
                    'success': True,
                    'capture_type': capture_type,
                    'config': defaults.get(capture_type, {}),
                    'warning': 'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            capture_config = yaml_manager.get_packet_capture_config(capture_type)

            return jsonify({
                'success': True,
                'capture_type': capture_type,
                'config': capture_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading {capture_type} config: {str(e)}'
            }), 500

    def update_packet_capture_config(self, capture_type):
        """Update Packet Capture configuration for any capture type"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            payload = request.get_json(silent=True) or {}
            settings = payload.get('config') or {}

            if not isinstance(settings, dict) or not settings:
                return jsonify({
                    'success': False,
                    'message': f'No {capture_type} settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)

            if not yaml_manager.update_packet_capture_config(capture_type, settings):
                return jsonify({
                    'success': False,
                    'message': f'Failed to update {capture_type} configuration'
                }), 500

            return jsonify({
                'success': True,
                'message': f'{capture_type.upper()} configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating {capture_type} config: {str(e)}'
            }), 500

    # ==================== AF-Packet (Backward Compatibility) ====================
    def get_af_packet_config(self):
        """Get AF-Packet configuration - Legacy method for backward compatibility"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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
        """Update AF-Packet configuration - Legacy method for backward compatibility"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== Stream ====================
    def get_stream_config(self):
        """Get stream configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== Variables ====================
    def get_vars_config(self):
        """Get Suricata variables configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== Logging ====================
    def get_logging_config(self):
        """Get logging configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== Detection ====================
    def get_detection_config(self):
        """Get detection engine configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== Host ====================
    def get_host_config(self):
        """Get host configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

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

    # ==================== IPS ====================
    def get_ips_config(self):
        """Get IPS/Preventive configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                default_ips = {
                    'action-order': ['pass', 'drop', 'reject', 'alert'],
                    'default-rule-action': 'alert'
                }
                return jsonify({
                    'success': True,
                    'ips': default_ips,
                    'warning': f'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            ips_config = yaml_manager.get_ips()

            return jsonify({
                'success': True,
                'ips': ips_config or {}
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading IPS config: {str(e)}'
            }), 500

    def update_ips_config(self):
        """Update IPS/Preventive configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            payload = request.get_json(silent=True) or {}
            ips_settings = payload.get('ips', {})

            if not ips_settings:
                return jsonify({
                    'success': False,
                    'message': 'No IPS settings provided'
                }), 400

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)
            yaml_manager.update_ips(ips_settings)

            return jsonify({
                'success': True,
                'message': 'IPS configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating IPS config: {str(e)}'
            }), 500

    # ==================== Interfaces ====================
    def get_system_interfaces(self):
        """Get available network interfaces from system"""
        try:
            import psutil

            interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for interface_name, addrs in net_if_addrs.items():
                stats = net_if_stats.get(interface_name, None)
                is_up = stats.isup if stats else False

                ipv4_addr = None
                ipv6_addr = None
                mac_addr = None

                for addr in addrs:
                    if addr.family == 2:  # AF_INET (IPv4)
                        ipv4_addr = addr.address
                    elif addr.family == 23:  # AF_INET6 (IPv6)
                        ipv6_addr = addr.address
                    elif addr.family == -1 or addr.family == 17:  # AF_LINK/AF_PACKET (MAC)
                        mac_addr = addr.address

                interfaces.append({
                    'name': interface_name,
                    'ipv4': ipv4_addr,
                    'ipv6': ipv6_addr,
                    'mac': mac_addr,
                    'is_up': is_up,
                    'speed': stats.speed if stats else 0
                })

            return jsonify({
                'success': True,
                'interfaces': interfaces
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error getting system interfaces: {str(e)}',
                'interfaces': []
            }), 500

    def get_interfaces_config(self):
        """Get interface configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': True,
                    'interfaces': [],
                    'warning': f'Config file not found. Using defaults.'
                })

            yaml_manager = YAMLConfigManager(config_path)
            interfaces_config = yaml_manager.get_interfaces()

            return jsonify({
                'success': True,
                'interfaces': interfaces_config or []
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error loading interfaces config: {str(e)}'
            }), 500

    def update_interfaces_config(self):
        """Update interface configuration"""
        try:
            from binary.config.yaml_manager import YAMLConfigManager

            payload = request.get_json(silent=True) or {}
            interfaces_settings = payload.get('interfaces', [])

            config_path = self.controller.config.config_path

            if not os.path.exists(config_path):
                return jsonify({
                    'success': False,
                    'message': f'Config file not found at {config_path}'
                }), 404

            yaml_manager = YAMLConfigManager(config_path)
            yaml_manager.update_interfaces(interfaces_settings)

            return jsonify({
                'success': True,
                'message': 'Interface configuration updated successfully'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating interfaces config: {str(e)}'
            }), 500
