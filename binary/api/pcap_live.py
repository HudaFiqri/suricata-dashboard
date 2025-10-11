"""
Live Packet Capture API - Real-time packet monitoring from eve.json
"""
import os
import json
from flask import jsonify, request


class LivePacketCaptureAPI:
    """API for real-time packet capture monitoring"""

    def __init__(self, config):
        self.config = config
        self.eve_log_path = f"{config.SURICATA_LOG_DIR}/eve.json"

    def get_live_packets(self):
        """Get latest packets from eve.json for live monitoring"""
        limit = request.args.get('limit', 50, type=int)
        event_type = request.args.get('type', None)
        protocol = request.args.get('protocol', None)

        if not os.path.exists(self.eve_log_path):
            return jsonify({
                'success': False,
                'packets': [],
                'error': f'eve.json not found at {self.eve_log_path}'
            })

        try:
            packets = []

            # Read file from the end to get most recent packets
            with open(self.eve_log_path, 'r') as f:
                lines = f.readlines()

            # Process lines in reverse order (newest first)
            for line in reversed(lines):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line.strip())

                    # Apply event type filter
                    if event_type and event.get('event_type', '').lower() != event_type.lower():
                        continue

                    # Apply protocol filter
                    if protocol and event.get('proto', '').upper() != protocol.upper():
                        continue

                    # Parse packet data
                    packet_data = self._parse_packet(event)
                    packets.append(packet_data)

                    # Stop if we reached the limit
                    if len(packets) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

            return jsonify({
                'success': True,
                'packets': packets,
                'total': len(packets),
                'path': self.eve_log_path
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'packets': [],
                'error': f'{str(e)}'
            })

    def _parse_packet(self, event):
        """Parse event JSON into packet format for display"""
        event_type = event.get('event_type', 'unknown')

        # Base packet information
        packet = {
            'timestamp': event.get('timestamp', ''),
            'event_type': event_type,
            'protocol': event.get('proto', 'N/A'),
            'src_ip': event.get('src_ip', 'N/A'),
            'src_port': event.get('src_port', ''),
            'dest_ip': event.get('dest_ip', 'N/A'),
            'dest_port': event.get('dest_port', ''),
            'flow_id': event.get('flow_id', ''),
            'in_iface': event.get('in_iface', ''),
            'packet_info': self._get_packet_details(event, event_type)
        }

        # Add payload size if available
        if 'payload' in event:
            packet['payload_size'] = len(event['payload'])

        # Add flow information if available
        if 'flow' in event:
            flow = event['flow']
            packet['flow'] = {
                'pkts_toserver': flow.get('pkts_toserver', 0),
                'pkts_toclient': flow.get('pkts_toclient', 0),
                'bytes_toserver': flow.get('bytes_toserver', 0),
                'bytes_toclient': flow.get('bytes_toclient', 0),
                'start': flow.get('start', ''),
            }

        return packet

    def _get_packet_details(self, event, event_type):
        """Extract detailed information based on event type"""
        details = {
            'type': event_type,
            'description': ''
        }

        if event_type == 'alert':
            alert_info = event.get('alert', {})
            details['description'] = alert_info.get('signature', 'Unknown Alert')
            details['category'] = alert_info.get('category', 'Unknown')
            details['severity'] = alert_info.get('severity', 3)
            details['signature_id'] = alert_info.get('signature_id', 0)

        elif event_type == 'http':
            http_data = event.get('http', {})
            details['description'] = f"{http_data.get('http_method', 'GET')} {http_data.get('hostname', '')}{http_data.get('url', '')}"
            details['status'] = http_data.get('status', '')
            details['length'] = http_data.get('length', 0)
            details['user_agent'] = http_data.get('http_user_agent', '')

        elif event_type == 'dns':
            dns_data = event.get('dns', {})
            details['description'] = f"Query: {dns_data.get('rrname', '')}"
            details['type'] = dns_data.get('rrtype', '')
            details['rcode'] = dns_data.get('rcode', '')

        elif event_type == 'tls':
            tls_data = event.get('tls', {})
            details['description'] = f"TLS {tls_data.get('version', '')}"
            details['sni'] = tls_data.get('sni', 'N/A')
            details['subject'] = tls_data.get('subject', '')
            details['issuer'] = tls_data.get('issuerdn', '')

        elif event_type == 'ssh':
            ssh_data = event.get('ssh', {})
            details['description'] = "SSH Connection"
            details['client'] = ssh_data.get('client', {}).get('software_version', '')
            details['server'] = ssh_data.get('server', {}).get('software_version', '')

        elif event_type == 'flow':
            details['description'] = f"Flow - {event.get('proto', 'N/A')}"
            details['state'] = event.get('flow', {}).get('state', '')
            details['reason'] = event.get('flow', {}).get('reason', '')

        elif event_type == 'fileinfo':
            fileinfo = event.get('fileinfo', {})
            details['description'] = f"File: {fileinfo.get('filename', 'N/A')}"
            details['size'] = fileinfo.get('size', 0)
            details['magic'] = fileinfo.get('magic', '')

        elif event_type == 'stats':
            details['description'] = "Statistics Update"
            stats = event.get('stats', {})
            details['capture'] = stats.get('capture', {})
            details['decoder'] = stats.get('decoder', {})

        else:
            details['description'] = event_type.upper()

        return details

    def get_packet_stats(self):
        """Get live packet statistics"""
        if not os.path.exists(self.eve_log_path):
            return jsonify({
                'success': False,
                'error': f'eve.json not found at {self.eve_log_path}'
            })

        try:
            stats = {
                'total_packets': 0,
                'protocols': {},
                'event_types': {},
                'top_sources': {},
                'top_destinations': {}
            }

            # Read last 1000 lines for statistics
            with open(self.eve_log_path, 'r') as f:
                lines = f.readlines()

            for line in reversed(lines[-1000:]):
                if not line.strip():
                    continue

                try:
                    event = json.loads(line.strip())
                    stats['total_packets'] += 1

                    # Count by protocol
                    proto = event.get('proto', 'OTHER')
                    stats['protocols'][proto] = stats['protocols'].get(proto, 0) + 1

                    # Count by event type
                    event_type = event.get('event_type', 'unknown')
                    stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1

                    # Count top sources
                    src_ip = event.get('src_ip', '')
                    if src_ip:
                        stats['top_sources'][src_ip] = stats['top_sources'].get(src_ip, 0) + 1

                    # Count top destinations
                    dest_ip = event.get('dest_ip', '')
                    if dest_ip:
                        stats['top_destinations'][dest_ip] = stats['top_destinations'].get(dest_ip, 0) + 1

                except json.JSONDecodeError:
                    continue

            # Sort and limit top IPs
            stats['top_sources'] = dict(sorted(stats['top_sources'].items(), key=lambda x: x[1], reverse=True)[:10])
            stats['top_destinations'] = dict(sorted(stats['top_destinations'].items(), key=lambda x: x[1], reverse=True)[:10])

            return jsonify({
                'success': True,
                'stats': stats
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
