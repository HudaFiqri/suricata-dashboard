import subprocess
import psutil
import os
import time
from typing import Dict, Optional, Any

class SuricataBackendController:
    """Backend controller for Suricata service management using systemctl"""

    def __init__(self,
                 binary_path: str = "suricata",
                 config_path: str = "/etc/suricata/suricata.yaml"):
        self.binary_path = binary_path
        self.config_path = config_path

    def get_status(self) -> Dict[str, Any]:
        """Get Suricata service status using systemctl"""
        try:
            cmd = ['systemctl', 'is-active', 'suricata']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip() == 'active':
                cmd_status = ['systemctl', 'status', 'suricata']
                status_result = subprocess.run(cmd_status, capture_output=True, text=True)

                pid: Optional[int] = None
                for line in status_result.stdout.split('\n'):
                    if 'Main PID:' in line:
                        pid_part = line.split('Main PID:')[1].strip().split()[0]
                        try:
                            pid = int(pid_part)
                        except ValueError:
                            pid = None
                        break

                uptime = None
                uptime_seconds: Optional[int] = None
                if pid:
                    try:
                        process = psutil.Process(pid)
                        uptime_seconds = max(int(time.time() - process.create_time()), 0)
                        uptime = self._format_duration(uptime_seconds)
                    except (psutil.Error, OSError, ValueError):
                        uptime = None
                        uptime_seconds = None

                return {
                    'status': 'running',
                    'running': True,
                    'pid': pid if pid else 'N/A',
                    'uptime': uptime,
                    'uptime_seconds': uptime_seconds
                }
            else:
                return {'status': 'stopped', 'running': False}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'running': False}


    @staticmethod
    def _format_duration(total_seconds: int) -> str:
        """Format uptime seconds into a compact human-readable string"""
        if total_seconds <= 0:
            return '0s'

        periods = [
            ('d', 86400),
            ('h', 3600),
            ('m', 60),
            ('s', 1),
        ]
        parts = []
        remainder = total_seconds
        for suffix, length in periods:
            value, remainder = divmod(remainder, length)
            if value:
                parts.append(f"{value}{suffix}")

        return ' '.join(parts) or '0s'

    def start(self) -> Dict[str, Any]:
        """Start Suricata service using systemctl"""
        try:
            current_status = self.get_status()
            if current_status['status'] == 'running':
                return {'success': False, 'message': 'Suricata is already running'}

            cmd = ['systemctl', 'start', 'suricata']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                time.sleep(2)
                new_status = self.get_status()
                if new_status['status'] == 'running':
                    return {'success': True, 'message': 'Suricata service started successfully'}
                else:
                    return {'success': False, 'message': 'Suricata service command executed but not running. Check logs.'}
            else:
                return {'success': False, 'message': f'Failed to start Suricata service: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Start command timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error starting Suricata: {e}'}

    def stop(self) -> Dict[str, Any]:
        """Stop Suricata service using systemctl"""
        try:
            cmd = ['systemctl', 'stop', 'suricata']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {'success': True, 'message': 'Suricata service stopped successfully'}
            else:
                return {'success': False, 'message': f'Failed to stop Suricata service: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Stop command timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error stopping Suricata: {e}'}

    def restart(self) -> Dict[str, Any]:
        """Restart Suricata service using systemctl"""
        try:
            cmd = ['systemctl', 'restart', 'suricata']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                time.sleep(2)
                new_status = self.get_status()
                if new_status['status'] == 'running':
                    return {'success': True, 'message': 'Suricata service restarted successfully'}
                else:
                    return {'success': False, 'message': 'Suricata restart command executed but not running. Check logs.'}
            else:
                return {'success': False, 'message': f'Failed to restart Suricata service: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Restart command timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error restarting Suricata: {e}'}

    def reload_rules(self) -> Dict[str, Any]:
        """Reload Suricata rules by sending signal to process"""
        try:
            status = self.get_status()
            if status['status'] != 'running':
                return {'success': False, 'message': 'Suricata is not running'}

            pid = status.get('pid')
            if not pid or pid == 'N/A':
                return {'success': False, 'message': 'Cannot find Suricata PID'}

            psutil_process = psutil.Process(pid)
            psutil_process.send_signal(2)  # SIGUSR2 for rule reload

            return {'success': True, 'message': 'Rules reload signal sent to Suricata'}

        except Exception as e:
            return {'success': False, 'message': f'Error reloading rules: {e}'}

    def validate_config(self) -> Dict[str, Any]:
        """Validate Suricata configuration"""
        try:
            cmd = [self.binary_path, '-T', '-c', self.config_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {'success': True, 'message': 'Configuration is valid'}
            else:
                return {'success': False, 'message': f'Configuration validation failed: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Configuration validation timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error validating configuration: {e}'}

    def get_service_info(self) -> Dict[str, Any]:
        """Get detailed service information"""
        try:
            cmd = ['systemctl', 'show', 'suricata', '--no-pager']
            result = subprocess.run(cmd, capture_output=True, text=True)

            info = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value

            return info
        except Exception as e:
            return {'error': str(e)}

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'platform': os.name,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }
