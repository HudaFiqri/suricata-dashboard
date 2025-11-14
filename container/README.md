# Docker Deployment

Deploy Suricata Multi-Agent Dashboard menggunakan Docker Compose.

## Quick Start

```bash
# Dari root directory
cd container
docker-compose up -d
```

## Services

Docker Compose akan deploy 3 services:

1. **PostgreSQL** - Database untuk structured data (agents, users, configs)
2. **MongoDB** - Database untuk time-series events & logs
3. **Dashboard** - Flask application dengan WebSocket

Optional:
4. **Nginx** - Reverse proxy (enable dengan `--profile production`)

## Setup

### 1. Configure Environment

```bash
# Copy example
cp ../.env.example ../.env

# Edit configuration
nano ../.env
```

### 2. Start Services

```bash
cd container
docker-compose up -d
```

### 3. Check Status

```bash
docker-compose ps
docker-compose logs -f dashboard
```

### 4. Create Admin User

```bash
docker-compose exec dashboard python binary/tools/create_user.py admin password admin
```

### 5. Access Dashboard

- Web UI: http://localhost:5000
- API: http://localhost:5000/api/v1/
- Health: http://localhost:5000/api/v1/health

## Management Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Scale dashboard
docker-compose up -d --scale dashboard=3
```

## Database Access

### PostgreSQL

```bash
# Connect to PostgreSQL
docker-compose exec postgresql psql -U suricata -d suricata_dashboard

# Backup
docker-compose exec postgresql pg_dump -U suricata suricata_dashboard > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgresql psql -U suricata suricata_dashboard
```

### MongoDB

```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh suricata

# Backup
docker-compose exec mongodb mongodump --db suricata --out /tmp/backup
docker cp suricata-mongodb:/tmp/backup ./mongodb-backup

# Restore
docker cp ./mongodb-backup suricata-mongodb:/tmp/backup
docker-compose exec mongodb mongorestore --db suricata /tmp/backup/suricata
```

## Production Deployment

### Enable Nginx Reverse Proxy

```bash
# Create nginx config
mkdir -p ../nginx
# Copy your nginx.conf here

# Start with nginx
docker-compose --profile production up -d
```

### SSL/TLS

```bash
# Place certificates
mkdir -p ../nginx/ssl
cp your-cert.crt ../nginx/ssl/
cp your-key.key ../nginx/ssl/

# Update nginx config to use SSL
# Restart nginx
docker-compose restart nginx
```

### Environment Variables

Edit `.env` file:

```bash
# Security
SECRET_KEY=your-random-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
POSTGRES_PASSWORD=secure-password

# Scaling
EVENTS_RETENTION_DAYS=90
LOGS_RETENTION_DAYS=30
```

## Troubleshooting

### Dashboard won't start

```bash
# Check logs
docker-compose logs dashboard

# Check database connectivity
docker-compose exec dashboard ping postgresql
docker-compose exec dashboard ping mongodb
```

### Database connection errors

```bash
# Wait for databases to be healthy
docker-compose ps

# Check health
docker-compose exec postgresql pg_isready -U suricata
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Port already in use

```bash
# Change ports in docker-compose.yml
ports:
  - "8080:5000"  # Use port 8080 instead
```

## Volumes

Persistent data is stored in Docker volumes:

- `postgres_data` - PostgreSQL database
- `mongo_data` - MongoDB database
- `mongo_config` - MongoDB config

To backup volumes:

```bash
docker run --rm -v container_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .
```

## Network

All services run in `suricata-network` bridge network.

Internal hostnames:
- `postgresql` - PostgreSQL server
- `mongodb` - MongoDB server
- `dashboard` - Dashboard application

## Health Checks

All services have health checks configured:

```bash
# Check health status
docker-compose ps

# Force health check
docker inspect container_suricata-postgres --format='{{.State.Health.Status}}'
```

## Useful Commands

```bash
# Shell access
docker-compose exec dashboard bash
docker-compose exec postgresql sh
docker-compose exec mongodb sh

# View resource usage
docker stats

# Clean up
docker-compose down
docker system prune -a
```

---

**For Kubernetes deployment, see: `../k8s/README.md`**
