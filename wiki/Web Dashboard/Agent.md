# Agent Protocol & Message Format

## Overview

Communication protocol between Suricata Agent (remote host) and Dashboard (centralized server).

**Transport Layers:**
- **Primary**: WebSocket (WSS) - Real-time bi-directional
- **Fallback**: HTTPS REST - Batch & reliable delivery

---

## Authentication & Encryption

### Token Generation

```python
# Dashboard generates token during agent registration
import secrets
import hashlib
from cryptography.fernet import Fernet

def generate_agent_token(agent_id: int, secret_key: str) -> dict:
    # Generate random token
    plain_token = secrets.token_urlsafe(32)

    # Hash for storage (bcrypt/argon2)
    token_hash = hashlib.pbkdf2_hmac('sha256',
                                      plain_token.encode(),
                                      secret_key.encode(),
                                      100000).hex()

    # Generate encryption key (Fernet)
    key_material = f"{secret_key}:{agent_id}".encode()
    encryption_key = hashlib.sha256(key_material).digest()

    return {
        'plain_token': plain_token,  # Send to agent (once)
        'token_hash': token_hash,    # Store in DB
        'encryption_key': encryption_key  # Store in DB
    }
```

### Token Encryption (Agent Side)

```python
# Agent encrypts token before every request
from cryptography.fernet import Fernet
import base64
import hashlib

class TokenEncryptor:
    def __init__(self, plain_token: str, secret_key: str, agent_id: int):
        self.plain_token = plain_token

        # Derive same key as dashboard
        key_material = f"{secret_key}:{agent_id}".encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        self.fernet = Fernet(key)

    def encrypt(self) -> str:
        """Encrypt token for transmission"""
        encrypted = self.fernet.encrypt(self.plain_token.encode())
        return encrypted.decode()

    def get_header(self) -> dict:
        """Get HTTP header with encrypted token"""
        return {
            'X-Agent-Token': self.encrypt(),
            'X-Agent-ID': str(self.agent_id)
        }
```

### Token Validation (Dashboard Side)

```python
# Dashboard decrypts and validates
def validate_agent_token(encrypted_token: str, agent_id: int) -> bool:
    # Get agent from DB
    agent = db.query(Agent).filter_by(id=agent_id).first()
    if not agent:
        return False

    # Decrypt token
    fernet = Fernet(agent.encryption_key)
    try:
        plain_token = fernet.decrypt(encrypted_token.encode()).decode()
    except:
        return False

    # Validate hash
    token_hash = hashlib.pbkdf2_hmac('sha256',
                                      plain_token.encode(),
                                      SECRET_KEY.encode(),
                                      100000).hex()

    return token_hash == agent.token_hash
```

---

## WebSocket Protocol (Primary)

### Connection Establishment

**1. Agent Initiates Connection:**
```
WSS: wss://dashboard.example.com/ws/v1/agent
```

**2. Authentication Message:**
```json
{
    "type": "auth",
    "agent_id": 123,
    "token": "<encrypted_token>",
    "agent_version": "1.0.0",
    "timestamp": "2025-01-14T10:30:00Z"
}
```

**3. Dashboard Response:**
```json
{
    "type": "auth_response",
    "success": true,
    "session_id": "sess_abc123",
    "config": {
        "heartbeat_interval": 30,
        "batch_size": 100,
        "compression": "gzip"
    }
}
```

### Message Format

All WebSocket messages follow this structure:

```json
{
    "type": "<message_type>",
    "sequence": 12345,           // Optional: for ordering/ack
    "timestamp": "ISO8601",
    "payload": { /* type-specific data */ }
}
```

### Message Types

#### 1. **Heartbeat (Keepalive)**

**Agent → Dashboard (every 30s):**
```json
{
    "type": "heartbeat",
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "health": {
            "cpu_percent": 45.2,
            "memory_mb": 1024,
            "disk_percent": 65
        },
        "suricata": {
            "pid": 12345,
            "running": true,
            "uptime": 86400
        }
    }
}
```

**Dashboard → Agent:**
```json
{
    "type": "heartbeat_ack",
    "timestamp": "2025-01-14T10:30:00Z"
}
```

#### 2. **Event Streaming**

**Agent → Dashboard:**
```json
{
    "type": "event",
    "sequence": 12345,
    "timestamp": "2025-01-14T10:30:00.123Z",
    "payload": {
        "event_type": "alert",
        "data": {
            // Full eve.json event
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
}
```

**Dashboard → Agent (Acknowledgment):**
```json
{
    "type": "event_ack",
    "sequence": 12345,
    "timestamp": "2025-01-14T10:30:00.125Z"
}
```

**Batch Events (Multiple in one message):**
```json
{
    "type": "event_batch",
    "sequence": 12346,
    "timestamp": "2025-01-14T10:30:01Z",
    "payload": {
        "count": 100,
        "events": [
            { /* event 1 */ },
            { /* event 2 */ },
            // ... up to 100 events
        ]
    }
}
```

#### 3. **Log Streaming**

**Agent → Dashboard:**
```json
{
    "type": "log",
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "log_type": "suricata",
        "level": "INFO",
        "message": "rule reload complete",
        "raw_line": "14/1/2025 -- 10:30:00 - <Info> - rule reload complete"
    }
}
```

#### 4. **Config Sync**

**Agent → Dashboard (Initial sync):**
```json
{
    "type": "config_push",
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "config_type": "suricata.yaml",
        "content": "# Suricata Configuration\n...",
        "hash": "sha256:abc123...",
        "last_modified": "2025-01-10T15:00:00Z"
    }
}
```

**Dashboard → Agent (Config update):**
```json
{
    "type": "config_update",
    "command_id": 456,
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "config_type": "suricata.yaml",
        "content": "# Updated configuration\n...",
        "hash": "sha256:def456...",
        "reload_method": "graceful"  // graceful, restart, test-only
    }
}
```

**Agent → Dashboard (Config update result):**
```json
{
    "type": "config_update_result",
    "command_id": 456,
    "timestamp": "2025-01-14T10:30:05Z",
    "payload": {
        "success": true,
        "message": "Config applied and Suricata reloaded",
        "validation_output": "Config test OK",
        "reload_duration_ms": 250
    }
}
```

#### 5. **Command Execution**

**Dashboard → Agent:**
```json
{
    "type": "command",
    "command_id": 457,
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "command_type": "restart_suricata",
        "parameters": {
            "graceful": true,
            "timeout": 30
        }
    }
}
```

**Agent → Dashboard (Progress updates):**
```json
{
    "type": "command_progress",
    "command_id": 457,
    "timestamp": "2025-01-14T10:30:01Z",
    "payload": {
        "status": "running",
        "progress": 50,
        "message": "Stopping Suricata gracefully..."
    }
}
```

**Agent → Dashboard (Final result):**
```json
{
    "type": "command_result",
    "command_id": 457,
    "timestamp": "2025-01-14T10:30:10Z",
    "payload": {
        "status": "completed",
        "success": true,
        "result": {
            "old_pid": 12345,
            "new_pid": 12789,
            "restart_duration_ms": 10000
        }
    }
}
```

#### 6. **PCAP Capture**

**Dashboard → Agent (Start capture):**
```json
{
    "type": "command",
    "command_id": 458,
    "payload": {
        "command_type": "pcap_start",
        "parameters": {
            "capture_id": "cap_abc123",
            "interface": "eth0",
            "bpf_filter": "tcp port 80",
            "duration": 300,
            "max_size_mb": 100
        }
    }
}
```

**Agent → Dashboard (Capture stats - periodic):**
```json
{
    "type": "pcap_stats",
    "timestamp": "2025-01-14T10:30:30Z",
    "payload": {
        "capture_id": "cap_abc123",
        "status": "running",
        "stats": {
            "packets_captured": 50000,
            "packets_dropped": 10,
            "bytes_total": 5242880,
            "duration_seconds": 30
        }
    }
}
```

**Agent → Dashboard (Capture complete):**
```json
{
    "type": "command_result",
    "command_id": 458,
    "payload": {
        "success": true,
        "result": {
            "capture_id": "cap_abc123",
            "file_path": "/tmp/capture_20250114.pcap",
            "file_size_bytes": 52428800,
            "packets_total": 150000,
            "duration_seconds": 300,
            "download_url": "https://dashboard/api/v1/pcap/download/cap_abc123"
        }
    }
}
```

#### 7. **Error Handling**

**Any side → Other side:**
```json
{
    "type": "error",
    "sequence": 12345,  // Reference to failed message
    "timestamp": "2025-01-14T10:30:00Z",
    "payload": {
        "error_code": "COMMAND_FAILED",
        "message": "Failed to reload Suricata: config validation error",
        "details": {
            "validation_output": "Error on line 42: invalid YAML"
        }
    }
}
```

---

## HTTP REST Protocol (Fallback)

Used when WebSocket connection unavailable or for batch operations.

### Event Batch Upload

**Endpoint:** `POST /api/v1/events/batch`

**Headers:**
```
X-Agent-Token: <encrypted_token>
X-Agent-ID: 123
Content-Type: application/json
Content-Encoding: gzip  // Optional compression
```

**Request Body:**
```json
{
    "agent_id": 123,
    "batch_id": "batch_20250114_103000",
    "events": [
        {
            "timestamp": "2025-01-14T10:30:00.123Z",
            "event_type": "alert",
            "data": { /* full event */ }
        }
        // ... up to 1000 events
    ]
}
```

**Response:**
```json
{
    "success": true,
    "batch_id": "batch_20250114_103000",
    "received": 1000,
    "processed": 1000,
    "failed": 0,
    "next_batch_delay_ms": 1000
}
```

### Log Batch Upload

**Endpoint:** `POST /api/v1/logs/batch`

Same structure as events.

### Heartbeat (HTTP)

**Endpoint:** `POST /api/v1/agents/{agent_id}/heartbeat`

**Request:**
```json
{
    "timestamp": "2025-01-14T10:30:00Z",
    "health": { /* health metrics */ },
    "suricata": { /* suricata status */ }
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

---

## Retry & Reliability

### WebSocket Reconnection

```python
class WebSocketClient:
    def __init__(self):
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 300  # Max 5 minutes

    async def connect_with_retry(self):
        while True:
            try:
                await self.connect()
                self.reconnect_delay = 1  # Reset on success
                break
            except ConnectionError:
                logger.warning(f"Connection failed, retry in {self.reconnect_delay}s")
                await asyncio.sleep(self.reconnect_delay)

                # Exponential backoff
                self.reconnect_delay = min(
                    self.reconnect_delay * 2,
                    self.max_reconnect_delay
                )
```

### Event Buffering

```python
# Agent buffers events locally when offline
class EventBuffer:
    def __init__(self, db_path='/var/lib/suricata-agent/buffer.db'):
        self.db = sqlite3.connect(db_path)
        self.max_size = 100000  # Max events to buffer

    def add_event(self, event: dict):
        """Add event to buffer"""
        self.db.execute(
            "INSERT INTO events (timestamp, data) VALUES (?, ?)",
            (event['timestamp'], json.dumps(event))
        )

    def get_batch(self, size=1000) -> list:
        """Get oldest events for sending"""
        cursor = self.db.execute(
            "SELECT id, data FROM events ORDER BY id LIMIT ?",
            (size,)
        )
        return [(row[0], json.loads(row[1])) for row in cursor]

    def delete_batch(self, ids: list):
        """Delete sent events"""
        placeholders = ','.join(['?'] * len(ids))
        self.db.execute(f"DELETE FROM events WHERE id IN ({placeholders})", ids)
        self.db.commit()
```

### Message Acknowledgment

**Sequence Numbers:**
- Each message gets unique sequence number
- Sender waits for ACK before considering message delivered
- Timeout → resend with same sequence number
- Receiver deduplicates by sequence number

```python
class MessageTracker:
    def __init__(self):
        self.pending = {}  # sequence -> (message, sent_at, retry_count)
        self.ack_timeout = 5  # seconds

    def send_with_ack(self, message: dict):
        sequence = self.get_next_sequence()
        message['sequence'] = sequence

        self.pending[sequence] = {
            'message': message,
            'sent_at': time.time(),
            'retry_count': 0
        }

        self.ws.send(json.dumps(message))

    def handle_ack(self, sequence: int):
        if sequence in self.pending:
            del self.pending[sequence]

    def check_timeouts(self):
        now = time.time()
        for seq, info in list(self.pending.items()):
            if now - info['sent_at'] > self.ack_timeout:
                if info['retry_count'] < 3:
                    # Retry
                    info['retry_count'] += 1
                    info['sent_at'] = now
                    self.ws.send(json.dumps(info['message']))
                else:
                    # Give up, buffer to disk
                    self.buffer.add_event(info['message'])
                    del self.pending[seq]
```

---

## Compression

For large payloads (events, logs, configs), use gzip compression:

**HTTP:**
```
Content-Encoding: gzip
```

**WebSocket:**
```json
{
    "type": "event_batch",
    "compressed": true,
    "compression": "gzip",
    "payload": "<base64_encoded_gzip_data>"
}
```

```python
import gzip
import base64

def compress_payload(data: dict) -> str:
    json_bytes = json.dumps(data).encode()
    compressed = gzip.compress(json_bytes)
    return base64.b64encode(compressed).decode()

def decompress_payload(encoded: str) -> dict:
    compressed = base64.b64decode(encoded)
    json_bytes = gzip.decompress(compressed)
    return json.loads(json_bytes)
```

---

## Rate Limiting

Agent should respect rate limits:

**HTTP Response Headers:**
```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9500
X-RateLimit-Reset: 1642176000
```

**Agent Behavior:**
```python
class RateLimiter:
    def __init__(self):
        self.limit = 10000
        self.remaining = 10000
        self.reset_at = 0

    def update_from_headers(self, headers: dict):
        self.remaining = int(headers.get('X-RateLimit-Remaining', 10000))
        self.reset_at = int(headers.get('X-RateLimit-Reset', 0))

    def should_throttle(self) -> bool:
        if self.remaining < 100:  # Safety margin
            if time.time() < self.reset_at:
                return True
        return False

    def wait_time(self) -> float:
        if self.should_throttle():
            return max(0, self.reset_at - time.time())
        return 0
```

---

## Protocol State Machine

```
┌─────────────┐
│ DISCONNECTED│
└──────┬──────┘
       │ connect()
       ▼
┌─────────────┐
│ CONNECTING  │
└──────┬──────┘
       │ send auth
       ▼
┌─────────────┐     auth failed
│AUTHENTICATING│──────────────────┐
└──────┬──────┘                  │
       │ auth success             │
       ▼                          ▼
┌─────────────┐              ┌────────┐
│  CONNECTED  │◀─────────────│  ERROR │
└──────┬──────┘   reconnect  └────────┘
       │                          ▲
       │ send/receive             │
       │ heartbeat                │
       │                          │
       │ timeout/error            │
       └──────────────────────────┘
```

---

## Security Considerations

1. **Token Rotation**: Agents should support token rotation without restart
2. **Certificate Pinning**: Agent validates dashboard SSL certificate
3. **Replay Attack Prevention**: Timestamp validation (reject messages > 5min old)
4. **Command Whitelist**: Agent only executes allowed commands
5. **Input Validation**: All incoming data validated before processing

```python
# Timestamp validation
def validate_timestamp(timestamp_str: str, max_age_seconds=300):
    msg_time = datetime.fromisoformat(timestamp_str)
    now = datetime.utcnow()
    age = (now - msg_time).total_seconds()

    if abs(age) > max_age_seconds:
        raise ValueError(f"Message too old/future: {age}s")
```

---

## Next Steps
- [ ] Implement WebSocket client/server
- [ ] Create protocol test suite
- [ ] Write protocol documentation for agent developers
- [ ] Create protocol debugging tools (message inspector)
