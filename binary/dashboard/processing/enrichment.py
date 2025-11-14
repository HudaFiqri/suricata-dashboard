"""
Event Enrichment
Add GeoIP, threat intel, and other contextual data to events
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventEnricher:
    """Enrich events with additional context"""

    def __init__(self):
        self.geoip_enabled = False
        self.threat_intel_enabled = False

    def enrich(self, event):
        """
        Enrich a single event with additional data

        Args:
            event: Raw event dict from agent

        Returns:
            Enriched event dict
        """
        enriched = event.copy()

        # Add processing timestamp
        enriched['processed_at'] = datetime.utcnow()

        # Enrich IP addresses
        if 'indexed' in enriched and 'src_ip' in enriched['indexed']:
            enriched['src_ip_info'] = self._enrich_ip(enriched['indexed']['src_ip'])

        if 'indexed' in enriched and 'dest_ip' in enriched['indexed']:
            enriched['dest_ip_info'] = self._enrich_ip(enriched['indexed']['dest_ip'])

        # Enrich signature
        if 'indexed' in enriched and 'signature_id' in enriched['indexed']:
            enriched['signature_info'] = self._enrich_signature(enriched['indexed']['signature_id'])

        # Threat intelligence
        if self.threat_intel_enabled:
            enriched['threat_intel'] = self._check_threat_intel(enriched)

        return enriched

    def _enrich_ip(self, ip_address):
        """
        Enrich IP address with GeoIP and other data

        In production, integrate with MaxMind GeoIP2 or similar
        """
        if not self.geoip_enabled:
            return None

        # TODO: Integrate with GeoIP database
        # Example response:
        return {
            'country': None,
            'city': None,
            'asn': None,
            'isp': None,
            'is_private': self._is_private_ip(ip_address)
        }

    def _is_private_ip(self, ip):
        """Check if IP is private/internal"""
        if ip.startswith('10.'):
            return True
        if ip.startswith('192.168.'):
            return True
        if ip.startswith('172.'):
            # Check if in 172.16.0.0 - 172.31.255.255 range
            parts = ip.split('.')
            if len(parts) >= 2:
                try:
                    second_octet = int(parts[1])
                    if 16 <= second_octet <= 31:
                        return True
                except ValueError:
                    pass
        return False

    def _enrich_signature(self, signature_id):
        """
        Enrich signature with additional metadata

        In production, integrate with signature database
        """
        # TODO: Query signature database
        return {
            'category': None,
            'severity': None,
            'reference': None
        }

    def _check_threat_intel(self, event):
        """
        Check against threat intelligence feeds

        In production, integrate with MISP, OTX, etc.
        """
        # TODO: Implement threat intel lookup
        return {
            'is_malicious': False,
            'confidence': 0,
            'sources': []
        }

    def enrich_batch(self, events):
        """
        Enrich multiple events

        Args:
            events: List of raw event dicts

        Returns:
            List of enriched event dicts
        """
        return [self.enrich(event) for event in events]
