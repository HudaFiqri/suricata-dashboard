"""
Monitor API - Handles traffic monitoring and statistics
"""
import os
import json
from datetime import datetime, timedelta, timezone
from flask import jsonify


class MonitorAPI:
    """API for monitoring traffic and statistics from eve.json"""

    def __init__(self, config):
        self.config = config
        self.eve_log_path = f"{config.SURICATA_LOG_DIR}/eve.json"

    def get_monitor_data(self, timespan='1h'):
        """Get monitoring data (TCP, UDP, Alerts counts)"""
        if not os.path.exists(self.eve_log_path):
            return {
                'success': False,
                'tcp_traffic': 0,
                'udp_traffic': 0,
                'total_alerts': 0,
                'error': f'eve.json not found at {self.eve_log_path}'
            }

        try:
            hours = self._parse_timespan(timespan)
            cutoff_time = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=hours)

            counts = {
                'tcp': 0,
                'udp': 0,
                'icmp': 0,
                'alerts': 0,
                'flows': 0,
                'total': 0
            }

            with open(self.eve_log_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line.strip())
                        counts['total'] += 1

                        # Skip old events
                        if self._is_old_event(event, cutoff_time):
                            continue

                        event_type = event.get('event_type', '')
                        proto = event.get('proto', '').upper()

                        # Count flows by protocol
                        if event_type == 'flow':
                            counts['flows'] += 1
                            if proto == 'TCP':
                                counts['tcp'] += 1
                            elif proto == 'UDP':
                                counts['udp'] += 1
                            elif proto == 'ICMP':
                                counts['icmp'] += 1

                        # Count alerts
                        if event_type == 'alert':
                            counts['alerts'] += 1

                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue

            return {
                'success': True,
                'tcp_traffic': counts['tcp'],
                'udp_traffic': counts['udp'],
                'icmp_traffic': counts['icmp'],
                'total_alerts': counts['alerts'],
                'total_flows': counts['flows'],
                'total_events': counts['total'],
                'timespan': timespan,
                'path': self.eve_log_path
            }

        except Exception as e:
            return {
                'success': False,
                'tcp_traffic': 0,
                'udp_traffic': 0,
                'total_alerts': 0,
                'error': f'{str(e)} (path: {self.eve_log_path})'
            }

    def get_debug_info(self):
        """Debug endpoint to check eve.json status"""
        debug_info = {
            'eve_path': self.eve_log_path,
            'exists': os.path.exists(self.eve_log_path),
            'readable': False,
            'line_count': 0,
            'sample_events': [],
            'event_types': {},
            'protocols': {}
        }

        try:
            if os.path.exists(self.eve_log_path):
                debug_info['readable'] = True

                with open(self.eve_log_path, 'r') as f:
                    lines = f.readlines()
                    debug_info['line_count'] = len(lines)

                    # Get last 10 lines
                    for line in lines[-10:]:
                        try:
                            event = json.loads(line.strip())
                            event_type = event.get('event_type', 'unknown')
                            proto = event.get('proto', 'none')

                            debug_info['event_types'][event_type] = \
                                debug_info['event_types'].get(event_type, 0) + 1

                            if proto != 'none':
                                debug_info['protocols'][proto] = \
                                    debug_info['protocols'].get(proto, 0) + 1

                            debug_info['sample_events'].append({
                                'event_type': event_type,
                                'proto': proto,
                                'timestamp': event.get('timestamp', '')
                            })
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            debug_info['error'] = str(e)

        return debug_info

    def _parse_timespan(self, timespan):
        """Parse timespan string to hours"""
        if timespan.endswith('h'):
            return int(timespan[:-1])
        elif timespan.endswith('d'):
            return int(timespan[:-1]) * 24
        return 1

    def _is_old_event(self, event, cutoff_time):
        """Check if event is older than cutoff time"""
        timestamp_str = event.get('timestamp', '')
        if not timestamp_str:
            return False

        try:
            if 'Z' in timestamp_str:
                event_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif '+' in timestamp_str:
                event_time = datetime.fromisoformat(timestamp_str)
            else:
                event_time = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
                event_time = event_time.replace(tzinfo=timezone.utc)

            return event_time < cutoff_time
        except (ValueError, AttributeError):
            return False
