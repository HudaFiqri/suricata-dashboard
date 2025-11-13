# Docker Deployment - Suricata Dashboard

Complete guide untuk deploy Suricata Dashboard menggunakan Docker dan Docker Compose.

## 📋 Daftar Isi
- [Overview](#overview)
- [Arsitektur](#arsitektur)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Operations](#operations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Overview

### Tentang Docker Deployment

Suricata Dashboard dapat di-deploy menggunakan Docker untuk memudahkan:
- **Portabilitas**: Deploy di berbagai environment dengan konsisten
- **Isolasi**: Aplikasi dan dependencies terisolasi dari host system
- **Skalabilitas**: Mudah untuk scale up/down
- **Reproducibility**: Environment yang sama di development dan production

### Components

1. **Dashboard Container**
   - Base: Python 3.11 Slim Bookworm
   - Framework: Flask
   - Dependencies: RRDtool, PostgreSQL/MySQL clients
   - User: Non-root (uid 1000)

2. **Database Container**
   - PostgreSQL 15 Alpine (default)
   - MySQL 8.0 (optional)

3. **Networks & Volumes**
   - Bridge network untuk inter-container communication
   - Persistent volumes untuk data
   - Host mounts untuk Suricata files

---

## Arsitektur

### Container Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Suricata Installation                             │  │
│  │  - /etc/suricata/suricata.yaml                     │  │
│  │  - /etc/suricata/rules/                            │  │
│  │  - /var/log/suricata/eve.json                      │  │
│  └──────────────┬─────────────────────────────────────┘  │
│                 │ (mounted read-only)                    │
│  ┌──────────────┴─────────────────────────────────────┐  │
│  │         Docker Network: suricata-network           │  │
│  │                                                     │  │
│  │  ┌─────────────────────┐  ┌───────────────────┐   │  │
│  │  │  Dashboard          │  │  PostgreSQL       │   │  │
│  │  │  Container          │◄─┤  Container        │   │  │
│  │  │                     │  │                   │   │  │
│  │  │  Port: 5000        │  │  Port: 5432       │   │  │
│  │  │  User: suricata    │  │  (internal)       │   │  │
│  │  └─────────────────────┘  └───────────────────┘   │  │
│  │           │                        │               │  │
│  └───────────┼────────────────────────┼───────────────┘  │
│              │                        │                  │
│  ┌───────────▼────────────┐  ┌───────▼────────────┐    │
│  │  Volumes               │  │  Volumes           │    │
│  │  - dashboard-data      │  │  - postgres-data   │    │
│  │  - dashboard-logs      │  │                    │    │
│  │  - dashboard-rrd       │  │                    │    │
│  └────────────────────────┘  └────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Suricata → Dashboard**
   - Suricata writes logs ke `/var/log/suricata/eve.json`
   - Dashboard reads logs via mounted volume (read-only)
   - Dashboard parses dan stores ke database

2. **Dashboard → Database**
   - Dashboard connects via Docker network
   - Stores alerts, traffic stats, metrics
   - Queries untuk dashboard display

3. **User → Dashboard**
   - HTTP requests ke port 5000
   - Flask handles requests
   - Returns HTML + API responses

---

## Installation Guide

### Prerequisites Check

Sebelum install, pastikan:

```bash
# Check Docker version
docker --version
# Required: Docker version 20.10+

# Check Docker Compose version
docker-compose --version
# Required: Docker Compose v2.0+

# Check Suricata installation
which suricata
ls -la /etc/suricata/suricata.yaml
ls -la /var/log/suricata/

# Check port availability
sudo netstat -tulpn | grep 5000
# Port 5000 harus available
```

### Step-by-Step Installation

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/suricata-dashboard.git
cd suricata-dashboard/container/docker
```

#### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimal configuration:**

```ini
# Database password (IMPORTANT!)
DB_PASSWORD=your_secure_password_here

# Suricata paths (sesuaikan dengan instalasi Anda)
HOST_SURICATA_CONFIG=/etc/suricata
HOST_SURICATA_LOG=/var/log/suricata
```

#### 3. Build Images

```bash
# Build dashboard image
docker-compose build

# Verify image created
docker images | grep suricata-dashboard
```

#### 4. Start Services

```bash
# Start all services in background
docker-compose up -d

# Monitor startup logs
docker-compose logs -f
```

#### 5. Verify Deployment

```bash
# Check services status
docker-compose ps

# Should show:
# NAME                    STATUS              PORTS
# suricata-dashboard      Up (healthy)        0.0.0.0:5000->5000/tcp
# suricata-postgres       Up (healthy)        5432/tcp

# Test dashboard access
curl http://localhost:5000/api/status

# Test database connection
docker-compose exec postgres psql -U suricata -c "SELECT version();"
```

#### 6. Access Dashboard

Open browser:
```
http://localhost:5000
```

### Alternative: Standalone Dockerfile

Jika tidak mau pakai Docker Compose:

```bash
# Build image
cd ../../
docker build -f container/docker/Dockerfile -t suricata-dashboard:latest .

# Run with external database
docker run -d \
  --name suricata-dashboard \
  -p 5000:5000 \
  -e DB_HOST=your-postgres-host \
  -e DB_PASSWORD=your-password \
  -v /etc/suricata:/etc/suricata:ro \
  -v /var/log/suricata:/var/log/suricata:ro \
  suricata-dashboard:latest
```

---

## Configuration

### Environment Variables Reference

#### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Flask bind address |
| `FLASK_PORT` | `5000` | Flask port |
| `FLASK_DEBUG` | `False` | Debug mode (use False in production) |

#### Suricata Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_SURICATA_CONFIG` | `/etc/suricata` | Host path untuk Suricata config |
| `HOST_SURICATA_LOG` | `/var/log/suricata` | Host path untuk Suricata logs |
| `SURICATA_BINARY_PATH` | `suricata` | Binary name/path |
| `SURICATA_CONFIG_PATH` | `/etc/suricata/suricata.yaml` | Config file path |
| `SURICATA_RULES_DIR` | `/etc/suricata/rules` | Rules directory |
| `SURICATA_LOG_DIR` | `/var/log/suricata` | Logs directory |

#### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | `postgresql` | Database type (postgresql/mysql) |
| `DB_HOST` | `postgres` | Database hostname |
| `DB_PORT` | `5432` | Database port |
| `DB_USER` | `suricata` | Database username |
| `DB_PASSWORD` | `changeme` | **CHANGE THIS!** |
| `DB_NAME` | `suricata` | Database name |
| `DB_RETENTION_DAYS` | `30` | Alert retention period |

#### Monitoring Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAFFIC_AGGREGATION_INTERVAL` | `300` | Traffic aggregation (seconds) |
| `DB_STORE_TIME` | `60` | Database write interval (seconds) |
| `RRD_DIR` | `/var/lib/suricata/rrd` | RRD files location |

### Volume Configuration

#### Default Volumes

```yaml
volumes:
  # Database persistence
  postgres-data:
    driver: local

  # Application data
  dashboard-data:
    driver: local
  dashboard-logs:
    driver: local
  dashboard-rrd:
    driver: local
```

#### Custom Volume Paths

Untuk menggunakan specific host paths:

```yaml
services:
  dashboard:
    volumes:
      # Use host directory instead of named volume
      - /opt/dashboard/data:/opt/suricata_monitoring/data
      - /opt/dashboard/logs:/opt/suricata_monitoring/log
      - /opt/dashboard/rrd:/var/lib/suricata/rrd
```

### Network Configuration

#### Default Network

```yaml
networks:
  suricata-network:
    driver: bridge
```

#### Custom Network

Untuk advanced networking:

```yaml
networks:
  suricata-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

### SSL/TLS Configuration

Enable HTTPS:

1. Generate certificates:
```bash
mkdir -p certificates
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certificates/key.pem \
  -out certificates/cert.pem \
  -days 365
```

2. Update `.env`:
```ini
USE_HTTPS=True
SSL_CERT_PATH=binary/certificates/cert.pem
SSL_KEY_PATH=binary/certificates/key.pem
```

3. Mount certificates:
```yaml
services:
  dashboard:
    volumes:
      - ./certificates:/app/binary/certificates:ro
```

---

## Operations

### Daily Operations

#### Start/Stop Services

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart specific service
docker-compose restart dashboard

# Stop specific service
docker-compose stop dashboard
```

#### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f dashboard
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 dashboard

# With timestamps
docker-compose logs -f -t dashboard
```

#### Service Status

```bash
# Service list and status
docker-compose ps

# Detailed container info
docker inspect suricata-dashboard

# Resource usage
docker stats suricata-dashboard
```

### Database Operations

#### Backup Database

```bash
# Backup to file
docker-compose exec postgres pg_dump -U suricata suricata > backup_$(date +%Y%m%d).sql

# Compressed backup
docker-compose exec postgres pg_dump -U suricata suricata | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U suricata suricata < backup_20231201.sql

# From compressed
gunzip -c backup_20231201.sql.gz | docker-compose exec -T postgres psql -U suricata suricata
```

#### Database Maintenance

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U suricata

# In psql:
# Check database size
SELECT pg_size_pretty(pg_database_size('suricata'));

# Vacuum database
VACUUM ANALYZE;

# Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Application Updates

#### Update Application Code

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build dashboard

# Restart with new image
docker-compose up -d dashboard

# Verify update
docker-compose logs -f dashboard
```

#### Update Dependencies

```bash
# Update requirements.txt
# Edit requirements.txt with new versions

# Rebuild
docker-compose build --no-cache dashboard
docker-compose up -d dashboard
```

### Resource Management

#### Monitor Resources

```bash
# Real-time stats
docker stats

# Check disk usage
docker system df

# Volume usage
docker volume ls
du -sh /var/lib/docker/volumes/*
```

#### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (CAREFUL!)
docker volume prune

# Remove unused networks
docker network prune

# Complete cleanup (CAREFUL!)
docker system prune -a --volumes
```

---

## Troubleshooting

### Common Issues

#### 1. Dashboard Cannot Connect to Database

**Symptom:**
```
Cannot connect to database: Connection refused
```

**Solution:**
```bash
# Check database status
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify network
docker network inspect container_suricata-network

# Test connection from dashboard
docker-compose exec dashboard ping postgres
```

#### 2. Suricata Logs Not Visible

**Symptom:**
Dashboard shows no logs or alerts

**Diagnosis:**
```bash
# Check if eve.json exists on host
ls -la /var/log/suricata/eve.json

# Check mount inside container
docker-compose exec dashboard ls -la /var/log/suricata/

# Check permissions
docker-compose exec dashboard cat /var/log/suricata/eve.json
```

**Solution:**
```bash
# Fix permissions on host
sudo chmod o+r /var/log/suricata/eve.json
sudo chmod o+rx /var/log/suricata

# Or change Suricata log permissions
sudo usermod -aG suricata $(whoami)
```

#### 3. Port Already in Use

**Symptom:**
```
Error: Bind for 0.0.0.0:5000 failed: port is already allocated
```

**Solution:**
```bash
# Check what's using port
sudo netstat -tulpn | grep 5000

# Option 1: Kill process using port
sudo kill $(sudo lsof -t -i:5000)

# Option 2: Use different port in .env
echo "FLASK_PORT=5001" >> .env
docker-compose down
docker-compose up -d
```

#### 4. Container Keeps Restarting

**Diagnosis:**
```bash
# Check logs
docker-compose logs --tail=50 dashboard

# Check exit code
docker inspect suricata-dashboard | grep ExitCode

# Check health
docker inspect --format='{{.State.Health}}' suricata-dashboard
```

**Common causes:**
- Missing dependencies
- Database not ready
- Configuration errors
- Permission issues

#### 5. Database Migration Issues

**Symptom:**
```
Table 'alerts' doesn't exist
```

**Solution:**
```bash
# Check if tables exist
docker-compose exec postgres psql -U suricata -c "\dt"

# If no tables, restart to trigger migration
docker-compose restart dashboard

# Manual migration (if needed)
docker-compose exec dashboard python -c "
from binary.database import db_manager
db = db_manager.DatabaseManager()
db.initialize()
"
```

### Debug Mode

Enable debug untuk troubleshooting:

```ini
# .env
FLASK_DEBUG=True
```

```bash
# Restart with logs
docker-compose down
docker-compose up
```

### Health Checks

```bash
# Dashboard health
curl http://localhost:5000/api/status

# Database health
docker-compose exec postgres pg_isready -U suricata

# Container health status
docker inspect --format='{{.State.Health.Status}}' suricata-dashboard
docker inspect --format='{{.State.Health.Status}}' suricata-postgres
```

---

## Best Practices

### Security

1. **Change Default Passwords**
   ```ini
   DB_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Don't Expose Database Port**
   Keep `ports:` commented in postgres service

3. **Use HTTPS in Production**
   ```ini
   USE_HTTPS=True
   ```

4. **Regular Security Updates**
   ```bash
   # Update base images
   docker-compose pull
   docker-compose up -d
   ```

5. **Limit Container Resources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
       reservations:
         memory: 256M
   ```

### Performance

1. **Use Volume Drivers**
   For better I/O performance

2. **Adjust Aggregation Intervals**
   ```ini
   TRAFFIC_AGGREGATION_INTERVAL=600  # 10 minutes for high-traffic
   ```

3. **Database Tuning**
   ```yaml
   postgres:
     command:
       - postgres
       - -c
       - shared_buffers=256MB
       - -c
       - effective_cache_size=1GB
   ```

4. **Regular Database Maintenance**
   ```bash
   # Weekly vacuum
   docker-compose exec postgres psql -U suricata -c "VACUUM ANALYZE;"
   ```

### Reliability

1. **Automated Backups**
   ```bash
   # Cron job
   0 2 * * * cd /path/to/container/docker && docker-compose exec -T postgres pg_dump -U suricata suricata | gzip > /backups/dashboard_$(date +\%Y\%m\%d).sql.gz
   ```

2. **Health Monitoring**
   ```bash
   # Monitor script
   #!/bin/bash
   if ! docker inspect --format='{{.State.Health.Status}}' suricata-dashboard | grep -q healthy; then
     echo "Dashboard unhealthy, restarting..."
     docker-compose restart dashboard
   fi
   ```

3. **Log Rotation**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

### Maintenance

1. **Regular Updates**
   - Weekly: Check for security updates
   - Monthly: Update application code
   - Quarterly: Major version updates

2. **Monitoring**
   - Setup alerts for container health
   - Monitor disk usage
   - Track database size

3. **Documentation**
   - Document all configuration changes
   - Keep runbooks updated
   - Update this wiki with new findings

---

## Migration dari Non-Docker

### Backup Existing Setup

```bash
# Backup configuration
cp -r /etc/suricata /backup/suricata_config

# Backup database
pg_dump -U postgres suricata > /backup/suricata_db.sql

# Backup RRD files (if exists)
cp -r /var/lib/suricata/rrd /backup/rrd_data
```

### Import to Docker

```bash
# Start containers
cd container/docker
docker-compose up -d

# Import database
cat /backup/suricata_db.sql | docker-compose exec -T postgres psql -U suricata suricata

# Import RRD data
docker cp /backup/rrd_data/. suricata-dashboard:/var/lib/suricata/rrd/

# Verify
docker-compose exec dashboard ls -la /var/lib/suricata/rrd/
```

---

## FAQ

### Q: Apakah Suricata juga berjalan di container?
**A:** Tidak. Suricata tetap berjalan di host. Dashboard hanya membaca logs dan config via mounted volumes.

### Q: Bagaimana cara scale dashboard?
**A:** Gunakan load balancer di depan multiple dashboard containers. Database shared.

### Q: Bisa pakai Docker di Windows?
**A:** Ya, gunakan Docker Desktop. Path mounting perlu disesuaikan:
```yaml
volumes:
  - C:/Program Files/Suricata:/etc/suricata:ro
```

### Q: Minimum hardware requirements?
**A:**
- CPU: 2 cores
- RAM: 2GB (4GB recommended)
- Disk: 20GB (depends on retention)

### Q: Production ready?
**A:** Ya, dengan catatan:
- Enable HTTPS
- Use strong passwords
- Set up monitoring
- Regular backups
- Resource limits

### Q: Bagaimana cara menggunakan MySQL instead of PostgreSQL?
**A:** Uncomment MySQL service di `docker-compose.yml` dan ubah:
```ini
DB_TYPE=mysql
DB_HOST=mysql
DB_PORT=3306
```

---

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Suricata Documentation](https://suricata.readthedocs.io/)
- [Main Containerization Wiki](containerization.md)
- [Kubernetes Deployment Wiki](containerization-kubernetes.md)

## Changelog

- **2024-12**: Initial Docker deployment documentation
- Added PostgreSQL and MySQL support
- Implemented health checks
- Added backup procedures
- Split from main containerization wiki

---

**Last Updated:** 2024-12
**Maintainer:** Suricata Dashboard Team

**See Also:**
- [Kubernetes Deployment](containerization-kubernetes.md)
- [Main Containerization Overview](containerization.md)
