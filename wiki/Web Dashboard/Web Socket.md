# WebSocket & Real-time Architecture

## Overview

Real-time bidirectional communication using WebSocket protocol for:
- Event streaming (Agent → Dashboard → Web UI)
- Command execution (Web UI → Dashboard → Agent)
- Live monitoring and updates

**Technology**: Flask-SocketIO (Socket.IO protocol over WebSocket)

---

## Architecture

```
┌──────────────┐         WebSocket          ┌───────────────┐
│    Agent     │─────────────────────────────│   Dashboard   │
│  (Remote)    │   /ws/v1/agent             │    Server     │
│              │◄────────────────────────────│               │
└──────────────┘      Commands               │               │
                                             │               │
                                             │               │
┌──────────────┐         WebSocket          │               │
│   Web UI     │─────────────────────────────│               │
│  (Browser)   │   /ws/v1/ui                │               │
│              │◄────────────────────────────│               │
└──────────────┘   Real-time Updates         └───────────────┘

Data Flow:
  1. Agent sends events → Dashboard receives
  2. Dashboard stores in MongoDB
  3. Dashboard broadcasts to Web UI clients
  4. Web UI displays in real-time
```

---

## Server Implementation

### 1. Setup Flask-SocketIO

**File**: `apps/__init__.py`

```python
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Enable CORS for WebSocket
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',  # or 'eventlet', 'threading'
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Import WebSocket handlers
from apps.websocket import register_handlers
register_handlers(socketio)
```

### 2. WebSocket Server Handler

**File**: `apps/websocket/server.py`

```python
"""
WebSocket server for handling agent and UI connections.
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
import logging

logger = logging.getLogger(__name__)

# Track active connections
active_agents = {}  # {session_id: agent_info}
active_ui_clients = {}  # {session_id: user_info}

def register_handlers(socketio):
    """Register all WebSocket event handlers"""

    # ========== Agent Namespace (/ws/v1/agent) ==========

    @socketio.on('connect', namespace='/ws/v1/agent')
    def handle_agent_connect():
        """Agent establishes WebSocket connection"""
        session_id = request.sid
        logger.info(f"Agent connecting: {session_id}")

        # Return connection acknowledgment
        emit('connected', {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio.on('auth', namespace='/ws/v1/agent')
    def handle_agent_auth(data):
        """Authenticate agent"""
        session_id = request.sid
        agent_id = data.get('agent_id')
        encrypted_token = data.get('token')

        # Validate token
        from apps.lib.auth import validate_agent_token
        if not validate_agent_token(encrypted_token, agent_id):
            logger.warning(f"Agent auth failed: {agent_id}")
            emit('auth_response', {'success': False, 'error': 'Invalid token'})
            disconnect()
            return

        # Get agent from DB
        from apps.models import Agent
        agent = Agent.query.get(agent_id)
        if not agent:
            emit('auth_response', {'success': False, 'error': 'Agent not found'})
            disconnect()
            return

        # Store in active connections
        active_agents[session_id] = {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'connected_at': datetime.utcnow()
        }

        # Join agent-specific room
        join_room(f'agent_{agent_id}')

        # Update agent status
        agent.status = 'online'
        agent.last_seen = datetime.utcnow()
        db.session.commit()

        # Broadcast to UI clients
        socketio.emit('agent_status', {
            'agent_id': agent_id,
            'status': 'online'
        }, namespace='/ws/v1/ui')

        logger.info(f"Agent authenticated: {agent.name} (ID: {agent_id})")

        # Send auth success with config
        emit('auth_response', {
            'success': True,
            'config': {
                'heartbeat_interval': 30,
                'batch_size': 100,
                'compression': True
            }
        })

    @socketio.on('event', namespace='/ws/v1/agent')
    def handle_event(data):
        """Receive single event from agent"""
        session_id = request.sid
        if session_id not in active_agents:
            logger.warning(f"Unauthenticated event from {session_id}")
            return

        agent_info = active_agents[session_id]
        agent_id = agent_info['agent_id']

        # Process event
        from apps.lib.event_processor import EventProcessor
        processor = EventProcessor()
        processor.process(agent_id, data)

        # Acknowledge
        sequence = data.get('sequence')
        if sequence:
            emit('event_ack', {'sequence': sequence})

        # Broadcast to UI clients
        socketio.emit('new_event', {
            'agent_id': agent_id,
            'agent_name': agent_info['agent_name'],
            'event': data
        }, namespace='/ws/v1/ui', room='events')

    @socketio.on('event_batch', namespace='/ws/v1/agent')
    def handle_event_batch(data):
        """Receive batch of events from agent"""
        session_id = request.sid
        if session_id not in active_agents:
            return

        agent_info = active_agents[session_id]
        agent_id = agent_info['agent_id']

        events = data.get('events', [])
        logger.info(f"Received batch of {len(events)} events from agent {agent_id}")

        # Process events in bulk
        from apps.lib.event_processor import EventProcessor
        processor = EventProcessor()
        results = processor.process_batch(agent_id, events)

        # Acknowledge
        emit('event_batch_ack', {
            'sequence': data.get('sequence'),
            'processed': results['processed'],
            'failed': results['failed']
        })

        # Broadcast summary to UI
        socketio.emit('event_batch_received', {
            'agent_id': agent_id,
            'count': len(events)
        }, namespace='/ws/v1/ui')

    @socketio.on('log', namespace='/ws/v1/agent')
    def handle_log(data):
        """Receive log entry from agent"""
        session_id = request.sid
        if session_id not in active_agents:
            return

        agent_info = active_agents[session_id]
        agent_id = agent_info['agent_id']

        # Store in MongoDB
        from apps.database import mongo_db
        mongo_db.logs.insert_one({
            'agent_id': agent_id,
            'agent_name': agent_info['agent_name'],
            'timestamp': datetime.fromisoformat(data['timestamp']),
            'level': data['level'],
            'message': data['message'],
            'raw_line': data['raw_line'],
            'received_at': datetime.utcnow()
        })

        # Broadcast to UI clients watching logs
        socketio.emit('new_log', {
            'agent_id': agent_id,
            'agent_name': agent_info['agent_name'],
            'log': data
        }, namespace='/ws/v1/ui', room='logs')

    @socketio.on('heartbeat', namespace='/ws/v1/agent')
    def handle_heartbeat(data):
        """Agent heartbeat"""
        session_id = request.sid
        if session_id not in active_agents:
            return

        agent_info = active_agents[session_id]
        agent_id = agent_info['agent_id']

        # Update last_seen
        from apps.models import Agent
        agent = Agent.query.get(agent_id)
        if agent:
            agent.last_seen = datetime.utcnow()
            agent.health_metrics = data.get('health', {})
            db.session.commit()

        # Check for pending commands
        from apps.models import AgentCommand
        pending_commands = AgentCommand.query.filter_by(
            agent_id=agent_id,
            status='pending'
        ).limit(10).all()

        commands = []
        for cmd in pending_commands:
            commands.append({
                'command_id': cmd.id,
                'command_type': cmd.command_type,
                'parameters': cmd.parameters
            })
            cmd.status = 'sent'
            cmd.sent_at = datetime.utcnow()

        db.session.commit()

        # Respond with pending commands
        emit('heartbeat_ack', {
            'pending_commands': commands
        })

    @socketio.on('command_result', namespace='/ws/v1/agent')
    def handle_command_result(data):
        """Agent reports command execution result"""
        session_id = request.sid
        if session_id not in active_agents:
            return

        command_id = data.get('command_id')
        status = data.get('status')
        result = data.get('result', {})

        # Update command in DB
        from apps.models import AgentCommand
        cmd = AgentCommand.query.get(command_id)
        if cmd:
            cmd.status = status
            cmd.result = result
            cmd.completed_at = datetime.utcnow()
            db.session.commit()

            # Notify UI clients
            socketio.emit('command_completed', {
                'command_id': command_id,
                'status': status,
                'result': result
            }, namespace='/ws/v1/ui', room=f'agent_{cmd.agent_id}')

    @socketio.on('disconnect', namespace='/ws/v1/agent')
    def handle_agent_disconnect():
        """Agent disconnects"""
        session_id = request.sid
        if session_id in active_agents:
            agent_info = active_agents[session_id]
            agent_id = agent_info['agent_id']

            # Update status
            from apps.models import Agent
            agent = Agent.query.get(agent_id)
            if agent:
                agent.status = 'offline'
                db.session.commit()

            # Broadcast to UI
            socketio.emit('agent_status', {
                'agent_id': agent_id,
                'status': 'offline'
            }, namespace='/ws/v1/ui')

            logger.info(f"Agent disconnected: {agent_info['agent_name']}")
            del active_agents[session_id]

    # ========== UI Namespace (/ws/v1/ui) ==========

    @socketio.on('connect', namespace='/ws/v1/ui')
    def handle_ui_connect():
        """Web UI client connects"""
        session_id = request.sid
        logger.info(f"UI client connecting: {session_id}")

        emit('connected', {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    @socketio.on('auth', namespace='/ws/v1/ui')
    def handle_ui_auth(data):
        """Authenticate UI client (JWT token)"""
        session_id = request.sid
        token = data.get('token')

        # Validate JWT
        from apps.lib.auth import validate_jwt
        user = validate_jwt(token)
        if not user:
            emit('auth_response', {'success': False, 'error': 'Invalid token'})
            disconnect()
            return

        # Store in active UI clients
        active_ui_clients[session_id] = {
            'user_id': user.id,
            'username': user.username,
            'connected_at': datetime.utcnow()
        }

        logger.info(f"UI client authenticated: {user.username}")

        emit('auth_response', {
            'success': True,
            'user': {
                'username': user.username,
                'role': user.role
            }
        })

    @socketio.on('subscribe', namespace='/ws/v1/ui')
    def handle_subscribe(data):
        """Subscribe to specific data streams"""
        session_id = request.sid
        if session_id not in active_ui_clients:
            return

        channel = data.get('channel')  # 'events', 'logs', 'agent_123'

        join_room(channel)
        logger.info(f"Client {session_id} subscribed to {channel}")

        emit('subscribed', {'channel': channel})

    @socketio.on('unsubscribe', namespace='/ws/v1/ui')
    def handle_unsubscribe(data):
        """Unsubscribe from data stream"""
        session_id = request.sid
        channel = data.get('channel')

        leave_room(channel)
        logger.info(f"Client {session_id} unsubscribed from {channel}")

        emit('unsubscribed', {'channel': channel})

    @socketio.on('send_command', namespace='/ws/v1/ui')
    def handle_send_command(data):
        """UI sends command to agent"""
        session_id = request.sid
        if session_id not in active_ui_clients:
            emit('error', {'message': 'Not authenticated'})
            return

        user_info = active_ui_clients[session_id]
        agent_id = data.get('agent_id')
        command_type = data.get('command_type')
        parameters = data.get('parameters', {})

        # Create command in DB
        from apps.models import AgentCommand
        cmd = AgentCommand(
            agent_id=agent_id,
            command_type=command_type,
            parameters=parameters,
            created_by=user_info['username'],
            status='pending'
        )
        db.session.add(cmd)
        db.session.commit()

        # Command will be picked up by agent on next heartbeat
        # Or if agent is connected, send immediately
        agent_session = None
        for sid, info in active_agents.items():
            if info['agent_id'] == agent_id:
                agent_session = sid
                break

        if agent_session:
            socketio.emit('command', {
                'command_id': cmd.id,
                'command_type': command_type,
                'parameters': parameters
            }, namespace='/ws/v1/agent', room=agent_session)

        emit('command_sent', {
            'command_id': cmd.id,
            'status': 'pending'
        })

    @socketio.on('disconnect', namespace='/ws/v1/ui')
    def handle_ui_disconnect():
        """UI client disconnects"""
        session_id = request.sid
        if session_id in active_ui_clients:
            user_info = active_ui_clients[session_id]
            logger.info(f"UI client disconnected: {user_info['username']}")
            del active_ui_clients[session_id]
```

---

## Client Implementation

### 1. Agent WebSocket Client

**File**: `agent/transport/websocket_client.py`

```python
"""
WebSocket client for agent-dashboard communication.
"""

import socketio
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class AgentWebSocketClient:
    def __init__(self, dashboard_url: str, agent_id: int, token: str):
        self.dashboard_url = dashboard_url
        self.agent_id = agent_id
        self.token = token

        # Create Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite
            reconnection_delay=1,
            reconnection_delay_max=60,
            logger=True,
            engineio_logger=True
        )

        self.setup_handlers()

    def setup_handlers(self):
        """Setup event handlers"""

        @self.sio.on('connect', namespace='/ws/v1/agent')
        def on_connect():
            logger.info("Connected to dashboard, authenticating...")
            self.sio.emit('auth', {
                'agent_id': self.agent_id,
                'token': self.token,
                'agent_version': '1.0.0'
            }, namespace='/ws/v1/agent')

        @self.sio.on('auth_response', namespace='/ws/v1/agent')
        def on_auth_response(data):
            if data.get('success'):
                logger.info("Authentication successful")
                self.on_authenticated(data.get('config', {}))
            else:
                logger.error(f"Authentication failed: {data.get('error')}")
                self.sio.disconnect()

        @self.sio.on('event_ack', namespace='/ws/v1/agent')
        def on_event_ack(data):
            sequence = data.get('sequence')
            logger.debug(f"Event acknowledged: {sequence}")
            # Remove from pending queue

        @self.sio.on('command', namespace='/ws/v1/agent')
        def on_command(data):
            command_id = data.get('command_id')
            command_type = data.get('command_type')
            parameters = data.get('parameters', {})

            logger.info(f"Received command {command_id}: {command_type}")
            self.on_command_received(command_id, command_type, parameters)

        @self.sio.on('disconnect', namespace='/ws/v1/agent')
        def on_disconnect():
            logger.warning("Disconnected from dashboard")

    def connect(self):
        """Connect to dashboard"""
        ws_url = self.dashboard_url.replace('https://', 'wss://').replace('http://', 'ws://')
        logger.info(f"Connecting to {ws_url}/ws/v1/agent")

        self.sio.connect(
            ws_url,
            namespaces=['/ws/v1/agent'],
            transports=['websocket']
        )

    def send_event(self, event_type: str, data: dict, sequence: int = None):
        """Send single event"""
        self.sio.emit('event', {
            'event_type': event_type,
            'data': data,
            'sequence': sequence,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    def send_event_batch(self, events: list, sequence: int = None):
        """Send batch of events"""
        self.sio.emit('event_batch', {
            'events': events,
            'sequence': sequence,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    def send_log(self, log_type: str, level: str, message: str, raw_line: str):
        """Send log entry"""
        self.sio.emit('log', {
            'log_type': log_type,
            'level': level,
            'message': message,
            'raw_line': raw_line,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    def send_heartbeat(self, health_metrics: dict):
        """Send heartbeat"""
        self.sio.emit('heartbeat', {
            'health': health_metrics,
            'suricata': {
                'pid': self.get_suricata_pid(),
                'running': self.is_suricata_running()
            },
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    def send_command_result(self, command_id: int, status: str, result: dict):
        """Send command execution result"""
        self.sio.emit('command_result', {
            'command_id': command_id,
            'status': status,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/ws/v1/agent')

    # Callbacks (override in agent.py)
    def on_authenticated(self, config: dict):
        pass

    def on_command_received(self, command_id: int, command_type: str, parameters: dict):
        pass
```

### 2. Web UI WebSocket Client

**File**: `apps/static/js/websocket.js`

```javascript
/**
 * WebSocket client for web UI real-time updates
 */

class DashboardWebSocket {
    constructor(dashboardUrl, jwtToken) {
        this.dashboardUrl = dashboardUrl;
        this.jwtToken = jwtToken;
        this.socket = null;
        this.callbacks = {};
    }

    connect() {
        // Create Socket.IO connection
        this.socket = io(`${this.dashboardUrl}/ws/v1/ui`, {
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 60000
        });

        // Setup handlers
        this.socket.on('connect', () => {
            console.log('Connected to dashboard WebSocket');
            this.authenticate();
        });

        this.socket.on('auth_response', (data) => {
            if (data.success) {
                console.log('WebSocket authenticated');
                this.trigger('authenticated', data.user);
            } else {
                console.error('WebSocket auth failed:', data.error);
            }
        });

        this.socket.on('new_event', (data) => {
            this.trigger('event', data);
        });

        this.socket.on('new_log', (data) => {
            this.trigger('log', data);
        });

        this.socket.on('agent_status', (data) => {
            this.trigger('agent_status', data);
        });

        this.socket.on('command_completed', (data) => {
            this.trigger('command_completed', data);
        });

        this.socket.on('disconnect', () => {
            console.warn('Disconnected from WebSocket');
        });
    }

    authenticate() {
        this.socket.emit('auth', {
            token: this.jwtToken
        });
    }

    subscribe(channel) {
        this.socket.emit('subscribe', { channel });
    }

    unsubscribe(channel) {
        this.socket.emit('unsubscribe', { channel });
    }

    sendCommand(agentId, commandType, parameters) {
        this.socket.emit('send_command', {
            agent_id: agentId,
            command_type: commandType,
            parameters: parameters
        });
    }

    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(cb => cb(data));
        }
    }
}

// Usage example
const ws = new DashboardWebSocket(DASHBOARD_URL, JWT_TOKEN);
ws.connect();

ws.on('authenticated', (user) => {
    console.log('Authenticated as:', user.username);
    ws.subscribe('events');  // Subscribe to all events
    ws.subscribe('agent_123');  // Subscribe to specific agent
});

ws.on('event', (data) => {
    console.log('New event:', data);
    updateEventFeed(data.event);
});

ws.on('agent_status', (data) => {
    updateAgentStatus(data.agent_id, data.status);
});
```

---

## Scaling Considerations

### 1. Multiple Dashboard Instances

Use Redis for pub/sub between instances:

```python
# apps/__init__.py
from flask_socketio import SocketIO

socketio = SocketIO(
    app,
    message_queue='redis://localhost:6379/0',
    cors_allowed_origins="*"
)
```

### 2. Room-based Broadcasting

Instead of broadcasting to all clients:

```python
# Broadcast only to clients subscribed to specific agent
socketio.emit('new_event', data, room=f'agent_{agent_id}')

# Broadcast only to specific event types
socketio.emit('alert', data, room='alerts')
```

### 3. Connection Limits

Limit concurrent connections per dashboard instance:

```python
MAX_AGENTS_PER_INSTANCE = 1000
MAX_UI_CLIENTS_PER_INSTANCE = 500

@socketio.on('connect')
def handle_connect():
    if len(active_agents) >= MAX_AGENTS_PER_INSTANCE:
        return False  # Reject connection
```

---

## Monitoring

### WebSocket Metrics

```python
from prometheus_client import Counter, Gauge

ws_connections_total = Gauge('ws_connections', 'Active WebSocket connections', ['type'])
ws_messages_total = Counter('ws_messages_total', 'Total WebSocket messages', ['direction', 'type'])

# Update metrics
ws_connections_total.labels(type='agent').set(len(active_agents))
ws_connections_total.labels(type='ui').set(len(active_ui_clients))
ws_messages_total.labels(direction='inbound', type='event').inc()
```

---

## Next Steps
- [ ] Implement WebSocket server handlers
- [ ] Create agent WebSocket client
- [ ] Build web UI WebSocket client
- [ ] Setup Redis for multi-instance support
- [ ] Add WebSocket metrics and monitoring
- [ ] Write integration tests
