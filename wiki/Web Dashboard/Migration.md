# Migration Guide: Local → Remote Architecture

## Overview

Complete migration plan from local file-based dashboard to remote agent-based architecture.

**Timeline**: Estimated 2-3 weeks for full migration

---

## Pre-Migration Checklist

- [ ] Backup current dashboard data
- [ ] Backup Suricata configurations
- [ ] Export existing events/logs (if needed)
- [ ] Document current setup (paths, configs)
- [ ] Test new architecture in staging environment
- [ ] Plan maintenance window
- [ ] Communicate with users

---

## Migration Strategy

### Option A: Clean Migration (Recommended)
Fresh install of new architecture, no data migration.

**Pros:**
- Clean start
- No compatibility issues
- Faster deployment

**Cons:**
- Loss of historical data
- Need to reconfigure everything

### Option B: Parallel Migration
Run old and new side-by-side, gradual cutover.

**Pros:**
- Zero downtime
- Can compare behavior
- Rollback easy

**Cons:**
- More complex
- Higher resource usage
- Longer migration period

### Option C: In-Place Migration
Upgrade existing installation.

**Pros:**
- Preserve data
- Minimal disruption

**Cons:**
- Risk of conflicts
- Complex database migration
- Harder rollback

**Recommended**: **Option B (Parallel)** for production, **Option A** for new deployments.

---

## Phase 1: Preparation (Week 1)

### 1.1 Backup Everything

```bash
# Backup dashboard
tar -czf dashboard-backup-$(date +%Y%m%d).tar.gz \
    /opt/suricata-dashboard \
    /etc/suricata-dashboard \
    /var/lib/suricata-dashboard

# Backup database (if exists)
pg_dump suricata_dashboard > suricata_dashboard_backup.sql

# Backup Suricata config
tar -czf suricata-config-backup-$(date +%Y%m%d).tar.gz \
    /etc/suricata \
    /var/log/suricata
```

### 1.2 Setup New Infrastructure

#### Deploy PostgreSQL
```bash
# Docker
docker run -d \
    --name suricata-postgres \
    -e POSTGRES_DB=suricata_dashboard \
    -e POSTGRES_USER=suricata \
    -e POSTGRES_PASSWORD=<secure_password> \
    -v postgres_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:15-alpine

# Or use existing PostgreSQL server
```

#### Deploy MongoDB
```bash
# Docker
docker run -d \
    --name suricata-mongodb \
    -e MONGO_INITDB_ROOT_USERNAME=suricata \
    -e MONGO_INITDB_ROOT_PASSWORD=<secure_password> \
    -e MONGO_INITDB_DATABASE=suricata \
    -v mongodb_data:/data/db \
    -p 27017:27017 \
    mongo:7

# Or use existing MongoDB cluster
```

### 1.3 Initialize Databases

#### PostgreSQL Schema
```bash
# Run migrations
cd suricata-dashboard
python migrations/migrate.py --database postgresql --action upgrade

# Verify
psql -h localhost -U suricata -d suricata_dashboard -c "\dt"
```

Expected tables:
- agents
- agent_configs
- agent_commands
- agent_statistics
- users
- audit_logs

#### MongoDB Collections
```bash
# Run MongoDB init script
mongo suricata < migrations/mongodb/001_create_collections.js
mongo suricata < migrations/mongodb/002_create_indexes.js

# Verify
mongo suricata --eval "db.getCollectionNames()"
```

Expected collections:
- events
- logs
- pcap_captures

### 1.4 Deploy New Dashboard

```bash
# Clone repo (new version)
git clone https://github.com/user/suricata-dashboard.git /opt/suricata-dashboard-v2
cd /opt/suricata-dashboard-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
nano config/config.yaml
```

**config.yaml:**
```yaml
dashboard:
  host: 0.0.0.0
  port: 5001  # Different port during migration
  debug: false
  secret_key: "<generate_secure_key>"

databases:
  postgresql:
    host: localhost
    port: 5432
    database: suricata_dashboard
    user: suricata
    password: "<password>"
    pool_size: 20

  mongodb:
    host: localhost
    port: 27017
    database: suricata
    user: suricata
    password: "<password>"
    auth_source: admin

websocket:
  enabled: true
  cors_origins: "*"

agent:
  registration:
    auto_approve: false  # Require manual approval initially
    require_tags: true
```

```bash
# Start dashboard
python run.py
```

Dashboard should be accessible at `http://localhost:5001`

---

## Phase 2: Testing & Validation (Week 1-2)

### 2.1 Install Test Agent

On a non-production Suricata host:

```bash
curl -sSL http://localhost:5001/agent/install.sh | sudo bash -s -- --name test-agent
```

### 2.2 Verify Agent Connection

#### Check Dashboard
```bash
# API
curl -H "Authorization: Bearer <jwt_token>" \
    http://localhost:5001/api/v1/agents

# Expected:
# {
#   "agents": [
#     {
#       "id": 1,
#       "name": "test-agent",
#       "status": "online",
#       ...
#     }
#   ]
# }
```

#### Check Agent Logs
```bash
# On agent host
journalctl -u suricata-agent -f
```

Look for:
```
[INFO] Connected to dashboard
[INFO] WebSocket connection established
[INFO] Sending heartbeat
```

### 2.3 Validate Data Flow

#### Events
```bash
# Generate test alert in Suricata
sudo suricata -T  # Trigger test mode

# Check MongoDB
mongo suricata --eval 'db.events.find().limit(5).pretty()'

# Check dashboard UI
# Navigate to http://localhost:5001/monitor/realtime
# Should see events streaming in real-time
```

#### Logs
```bash
# Check log streaming
mongo suricata --eval 'db.logs.find().limit(5).pretty()'
```

#### Configuration Sync
```bash
# Web UI: Navigate to agent config editor
# Make a change to suricata.yaml
# Click "Apply"

# On agent host, verify config updated
cat /etc/suricata/suricata.yaml
journalctl -u suricata-agent | grep "Config applied"
```

### 2.4 Performance Testing

#### Load Test
```bash
# Generate high event volume
# Use tcpreplay or similar tool

# Monitor agent performance
top -p $(pgrep -f suricata-agent)

# Monitor dashboard performance
curl http://localhost:5001/api/v1/stats/summary

# Check MongoDB performance
mongo suricata --eval 'db.events.stats()'
```

#### Stress Test
- Multiple agents (5-10)
- High event rate (10k/sec)
- Concurrent API requests
- WebSocket connections from multiple browsers

---

## Phase 3: Production Deployment (Week 2-3)

### 3.1 Deploy to Production Hosts

Create deployment plan:

| Host | Priority | Agent Name | Schedule |
|------|----------|------------|----------|
| web-01 | High | web-frontend-01 | Day 1, 10:00 AM |
| web-02 | High | web-frontend-02 | Day 1, 11:00 AM |
| db-01 | Critical | database-01 | Day 2, 10:00 AM |
| app-01 | Medium | app-server-01 | Day 3, 10:00 AM |

#### Deployment Script
```bash
#!/bin/bash
# deploy-agent.sh

HOSTS=(
    "web-01:web-frontend-01:production,web"
    "web-02:web-frontend-02:production,web"
    "db-01:database-01:critical,database"
)

for HOST_INFO in "${HOSTS[@]}"; do
    IFS=':' read -r HOST NAME TAGS <<< "$HOST_INFO"

    echo "Deploying to $HOST ($NAME)..."

    ssh root@$HOST "curl -sSL https://dashboard.example.com/agent/install.sh | \
        bash -s -- --name $NAME --tags $TAGS"

    # Wait for agent to connect
    sleep 10

    # Verify
    curl -H "Authorization: Bearer $JWT_TOKEN" \
        "https://dashboard.example.com/api/v1/agents" | \
        jq ".agents[] | select(.name == \"$NAME\")"

    echo "$HOST deployed successfully"
done
```

### 3.2 Cutover from Old Dashboard

#### Before Cutover
```bash
# Stop old dashboard
systemctl stop suricata-dashboard-old

# Verify no active connections
netstat -an | grep :5000
```

#### Update Configuration
```bash
# Update new dashboard to use production port
sed -i 's/port: 5001/port: 5000/' /opt/suricata-dashboard-v2/config/config.yaml

# Restart
systemctl restart suricata-dashboard
```

#### Update DNS/Load Balancer
```bash
# Update nginx/load balancer to point to new dashboard
# Or update DNS if applicable
```

#### Verify
```bash
# Access dashboard at production URL
curl https://dashboard.example.com/api/v1/health

# Check web UI
# Open https://dashboard.example.com in browser
```

### 3.3 Post-Deployment Validation

#### Checklist
- [ ] All agents connected and reporting
- [ ] Events streaming in real-time
- [ ] Logs visible in dashboard
- [ ] Config management working
- [ ] PCAP capture functional
- [ ] Alerts triggering correctly
- [ ] WebSocket connections stable
- [ ] API responding within SLA
- [ ] Database queries performant

#### Monitor for 48 Hours
```bash
# Agent health
watch -n 5 'curl -s https://dashboard.example.com/api/v1/agents | jq ".agents[] | {name, status}"'

# Event ingestion rate
mongo suricata --eval 'db.events.count()'

# System resources
htop
iotop
```

---

## Phase 4: Decommissioning Old System (Week 3+)

### 4.1 Archive Old Data (Optional)

```bash
# Export old events if needed
# (This depends on your old dashboard structure)

# Archive
tar -czf old-dashboard-archive-$(date +%Y%m%d).tar.gz \
    /opt/suricata-dashboard-old \
    /var/lib/suricata-dashboard-old

# Move to cold storage
mv old-dashboard-archive-*.tar.gz /mnt/archive/
```

### 4.2 Uninstall Old Dashboard

```bash
# Stop service
systemctl stop suricata-dashboard-old
systemctl disable suricata-dashboard-old

# Remove files
rm -rf /opt/suricata-dashboard-old
rm -rf /etc/suricata-dashboard-old
rm -rf /var/lib/suricata-dashboard-old
rm /etc/systemd/system/suricata-dashboard-old.service

# Reload systemd
systemctl daemon-reload
```

### 4.3 Cleanup

```bash
# Remove old Python dependencies
# (if using system Python, not venv)

# Remove old cronjobs (if any)
crontab -e  # Remove old dashboard related jobs

# Update documentation
# Update runbooks, wiki, etc.
```

---

## Rollback Plan

If critical issues occur during migration:

### Emergency Rollback

```bash
# Stop new dashboard
systemctl stop suricata-dashboard

# Start old dashboard
systemctl start suricata-dashboard-old

# Update nginx/load balancer to point to old dashboard

# Stop agents (optional)
# SSH to each agent host
systemctl stop suricata-agent
```

### Partial Rollback

```bash
# Keep new dashboard running
# Stop specific agents having issues
ssh agent-host "systemctl stop suricata-agent"

# Troubleshoot
# Once fixed, restart
ssh agent-host "systemctl start suricata-agent"
```

---

## Common Migration Issues

### Issue 1: Agent Cannot Connect

**Symptoms:**
```
journalctl -u suricata-agent
# [ERROR] Connection refused to dashboard
```

**Solution:**
```bash
# Check firewall
sudo ufw status
sudo ufw allow from <agent_ip> to any port 5000
sudo ufw allow from <agent_ip> to any port 443

# Check dashboard is listening
netstat -tln | grep 5000

# Check SSL certificate (if HTTPS)
curl -v https://dashboard.example.com/api/v1/health
```

### Issue 2: Events Not Appearing in Dashboard

**Symptoms:**
- Agent shows "online"
- No events in MongoDB

**Solution:**
```bash
# Check agent logs
journalctl -u suricata-agent | grep ERROR

# Check eve.json permissions
ls -la /var/log/suricata/eve.json
# Should be readable by root (agent runs as root)

# Check MongoDB connection
mongo suricata --eval 'db.runCommand({ping: 1})'

# Check dashboard event processor
# Look for errors in dashboard logs
tail -f /var/log/suricata-dashboard/dashboard.log | grep event
```

### Issue 3: High CPU/Memory on Agent

**Symptoms:**
```bash
top -p $(pgrep -f suricata-agent)
# Shows high CPU/memory usage
```

**Solution:**
```bash
# Check buffer size
sqlite3 /var/lib/suricata-agent/buffer.db "SELECT COUNT(*) FROM events;"
# If > 50000, buffer is overflowing

# Check network connectivity to dashboard
ping dashboard.example.com

# Increase batch size
nano /etc/suricata-agent/config.yaml
# streaming.batch_size: 500 (from 100)

# Restart agent
systemctl restart suricata-agent
```

### Issue 4: MongoDB Disk Usage High

**Symptoms:**
```bash
df -h
# /var/lib/mongodb at 90%
```

**Solution:**
```bash
# Check collection sizes
mongo suricata --eval 'db.stats(1024*1024)'  # MB

# Enable TTL if not already
mongo suricata --eval '
db.events.createIndex(
    { "expire_at": 1 },
    { expireAfterSeconds: 0 }
)
'

# Set retention policy
mongo suricata --eval '
db.events.updateMany(
    { expire_at: { $exists: false } },
    { $set: { expire_at: new Date(Date.now() + 90*24*60*60*1000) } }
)
'

# Manual cleanup (old data)
mongo suricata --eval '
db.events.deleteMany({
    timestamp: { $lt: new Date("2024-01-01") }
})
'
```

---

## Post-Migration Optimization

### 1. Database Tuning

#### PostgreSQL
```sql
-- Analyze tables
ANALYZE agents;
ANALYZE agent_configs;
ANALYZE agent_statistics;

-- Vacuum
VACUUM ANALYZE;

-- Check indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

#### MongoDB
```javascript
// Analyze collection stats
db.events.stats(1024*1024)

// Check index usage
db.events.aggregate([{ $indexStats: {} }])

// Optimize indexes
db.events.createIndex({ "indexed.src_ip": 1, timestamp: -1 })
db.events.createIndex({ "indexed.signature_id": 1, timestamp: -1 })
```

### 2. Enable Sharding (Large Scale)

If ingesting > 100k events/sec:

```javascript
// Enable sharding
sh.enableSharding("suricata")

// Shard events collection
sh.shardCollection("suricata.events", { agent_id: 1, timestamp: 1 })
```

### 3. Setup Monitoring

```bash
# Prometheus exporter for dashboard
pip install prometheus-flask-exporter

# Add to dashboard
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)

# Expose /metrics endpoint
# Scrape with Prometheus

# Grafana dashboard
# Import dashboard template
```

### 4. Backup Strategy

```bash
# Automated backups
cat > /etc/cron.daily/backup-suricata-dashboard << 'EOF'
#!/bin/bash
# PostgreSQL
pg_dump suricata_dashboard | gzip > /backup/postgres-$(date +%Y%m%d).sql.gz

# MongoDB
mongodump --db suricata --gzip --archive=/backup/mongo-$(date +%Y%m%d).gz

# Cleanup old backups (> 30 days)
find /backup -name "*.gz" -mtime +30 -delete
EOF

chmod +x /etc/cron.daily/backup-suricata-dashboard
```

---

## Success Criteria

Migration is considered successful when:

- [x] All production agents connected and online
- [x] Event ingestion rate matches Suricata output rate
- [x] Dashboard load time < 2 seconds
- [x] API response time < 100ms (p95)
- [x] WebSocket connections stable for > 24 hours
- [x] Zero data loss during migration
- [x] Config management functional on all agents
- [x] User training completed
- [x] Documentation updated
- [x] Old dashboard decommissioned

---

## Timeline Summary

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Preparation | 3-5 days | Backup, setup infra, deploy new dashboard |
| Testing | 5-7 days | Install test agent, validate, performance test |
| Production Deployment | 5-7 days | Roll out agents, cutover, validate |
| Decommission | 2-3 days | Archive, cleanup old system |
| **Total** | **2-3 weeks** | |

---

## Support & Resources

- Documentation: https://dashboard.example.com/docs
- Wiki: https://github.com/user/suricata-dashboard/wiki
- Issues: https://github.com/user/suricata-dashboard/issues
- Slack: #suricata-dashboard

---

## Next Steps
- [ ] Review migration plan with team
- [ ] Schedule maintenance windows
- [ ] Setup staging environment
- [ ] Create runbook for operations team
- [ ] Plan rollback procedures
