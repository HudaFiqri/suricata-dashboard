"""
Logging API - Handles Suricata logs
"""
from flask import jsonify


class LoggingAPI:
    """API for retrieving and formatting Suricata logs"""

    def __init__(self, controller):
        self.controller = controller

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
