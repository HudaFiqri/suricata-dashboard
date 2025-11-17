"""
Heartbeat and health monitoring module
"""

import threading
import time
import logging
import psutil
import os
import socket
from typing import Dict

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """Manages agent heartbeat and health monitoring"""

    def __init__(self, client, agent_name: str, agent_id: str, interval: int = 30):
        """Initialize heartbeat manager"""
        self.client = client
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        """Start heartbeat thread"""
        if self.running:
            logger.warning("Heartbeat manager already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        logger.info(f"Heartbeat manager started (interval: {self.interval}s)")

    def stop(self):
        """Stop heartbeat thread"""
        if not self.running:
            return

        logger.info("Stopping heartbeat manager...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        logger.info("Heartbeat manager stopped")

    def _heartbeat_loop(self):
        """Main heartbeat loop"""
        while self.running:
            try:
                # Collect health data
                health_data = self._collect_health_data()

                # Send heartbeat
                self.client.send_heartbeat(self.agent_id, health_data)

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            # Sleep until next heartbeat
            time.sleep(self.interval)

    def _collect_health_data(self) -> Dict:
        """Collect system health metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network stats
            net_io = psutil.net_io_counters()

            # Process info
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Check if Suricata is running
            suricata_running = self._check_suricata_running()
            suricata_pid = self._get_suricata_pid() if suricata_running else None
            suricata_version = self._get_suricata_version() if suricata_running else None

            # Get agent version
            try:
                import agent
                agent_version = agent.__version__
            except (ImportError, AttributeError):
                agent_version = '1.0.0'

            health_data = {
                'hostname': socket.gethostname(),
                'ip_address': self._get_local_ip(),
                'agent_version': agent_version,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'network_sent_bytes': net_io.bytes_sent,
                'network_recv_bytes': net_io.bytes_recv,
                'agent_memory_mb': process_memory,
                'suricata': {
                    'running': suricata_running,
                    'pid': suricata_pid,
                    'version': suricata_version
                }
            }

            return health_data

        except Exception as e:
            logger.error(f"Failed to collect health data: {e}")
            return {}

    def _check_suricata_running(self) -> bool:
        """Check if Suricata process is running"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'suricata':
                    return True
            return False
        except Exception:
            return False

    def _get_suricata_pid(self) -> int:
        """Get Suricata process ID"""
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] == 'suricata':
                    return proc.info['pid']
            return None
        except Exception:
            return None

    def _get_suricata_version(self) -> str:
        """Get Suricata version"""
        try:
            import subprocess
            result = subprocess.run(['suricata', '--version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                # Parse version from output like "This is Suricata version 7.0.0"
                output = result.stdout.strip()
                if 'version' in output.lower():
                    parts = output.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'version' and i + 1 < len(parts):
                            return parts[i + 1]
            return None
        except Exception:
            return None

    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
