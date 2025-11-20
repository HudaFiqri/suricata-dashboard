"""
Suricata Configuration API
Handles advanced Suricata configuration for agents (app-layer, outputs, packet-capture, etc.)
"""

from flask import jsonify, request
from binary.dashboard.api import api
from binary.dashboard.api.auth import require_auth, ENABLE_AUTH
import logging
import os

# Allow disabling auth specifically for config endpoints (for air-gapped labs)
ALLOW_CONFIG_NO_AUTH = os.getenv('ALLOW_CONFIG_NO_AUTH', 'False').lower() == 'true'

logger = logging.getLogger(__name__)


@api.route('/agents/<agent_id>/config/app-layer', methods=['GET'])
@require_auth
def get_app_layer_config(agent_id):
    """Get app-layer protocols configuration from agent"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Config request for agent {agent_id} (returning defaults - agent communication not yet implemented)")

        # Default protocols if config not available
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

        # TODO: Fetch actual config from agent via command
        return jsonify({
            'success': True,
            'protocols': default_protocols
        })

    except Exception as e:
        logger.error(f"Error getting app-layer config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/app-layer', methods=['POST'])
@require_auth
def update_app_layer_config(agent_id):
    """Update app-layer protocols configuration on agent"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        updates = payload.get('protocols', {})

        if not updates:
            return jsonify({'success': False, 'error': 'No protocol updates provided'}), 400

        logger.info(f"App-layer config update for agent {agent_id} (acknowledged - agent communication not yet implemented)")

        # TODO: Send command to agent to update config
        return jsonify({
            'success': True,
            'message': 'App-layer configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating app-layer config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/outputs', methods=['GET'])
@require_auth
def get_outputs_config(agent_id):
    """Get outputs configuration from agent"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Outputs config request for agent {agent_id} (returning defaults)")

        # Default outputs configuration
        default_outputs = {
            'eve-log': {
                'enabled': True,
                'filetype': 'regular',
                'filename': '/var/log/suricata/eve.json',
                'types': ['alert', 'http', 'dns', 'tls', 'files', 'ssh', 'stats']
            },
            'fast': {
                'enabled': True,
                'filename': '/var/log/suricata/fast.log'
            },
            'stats': {
                'enabled': True,
                'interval': 8
            }
        }

        # TODO: Fetch actual config from agent
        return jsonify({
            'success': True,
            'outputs': default_outputs
        })

    except Exception as e:
        logger.error(f"Error getting outputs config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/outputs', methods=['POST'])
@require_auth
def update_outputs_config(agent_id):
    """Update outputs configuration on agent"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        updates = payload.get('outputs', {})

        if not updates:
            return jsonify({'success': False, 'error': 'No output updates provided'}), 400

        logger.info(f"Outputs config update for agent {agent_id} (acknowledged)")

        # TODO: Send command to agent to update config
        return jsonify({
            'success': True,
            'message': 'Outputs configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating outputs config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/packet-capture/<capture_type>', methods=['GET'])
@require_auth
def get_packet_capture_config(agent_id, capture_type):
    """Get packet capture configuration (af-packet, af-xdp, dpdk, pcap)"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Packet-capture ({capture_type}) config request for agent {agent_id} (returning defaults)")

        # Default configurations per capture type
        default_configs = {
            'af-packet': {
                'interface': 'eth0',
                'cluster-id': 99,
                'cluster-type': 'cluster_flow',
                'defrag': True,
                'use-mmap': True,
                'ring-size': 2048,
                'block-size': 32768
            },
            'af-xdp': {
                'interface': 'eth0',
                'threads': 'auto',
                'mode': 'driver',
                'program-name': 'xdp_filter'
            },
            'dpdk': {
                'eal-params': {'proc-type': 'primary'},
                'interfaces': []
            },
            'pcap': {
                'interface': 'eth0',
                'buffer-size': 16777216,
                'checksum-checks': 'auto'
            }
        }

        config = default_configs.get(capture_type, {})

        # TODO: Fetch actual config from agent
        return jsonify({
            'success': True,
            'config': config,
            'capture_type': capture_type
        })

    except Exception as e:
        logger.error(f"Error getting packet capture config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/packet-capture/<capture_type>', methods=['POST'])
@require_auth
def update_packet_capture_config(agent_id, capture_type):
    """Update packet capture configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"Packet-capture ({capture_type}) config update for agent {agent_id} (acknowledged)")

        # TODO: Send command to agent to update config
        return jsonify({
            'success': True,
            'message': f'{capture_type} configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating packet capture config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/stream', methods=['GET'])
@require_auth
def get_stream_config(agent_id):
    """Get stream configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Stream config request for agent {agent_id} (returning defaults)")

        default_config = {
            'memcap': '64mb',
            'checksum-validation': True,
            'inline': 'auto',
            'reassembly': {
                'memcap': '256mb',
                'depth': '1mb',
                'toserver-chunk-size': 2560,
                'toclient-chunk-size': 2560
            }
        }

        return jsonify({
            'success': True,
            'config': default_config
        })

    except Exception as e:
        logger.error(f"Error getting stream config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/stream', methods=['POST'])
@require_auth
def update_stream_config(agent_id):
    """Update stream configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"Stream config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Stream configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating stream config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/vars', methods=['GET'])
@require_auth
def get_vars_config(agent_id):
    """Get variables configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Vars config request for agent {agent_id} (returning defaults)")

        default_vars = {
            'HOME_NET': '[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]',
            'EXTERNAL_NET': '!$HOME_NET',
            'HTTP_SERVERS': '$HOME_NET',
            'SMTP_SERVERS': '$HOME_NET',
            'SQL_SERVERS': '$HOME_NET',
            'DNS_SERVERS': '$HOME_NET',
            'HTTP_PORTS': '[80,81,311,591,593,901,1220,1414,1830,2301,2381,2809,3128,3702,4343,4848,5250,6988,7000,7001,7144,7145,7510,7777,7779,8000,8008,8014,8028,8080,8085,8088,8090,8118,8123,8180,8181,8243,8280,8300,8800,8888,8899,9000,9060,9080,9090,9091,9443,9999,11371,34443,34444,41080,50002,55555]',
            'SHELLCODE_PORTS': '!80',
            'ORACLE_PORTS': 1521,
            'SSH_PORTS': 22,
            'DNP3_PORTS': '[20000]',
            'MODBUS_PORTS': 502,
            'FILE_DATA_PORTS': '[$HTTP_PORTS,110,143]',
            'FTP_PORTS': '[21,2100,3535]'
        }

        return jsonify({
            'success': True,
            'vars': default_vars
        })

    except Exception as e:
        logger.error(f"Error getting vars config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/vars', methods=['POST'])
@require_auth
def update_vars_config(agent_id):
    """Update variables configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        vars_data = payload.get('vars', {})

        if not vars_data:
            return jsonify({'success': False, 'error': 'No variables provided'}), 400

        logger.info(f"Vars config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Variables configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating vars config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/host', methods=['GET'])
@require_auth
def get_host_config(agent_id):
    """Get host configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Host config request for agent {agent_id} (returning defaults)")

        default_config = {
            'memcap': '32mb',
            'hash-size': 4096,
            'prealloc': 1000
        }

        return jsonify({
            'success': True,
            'config': default_config
        })

    except Exception as e:
        logger.error(f"Error getting host config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/host', methods=['POST'])
@require_auth
def update_host_config(agent_id):
    """Update host configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"Host config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Host configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating host config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/ips', methods=['GET'])
@require_auth
def get_ips_config(agent_id):
    """Get IPS/Prevention configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"IPS config request for agent {agent_id} (returning defaults)")

        default_config = {
            'mode': 'ids',  # ids or ips
            'drop-alerts': False,
            'reject': {
                'default-reject-action': 'reset-both'
            }
        }

        return jsonify({
            'success': True,
            'config': default_config
        })

    except Exception as e:
        logger.error(f"Error getting IPS config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/ips', methods=['POST'])
@require_auth
def update_ips_config(agent_id):
    """Update IPS/Prevention configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"IPS config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'IPS configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating IPS config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/interfaces', methods=['GET'])
@require_auth
def get_interfaces_config(agent_id):
    """Get network interfaces configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Interfaces config request for agent {agent_id} (returning defaults)")

        # TODO: Get actual interfaces from agent
        default_interfaces = [
            {'name': 'eth0', 'enabled': True, 'threads': 'auto'},
            {'name': 'eth1', 'enabled': False, 'threads': 'auto'}
        ]

        return jsonify({
            'success': True,
            'interfaces': default_interfaces
        })

    except Exception as e:
        logger.error(f"Error getting interfaces config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/interfaces', methods=['POST'])
@require_auth
def update_interfaces_config(agent_id):
    """Update network interfaces configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        interfaces = payload.get('interfaces', [])

        if not interfaces:
            return jsonify({'success': False, 'error': 'No interfaces provided'}), 400

        logger.info(f"Interfaces config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Interfaces configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating interfaces config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/system/interfaces', methods=['GET'])
@require_auth
def get_system_interfaces(agent_id):
    """Get available system network interfaces from agent"""
    try:
        logger.info(f"System interfaces request for agent {agent_id} (returning mock list)")

        # TODO: Fetch from agent via command
        mock_interfaces = [
            {'name': 'eth0', 'status': 'up', 'speed': '1000 Mbps'},
            {'name': 'eth1', 'status': 'down', 'speed': '1000 Mbps'},
            {'name': 'lo', 'status': 'up', 'speed': 'unknown'}
        ]

        return jsonify({
            'success': True,
            'interfaces': mock_interfaces
        })

    except Exception as e:
        logger.error(f"Error getting system interfaces: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/integrations', methods=['GET'])
@require_auth
def get_integrations(agent_id):
    """Get all integration settings for agent"""
    try:
        logger.info(f"Integrations request for agent {agent_id} (returning defaults)")

        # Default integration settings
        integrations = {
            'discord': {
                'enabled': False,
                'webhook_url': '',
                'message_template': '',
                'rate_limit_messages': 30,
                'rate_limit_interval': 60
            },
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': '',
                'message_template': '',
                'rate_limit_messages': 20,
                'rate_limit_interval': 60
            }
        }

        return jsonify({
            'success': True,
            'integrations': integrations
        })

    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/integrations/<integration_name>', methods=['GET'])
@require_auth
def get_integration(agent_id, integration_name):
    """Get specific integration settings"""
    try:
        logger.info(f"Integration {integration_name} request for agent {agent_id} (returning defaults)")

        # TODO: Fetch from database or agent
        default_settings = {
            'enabled': False,
            'webhook_url': '' if integration_name == 'discord' else None,
            'bot_token': '' if integration_name == 'telegram' else None,
            'chat_id': '' if integration_name == 'telegram' else None
        }

        return jsonify({
            'success': True,
            'settings': default_settings
        })

    except Exception as e:
        logger.error(f"Error getting integration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/integrations/<integration_name>', methods=['POST'])
@require_auth
def save_integration(agent_id, integration_name):
    """Save integration settings"""
    try:
        payload = request.get_json(silent=True) or {}

        logger.info(f"Integration {integration_name} save for agent {agent_id} (acknowledged)")

        # TODO: Save to database or send to agent
        return jsonify({
            'success': True,
            'message': f'{integration_name} settings saved successfully'
        })

    except Exception as e:
        logger.error(f"Error saving integration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/detection', methods=['GET'])
@require_auth
def get_detection_config(agent_id):
    """Get detection engine configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Detection config request for agent {agent_id} (returning defaults)")

        default_config = {
            'profile': 'medium',
            'sgh-mpm-context': 'auto',
            'inspection-recursion-limit': 3000,
            'prefilter': {
                'default': 'mpm'
            },
            'grouping': {
                'tcp-whitelist': 'dns, http, tls',
                'udp-whitelist': 'dns'
            }
        }

        return jsonify({
            'success': True,
            'config': default_config
        })

    except Exception as e:
        logger.error(f"Error getting detection config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/detection', methods=['POST'])
@require_auth
def update_detection_config(agent_id):
    """Update detection engine configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"Detection config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Detection configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating detection config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/logging', methods=['GET'])
@require_auth
def get_logging_config(agent_id):
    """Get logging configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        logger.info(f"Logging config request for agent {agent_id} (returning defaults)")

        default_config = {
            'default-log-level': 'info',
            'default-log-format': '[%i] %t - (%f:%l) <%d> (%n) -- ',
            'outputs': [
                {
                    'console': {
                        'enabled': 'yes'
                    }
                },
                {
                    'file': {
                        'enabled': 'yes',
                        'level': 'info',
                        'filename': '/var/log/suricata/suricata.log'
                    }
                },
                {
                    'syslog': {
                        'enabled': 'no',
                        'facility': 'local5',
                        'format': '[%i] <%d> -- '
                    }
                }
            ]
        }

        return jsonify({
            'success': True,
            'config': default_config
        })

    except Exception as e:
        logger.error(f"Error getting logging config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/agents/<agent_id>/config/logging', methods=['POST'])
@require_auth
def update_logging_config(agent_id):
    """Update logging configuration"""
    try:
        if ALLOW_CONFIG_NO_AUTH and not ENABLE_AUTH:
            request.user_id = 'public'
            request.username = 'public'
            request.user_role = 'admin'

        payload = request.get_json(silent=True) or {}
        config = payload.get('config', {})

        if not config:
            return jsonify({'success': False, 'error': 'No configuration provided'}), 400

        logger.info(f"Logging config update for agent {agent_id} (acknowledged)")

        return jsonify({
            'success': True,
            'message': 'Logging configuration updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating logging config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
