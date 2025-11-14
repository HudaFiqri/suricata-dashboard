# Suricata Multi-Agent Dashboard

**Enterprise-grade multi-agent monitoring and management for Suricata IDS/IPS**

Modern Python Flask dashboard with remote agent-based architecture. Monitor and manage **multiple Suricata instances** from a centralized web interface with real-time WebSocket streaming.

## 🚀 Key Features

### Multi-Agent Architecture
- **🌐 Centralized Management** - Monitor unlimited Suricata agents from one dashboard
- **📡 Real-time Streaming** - WebSocket-based live event streaming from all agents
- **🔄 Remote Configuration** - Push configs to agents remotely via web UI
- **📊 Unified View** - Aggregate events, alerts, and statistics across all agents
- **🏷️ Agent Tagging** - Organize agents by tags (production, staging, datacenter, etc.)

### Remote Monitoring
- **🤖 Agent-Based** - Python agents run on each Suricata server
- **💾 Offline Resilience** - SQLite buffer for network failures
- **🔐 Encrypted Auth** - Fernet-encrypted tokens for agent authentication
- **📈 Auto-Scaling** - Support 100+ concurrent agents

### Data Storage
- **PostgreSQL** - Structured data (agents, users, configs, commands)
- **MongoDB** - Time-series events and logs with TTL auto-cleanup
- **Hybrid Design** - Best of both SQL and NoSQL worlds

### Modern Web UI
- **Real-time Updates** - Live WebSocket push notifications
- **Responsive Design** - Bootstrap 5 with mobile support
- **Multi-agent Dashboard** - Visual overview of all agents
- **Per-Agent Views** - Drill down into individual agent details
- **Event Filtering** - Search and filter events across all agents

## 📋 Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Suricata #1    │         │  Suricata #2    │         │  Suricata #N    │
│  + Agent        │         │  + Agent        │         │  + Agent        │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         │          WebSocket / HTTP (with fallback)            │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
                          ┌──────────────────────┐
                          │  Central Dashboard   │
                          │  - Flask + SocketIO  │
                          │  - PostgreSQL        │
                          │  - MongoDB           │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   Web Browser UI     │
                          │   (WebSocket)        │
                          └──────────────────────┘
```

## 🎯 Use Cases

1. **Multi-Site Monitoring** - Monitor Suricata across multiple data centers
2. **MSP / MSSP** - Manage customer Suricata instances from central dashboard
3. **Enterprise SOC** - Unified view of all IDS/IPS sensors
4. **Cloud Deployments** - Monitor distributed Suricata instances in cloud/containers
5. **Hybrid Infrastructure** - Mix on-premise and cloud Suricata deployments

## ⚡ Quick Start

### 1. Install Dashboard Server

```bash
# Clone repository
git clone https://github.com/yourusername/suricata-dashboard.git
cd suricata-dashboard

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit database credentials

# Setup databases
docker-compose up -d postgresql mongodb  # Or install manually

# Run migrations
cd bin/migrations
python migrate.py up

# Start dashboard
python run.py
```

Dashboard will be available at: **http://localhost:5000**

### 2. Install Agent on Remote Servers

From the dashboard web UI:
1. Go to **Agents** page
2. Click **Add New Agent**
3. Enter agent name and tags
4. Click **Generate Installer**
5. Copy the installation command
6. Run on your Suricata server:

```bash
curl -sSL "http://dashboard-url/api/v1/agent/install.sh?token=TOKEN&name=agent-name" | sudo bash
```

The agent will:
- Auto-install dependencies
- Configure itself
- Connect to dashboard
- Start streaming events

### 3. Monitor Your Agents

- **Dashboard** - `/` - Overview of all agents
- **Agents** - `/agents` - Manage agents, view status
- **Events** - `/events` - Real-time events from all agents
- **Alerts** - `/alerts` - Critical alerts across infrastructure
- **Statistics** - `/statistics` - Aggregate analytics

## 📦 What's Included

### Dashboard Components
- ✅ **REST API** - Complete API for agent communication (`apps/api/`)
- ✅ **WebSocket Server** - Real-time bidirectional communication (`apps/websocket/`)
- ✅ **Web UI** - Modern responsive interface (`apps/web/`)
- ✅ **Database Layer** - PostgreSQL + MongoDB integration (`apps/database.py`)
- ✅ **Agent Management** - Register, configure, monitor agents
- ✅ **Event Processing** - Ingest, store, query events
- ✅ **Configuration Management** - Remote config push
- ✅ **Command System** - Send commands to agents

### Agent Components
- ✅ **File Monitoring** - Tail Suricata eve.json and logs (`bin/agent/core/tailer.py`)
- ✅ **Event Parsing** - Parse and index events (`bin/agent/core/parser.py`)
- ✅ **WebSocket Client** - Real-time streaming (`bin/agent/transport/websocket_client.py`)
- ✅ **HTTP Fallback** - Batch upload if WebSocket fails (`bin/agent/transport/http_client.py`)
- ✅ **Offline Buffer** - SQLite for network failures (`bin/agent/core/buffer.py`)
- ✅ **Health Monitoring** - System metrics (CPU, memory, disk) (`bin/agent/core/health.py`)
- ✅ **Auto-installer** - One-command installation

## 🗄️ Database Setup

### PostgreSQL

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE suricata_dashboard;
CREATE USER suricata WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE suricata_dashboard TO suricata;
\q

# Run migrations
cd bin/migrations
python migrate.py up
```

### MongoDB

```bash
# Create user
mongosh
use suricata
db.createUser({
  user: "suricata",
  pwd: "your-password",
  roles: [{role: "readWrite", db: "suricata"}]
})

# Create collections and indexes
cd bin/migrations/mongodb
mongosh < 001_create_collections.js
mongosh < 002_create_indexes.js
```

## 🔧 Configuration

Edit `.env` file:

```bash
# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=your-secret-key

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=suricata_dashboard
POSTGRES_USER=suricata
POSTGRES_PASSWORD=your-password

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=suricata
MONGO_USER=suricata
MONGO_PASSWORD=your-password

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_HOURS=24

# Data Retention
EVENTS_RETENTION_DAYS=90
LOGS_RETENTION_DAYS=30
```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Agents (Multi-Agent Management)
- `GET /api/v1/agents` - **List all agents**
- `POST /api/v1/agents/register` - Register new agent
- `GET /api/v1/agents/:id` - Get agent details
- `PUT /api/v1/agents/:id` - Update agent
- `DELETE /api/v1/agents/:id` - Delete agent

### Events (Unified View)
- `POST /api/v1/query/events` - Query events from all agents
- `POST /api/v1/events` - Ingest single event
- `POST /api/v1/events/batch` - Batch event ingestion

### Configuration Management
- `GET /api/v1/configs/:agent_id` - Get agent config
- `POST /api/v1/configs/:agent_id` - Push config to agent
- `GET /api/v1/configs/:agent_id/history` - Config history

### Commands
- `POST /api/v1/commands/:agent_id` - Send command to agent
- `GET /api/v1/commands/:command_id` - Get command status

### Statistics
- `GET /api/v1/stats/summary` - **Multi-agent summary**
- `GET /api/v1/stats/agents/:id` - Per-agent statistics

## 🌐 WebSocket Protocol

### Agent Namespace (`/ws/v1/agent`)
```javascript
// Agent connects and authenticates
emit('auth', {agent_id: 'uuid', token: 'encrypted'})

// Agent streams events
emit('event_batch', {events: [...]})

// Agent sends heartbeat
emit('heartbeat', {health: {...}})
```

### UI Namespace (`/ws/v1/ui`)
```javascript
// UI authenticates
emit('auth', {token: 'jwt'})

// Subscribe to all events
emit('subscribe', {channel: 'events'})

// Subscribe to specific agent
emit('subscribe', {channel: 'agent_123'})

// Receive real-time updates
on('new_event', (data) => {...})
on('agent_status', (data) => {...})
```

## 🚢 Production Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

Includes:
- Dashboard (Flask + Gunicorn)
- PostgreSQL
- MongoDB
- Nginx reverse proxy

### Using Kubernetes

```bash
kubectl apply -f k8s/
```

Includes:
- Dashboard deployment (3 replicas)
- PostgreSQL StatefulSet
- MongoDB StatefulSet
- Services and Ingress

### Manual Deployment

```bash
# Install gunicorn
pip install gunicorn gevent

# Run with gevent workers
gunicorn --worker-class gevent \
         --workers 4 \
         --bind 0.0.0.0:5000 \
         --timeout 120 \
         wsgi:app
```

## 📚 Documentation

- **[README-REMOTE.md](README-REMOTE.md)** - Complete remote monitoring guide
- **[wiki/00-refactor-overview.md](wiki/00-refactor-overview.md)** - Architecture overview
- **[wiki/01-database-schema.md](wiki/01-database-schema.md)** - Database schema
- **[wiki/02-api-specification.md](wiki/02-api-specification.md)** - Full API docs
- **[wiki/03-agent-protocol.md](wiki/03-agent-protocol.md)** - Agent communication protocol
- **[wiki/07-websocket-real-time.md](wiki/07-websocket-real-time.md)** - WebSocket protocol

## 🔐 Security

- **Agent Auth** - Fernet-encrypted tokens
- **Web UI Auth** - JWT with configurable expiration
- **Database** - Use strong passwords, enable SSL
- **HTTPS** - Use reverse proxy (Nginx/Traefik) with Let's Encrypt
- **Firewall** - Restrict agent connections to known IPs

## 🛠️ Troubleshooting

### Agent Not Connecting
```bash
# Check agent logs
sudo journalctl -u suricata-agent -f

# Test connectivity
telnet dashboard-url 5000

# Verify token
cat /etc/suricata-agent/config.yaml
```

### Events Not Showing
```bash
# Check MongoDB connection
mongo --eval "db.events.count()"

# Check WebSocket connection
# Browser console -> Network -> WS tab

# Check buffer
sqlite3 /var/lib/suricata-agent/buffer.db "SELECT COUNT(*) FROM events;"
```

## 🤝 Migration from Local Mode

See **[wiki/06-migration-guide.md](wiki/06-migration-guide.md)** for complete migration steps.

Quick migration:
1. Backup existing data
2. Install new version
3. Run database migrations
4. Install agents on remote servers
5. Import historical data (optional)

## 📊 Features Comparison

| Feature | Local Mode | Remote Multi-Agent |
|---------|------------|-------------------|
| Agents | Single | **Unlimited** |
| Deployment | Same server | **Distributed** |
| Resilience | Single point of failure | **Offline buffer** |
| Scalability | Limited | **100+ agents** |
| Configuration | Manual | **Remote push** |
| Real-time | File polling | **WebSocket stream** |
| Multi-tenant | No | **Tag-based** |

## 🎓 Use Case Examples

### Example 1: Multi-Datacenter Monitoring
```
Dashboard (Central):
  ├── Agent: DC1-Gateway (prod, gateway)
  ├── Agent: DC1-DMZ (prod, dmz)
  ├── Agent: DC2-Gateway (prod, gateway)
  └── Agent: DC2-DMZ (prod, dmz)
```

### Example 2: MSP Customer Management
```
Dashboard (MSP):
  ├── Agent: Customer-A-FW (customer-a, firewall)
  ├── Agent: Customer-A-Web (customer-a, web-server)
  ├── Agent: Customer-B-FW (customer-b, firewall)
  └── Agent: Customer-B-Web (customer-b, web-server)
```

### Example 3: Cloud + On-Premise
```
Dashboard:
  ├── Agent: AWS-VPC-1 (cloud, aws, production)
  ├── Agent: Azure-VNet-1 (cloud, azure, production)
  ├── Agent: OnPrem-DC1 (on-premise, datacenter-1)
  └── Agent: OnPrem-DC2 (on-premise, datacenter-2)
```

## 📝 License

See LICENSE file for details.

## 🙏 Credits

Built with:
- Flask + Flask-SocketIO
- PostgreSQL + MongoDB
- Bootstrap 5
- Socket.IO
- Chart.js

---

**🌟 Star this repo if you find it useful!**

For questions and support, please open an issue on GitHub.
