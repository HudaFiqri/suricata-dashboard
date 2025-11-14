"""
Event and Log Parsers
Parse Suricata eve.json events and log entries
"""

import json
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventParser:
    """Parse Suricata eve.json events"""

    @staticmethod
    def parse(line):
        """
        Parse a single eve.json line

        Args:
            line: JSON string from eve.json

        Returns:
            dict: Parsed event or None if invalid
        """
        try:
            event = json.loads(line)

            # Extract common fields for indexing
            indexed = EventParser._extract_indexed_fields(event)

            return {
                'timestamp': event.get('timestamp'),
                'event_type': event.get('event_type'),
                'data': event,  # Full original event
                'indexed': indexed  # Extracted fields for fast queries
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in eve.json: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None

    @staticmethod
    def _extract_indexed_fields(event):
        """Extract commonly-queried fields for indexing"""
        indexed = {}

        # Flow IDs
        if 'flow_id' in event:
            indexed['flow_id'] = event['flow_id']

        # Network layer
        if 'src_ip' in event:
            indexed['src_ip'] = event['src_ip']
        if 'dest_ip' in event:
            indexed['dest_ip'] = event['dest_ip']
        if 'src_port' in event:
            indexed['src_port'] = event['src_port']
        if 'dest_port' in event:
            indexed['dest_port'] = event['dest_port']
        if 'proto' in event:
            indexed['proto'] = event['proto']

        # Alert-specific fields
        if event.get('event_type') == 'alert' and 'alert' in event:
            alert = event['alert']
            indexed['signature_id'] = alert.get('signature_id')
            indexed['signature'] = alert.get('signature')
            indexed['severity'] = alert.get('severity')
            indexed['category'] = alert.get('category')

        # HTTP fields
        if 'http' in event:
            http = event['http']
            indexed['http_hostname'] = http.get('hostname')
            indexed['http_url'] = http.get('url')
            indexed['http_method'] = http.get('http_method')
            indexed['http_status'] = http.get('status')

        # DNS fields
        if 'dns' in event:
            dns = event['dns']
            if 'query' in dns:
                indexed['dns_query'] = dns['query'][0].get('rrname') if dns['query'] else None

        # TLS fields
        if 'tls' in event:
            tls = event['tls']
            indexed['tls_sni'] = tls.get('sni')
            indexed['tls_subject'] = tls.get('subject')

        return indexed


class LogParser:
    """Parse Suricata log files (suricata.log, fast.log)"""

    # Log level patterns
    LOG_PATTERN = re.compile(
        r'^(\d+/\d+/\d+-\d+:\d+:\d+\.\d+)\s+<(\w+)>\s+--\s+(.+)$'
    )

    FAST_LOG_PATTERN = re.compile(
        r'^\[(\d+:\d+:\d+)\]\s+(.+?)\s+\[Classification:\s*(.+?)\]\s+\[Priority:\s*(\d+)\]'
    )

    @staticmethod
    def parse_suricata_log(line):
        """
        Parse suricata.log line

        Format: 14/1/2025-10:30:00.123456 <Info> -- rule reload complete

        Returns:
            dict: Parsed log entry or None
        """
        match = LogParser.LOG_PATTERN.match(line)

        if match:
            timestamp_str, level, message = match.groups()

            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y-%H:%M:%S.%f')

                return {
                    'log_type': 'suricata',
                    'timestamp': timestamp.isoformat(),
                    'level': level.upper(),
                    'message': message.strip(),
                    'raw_line': line
                }
            except ValueError:
                logger.warning(f"Invalid timestamp in log: {timestamp_str}")

        return {
            'log_type': 'suricata',
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': line,
            'raw_line': line
        }

    @staticmethod
    def parse_fast_log(line):
        """
        Parse fast.log line

        Format: [1:2012345:6] ET MALWARE Botnet Traffic [Classification: Trojan] [Priority: 1]

        Returns:
            dict: Parsed log entry or None
        """
        match = LogParser.FAST_LOG_PATTERN.match(line)

        if match:
            signature, description, classification, priority = match.groups()

            return {
                'log_type': 'fast',
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'ALERT',
                'message': f"{description} (Priority: {priority})",
                'raw_line': line,
                'structured': {
                    'signature': signature,
                    'description': description,
                    'classification': classification,
                    'priority': int(priority)
                }
            }

        return {
            'log_type': 'fast',
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': line,
            'raw_line': line
        }

    @staticmethod
    def parse(file_path, line):
        """
        Auto-detect log type and parse

        Args:
            file_path: Path to log file
            line: Log line

        Returns:
            dict: Parsed log entry
        """
        if 'fast.log' in file_path:
            return LogParser.parse_fast_log(line)
        else:
            return LogParser.parse_suricata_log(line)
