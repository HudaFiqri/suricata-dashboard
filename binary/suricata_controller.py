import subprocess
import psutil
import os
import time
from typing import Dict, Optional, Any
from .suricata_process import SuricataProcess
from .suricata_config import SuricataConfig
from .suricata_rule_manager import SuricataRuleManager
from .suricata_log_manager import SuricataLogManager

class SuricataController:
    def __init__(self, 
                 binary_path: str = "suricata",
                 config_path: str = "/etc/suricata/suricata.yaml",
                 rules_directory: str = "/etc/suricata/rules",
                 log_directory: str = "/var/log/suricata"):
        
        self.binary_path = binary_path
        self.config = SuricataConfig(config_path)
        self.rule_manager = SuricataRuleManager(rules_directory)
        self.log_manager = SuricataLogManager(log_directory)
        
        self._current_process: Optional[SuricataProcess] = None
    
    def get_status(self) -> Dict[str, Any]:
        try:
            process = self._find_suricata_process()
            if process:
                self._current_process = process
                return {
                    'status': 'running',
                    'pid': process.pid,
                    'uptime': process.uptime,
                    'cmdline': ' '.join(process.cmdline)
                }
            else:
                self._current_process = None
                return {'status': 'stopped'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def start(self, interface: str = None, daemon: bool = True) -> Dict[str, Any]:
        try:
            current_status = self.get_status()
            if current_status['status'] == 'running':
                return {'success': False, 'message': 'Suricata is already running'}
            
            # Clean stale PID file
            self._clean_stale_pid_file()
            
            if not interface:
                interfaces = self.config.get_interfaces()
                if interfaces:
                    interface = interfaces[0]
                else:
                    interface = 'eth0'
            
            cmd = [self.binary_path, '-c', self.config.config_path, '-i', interface]
            if daemon:
                cmd.append('-D')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                if daemon:
                    # Wait longer and retry process detection
                    for attempt in range(5):
                        time.sleep(1)
                        new_status = self.get_status()
                        if new_status['status'] == 'running':
                            return {'success': True, 'message': f'Suricata started successfully on interface {interface}'}
                    
                    # Check if process started but exited quickly
                    return {'success': False, 'message': f'Suricata command executed but process not found. Check logs: {result.stdout}'}
                else:
                    return {'success': True, 'message': f'Suricata started in foreground mode on interface {interface}'}
            else:
                return {'success': False, 'message': f'Failed to start Suricata: {result.stderr}'}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Suricata start command timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error starting Suricata: {e}'}
    
    def stop(self, force: bool = False) -> Dict[str, Any]:
        try:
            cmd = ['systemctl', 'stop', 'suricata']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self._current_process = None
                return {'success': True, 'message': 'Suricata service stopped successfully'}
            else:
                return {'success': False, 'message': f'Failed to stop Suricata service: {result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Stop command timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error stopping Suricata: {e}'}
    
    def restart(self, interface: str = None) -> Dict[str, Any]:
        stop_result = self.stop()
        if stop_result['success'] or 'not running' in stop_result['message']:
            time.sleep(2)  # Wait a bit between stop and start
            return self.start(interface)
        return stop_result
    
    def reload_rules(self) -> Dict[str, Any]:
        try:
            process = self._find_suricata_process()
            if not process:
                return {'success': False, 'message': 'Suricata is not running'}
            
            psutil_process = psutil.Process(process.pid)
            psutil_process.send_signal(2)  # SIGUSR2 for rule reload
            
            return {'success': True, 'message': 'Rules reload signal sent to Suricata'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error reloading rules: {e}'}
    
    def validate_config(self) -> Dict[str, Any]:
        try:
            cmd = [self.binary_path, '-T', '-c', self.config.config_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Configuration is valid'}
            else:
                return {'success': False, 'message': f'Configuration validation failed: {result.stderr}'}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'message': 'Configuration validation timed out'}
        except Exception as e:
            return {'success': False, 'message': f'Error validating configuration: {e}'}
    
    def _find_suricata_process(self) -> Optional[SuricataProcess]:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                proc_name = proc.info['name']
                cmdline = proc.info['cmdline'] or []
                
                # Check process name or command line for suricata
                if (proc_name and 'suricata' in proc_name.lower()) or \
                   (cmdline and any('suricata' in str(cmd).lower() for cmd in cmdline)):
                    return SuricataProcess(proc.info['pid'], cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def _clean_stale_pid_file(self) -> None:
        """Remove stale PID files if Suricata is not actually running"""
        pid_files = ['/var/run/suricata.pid', '/run/suricata.pid']
        
        for pid_file in pid_files:
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Check if process with this PID exists and is Suricata
                    try:
                        proc = psutil.Process(pid)
                        if 'suricata' not in proc.name().lower():
                            # PID exists but not Suricata, remove stale file
                            os.remove(pid_file)
                    except psutil.NoSuchProcess:
                        # PID doesn't exist, remove stale file
                        os.remove(pid_file)
                        
                except (ValueError, IOError, PermissionError):
                    # Can't read/remove file, try to continue anyway
                    pass
    
    def get_system_info(self) -> Dict[str, Any]:
        return {
            'platform': os.name,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }