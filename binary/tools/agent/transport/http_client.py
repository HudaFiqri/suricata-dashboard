"""
HTTP Client for Agent
Fallback HTTP/REST communication with dashboard
"""

import requests
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentHTTPClient:
    """HTTP client for REST API communication"""

    def __init__(self, config, auth):
        """
        Initialize HTTP client

        Args:
            config: Agent configuration
            auth: TokenEncryptor instance
        """
        self.config = config
        self.auth = auth

        self.base_url = config.get('dashboard.url')
        self.api_version = config.get('dashboard.api_version', 'v1')
        self.verify_ssl = config.get('dashboard.verify_ssl', True)

        self.session = requests.Session()
        self.session.verify = self.verify_ssl

    def _get_url(self, endpoint):
        """Build full API URL"""
        return f"{self.base_url}/api/{self.api_version}/{endpoint.lstrip('/')}"

    def _request(self, method, endpoint, data=None, timeout=30):
        """Make HTTP request with retry logic"""
        url = self._get_url(endpoint)
        headers = self.auth.get_headers()

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    json=data,
                    headers=headers,
                    timeout=timeout
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP {e.response.status_code}: {e}")
                if e.response.status_code in [401, 403]:
                    # Authentication error, don't retry
                    raise
                elif attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

            except requests.exceptions.Timeout as e:
                logger.error(f"Request timeout: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

    def register(self, agent_info):
        """
        Register agent with dashboard

        Args:
            agent_info: Dictionary with agent details

        Returns:
            dict: Registration response
        """
        logger.info("Registering agent with dashboard")

        response = self._request('POST', '/agents/register', agent_info)

        if response.get('success'):
            agent_id = response.get('agent_id')
            logger.info(f"Agent registered successfully (ID: {agent_id})")
        else:
            logger.error(f"Registration failed: {response.get('message')}")

        return response

    def send_heartbeat(self, health_metrics):
        """
        Send heartbeat to dashboard

        Args:
            health_metrics: Health metrics dictionary

        Returns:
            dict: Heartbeat response with pending commands
        """
        agent_id = self.auth.agent_id

        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'health': health_metrics.get('system', {}),
            'suricata': health_metrics.get('suricata', {})
        }

        response = self._request('POST', f'/agents/{agent_id}/heartbeat', data)
        return response

    def send_event_batch(self, events):
        """
        Send batch of events via HTTP

        Args:
            events: List of event dictionaries

        Returns:
            dict: Response
        """
        agent_id = self.auth.agent_id

        data = {
            'agent_id': agent_id,
            'events': events
        }

        response = self._request('POST', '/events/batch', data, timeout=60)
        return response

    def send_log_batch(self, logs):
        """
        Send batch of log entries

        Args:
            logs: List of log dictionaries

        Returns:
            dict: Response
        """
        agent_id = self.auth.agent_id

        data = {
            'agent_id': agent_id,
            'logs': logs
        }

        response = self._request('POST', '/logs/batch', data, timeout=60)
        return response

    def send_config(self, config_type, content, content_hash):
        """
        Send current configuration to dashboard

        Args:
            config_type: Type of config (e.g., 'suricata.yaml')
            content: Config file content
            content_hash: SHA256 hash of content

        Returns:
            dict: Response
        """
        agent_id = self.auth.agent_id

        data = {
            'config_type': config_type,
            'content': content,
            'hash': content_hash
        }

        response = self._request('POST', f'/configs/{agent_id}', data)
        return response

    def send_command_result(self, command_id, status, result):
        """
        Send command execution result

        Args:
            command_id: Command ID
            status: Execution status (completed, failed, timeout)
            result: Result dictionary

        Returns:
            dict: Response
        """
        data = {
            'command_id': command_id,
            'status': status,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }

        response = self._request('POST', f'/commands/{command_id}/result', data)
        return response

    def health_check(self):
        """
        Check dashboard health

        Returns:
            bool: True if dashboard is reachable
        """
        try:
            response = self._request('GET', '/health', timeout=5)
            return response.get('success', False)
        except:
            return False
