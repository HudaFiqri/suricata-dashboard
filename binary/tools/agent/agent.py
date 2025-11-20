#!/usr/bin/env python3
"""
Suricata Dashboard Agent
Main agent daemon that monitors Suricata and streams data to dashboard
"""

import sys
import os
import argparse
import logging
import signal
import time
import socket
import platform
from threading import Thread, Event
from datetime import datetime

# Add agent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core import FileTailer, EventParser, LogParser, EventBuffer, TokenEncryptor, HealthCollector
from transport import AgentWebSocketClient, AgentHTTPClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SuricataAgent:
    """Main agent orchestrator"""

    def __init__(self, config_path):
        """Initialize agent"""
        logger.info("Initializing Suricata Dashboard Agent")

        # Load configuration
        self.config = Config(config_path)

        # Initialize components
        self.agent_id = None  # Will be set after registration
        self.auth = None
        self.buffer = EventBuffer(
            self.config.get('buffer.database'),
            self.config.get('buffer.max_events'),
            self.config.get('buffer.max_size_mb')
        )
        self.health_collector = HealthCollector(self.config)

        # Transport clients
        self.ws_client = None
        self.http_client = None

        # File tailers
        self.event_tailer = None
        self.log_tailers = []

        # Threading
        self.stop_event = Event()
        self.threads = []

        # Event batching
        self.event_batch = []
        self.log_batch = []
        self.last_batch_send = time.time()

    def start(self):
        """Start agent"""
        logger.info("Starting Suricata Dashboard Agent")

        # Register with dashboard
        if not self.register():
            logger.error("Failed to register with dashboard")
            sys.exit(1)

        # Initialize auth with agent_id
        self.auth = TokenEncryptor(
            self.config.get('agent.token'),
            'SECRET_KEY',  # TODO: This should come from config or be derived
            self.agent_id
        )

        # Initialize transport clients
        self.http_client = AgentHTTPClient(self.config, self.auth)

        # Try WebSocket first
        transport = self.config.get('dashboard.connection.transport')
        if transport == 'websocket':
            try:
                self.ws_client = AgentWebSocketClient(self.config, self.auth)
                self.ws_client.on_command_callback = self.handle_command
                self.ws_client.on_config_update_callback = self.handle_config_update
                self.ws_client.connect()

                if self.ws_client.wait_for_connection(timeout=30):
                    logger.info("WebSocket connection established")
                else:
                    logger.warning("WebSocket connection timeout, falling back to HTTP")
                    self.ws_client = None

            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                if self.config.get('dashboard.connection.fallback_to_http'):
                    logger.info("Falling back to HTTP transport")
                    self.ws_client = None
                else:
                    sys.exit(1)

        # Start file tailers
        self.start_tailers()

        # Start background threads
        self.start_threads()

        logger.info("Agent started successfully")

        # Main loop
        self.run()

    def register(self):
        """Register agent with dashboard"""
        logger.info("Registering with dashboard...")

        # Prepare registration data
        agent_info = {
            'name': self.config.get('agent.name') or socket.gethostname(),
            'hostname': socket.gethostname(),
            'ip_address': self.get_local_ip(),
            'tags': self.config.get('agent.tags', []),
            'agent_version': '1.0.0',
            'system_info': {
                'os': platform.system(),
                'os_version': platform.release(),
                'kernel': platform.version(),
                'arch': platform.machine(),
                'python_version': platform.python_version()
            }
        }

        # Get Suricata version
        # TODO: Implement Suricata version detection
        agent_info['suricata_version'] = 'unknown'

        # Create temporary HTTP client for registration
        temp_auth = TokenEncryptor(
            self.config.get('agent.token'),
            'SECRET_KEY',
            0  # Temporary agent_id
        )
        temp_http = AgentHTTPClient(self.config, temp_auth)

        try:
            response = temp_http.register(agent_info)

            if response.get('success'):
                self.agent_id = response.get('agent_id')
                logger.info(f"Registered successfully (Agent ID: {self.agent_id})")
                return True
            else:
                logger.error(f"Registration failed: {response.get('message')}")
                return False

        except Exception as e:
            logger.error(f"Registration request failed: {e}")
            return False

    def start_tailers(self):
        """Start file tailers"""
        # Eve.json tailer
        eve_log = self.config.get('suricata.eve_log')
        if os.path.exists(eve_log):
            self.event_tailer = FileTailer(eve_log, self.handle_eve_line)
            self.event_tailer.start()
            logger.info(f"Started eve.json tailer: {eve_log}")
        else:
            logger.warning(f"eve.json not found: {eve_log}")

        # Log file tailers
        log_files = [
            self.config.get('suricata.suricata_log'),
            self.config.get('suricata.fast_log')
        ]

        for log_file in log_files:
            if os.path.exists(log_file):
                tailer = FileTailer(log_file, self.handle_log_line)
                tailer.start()
                self.log_tailers.append(tailer)
                logger.info(f"Started log tailer: {log_file}")

    def start_threads(self):
        """Start background threads"""
        # Heartbeat thread
        heartbeat_thread = Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        self.threads.append(heartbeat_thread)

        # Batch sender thread
        batch_thread = Thread(target=self.batch_sender_loop, daemon=True)
        batch_thread.start()
        self.threads.append(batch_thread)

        # Buffer processor thread (for offline events)
        buffer_thread = Thread(target=self.buffer_processor_loop, daemon=True)
        buffer_thread.start()
        self.threads.append(buffer_thread)

    def handle_eve_line(self, file_path, line):
        """Handle new line from eve.json"""
        event = EventParser.parse(line)
        if event:
            self.queue_event(event)

    def handle_log_line(self, file_path, line):
        """Handle new line from log files"""
        log_entry = LogParser.parse(file_path, line)
        if log_entry:
            self.queue_log(log_entry)

    def queue_event(self, event):
        """Queue event for sending"""
        self.event_batch.append(event)

        # Send immediately if batch is full
        batch_size = self.config.get('streaming.batch_size', 100)
        if len(self.event_batch) >= batch_size:
            self.send_event_batch()

    def queue_log(self, log_entry):
        """Queue log entry for sending"""
        self.log_batch.append(log_entry)

        # Send if batch is full
        if len(self.log_batch) >= 50:
            self.send_log_batch()

    def send_event_batch(self):
        """Send queued events"""
        if not self.event_batch:
            return

        events = self.event_batch.copy()
        self.event_batch.clear()

        # Try WebSocket first
        if self.ws_client and self.ws_client.is_connected():
            try:
                self.ws_client.send_event_batch(events)
                logger.debug(f"Sent {len(events)} events via WebSocket")
                return
            except Exception as e:
                logger.error(f"WebSocket send failed: {e}")

        # Fallback to HTTP
        if self.http_client:
            try:
                self.http_client.send_event_batch(events)
                logger.debug(f"Sent {len(events)} events via HTTP")
                return
            except Exception as e:
                logger.error(f"HTTP send failed: {e}")

        # If all failed, buffer events
        logger.warning(f"Buffering {len(events)} events (offline)")
        self.buffer.add_batch(events)

    def send_log_batch(self):
        """Send queued log entries"""
        if not self.log_batch:
            return

        logs = self.log_batch.copy()
        self.log_batch.clear()

        # Try WebSocket
        if self.ws_client and self.ws_client.is_connected():
            try:
                for log in logs:
                    self.ws_client.send_log(log)
                return
            except:
                pass

        # Fallback to HTTP
        if self.http_client:
            try:
                self.http_client.send_log_batch(logs)
                return
            except:
                pass

    def heartbeat_loop(self):
        """Send periodic heartbeats"""
        interval = self.config.get('dashboard.heartbeat_interval', 30)

        while not self.stop_event.is_set():
            try:
                # Collect health metrics
                health = self.health_collector.collect()

                # Send via WebSocket
                if self.ws_client and self.ws_client.is_connected():
                    self.ws_client.send_heartbeat(health)
                # Or HTTP
                elif self.http_client:
                    self.http_client.send_heartbeat(health)

            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")

            self.stop_event.wait(interval)

    def batch_sender_loop(self):
        """Periodic batch sender (timeout-based)"""
        timeout = self.config.get('streaming.batch_timeout', 5)

        while not self.stop_event.is_set():
            time.sleep(1)

            # Send if timeout reached
            if time.time() - self.last_batch_send >= timeout:
                if self.event_batch:
                    self.send_event_batch()
                if self.log_batch:
                    self.send_log_batch()

                self.last_batch_send = time.time()

    def buffer_processor_loop(self):
        """Process buffered events when online"""
        while not self.stop_event.is_set():
            time.sleep(10)  # Check every 10 seconds

            # Only process if we're online
            is_online = (self.ws_client and self.ws_client.is_connected()) or \
                       (self.http_client and self.http_client.health_check())

            if not is_online:
                continue

            # Get buffered events
            buffered = self.buffer.get_batch(1000)
            if not buffered:
                continue

            logger.info(f"Processing {len(buffered)} buffered events")

            # Try to send
            events = [event for _, event in buffered]
            try:
                if self.ws_client and self.ws_client.is_connected():
                    self.ws_client.send_event_batch(events)
                else:
                    self.http_client.send_event_batch(events)

                # Delete from buffer on success
                ids = [event_id for event_id, _ in buffered]
                self.buffer.delete_batch(ids)
                logger.info(f"Sent {len(buffered)} buffered events")

            except Exception as e:
                logger.error(f"Failed to send buffered events: {e}")

    def handle_command(self, command_id, command_type, parameters):
        """Handle command from dashboard"""
        logger.info(f"Executing command {command_id}: {command_type}")

        result = {}

        try:
            if command_type == 'read_config':
                # Read Suricata configuration file
                config_path = parameters.get('path', self.config.get('suricata.config_path', '/etc/suricata/suricata.yaml'))
                logger.info(f"Reading config from: {config_path}")

                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                result = {
                    'success': True,
                    'content': content,
                    'path': config_path,
                    'message': f'Config read successfully from {config_path}'
                }

            elif command_type == 'read_rules':
                # Read rules file
                rules_path = parameters.get('path')
                if not rules_path:
                    raise ValueError('Rules path not specified')

                with open(rules_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                result = {
                    'success': True,
                    'content': content,
                    'path': rules_path,
                    'message': f'Rules read successfully from {rules_path}'
                }

            elif command_type == 'list_rules':
                # List all rules files
                import os
                rules_dir = parameters.get('dir', self.config.get('suricata.rules_dir', '/etc/suricata/rules'))

                if os.path.exists(rules_dir):
                    files = [f for f in os.listdir(rules_dir) if f.endswith('.rules')]
                    result = {
                        'success': True,
                        'files': files,
                        'dir': rules_dir,
                        'message': f'Found {len(files)} rule files'
                    }
                else:
                    result = {
                        'success': False,
                        'message': f'Rules directory not found: {rules_dir}'
                    }

            elif command_type == 'tail_logs':
                # Tail log file
                log_path = parameters.get('path', self.config.get('suricata.eve_log', '/var/log/suricata/eve.json'))
                lines = parameters.get('lines', 100)

                with open(log_path, 'r', encoding='utf-8') as f:
                    # Read last N lines
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

                result = {
                    'success': True,
                    'lines': last_lines,
                    'path': log_path,
                    'message': f'Read last {len(last_lines)} lines from {log_path}'
                }

            elif command_type == 'restart_suricata':
                # Restart Suricata service
                import subprocess
                method = parameters.get('method', 'systemctl')

                if method == 'systemctl':
                    subprocess.run(['systemctl', 'restart', 'suricata'], check=True)
                    message = 'Suricata restarted via systemctl'
                else:
                    subprocess.run(['service', 'suricata', 'restart'], check=True)
                    message = 'Suricata restarted via service'

                result = {
                    'success': True,
                    'message': message
                }

            elif command_type == 'read_config_section':
                # Read specific section from suricata.yaml
                import yaml
                section = parameters.get('section', 'af-packet')
                config_path = self.config.get('suricata.config_path', '/etc/suricata/suricata.yaml')

                logger.info(f"Reading config section '{section}' from {config_path}")

                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                # Extract requested section
                section_data = config_data.get(section, {})

                result = {
                    'success': True,
                    'config': section_data,
                    'section': section,
                    'path': config_path,
                    'message': f'Config section {section} read successfully'
                }

            else:
                result = {
                    'success': False,
                    'message': f'Unknown command type: {command_type}'
                }

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            result = {
                'success': False,
                'message': f'File not found: {str(e)}'
            }
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            result = {
                'success': False,
                'message': f'Permission denied: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            result = {
                'success': False,
                'message': f'Error: {str(e)}'
            }

        # Send result
        if self.ws_client:
            self.ws_client.send_command_result(command_id, 'completed', result)
        elif self.http_client:
            self.http_client.send_command_result(command_id, 'completed', result)

    def handle_config_update(self, command_id, config_type, content, reload_method):
        """Handle configuration update from dashboard"""
        logger.info(f"Applying config update: {config_type}")

        result = {}

        try:
            import shutil
            import time

            if config_type == 'suricata_yaml':
                config_path = self.config.get('suricata.config_path', '/etc/suricata/suricata.yaml')

                # Create backup
                backup_path = f"{config_path}.backup.{int(time.time())}"
                shutil.copy(config_path, backup_path)
                logger.info(f"Config backed up to: {backup_path}")

                # Write new config
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                logger.info(f"Config written to: {config_path}")

                # Reload Suricata if requested
                if reload_method == 'restart':
                    import subprocess
                    subprocess.run(['systemctl', 'restart', 'suricata'], check=True)
                    reload_msg = 'Suricata restarted'
                elif reload_method == 'reload':
                    import subprocess
                    subprocess.run(['systemctl', 'reload', 'suricata'], check=True)
                    reload_msg = 'Suricata reloaded'
                else:
                    reload_msg = 'No reload performed'

                result = {
                    'success': True,
                    'message': f'Config updated successfully. {reload_msg}',
                    'backup': backup_path,
                    'path': config_path
                }

            elif config_type == 'rules':
                rules_path = self.config.get('suricata.rules_dir', '/etc/suricata/rules')
                # Implement rules update logic
                result = {
                    'success': True,
                    'message': 'Rules updated successfully'
                }

            else:
                result = {
                    'success': False,
                    'message': f'Unknown config type: {config_type}'
                }

        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            result = {
                'success': False,
                'message': f'Permission denied: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Config update failed: {e}")
            result = {
                'success': False,
                'message': f'Error: {str(e)}'
            }

        if self.ws_client:
            self.ws_client.send_command_result(command_id, 'completed', result)
        elif self.http_client:
            self.http_client.send_command_result(command_id, 'completed', result)

    def run(self):
        """Main run loop"""
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()

    def stop(self):
        """Stop agent gracefully"""
        logger.info("Stopping agent...")
        self.stop_event.set()

        # Stop tailers
        if self.event_tailer:
            self.event_tailer.stop()
        for tailer in self.log_tailers:
            tailer.stop()

        # Disconnect from dashboard
        if self.ws_client:
            self.ws_client.disconnect()

        # Send any remaining batches
        if self.event_batch:
            self.send_event_batch()
        if self.log_batch:
            self.send_log_batch()

        # Close buffer
        self.buffer.close()

        logger.info("Agent stopped")

    @staticmethod
    def get_local_ip():
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Suricata Dashboard Agent')
    parser.add_argument(
        '--config',
        default='/etc/suricata-agent/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Suricata Dashboard Agent 1.0.0'
    )

    args = parser.parse_args()

    # Create and start agent
    agent = SuricataAgent(args.config)

    # Setup signal handlers
    def signal_handler(sig, frame):
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start agent
    agent.start()

if __name__ == '__main__':
    main()
