"""
Health Metrics Collector
Collects system and Suricata health metrics
"""

import os
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCollector:
    """Collect system and Suricata health metrics"""

    def __init__(self, config):
        """
        Initialize health collector

        Args:
            config: Agent configuration object
        """
        self.config = config
        self.suricata_pid_file = config.get('suricata.pid_file')

    def collect(self):
        """
        Collect all health metrics

        Returns:
            dict: Health metrics
        """
        return {
            'system': self.collect_system_metrics(),
            'suricata': self.collect_suricata_metrics()
        }

    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            memory_percent = memory.percent

            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network
            net_io = psutil.net_io_counters()

            # Uptime
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time

            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_used_mb': round(memory_used_mb, 2),
                'memory_total_mb': round(memory_total_mb, 2),
                'memory_percent': round(memory_percent, 2),
                'disk_percent': round(disk_percent, 2),
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'uptime_seconds': int(uptime_seconds)
            }

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    def collect_suricata_metrics(self):
        """Collect Suricata-specific metrics"""
        try:
            metrics = {
                'running': False,
                'pid': None,
                'cpu_percent': 0,
                'memory_mb': 0,
                'uptime_seconds': 0
            }

            # Get Suricata PID
            pid = self.get_suricata_pid()

            if pid:
                try:
                    process = psutil.Process(pid)

                    metrics['running'] = process.is_running()
                    metrics['pid'] = pid
                    metrics['cpu_percent'] = round(process.cpu_percent(interval=0.1), 2)
                    metrics['memory_mb'] = round(process.memory_info().rss / (1024 * 1024), 2)

                    # Uptime
                    create_time = process.create_time()
                    uptime = datetime.now().timestamp() - create_time
                    metrics['uptime_seconds'] = int(uptime)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    metrics['running'] = False

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect Suricata metrics: {e}")
            return {}

    def get_suricata_pid(self):
        """
        Get Suricata PID from pid file or process list

        Returns:
            int: PID or None
        """
        # Try pid file first
        if self.suricata_pid_file and os.path.exists(self.suricata_pid_file):
            try:
                with open(self.suricata_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    return pid
            except (ValueError, IOError):
                pass

        # Fall back to process search
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] == 'Suricata':
                    return proc.info['pid']
        except:
            pass

        return None

    def is_suricata_running(self):
        """Check if Suricata is running"""
        pid = self.get_suricata_pid()
        if not pid:
            return False

        try:
            process = psutil.Process(pid)
            return process.is_running()
        except:
            return False
