# Suricata Dashboard - Remote Monitoring

Remote agent-based monitoring system for Suricata IDS with real-time streaming.

## Architecture Overview

```
┌─────────────┐                      ┌──────────────────┐
│   Agent 1   │◄────WebSocket────────┤                  │
│  (Python)   │                      │   Dashboard      │
└─────────────┘                      │   (Flask +       │
                                     │    SocketIO)     │
┌─────────────┐                      │                  │
│   Agent 2   │◄────WebSocket────────┤                  │
│  (Python)   │                      │  ┌──────────┐   │
└─────────────┘                      │  │PostgreSQL│   │
                                     │  └──────────┘   │
┌─────────────┐                      │  ┌──────────┐   │
│   Agent N   │◄────HTTP Fallback────┤  │ MongoDB  │   │
│  (Python)   │                      │  └──────────┘   │
└─────────────┘                      └──────────────────┘
                                              ▲
                                              │
                                     ┌────────┴─────────┐
                                     │   Web Browser    │
                                     │  (WebSocket UI)  │
                                     └──────────────────┘
```

## Key Features

- **Remote Monitoring**: Agent-based architecture, no local file access needed
- **Real-time Streaming**: WebSocket for live event streaming
- **Offline Resilience**: SQLite buffer on agents for network failures
- **Centralized Config**: Configure agents remotely via web dashboard
- **Encrypted Auth**: Fernet-encrypted tokens for agent authentication
- **Hybrid Database**: PostgreSQL (structured) + MongoDB (time-series events)
- **Auto Installer**: Single `.sh` script with embedded agent code
- **Scalable**: Support 100+ agents with connection pooling

## Quick Start

### 1. Setup Dashboard Server

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit database credentials

# Run migrations
cd bin/migrations
python migrate.py up

# Start dashboard
python run.py
```

Dashboard will be available at:
- Web UI: http://localhost:5000
- WebSocket Agent: ws://localhost:5000/ws/v1/agent
- WebSocket UI: ws://localhost:5000/ws/v1/ui

### 2. Install Agent on Remote Host

```bash
# Download installer from dashboard
curl http://dashboard-url/api/v1/agent/install.sh?token=TOKEN > install.sh

# Run installer
sudo bash install.sh

# Check agent status
sudo systemctl status suricata-agent
sudo journalctl -u suricata-agent -f
```

## Database Setup

### PostgreSQL

```sql
CREATE DATABASE suricata_dashboard;
CREATE USER suricata WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE suricata_dashboard TO suricata;
```

Run migrations:
```bash
cd bin/migrations
python migrate.py up
```

### MongoDB

```javascript
use suricata
db.createUser({
  user: "suricata",
  pwd: "password",
  roles: [{role: "readWrite", db: "suricata"}]
})
```

Run index creation:
```bash
cd bin/migrations/mongodb
mongosh < 001_create_collections.js
mongosh < 002_create_indexes.js
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Agents
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/agents` - Register new agent
- `GET /api/v1/agents/:id` - Get agent details
- `PUT /api/v1/agents/:id` - Update agent
- `DELETE /api/v1/agents/:id` - Delete agent
- `POST /api/v1/agents/:id/heartbeat` - Agent heartbeat

### Events & Logs
- `POST /api/v1/events` - Single event ingestion
- `POST /api/v1/events/batch` - Batch event ingestion
- `POST /api/v1/logs` - Log ingestion
- `POST /api/v1/query/events` - Query events
- `POST /api/v1/query/logs` - Query logs

### Configuration
- `GET /api/v1/configs/:agent_id` - Get agent config
- `POST /api/v1/configs/:agent_id` - Create/update config
- `GET /api/v1/configs/:agent_id/history` - Config history

### Commands
- `POST /api/v1/commands/:agent_id` - Send command to agent
- `GET /api/v1/commands/:command_id` - Get command status

### Statistics
- `GET /api/v1/stats/summary` - Dashboard summary
- `GET /api/v1/stats/agents/:id` - Agent statistics

## WebSocket Protocol

### Agent Namespace (`/ws/v1/agent`)

**Client → Server:**
```javascript
// Authentication
emit('auth', {
  agent_id: "agent-uuid",
  token: "encrypted-token"
})

// Send event
emit('event', {
  timestamp: "2025-01-14T10:00:00Z",
  event_type: "alert",
  data: {...}
})

// Send batch
emit('event_batch', {
  sequence: 123,
  events: [...]
})

// Heartbeat
emit('heartbeat', {
  health: {cpu: 25.5, memory: 60.2, ...}
})
```

**Server → Client:**
```javascript
// Auth response
on('auth_response', {
  success: true,
  config: {...}
})

// Command from dashboard
on('command', {
  command_id: "cmd-uuid",
  command_type: "reload_config",
  parameters: {...}
})
```

### UI Namespace (`/ws/v1/ui`)

**Client → Server:**
```javascript
// Authentication
emit('auth', {
  token: "jwt-token"
})

// Subscribe to events
emit('subscribe', {
  channel: 'events'  // or 'logs', 'agent_123', 'alerts'
})

// Send command to agent
emit('send_command', {
  agent_id: "agent-uuid",
  command_type: "reload_config"
})
```

**Server → Client:**
```javascript
// New event
on('new_event', {
  agent_id: "agent-uuid",
  agent_name: "Production Server",
  event: {...}
})

// Agent status change
on('agent_status', {
  agent_id: "agent-uuid",
  status: "online"
})
```

## Agent Configuration

Agent config file: `/etc/suricata-agent/config.yaml`

```yaml
agent:
  name: "Production Server"
  token: "encrypted-token"
  tags: ["production", "web-server"]

dashboard:
  url: "https://dashboard.example.com"
  api_version: "v1"
  verify_ssl: true

suricata:
  eve_log: /var/log/suricata/eve.json
  suricata_log: /var/log/suricata/suricata.log
  config_file: /etc/suricata/suricata.yaml

buffer:
  database: /var/lib/suricata-agent/buffer.db
  max_events: 100000

logging:
  level: INFO
  file: /var/log/suricata-agent/agent.log
```

## Production Deployment

### Using Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn gevent

# Run with gevent worker
gunicorn --worker-class gevent \
         --workers 4 \
         --bind 0.0.0.0:5000 \
         --timeout 120 \
         wsgi:app
```

Nginx config:
```nginx
upstream dashboard {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://dashboard/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### Using Docker

```bash
# Build image
docker build -t suricata-dashboard .

# Run with docker-compose
docker-compose up -d
```

### Using Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n suricata
```

## Security Considerations

1. **Agent Authentication**: Use encrypted tokens with Fernet
2. **JWT Tokens**: Rotate secrets regularly, use HTTPS
3. **Database**: Use strong passwords, enable SSL connections
4. **Network**: Use firewall rules to restrict agent connections
5. **HTTPS**: Enable SSL/TLS in production (use Let's Encrypt)

## Monitoring & Maintenance

### Health Check

```bash
# Check dashboard health
curl http://localhost:5000/api/v1/health

# Check database connections
curl http://localhost:5000/api/v1/health/db
```

### Logs

```bash
# Dashboard logs
tail -f /var/log/suricata-dashboard/dashboard.log

# Agent logs
sudo journalctl -u suricata-agent -f

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Backup

```bash
# PostgreSQL backup
pg_dump -U suricata suricata_dashboard > backup_pg.sql

# MongoDB backup
mongodump --db suricata --out backup_mongo/

# Restore
psql -U suricata suricata_dashboard < backup_pg.sql
mongorestore --db suricata backup_mongo/suricata
```

## Troubleshooting

### Agent Not Connecting

1. Check network connectivity: `telnet dashboard-url 5000`
2. Verify token: Check `/etc/suricata-agent/config.yaml`
3. Check agent logs: `journalctl -u suricata-agent -f`
4. Test WebSocket: Use browser dev tools

### High Memory Usage

1. Check MongoDB indexes: `db.events.getIndexes()`
2. Reduce retention: Lower `EVENTS_RETENTION_DAYS`
3. Enable compression in MongoDB
4. Increase connection pool limits

### Events Not Appearing

1. Check agent buffer: `sqlite3 /var/lib/suricata-agent/buffer.db "SELECT COUNT(*) FROM events;"`
2. Verify MongoDB connection: `mongo --eval "db.stats()"`
3. Check WebSocket connection in browser console
4. Review dashboard logs for errors

## Migration from Local Mode

See `wiki/06-migration-guide.md` for complete migration steps.

Quick migration:
```bash
# 1. Backup existing data
# 2. Install new dashboard version
# 3. Run migrations
cd bin/migrations && python migrate.py up
# 4. Install agents on remote hosts
# 5. Update monitoring dashboards
```

## Support & Documentation

- Full API Spec: `wiki/02-api-specification.md`
- WebSocket Protocol: `wiki/07-websocket-real-time.md`
- Agent Protocol: `wiki/03-agent-protocol.md`
- Database Schema: `wiki/01-database-schema.md`
- UI Mockups: `wiki/08-ui-mockups.md`

## License

See LICENSE file for details.
