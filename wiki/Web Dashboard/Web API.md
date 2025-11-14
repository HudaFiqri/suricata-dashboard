# API Specification

## Overview
RESTful API with WebSocket support for real-time communication.

**Base URL**: `https://dashboard.example.com/api/v1`

**Authentication**:
- Agents: Encrypted token in `X-Agent-Token` header
- Users: JWT in `Authorization: Bearer <token>` header or API key in `X-API-Key`

---

## Authentication Endpoints

### POST /auth/login
User login (get JWT token).

**Request:**
```json
{
    "username": "admin",
    "password": "securepassword"
}
```

**Response:**
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user": {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }
}
```

### POST /auth/refresh
Refresh JWT token.

**Headers:**
```
Authorization: Bearer <old_token>
```

**Response:**
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
}
```

---

## Agent Management API

### POST /agents/register
Register new agent (called during install).

**Headers:**
```
X-Agent-Token: <encrypted_token>
```

**Request:**
```json
{
    "name": "suricata-node-01",
    "hostname": "web-server-01",
    "ip_address": "192.168.1.100",
    "tags": ["production", "dmz"],
    "suricata_version": "7.0.2",
    "agent_version": "1.0.0",
    "system_info": {
        "os": "Ubuntu 22.04",
        "kernel": "5.15.0-91-generic",
        "arch": "x86_64"
    }
}
```

**Response:**
```json
{
    "success": true,
    "agent_id": 123,
    "message": "Agent registered successfully",
    "config": {
        "heartbeat_interval": 30,
        "batch_size": 100,
        "batch_timeout": 5
    }
}
```

### GET /agents
List all agents.

**Query Parameters:**
- `status`: Filter by status (online, offline, error)
- `tags`: Filter by tags (comma-separated)
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
    "success": true,
    "total": 10,
    "agents": [
        {
            "id": 123,
            "name": "suricata-node-01",
            "hostname": "web-server-01",
            "ip_address": "192.168.1.100",
            "status": "online",
            "last_seen": "2025-01-14T10:30:00Z",
            "tags": ["production", "dmz"],
            "suricata_version": "7.0.2",
            "health_metrics": {
                "cpu": 45.2,
                "memory": 1024,
                "uptime": 86400
            }
        }
    ]
}
```

### GET /agents/{agent_id}
Get single agent details.

**Response:**
```json
{
    "success": true,
    "agent": {
        "id": 123,
        "name": "suricata-node-01",
        "hostname": "web-server-01",
        "ip_address": "192.168.1.100",
        "status": "online",
        "last_seen": "2025-01-14T10:30:00Z",
        "last_event_at": "2025-01-14T10:29:55Z",
        "tags": ["production", "dmz"],
        "suricata_version": "7.0.2",
        "agent_version": "1.0.0",
        "health_metrics": {
            "cpu": 45.2,
            "memory_used_mb": 1024,
            "memory_total_mb": 16384,
            "uptime_seconds": 86400,
            "disk_usage_percent": 65
        },
        "system_info": {
            "os": "Ubuntu 22.04",
            "kernel": "5.15.0-91-generic"
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-14T10:30:00Z"
    }
}
```

### PUT /agents/{agent_id}
Update agent metadata.

**Request:**
```json
{
    "tags": ["production", "dmz", "critical"],
    "notes": "Primary web server"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Agent updated successfully"
}
```

### DELETE /agents/{agent_id}
Delete agent (requires confirmation).

**Query Parameters:**
- `confirm=true`: Required for actual deletion

**Response:**
```json
{
    "success": true,
    "message": "Agent deleted successfully"
}
```

### POST /agents/{agent_id}/heartbeat
Agent heartbeat (called periodically by agent).

**Headers:**
```
X-Agent-Token: <encrypted_token>
```

**Request:**
```json
{
    "health_metrics": {
        "cpu": 45.2,
        "memory_used_mb": 1024,
        "disk_usage_percent": 65
    },
    "suricata_pid": 12345,
    "suricata_running": true
}
```

**Response:**
```json
{
    "success": true,
    "pending_commands": [
        {
            "command_id": 456,
            "command_type": "reload_config",
            "parameters": {}
        }
    ]
}
```

### GET /agents/{agent_id}/install-command
Get install command for agent.

**Response:**
```json
{
    "success": true,
    "install_command": "curl -sSL https://dashboard.example.com/agent/install.sh?token=abc123 | sudo bash"
}
```

---

## Event Ingestion API

### POST /events/batch
Receive batch of events from agent (HTTP fallback).

**Headers:**
```
X-Agent-Token: <encrypted_token>
Content-Type: application/json
```

**Request:**
```json
{
    "agent_id": 123,
    "events": [
        {
            "timestamp": "2025-01-14T10:30:00.123456Z",
            "event_type": "alert",
            "data": {
                "timestamp": "2025-01-14T10:30:00.123456+0000",
                "flow_id": 123456789,
                "src_ip": "192.168.1.100",
                "dest_ip": "8.8.8.8",
                "alert": {
                    "signature": "ET MALWARE Botnet Traffic",
                    "signature_id": 2012345,
                    "severity": 1
                }
            }
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "received": 1,
    "processed": 1,
    "failed": 0
}
```

### WS /events/stream
WebSocket endpoint for real-time event streaming.

**Connection:**
```javascript
// Agent connects with token
ws://dashboard.example.com/api/v1/events/stream?token=<encrypted_token>
```

**Agent → Dashboard (Event Push):**
```json
{
    "type": "event",
    "agent_id": 123,
    "timestamp": "2025-01-14T10:30:00.123Z",
    "event_type": "alert",
    "data": { /* full eve.json event */ }
}
```

**Dashboard → Agent (Acknowledgment):**
```json
{
    "type": "ack",
    "sequence": 12345
}
```

**Dashboard → Agent (Command):**
```json
{
    "type": "command",
    "command_id": 456,
    "command_type": "reload_config",
    "parameters": {}
}
```

---

## Logs Ingestion API

### POST /logs/batch
Receive log entries from agent.

**Headers:**
```
X-Agent-Token: <encrypted_token>
```

**Request:**
```json
{
    "agent_id": 123,
    "logs": [
        {
            "timestamp": "2025-01-14T10:30:00Z",
            "log_type": "suricata",
            "level": "INFO",
            "message": "rule reload complete",
            "raw_line": "14/1/2025 -- 10:30:00 - <Info> - rule reload complete"
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "received": 1
}
```

---

## Config Management API

### GET /configs/{agent_id}
Get current agent configuration.

**Query Parameters:**
- `config_type`: Type of config (default: suricata.yaml)
- `version`: Specific version (default: latest active)

**Response:**
```json
{
    "success": true,
    "config": {
        "id": 789,
        "agent_id": 123,
        "config_type": "suricata.yaml",
        "content": "# Suricata Configuration\n...",
        "version": 5,
        "is_active": true,
        "applied_at": "2025-01-14T09:00:00Z",
        "changed_by": "admin",
        "created_at": "2025-01-14T08:55:00Z"
    }
}
```

### GET /configs/{agent_id}/history
Get config version history.

**Response:**
```json
{
    "success": true,
    "history": [
        {
            "id": 789,
            "version": 5,
            "is_active": true,
            "changed_by": "admin",
            "change_notes": "Enabled HTTP logging",
            "created_at": "2025-01-14T08:55:00Z",
            "applied_at": "2025-01-14T09:00:00Z"
        }
    ]
}
```

### POST /configs/{agent_id}
Upload new configuration.

**Request:**
```json
{
    "config_type": "suricata.yaml",
    "content": "# Suricata Configuration\n...",
    "change_notes": "Enable TLS logging",
    "validate_only": false,
    "auto_apply": false
}
```

**Response:**
```json
{
    "success": true,
    "config_id": 790,
    "version": 6,
    "validation": {
        "is_valid": true,
        "errors": []
    },
    "message": "Config saved as draft. Use /configs/{agent_id}/apply to deploy."
}
```

### POST /configs/{agent_id}/validate
Validate configuration without saving.

**Request:**
```json
{
    "config_type": "suricata.yaml",
    "content": "# Config content..."
}
```

**Response:**
```json
{
    "success": true,
    "validation": {
        "is_valid": false,
        "errors": [
            "Line 42: Invalid YAML syntax",
            "Line 100: Unknown configuration option 'invalid-option'"
        ],
        "warnings": [
            "Line 200: Deprecated option 'old-option', use 'new-option' instead"
        ]
    }
}
```

### POST /configs/{agent_id}/apply
Apply configuration to agent.

**Request:**
```json
{
    "config_id": 790,
    "reload_method": "graceful"  // graceful, restart, test-only
}
```

**Response:**
```json
{
    "success": true,
    "command_id": 456,
    "message": "Config deployment initiated. Check command status for progress."
}
```

### POST /configs/{agent_id}/rollback
Rollback to previous config version.

**Request:**
```json
{
    "version": 5
}
```

**Response:**
```json
{
    "success": true,
    "command_id": 457,
    "message": "Rollback initiated to version 5"
}
```

---

## Command Management API

### POST /commands/{agent_id}
Send command to agent.

**Request:**
```json
{
    "command_type": "reload_config",
    "parameters": {
        "config_type": "suricata.yaml"
    },
    "timeout_seconds": 300
}
```

**Available Commands:**
- `reload_config`: Reload Suricata configuration
- `restart_suricata`: Restart Suricata process
- `update_rules`: Update detection rules
- `get_pcap`: Capture PCAP file
- `get_stats`: Get detailed statistics
- `execute_script`: Run custom script (admin only)

**Response:**
```json
{
    "success": true,
    "command_id": 456,
    "status": "pending",
    "timeout_at": "2025-01-14T10:35:00Z"
}
```

### GET /commands/{command_id}
Get command status.

**Response:**
```json
{
    "success": true,
    "command": {
        "id": 456,
        "agent_id": 123,
        "command_type": "reload_config",
        "status": "completed",
        "result": {
            "success": true,
            "message": "Config reloaded successfully",
            "duration_ms": 250
        },
        "created_at": "2025-01-14T10:30:00Z",
        "completed_at": "2025-01-14T10:30:00.250Z"
    }
}
```

### GET /commands
List commands (with filters).

**Query Parameters:**
- `agent_id`: Filter by agent
- `status`: Filter by status
- `limit`, `offset`: Pagination

**Response:**
```json
{
    "success": true,
    "total": 100,
    "commands": [ /* command objects */ ]
}
```

---

## Statistics & Analytics API

### GET /stats/{agent_id}
Get agent statistics.

**Query Parameters:**
- `from`: Start timestamp (ISO 8601)
- `to`: End timestamp
- `interval`: Time bucket (1min, 1hour, 1day)
- `metrics`: Comma-separated metrics (packets,alerts,cpu)

**Response:**
```json
{
    "success": true,
    "agent_id": 123,
    "interval": "1hour",
    "data": [
        {
            "timestamp": "2025-01-14T10:00:00Z",
            "metrics": {
                "packets_total": 1000000,
                "packets_dropped": 50,
                "alerts_count": 25,
                "cpu_avg": 45.2,
                "memory_avg": 1024
            }
        }
    ]
}
```

### GET /stats/summary
Get dashboard summary across all agents.

**Response:**
```json
{
    "success": true,
    "summary": {
        "total_agents": 10,
        "online_agents": 8,
        "offline_agents": 2,
        "total_alerts_24h": 1250,
        "total_packets_24h": 50000000,
        "avg_cpu_usage": 42.5
    }
}
```

---

## Query & Search API

### POST /query/events
Query events from MongoDB.

**Request:**
```json
{
    "agent_id": 123,  // optional
    "event_type": "alert",  // optional
    "from": "2025-01-14T00:00:00Z",
    "to": "2025-01-14T23:59:59Z",
    "filters": {
        "src_ip": "192.168.1.100",
        "severity": [1, 2]
    },
    "sort": { "timestamp": -1 },
    "limit": 100,
    "offset": 0
}
```

**Response:**
```json
{
    "success": true,
    "total": 500,
    "events": [ /* event objects from MongoDB */ ]
}
```

### POST /query/logs
Query logs from MongoDB.

**Request:**
```json
{
    "agent_id": 123,
    "level": "ERROR",
    "search": "rule reload",
    "from": "2025-01-14T00:00:00Z",
    "to": "2025-01-14T23:59:59Z",
    "limit": 100
}
```

**Response:**
```json
{
    "success": true,
    "total": 50,
    "logs": [ /* log objects */ ]
}
```

---

## PCAP Management API

### POST /pcap/{agent_id}/start
Start PCAP capture on agent.

**Request:**
```json
{
    "interface": "eth0",
    "bpf_filter": "tcp port 80",
    "duration_seconds": 300,
    "max_size_mb": 100
}
```

**Response:**
```json
{
    "success": true,
    "capture_id": "65a1b2c3d4e5f6",
    "command_id": 458,
    "message": "Capture started"
}
```

### POST /pcap/{agent_id}/stop
Stop running capture.

**Request:**
```json
{
    "capture_id": "65a1b2c3d4e5f6"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Capture stopped",
    "stats": {
        "packets_captured": 10000,
        "bytes_total": 5242880
    }
}
```

### GET /pcap/{agent_id}/download/{capture_id}
Download PCAP file.

**Response:**
- Content-Type: application/vnd.tcpdump.pcap
- Binary PCAP file stream

---

## Agent Installer Endpoint

### GET /agent/install.sh
Generate agent installer script.

**Query Parameters:**
- `token`: Pre-generated agent token (optional, will generate if not provided)
- `name`: Agent name (optional, will prompt during install)
- `tags`: Comma-separated tags

**Response:**
```bash
#!/bin/bash
# Suricata Dashboard Agent Installer
# Generated: 2025-01-14T10:30:00Z
# Dashboard: https://dashboard.example.com

DASHBOARD_URL="https://dashboard.example.com"
AGENT_TOKEN="<encrypted_token>"

# ... (full installer script)
```

---

## Error Response Format

All endpoints return consistent error format:

```json
{
    "success": false,
    "error": {
        "code": "AGENT_NOT_FOUND",
        "message": "Agent with ID 123 not found",
        "details": {}
    }
}
```

**Common Error Codes:**
- `INVALID_TOKEN`: Authentication failed
- `AGENT_NOT_FOUND`: Agent doesn't exist
- `CONFIG_INVALID`: Configuration validation failed
- `COMMAND_TIMEOUT`: Command execution timeout
- `PERMISSION_DENIED`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## Rate Limiting

- **Agent API**: 1000 requests/min per agent
- **User API**: 100 requests/min per user
- **Ingestion API**: 10000 events/min per agent

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642176000
```

---

## WebSocket Protocol (Real-time)

### Connection
```
wss://dashboard.example.com/ws/v1
```

### Authentication
```json
{
    "type": "auth",
    "token": "<encrypted_token>",
    "agent_id": 123
}
```

### Message Types

**Ping/Pong (Keepalive):**
```json
// Client → Server
{ "type": "ping" }

// Server → Client
{ "type": "pong", "timestamp": "2025-01-14T10:30:00Z" }
```

**Event Streaming:**
```json
// Agent → Dashboard
{
    "type": "event",
    "sequence": 12345,
    "data": { /* eve.json event */ }
}

// Dashboard → Agent (ACK)
{
    "type": "ack",
    "sequence": 12345
}
```

**Command Execution:**
```json
// Dashboard → Agent
{
    "type": "command",
    "command_id": 456,
    "command_type": "reload_config",
    "parameters": {}
}

// Agent → Dashboard (Progress)
{
    "type": "command_progress",
    "command_id": 456,
    "status": "running",
    "progress": 50
}

// Agent → Dashboard (Result)
{
    "type": "command_result",
    "command_id": 456,
    "status": "completed",
    "result": { "success": true }
}
```

---

## API Versioning

- Current version: `v1`
- Version in URL: `/api/v1/*`
- Deprecation notice: 6 months before EOL
- Legacy support: v1 supported until at least 2026-01-01

---

## Next Steps
- [ ] Generate OpenAPI/Swagger schema
- [ ] Create Postman collection
- [ ] Write API client libraries (Python, JavaScript)
- [ ] Setup API documentation site (ReDoc/Swagger UI)
