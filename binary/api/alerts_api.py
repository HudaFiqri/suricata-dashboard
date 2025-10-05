"""
Alerts API - Handles all events from eve.json
"""
import os
import json
from flask import jsonify


class AlertsAPI:
    """API for retrieving and processing events from eve.json"""

    def __init__(self, config):
        self.config = config
        self.eve_log_path = f"{config.SURICATA_LOG_DIR}/eve.json"

    def get_all_events(self, limit=100, category=None, protocol=None):
        """Get all events from eve.json with optional filters"""
        if not os.path.exists(self.eve_log_path):
            return {
                'alerts': [],
                'error': f'eve.json not found at {self.eve_log_path}'
            }

        try:
            events = []

            with open(self.eve_log_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line.strip())

                        # Apply protocol filter
                        if protocol and event.get('proto', '').upper() != protocol.upper():
                            continue

                        # Parse event into alert format
                        alert_data = self._parse_event(event, len(events) + 1)

                        # Apply category filter
                        if category and alert_data['category'].upper() != category.upper():
                            continue

                        events.append(alert_data)

                    except json.JSONDecodeError:
                        continue

            # Get most recent events
            events.reverse()
            events = events[:limit]

            return {'alerts': events, 'path': self.eve_log_path}

        except Exception as e:
            return {'alerts': [], 'error': f'{str(e)} (path: {self.eve_log_path})'}

    def _parse_event(self, event, event_id):
        """Parse event JSON into standardized alert format"""
        event_type = event.get('event_type', 'unknown')
        signature, category, severity = self._get_event_details(event, event_type)

        return {
            'id': event_id,
            'timestamp': event.get('timestamp', ''),
            'signature': signature,
            'signature_id': None,
            'category': category,
            'severity': severity,
            'protocol': event.get('proto', 'N/A'),
            'src_ip': event.get('src_ip', 'N/A'),
            'src_port': event.get('src_port', ''),
            'dest_ip': event.get('dest_ip', 'N/A'),
            'dest_port': event.get('dest_port', ''),
            'payload': None,
        }

    def _get_event_details(self, event, event_type):
        """Extract signature, category, and severity from event"""
        severity = 3  # Default info level

        if event_type == 'alert':
            alert_info = event.get('alert', {})
            return (
                alert_info.get('signature', 'Unknown Alert'),
                alert_info.get('category', 'Unknown'),
                alert_info.get('severity', 1)
            )

        elif event_type == 'http':
            http_data = event.get('http', {})
            method = http_data.get('http_method', 'GET')
            host = http_data.get('hostname', '')
            url = http_data.get('url', '')
            return (f"HTTP: {method} {host}{url}", 'HTTP', severity)

        elif event_type == 'dns':
            dns_data = event.get('dns', {})
            return (f"DNS Query: {dns_data.get('rrname', '')}", 'DNS', severity)

        elif event_type == 'tls':
            tls_data = event.get('tls', {})
            return (f"TLS: {tls_data.get('sni', 'N/A')}", 'TLS', severity)

        elif event_type == 'ssh':
            return ("SSH Connection", 'SSH', severity)

        elif event_type == 'flow':
            return (f"Flow: {event.get('proto', 'N/A')}", 'FLOW', severity)

        elif event_type == 'stats':
            return ("Statistics Update", 'STATS', severity)

        elif event_type == 'fileinfo':
            fileinfo = event.get('fileinfo', {})
            return (f"File: {fileinfo.get('filename', 'N/A')}", 'FILE', severity)

        else:
            return (event_type.upper(), event_type.upper(), severity)
