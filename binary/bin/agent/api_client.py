"""
Dashboard API client for agent communication
"""

import requests
import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardClient:
    """Client for communicating with dashboard API"""

    def __init__(self, dashboard_url: str, token: str, verify_ssl: bool = True):
        """Initialize client"""
        self.dashboard_url = dashboard_url.rstrip('/')
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Suricata-Agent/1.0'
        })

    def test_connection(self) -> bool:
        """Test connection to dashboard"""
        try:
            response = self.session.get(
                f"{self.dashboard_url}/api/v1/health",
                verify=self.verify_ssl,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def send_heartbeat(self, agent_id: str, health_data: Dict) -> bool:
        """Send heartbeat to dashboard"""
        try:
            response = self.session.post(
                f"{self.dashboard_url}/api/v1/agents/{agent_id}/heartbeat",
                json=health_data,
                verify=self.verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
                return True
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    def send_events(self, events: List[Dict]) -> bool:
        """Send events batch to dashboard"""
        try:
            response = self.session.post(
                f"{self.dashboard_url}/api/v1/events",
                json={'events': events},
                verify=self.verify_ssl,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.debug(f"Sent {len(events)} events successfully")
                return True
            else:
                logger.warning(f"Failed to send events: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send events: {e}")
            return False

    def get_pending_commands(self, agent_id: str) -> Optional[List[Dict]]:
        """Get pending commands from dashboard"""
        try:
            response = self.session.get(
                f"{self.dashboard_url}/api/v1/agents/{agent_id}/commands",
                verify=self.verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('commands', [])
            else:
                logger.warning(f"Failed to get commands: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to get commands: {e}")
            return None

    def update_command_status(self, command_id: str, status: str, result: Optional[Dict] = None) -> bool:
        """Update command execution status"""
        try:
            payload = {'status': status}
            if result:
                payload['result'] = result

            response = self.session.put(
                f"{self.dashboard_url}/api/v1/commands/{command_id}",
                json=payload,
                verify=self.verify_ssl,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to update command status: {e}")
            return False
