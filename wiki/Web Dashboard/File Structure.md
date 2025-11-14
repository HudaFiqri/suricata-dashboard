# File Structure Overview

## Complete Project Structure

```
suricata-dashboard/
├── agent/                              # NEW: Suricata Agent (deployed to remote hosts)
│   ├── __init__.py
│   ├── agent.py                        # Main agent daemon
│   ├── config.py                       # Config loader & validator
│   ├── requirements.txt                # Agent dependencies
│   │
│   ├── core/                           # Core agent functionality
│   │   ├── __init__.py
│   │   ├── tailer.py                   # File tailer (eve.json, logs)
│   │   ├── parser.py                   # Event/log parser
│   │   ├── buffer.py                   # SQLite local buffer
│   │   ├── auth.py                     # Token encryption/auth
│   │   └── health.py                   # Health metrics collector
│   │
│   ├── transport/                      # Communication layer
│   │   ├── __init__.py
│   │   ├── websocket_client.py         # WebSocket client
│   │   ├── http_client.py              # HTTP/REST client
│   │   ├── message.py                  # Message format handler
│   │   └── retry.py                    # Retry & reliability logic
│   │
│   ├── handlers/                       # Command handlers
│   │   ├── __init__.py
│   │   ├── config_handler.py           # Config update handler
│   │   ├── command_handler.py          # Command execution
│   │   ├── pcap_handler.py             # PCAP capture handler
│   │   └── suricata_control.py         # Suricata control (reload, restart)
│   │
│   ├── installer/                      # Agent installer generator
│   │   ├── template.sh                 # Installer script template
│   │   ├── generator.py                # Generate custom installer
│   │   └── systemd.service.template    # Systemd service template
│   │
│   └── tests/                          # Agent tests
│       ├── test_tailer.py
│       ├── test_parser.py
│       └── test_websocket.py
│
├── apps/                               # MODIFIED: Dashboard application
│   ├── __init__.py                     # MODIFIED: Add WebSocket, MongoDB setup
│   ├── models.py                       # MODIFIED: New models (Agent, Config, Command)
│   ├── database.py                     # NEW: Database connections (PostgreSQL + MongoDB)
│   │
│   ├── api/                            # NEW: API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                     # Authentication API (JWT, API keys)
│   │   ├── agents.py                   # Agent management API
│   │   ├── events.py                   # Event ingestion API
│   │   ├── logs.py                     # Log ingestion API
│   │   ├── configs.py                  # Config management API
│   │   ├── commands.py                 # Command management API
│   │   ├── stats.py                    # Statistics API
│   │   ├── query.py                    # Query/search API
│   │   ├── pcap.py                     # PCAP management API
│   │   └── installer.py                # Agent installer endpoint
│   │
│   ├── websocket/                      # NEW: WebSocket server
│   │   ├── __init__.py
│   │   ├── server.py                   # WebSocket server (Socket.IO)
│   │   ├── handlers.py                 # Message handlers
│   │   ├── broadcast.py                # Broadcast to web UI
│   │   └── agent_sessions.py           # Track agent connections
│   │
│   ├── blueprints/                     # MODIFIED: Web UI routes
│   │   ├── __init__.py
│   │   ├── auth.py                     # EXISTING: User auth
│   │   ├── dashboard.py                # MODIFIED: Remote data dashboard
│   │   ├── agents.py                   # NEW: Agent management UI
│   │   ├── remote_config.py            # NEW: Remote config editor UI
│   │   ├── live_monitor.py             # NEW: Live monitoring UI
│   │   ├── query.py                    # NEW: Event/log query UI
│   │   ├── pcap.py                     # MODIFIED: Remote PCAP management
│   │   ├── rules.py                    # EXISTING: Rules editor (adapt for remote)
│   │   └── settings.py                 # EXISTING: Settings
│   │
│   ├── lib/                            # MODIFIED: Core libraries
│   │   ├── __init__.py
│   │   ├── suricata.py                 # REMOVED: Direct file reading
│   │   ├── data_source.py              # NEW: Abstract data source (MongoDB)
│   │   ├── event_processor.py          # NEW: Event processing pipeline
│   │   ├── enrichment.py               # NEW: GeoIP, threat intel enrichment
│   │   ├── aggregation.py              # NEW: Statistics aggregation
│   │   └── utils.py                    # EXISTING: Utilities
│   │
│   ├── static/                         # MODIFIED: Static assets
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   └── agent-dashboard.css     # NEW: Agent UI styles
│   │   │
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── websocket.js            # NEW: WebSocket client
│   │   │   ├── agent-manager.js        # NEW: Agent management
│   │   │   ├── config-editor.js        # NEW: Config editor (YAML)
│   │   │   ├── live-monitor.js         # NEW: Real-time monitoring
│   │   │   └── query-builder.js        # NEW: Query interface
│   │   │
│   │   └── vendor/                     # Third-party libraries
│   │       ├── socket.io.js            # NEW: Socket.IO client
│   │       ├── ace/                    # NEW: Code editor for YAML
│   │       └── ...
│   │
│   └── templates/                      # MODIFIED: HTML templates
│       ├── base.html                   # MODIFIED: Add WebSocket support
│       ├── index.html                  # MODIFIED: Remote dashboard
│       │
│       ├── agents/                     # NEW: Agent management pages
│       │   ├── list.html               # Agent list
│       │   ├── detail.html             # Single agent detail
│       │   ├── register.html           # Register new agent
│       │   └── install.html            # Installation instructions
│       │
│       ├── config/                     # NEW: Config management pages
│       │   ├── editor.html             # YAML config editor
│       │   ├── history.html            # Config version history
│       │   └── diff.html               # Config diff viewer
│       │
│       ├── monitor/                    # NEW: Live monitoring pages
│       │   ├── realtime.html           # Real-time event stream
│       │   ├── alerts.html             # Live alerts
│       │   └── logs.html               # Log stream viewer
│       │
│       └── query/                      # NEW: Query pages
│           ├── events.html             # Event query interface
│           ├── logs.html               # Log query interface
│           └── analytics.html          # Analytics dashboard
│
├── migrations/                         # NEW: Database migrations
│   ├── postgresql/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_add_agents.sql
│   │   ├── 003_add_configs.sql
│   │   └── 004_add_commands.sql
│   │
│   ├── mongodb/
│   │   ├── 001_create_collections.js
│   │   ├── 002_create_indexes.js
│   │   └── 003_setup_sharding.js       # Optional: for large scale
│   │
│   └── migrate.py                      # Migration runner
│
├── scripts/                            # Utility scripts
│   ├── install_agent.sh                # Quick agent installer
│   ├── generate_token.py               # Generate agent tokens
│   ├── backup_db.sh                    # Backup databases
│   └── cleanup_old_data.py             # Data retention cleanup
│
├── tests/                              # Dashboard tests
│   ├── test_api/
│   │   ├── test_agents.py
│   │   ├── test_events.py
│   │   └── test_configs.py
│   │
│   ├── test_websocket/
│   │   └── test_server.py
│   │
│   └── test_integration/
│       └── test_agent_communication.py
│
├── container/                          # EXISTING: Containerization
│   ├── docker/
│   │   ├── Dockerfile                  # MODIFIED: Add MongoDB, WebSocket deps
│   │   ├── docker-compose.yml          # MODIFIED: Add MongoDB service
│   │   └── ...
│   │
│   └── kubernetes/
│       └── ...
│
├── wiki/                               # EXISTING + NEW: Documentation
│   ├── 01-database-schema.md           # NEW: DB schema docs
│   ├── 02-api-specification.md         # NEW: API docs
│   ├── 03-agent-protocol.md            # NEW: Protocol docs
│   ├── 04-file-structure.md            # NEW: This file
│   ├── 05-agent-installer.md           # NEW: Installer docs
│   ├── 06-migration-guide.md           # NEW: Migration docs
│   ├── 07-websocket-protocol.md        # NEW: WebSocket docs
│   ├── 08-ui-guide.md                  # NEW: UI guide
│   ├── containerization.md             # EXISTING
│   ├── containerization-docker.md      # EXISTING
│   └── containerization-kubernetes.md  # EXISTING
│
├── config/                             # Configuration files
│   ├── config.py                       # MODIFIED: Add MongoDB, WebSocket config
│   ├── config.example.yaml             # NEW: Example dashboard config
│   ├── agent-config.example.yaml       # NEW: Example agent config
│   └── logging.yaml                    # Logging configuration
│
├── requirements.txt                    # MODIFIED: Dashboard dependencies
├── requirements-agent.txt              # NEW: Agent-only dependencies
├── setup.py                            # Package setup
├── README.md                           # MODIFIED: Update with remote architecture
└── .env.example                        # MODIFIED: Environment variables

```

---

## New File Details

### Agent Files

#### `agent/agent.py` (Main Agent Daemon)
```python
"""
Main agent daemon that runs on remote Suricata hosts.

Responsibilities:
- Initialize all components
- Establish connection to dashboard
- Coordinate tailers, parsers, handlers
- Main event loop
"""
```

#### `agent/core/tailer.py` (File Tailer)
```python
"""
Monitor Suricata log files for changes using inotify/polling.

Features:
- Watch eve.json, suricata.log, fast.log
- Handle log rotation
- Efficient incremental reading
- Multiple file support
"""
```

#### `agent/transport/websocket_client.py` (WebSocket Client)
```python
"""
WebSocket client with auto-reconnect and reliability.

Features:
- Async WebSocket connection
- Auto-reconnect with exponential backoff
- Message queuing during disconnect
- Heartbeat/keepalive
"""
```

#### `agent/installer/template.sh` (Installer Template)
```bash
#!/bin/bash
# Self-contained agent installer
# Variables injected by generator:
# - DASHBOARD_URL
# - AGENT_TOKEN
# - AGENT_NAME (optional)

# Embedded Python agent code (base64)
AGENT_CODE_B64="..."

# Installation logic
install_dependencies()
decode_agent()
setup_systemd()
start_agent()
```

---

### Dashboard Files

#### `apps/database.py` (Database Connections)
```python
"""
Database connection management for PostgreSQL and MongoDB.

Provides:
- SQLAlchemy engine for PostgreSQL
- PyMongo client for MongoDB
- Connection pooling
- Health checks
"""

from sqlalchemy import create_engine
from pymongo import MongoClient

# PostgreSQL
pg_engine = create_engine(POSTGRES_URI, pool_size=20)

# MongoDB
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DATABASE]
```

#### `apps/api/agents.py` (Agent Management API)
```python
"""
RESTful API for agent management.

Endpoints:
- POST /api/v1/agents/register
- GET /api/v1/agents
- GET /api/v1/agents/{id}
- PUT /api/v1/agents/{id}
- DELETE /api/v1/agents/{id}
- POST /api/v1/agents/{id}/heartbeat
"""
```

#### `apps/websocket/server.py` (WebSocket Server)
```python
"""
WebSocket server using Flask-SocketIO.

Features:
- Agent connections (/ws/v1/agent)
- Web UI connections (/ws/v1/ui)
- Message routing
- Session management
- Broadcast to UI clients
"""

from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect', namespace='/ws/v1/agent')
def handle_agent_connect():
    # Authenticate agent
    # Join agent room
    pass
```

#### `apps/lib/event_processor.py` (Event Processing Pipeline)
```python
"""
Process incoming events from agents.

Pipeline stages:
1. Validation
2. Enrichment (GeoIP, threat intel)
3. Aggregation (statistics)
4. Storage (MongoDB)
5. Broadcast (WebSocket to UI)
6. Alerting (if critical)
"""

class EventPipeline:
    def process(self, agent_id: int, event: dict):
        # Validate
        validated = self.validate(event)

        # Enrich
        enriched = self.enrich(validated)

        # Store
        self.store_mongodb(agent_id, enriched)

        # Aggregate stats
        self.update_stats(agent_id, enriched)

        # Broadcast to UI
        self.broadcast(agent_id, enriched)
```

#### `apps/static/js/websocket.js` (WebSocket Client for UI)
```javascript
/**
 * WebSocket client for real-time updates in web UI.
 *
 * Features:
 * - Connect to /ws/v1/ui
 * - Subscribe to events, logs, stats
 * - Auto-reconnect
 * - Update UI in real-time
 */

class DashboardWebSocket {
    constructor(url) {
        this.socket = io(url);
        this.setupHandlers();
    }

    setupHandlers() {
        this.socket.on('event', (data) => {
            // Update event stream UI
            updateEventStream(data);
        });

        this.socket.on('agent_status', (data) => {
            // Update agent status indicator
            updateAgentStatus(data);
        });
    }
}
```

#### `apps/templates/agents/list.html` (Agent List Page)
```html
<!-- Agent management page showing all registered agents -->
<div class="agent-list">
    {% for agent in agents %}
    <div class="agent-card {{ agent.status }}">
        <h3>{{ agent.name }}</h3>
        <span class="status-badge">{{ agent.status }}</span>
        <div class="metrics">
            <span>CPU: {{ agent.health.cpu }}%</span>
            <span>Memory: {{ agent.health.memory }}MB</span>
        </div>
        <div class="actions">
            <button onclick="viewAgent({{ agent.id }})">View</button>
            <button onclick="editConfig({{ agent.id }})">Config</button>
        </div>
    </div>
    {% endfor %}
</div>
```

---

## Modified Files

### `apps/__init__.py`
**Changes:**
```python
# BEFORE
from flask import Flask
app = Flask(__name__)

# Database (PostgreSQL only)
db.init_app(app)

# AFTER
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)

# Databases
from apps.database import init_databases
init_databases(app)  # PostgreSQL + MongoDB

# WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")
```

### `apps/models.py`
**Changes:**
```python
# ADD new models
class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    # ... (full schema from 01-database-schema.md)

class AgentConfig(db.Model):
    __tablename__ = 'agent_configs'
    # ...

class AgentCommand(db.Model):
    __tablename__ = 'agent_commands'
    # ...
```

### `apps/blueprints/dashboard.py`
**Changes:**
```python
# BEFORE: Read local files
@blueprint.route('/')
def index():
    events = read_local_eve_json()

# AFTER: Query MongoDB
@blueprint.route('/')
def index():
    # Get summary across all agents
    agents = Agent.query.filter_by(status='online').all()

    # Query recent events from MongoDB
    events = mongo_db.events.find(
        {'timestamp': {'$gte': datetime.now() - timedelta(hours=1)}}
    ).sort('timestamp', -1).limit(100)

    return render_template('index.html', agents=agents, events=events)
```

### `container/docker/docker-compose.yml`
**Changes:**
```yaml
# ADD MongoDB service
services:
  dashboard:
    # ... existing

  postgres:
    # ... existing

  mongodb:  # NEW
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: suricata
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: suricata
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"

volumes:
  mongodb_data:
```

---

## Removed Files

These files are removed or deprecated:

- `apps/lib/suricata.py` - Direct file reading logic (replaced by remote data source)
- Any local file path references in blueprints

---

## File Size Estimates

| Component | Files | Lines of Code | Estimated Size |
|-----------|-------|---------------|----------------|
| Agent | 20 | ~3000 | ~100KB |
| Dashboard API | 10 | ~2000 | ~70KB |
| WebSocket | 5 | ~800 | ~30KB |
| UI (JS) | 6 | ~1500 | ~50KB |
| UI (HTML) | 15 | ~2000 | ~60KB |
| Models & DB | 5 | ~800 | ~30KB |
| Migrations | 10 | ~500 | ~20KB |
| Tests | 15 | ~2000 | ~70KB |
| **Total** | **86** | **~12600** | **~430KB** |

---

## Development Workflow

### 1. Setup Development Environment
```bash
# Clone repo
git clone https://github.com/user/suricata-dashboard
cd suricata-dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup databases
docker-compose up -d postgres mongodb

# Run migrations
python migrations/migrate.py

# Start dashboard
python run.py
```

### 2. Develop Agent
```bash
cd agent

# Install agent deps
pip install -r requirements.txt

# Run agent locally (for testing)
python agent.py --config agent-config.yaml
```

### 3. Test Integration
```bash
# Terminal 1: Dashboard
python run.py

# Terminal 2: Agent
cd agent && python agent.py

# Terminal 3: Web browser
# Open http://localhost:5000
```

---

## Deployment Structure

### Dashboard Deployment
```
/opt/suricata-dashboard/
├── apps/
├── migrations/
├── config/
├── venv/
└── run.py
```

### Agent Deployment
```
/opt/suricata-agent/
├── agent.py
├── core/
├── transport/
├── handlers/
├── config.yaml
└── buffer.db
```

---

## Next Steps
- [ ] Create directory structure: `mkdir -p agent/{core,transport,handlers,installer}`
- [ ] Create __init__.py files
- [ ] Setup imports and package structure
- [ ] Create stub files for development
