# Database Schema Design

## Overview
Hybrid database architecture:
- **PostgreSQL**: Structured data (agents, users, configs, statistics)
- **MongoDB**: Unstructured data (events, logs, high-volume time-series)

---

## PostgreSQL Schema

### 1. `agents` Table
Stores registered remote Suricata agents.

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address INET,

    -- Authentication
    token_hash VARCHAR(512) NOT NULL,  -- Hashed token for validation
    encryption_key VARCHAR(512) NOT NULL,  -- For token encryption

    -- Metadata
    tags JSONB DEFAULT '[]',  -- ["production", "dmz", "web-frontend"]
    version VARCHAR(50),  -- Agent version

    -- Suricata Info
    suricata_version VARCHAR(50),
    suricata_pid INTEGER,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, online, offline, error
    last_seen TIMESTAMP WITH TIME ZONE,
    last_event_at TIMESTAMP WITH TIME ZONE,

    -- Health Metrics (cached from latest stats)
    health_metrics JSONB,  -- {"cpu": 45.2, "memory": 1024, "uptime": 86400}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_seen ON agents(last_seen);
CREATE INDEX idx_agents_tags ON agents USING GIN(tags);
```

### 2. `agent_configs` Table
Stores Suricata configuration files for each agent.

```sql
CREATE TABLE agent_configs (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Config Content
    config_type VARCHAR(50) NOT NULL,  -- 'suricata.yaml', 'threshold.config', etc
    content TEXT NOT NULL,  -- YAML/config file content
    content_hash VARCHAR(64),  -- SHA256 hash for change detection

    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,

    -- Validation
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors TEXT,

    -- Status
    applied_at TIMESTAMP WITH TIME ZONE,  -- When agent applied this config
    status VARCHAR(50) DEFAULT 'draft',  -- draft, pending, applied, failed

    -- Metadata
    changed_by VARCHAR(255),  -- Username who made changes
    change_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_configs_agent_id ON agent_configs(agent_id);
CREATE INDEX idx_agent_configs_active ON agent_configs(agent_id, is_active) WHERE is_active = TRUE;
CREATE UNIQUE INDEX idx_agent_configs_unique_active ON agent_configs(agent_id, config_type, is_active) WHERE is_active = TRUE;
```

### 3. `agent_commands` Table
Command queue for bi-directional communication (dashboard → agent).

```sql
CREATE TABLE agent_commands (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Command Details
    command_type VARCHAR(100) NOT NULL,  -- 'reload_config', 'restart_suricata', 'get_pcap', 'update_rules'
    parameters JSONB,  -- Command-specific parameters

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, acknowledged, completed, failed, timeout

    -- Result
    result JSONB,  -- Command execution result
    error_message TEXT,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE,  -- Command expires after this

    -- Metadata
    created_by VARCHAR(255),  -- User who initiated command
    priority INTEGER DEFAULT 5  -- 1=highest, 10=lowest
);

-- Indexes
CREATE INDEX idx_agent_commands_agent_status ON agent_commands(agent_id, status);
CREATE INDEX idx_agent_commands_pending ON agent_commands(status, created_at) WHERE status = 'pending';
```

### 4. `agent_statistics` Table
Aggregated statistics (hourly/daily rollups).

```sql
CREATE TABLE agent_statistics (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,

    -- Time bucket
    bucket_time TIMESTAMP WITH TIME ZONE NOT NULL,
    bucket_interval VARCHAR(20) NOT NULL,  -- '1min', '1hour', '1day'

    -- Metrics
    metrics JSONB NOT NULL,
    /*
    {
        "packets_total": 1000000,
        "packets_dropped": 50,
        "bytes_total": 52428800,
        "alerts_count": 25,
        "flows_count": 500,
        "cpu_avg": 45.2,
        "memory_avg": 1024
    }
    */

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_statistics_agent_time ON agent_statistics(agent_id, bucket_time DESC);
CREATE INDEX idx_agent_statistics_interval ON agent_statistics(bucket_interval, bucket_time DESC);

-- Partitioning by time (optional, for large deployments)
-- CREATE TABLE agent_statistics_2025_01 PARTITION OF agent_statistics
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### 5. `users` Table
Dashboard users (existing, may need minor modifications).

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(512) NOT NULL,

    -- Roles
    role VARCHAR(50) DEFAULT 'viewer',  -- admin, operator, viewer

    -- API Access
    api_key_hash VARCHAR(512),  -- For API access

    -- Permissions (JSONB for flexibility)
    permissions JSONB DEFAULT '{}',
    /*
    {
        "agents": ["read", "write", "delete"],
        "configs": ["read", "write"],
        "commands": ["execute"]
    }
    */

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. `audit_logs` Table
Audit trail for compliance and debugging.

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Who
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(255),  -- Denormalized for deleted users
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,

    -- What
    action VARCHAR(100) NOT NULL,  -- 'config_updated', 'command_executed', 'agent_registered'
    resource_type VARCHAR(50),  -- 'agent', 'config', 'command'
    resource_id INTEGER,

    -- Details
    details JSONB,
    ip_address INET,
    user_agent TEXT,

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_agent ON audit_logs(agent_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
```

---

## MongoDB Schema

### 1. `events` Collection
High-volume Suricata events (from eve.json).

```javascript
{
    _id: ObjectId("..."),

    // Agent reference
    agent_id: 123,  // References PostgreSQL agents.id
    agent_name: "suricata-node-01",

    // Event metadata
    event_type: "alert",  // alert, flow, http, dns, tls, ssh, stats, anomaly, files
    timestamp: ISODate("2025-01-14T10:30:00Z"),

    // Original Suricata event (preserved as-is)
    raw_event: {
        // Complete eve.json event
        "timestamp": "2025-01-14T10:30:00.123456+0000",
        "flow_id": 123456789,
        "event_type": "alert",
        "src_ip": "192.168.1.100",
        "dest_ip": "8.8.8.8",
        "alert": {
            "signature": "ET MALWARE Possible Botnet Traffic",
            "signature_id": 2012345,
            "severity": 1
        }
        // ... full event
    },

    // Indexed fields for fast queries (denormalized from raw_event)
    indexed: {
        src_ip: "192.168.1.100",
        dest_ip: "8.8.8.8",
        src_port: 54321,
        dest_port: 80,
        proto: "TCP",
        signature_id: 2012345,
        severity: 1,
        category: "Malware",
        flow_id: 123456789
    },

    // Enrichment data (added by dashboard)
    enriched: {
        geo_src: {
            country: "US",
            city: "New York",
            lat: 40.7128,
            lon: -74.0060
        },
        geo_dest: {
            country: "US",
            city: "Mountain View"
        },
        threat_intel: {
            is_malicious: true,
            reputation_score: 85,
            categories: ["botnet", "c2"]
        }
    },

    // Processing metadata
    received_at: ISODate("2025-01-14T10:30:01Z"),
    processed_at: ISODate("2025-01-14T10:30:01.500Z"),

    // TTL for auto-deletion (optional)
    expire_at: ISODate("2025-04-14T10:30:00Z")  // 90 days retention
}
```

**Indexes:**
```javascript
// Compound indexes for common queries
db.events.createIndex({ agent_id: 1, timestamp: -1 })
db.events.createIndex({ agent_id: 1, event_type: 1, timestamp: -1 })
db.events.createIndex({ "indexed.src_ip": 1, timestamp: -1 })
db.events.createIndex({ "indexed.dest_ip": 1, timestamp: -1 })
db.events.createIndex({ "indexed.signature_id": 1, timestamp: -1 })
db.events.createIndex({ timestamp: -1 })

// TTL index for auto-deletion
db.events.createIndex({ expire_at: 1 }, { expireAfterSeconds: 0 })

// Text search
db.events.createIndex({
    "raw_event.alert.signature": "text",
    "indexed.src_ip": "text",
    "indexed.dest_ip": "text"
})
```

**Sharding Strategy** (for very large deployments):
```javascript
// Shard by agent_id and timestamp
sh.shardCollection("suricata.events", { agent_id: 1, timestamp: 1 })
```

### 2. `logs` Collection
Suricata application logs (suricata.log, fast.log).

```javascript
{
    _id: ObjectId("..."),

    agent_id: 123,
    agent_name: "suricata-node-01",

    // Log metadata
    log_type: "suricata",  // suricata, fast, stats
    level: "INFO",  // DEBUG, INFO, WARNING, ERROR, CRITICAL
    timestamp: ISODate("2025-01-14T10:30:00Z"),

    // Log content
    message: "rule reload complete",

    // Structured data (if parseable)
    structured: {
        component: "detect",
        thread_id: 12345
    },

    // Full raw line
    raw_line: "14/1/2025 -- 10:30:00 - <Info> - rule reload complete",

    received_at: ISODate("2025-01-14T10:30:01Z"),
    expire_at: ISODate("2025-02-14T10:30:00Z")  // 30 days retention
}
```

**Indexes:**
```javascript
db.logs.createIndex({ agent_id: 1, timestamp: -1 })
db.logs.createIndex({ level: 1, timestamp: -1 })
db.logs.createIndex({ timestamp: -1 })
db.logs.createIndex({ expire_at: 1 }, { expireAfterSeconds: 0 })
db.logs.createIndex({ message: "text" })
```

### 3. `pcap_captures` Collection
PCAP capture session metadata.

```javascript
{
    _id: ObjectId("..."),

    agent_id: 123,
    agent_name: "suricata-node-01",

    // Capture details
    interface: "eth0",
    capture_mode: "AF_PACKET",  // PCAP, AF_PACKET, AF_XDP

    // Filters
    bpf_filter: "tcp port 80",

    // Status
    status: "running",  // running, stopped, error

    // Statistics
    stats: {
        packets_captured: 1000000,
        packets_dropped: 50,
        bytes_total: 52428800,
        duration_seconds: 3600
    },

    // Timing
    started_at: ISODate("2025-01-14T10:00:00Z"),
    stopped_at: ISODate("2025-01-14T11:00:00Z"),

    // File info (if saved)
    pcap_file: {
        path: "/var/log/suricata/capture_20250114_100000.pcap",
        size_bytes: 52428800,
        available_until: ISODate("2025-01-15T11:00:00Z")
    }
}
```

**Indexes:**
```javascript
db.pcap_captures.createIndex({ agent_id: 1, started_at: -1 })
db.pcap_captures.createIndex({ status: 1 })
```

---

## Data Flow

```
┌─────────────┐
│   Agent     │
└──────┬──────┘
       │
       │ (1) Events/Logs
       ▼
┌─────────────────┐
│  API Ingestion  │
└──────┬──────────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌──────────────┐  ┌────────────┐  ┌──────────────┐
│  PostgreSQL  │  │  MongoDB   │  │  WebSocket   │
│              │  │            │  │  Broadcast   │
│ - Agents     │  │ - Events   │  │              │
│ - Configs    │  │ - Logs     │  │ → Web UI     │
│ - Commands   │  │ - PCAPs    │  │              │
│ - Statistics │  │            │  │              │
└──────────────┘  └────────────┘  └──────────────┘
```

---

## Retention Policies

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Events (raw) | 90 days | MongoDB (with TTL) |
| Events (alerts only) | 1 year | MongoDB |
| Logs | 30 days | MongoDB (with TTL) |
| Statistics (1min) | 7 days | PostgreSQL |
| Statistics (1hour) | 90 days | PostgreSQL |
| Statistics (1day) | 2 years | PostgreSQL |
| Configs (history) | Forever | PostgreSQL |
| Audit logs | 2 years | PostgreSQL |

---

## Migration Script Structure

```sql
-- PostgreSQL migration
BEGIN;

-- Drop old local-only tables (if any)
DROP TABLE IF EXISTS local_events;

-- Create new tables
\i schema/agents.sql
\i schema/agent_configs.sql
\i schema/agent_commands.sql
\i schema/agent_statistics.sql
\i schema/audit_logs.sql

-- Migrate existing data (if applicable)
-- INSERT INTO agents (name, hostname, ...) VALUES ('local-legacy', 'localhost', ...);

COMMIT;
```

```javascript
// MongoDB initialization
use suricata;

// Create collections
db.createCollection("events", {
    timeseries: {
        timeField: "timestamp",
        metaField: "agent_id",
        granularity: "seconds"
    }
});

db.createCollection("logs");
db.createCollection("pcap_captures");

// Create indexes
load("indexes/events.js");
load("indexes/logs.js");
load("indexes/pcap_captures.js");
```

---

## Connection Configuration

```python
# config.py
DATABASES = {
    'postgresql': {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'suricata_dashboard'),
        'user': os.getenv('POSTGRES_USER', 'suricata'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    },
    'mongodb': {
        'host': os.getenv('MONGO_HOST', 'localhost'),
        'port': int(os.getenv('MONGO_PORT', 27017)),
        'database': os.getenv('MONGO_DB', 'suricata'),
        'user': os.getenv('MONGO_USER', 'suricata'),
        'password': os.getenv('MONGO_PASSWORD', 'password')
    }
}
```

---

## Next Steps
- [ ] Create actual SQL migration files
- [ ] Create MongoDB index scripts
- [ ] Design connection pooling strategy
- [ ] Plan backup/restore procedures
- [ ] Design data retention cleanup jobs
