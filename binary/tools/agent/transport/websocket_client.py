"""
WebSocket Client for Agent
Real-time bidirectional communication with dashboard
"""

import socketio
import logging
import time
from datetime import datetime
from threading import Thread

logger = logging.getLogger(__name__)

class AgentWebSocketClient:
    """WebSocket client using Socket.IO"""

    def __init__(self, config, auth):
        """
        Initialize WebSocket client

        Args:
            config: Agent configuration
            auth: TokenEncryptor instance
        """
        self.config = config
        self.auth = auth
        self.sio = None
        self.connected = False
        self.authenticated = False

        # Callbacks
        self.on_command_callback = None
        self.on_config_update_callback = None

        self._setup_client()

    def _setup_client(self):
        """Setup Socket.IO client with handlers"""
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite
            reconnection_delay=self.config.get('dashboard.connection.reconnect_interval', 5),
            reconnection_delay_max=self.config.get('dashboard.connection.max_reconnect_delay', 300),
            logger=False,
            engineio_logger=False
        )

        # Register event handlers
        @self.sio.on('connect', namespace='/ws/v1/agent')
        def on_connect():
            logger.info("Connected to dashboard WebSocket")
            self.connected = True
            self._authenticate()

        @self.sio.on('disconnect', namespace='/ws/v1/agent')
        def on_disconnect():
            logger.warning("Disconnected from dashboard WebSocket")
            self.connected = False
            self.authenticated = False

        @self.sio.on('auth_response', namespace='/ws/v1/agent')
        def on_auth_response(data):
            if data.get('success'):
                logger.info("WebSocket authentication successful")
                self.authenticated = True

                # Store server config
                server_config = data.get('config', {})
                logger.debug(f"Server config: {server_config}")
            else:
                logger.error(f"WebSocket authentication failed: {data.get('error')}")
                self.sio.disconnect()

        @self.sio.on('event_ack', namespace='/ws/v1/agent')
        def on_event_ack(data):
            sequence = data.get('sequence')
            logger.debug(f"Event acknowledged: {sequence}")

        @self.sio.on('event_batch_ack', namespace='/ws/v1/agent')
        def on_batch_ack(data):
            logger.debug(f"Batch acknowledged: {data.get('processed')} processed, {data.get('failed')} failed")

        @self.sio.on('command', namespace='/ws/v1/agent')
        def on_command(data):
            command_id = data.get('command_id')
            command_type = data.get('command_type')
            parameters = data.get('parameters', {})

            logger.info(f"Received command {command_id}: {command_type}")

            if self.on_command_callback:
                try:
                    self.on_command_callback(command_id, command_type, parameters)
                except Exception as e:
                    logger.error(f"Command callback error: {e}")

        @self.sio.on('config_update', namespace='/ws/v1/agent')
        def on_config_update(data):
            command_id = data.get('command_id')
            config_type = data.get('config_type')
            content = data.get('content')
            reload_method = data.get('reload_method', 'graceful')

            logger.info(f"Received config update: {config_type}")

            if self.on_config_update_callback:
                try:
                    self.on_config_update_callback(command_id, config_type, content, reload_method)
                except Exception as e:
                    logger.error(f"Config update callback error: {e}")

        @self.sio.on('heartbeat_ack', namespace='/ws/v1/agent')
        def on_heartbeat_ack(data):
            # Check for pending commands
            pending_commands = data.get('pending_commands', [])
            if pending_commands:
                logger.info(f"Received {len(pending_commands)} pending commands")
                for cmd in pending_commands:
                    on_command(cmd)

    def connect(self):
        """Connect to dashboard WebSocket"""
        ws_url = self.config.get('dashboard.connection.websocket_url')

        logger.info(f"Connecting to WebSocket: {ws_url}")

        try:
            self.sio.connect(
                ws_url,
                namespaces=['/ws/v1/agent'],
                transports=['websocket']
            )

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    def disconnect(self):
        """Disconnect from dashboard"""
        if self.sio and self.connected:
            self.sio.disconnect()
            logger.info("Disconnected from WebSocket")

    def _authenticate(self):
        """Send authentication message"""
        encrypted_token = self.auth.encrypt()

        self.sio.emit('auth', {
            'agent_id': self.auth.agent_id,
            'token': encrypted_token,
            'agent_version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    def send_event(self, event, sequence=None):
        """Send single event"""
        if not self.authenticated:
            logger.warning("Cannot send event: not authenticated")
            return False

        self.sio.emit('event', {
            'event_type': event.get('event_type'),
            'data': event.get('data'),
            'sequence': sequence,
            'timestamp': event.get('timestamp') or datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

        return True

    def send_event_batch(self, events, sequence=None):
        """Send batch of events"""
        if not self.authenticated:
            logger.warning("Cannot send batch: not authenticated")
            return False

        self.sio.emit('event_batch', {
            'events': events,
            'sequence': sequence,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

        return True

    def send_log(self, log_entry):
        """Send log entry"""
        if not self.authenticated:
            return False

        self.sio.emit('log', log_entry, namespace='/ws/v1/agent')
        return True

    def send_heartbeat(self, health_metrics):
        """Send heartbeat with health metrics"""
        if not self.authenticated:
            return False

        self.sio.emit('heartbeat', {
            'health': health_metrics.get('system', {}),
            'suricata': health_metrics.get('suricata', {}),
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

        return True

    def send_command_result(self, command_id, status, result):
        """Send command execution result"""
        if not self.authenticated:
            return False

        self.sio.emit('command_result', {
            'command_id': command_id,
            'status': status,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

        return True

    def is_connected(self):
        """Check if connected and authenticated"""
        return self.connected and self.authenticated

    def wait_for_connection(self, timeout=30):
        """Wait for connection to be established"""
        start_time = time.time()
        while not self.is_connected():
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.5)
        return True
