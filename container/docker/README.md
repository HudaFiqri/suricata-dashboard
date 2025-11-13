# Suricata Dashboard - Docker Deployment

Docker containerization untuk Suricata Dashboard dengan PostgreSQL/MySQL database.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Suricata sudah terinstall di host machine
- Port 5000 tersedia (atau sesuaikan di `.env`)

## 🚀 Quick Start

### 1. Setup Environment

Copy file environment example dan sesuaikan konfigurasi:

```bash
cd container
cp .env.example .env
nano .env  # Edit sesuai kebutuhan
```

**Konfigurasi penting yang perlu disesuaikan:**

```ini
# Path ke instalasi Suricata di host
HOST_SURICATA_CONFIG=/etc/suricata
HOST_SURICATA_LOG=/var/log/suricata

# Database credentials
DB_PASSWORD=your_secure_password
```

### 2. Build dan Run

```bash
# Build dan start semua services
docker-compose up -d

# Atau build terpisah
docker-compose build
docker-compose up -d
```

### 3. Akses Dashboard

Buka browser dan akses:
```
http://localhost:5000
```

## 🏗️ Arsitektur Container

```
┌─────────────────────────────────────┐
│   Suricata Dashboard Container      │
│   - Flask Application               │
│   - Python 3.11                     │
│   - Port: 5000                      │
└─────────────┬───────────────────────┘
              │
              ├── Volumes (Data Persistence)
              │   ├── /opt/suricata_monitoring/data
              │   ├── /opt/suricata_monitoring/log
              │   └── /var/lib/suricata/rrd
              │
              ├── Mounts (Host Suricata)
              │   ├── /etc/suricata (read-only)
              │   └── /var/log/suricata (read-only)
              │
              └── Network Connection
                  │
    ┌─────────────┴──────────────┐
    │   PostgreSQL Container     │
    │   - PostgreSQL 15          │
    │   - Port: 5432 (internal)  │
    └────────────────────────────┘
```

## 📦 Components

### Services

1. **dashboard** - Main application
   - Image: Custom built from Dockerfile
   - Port: 5000 (configurable)
   - User: non-root (uid 1000)
   - Health check: Setiap 30 detik

2. **postgres** - Database server
   - Image: postgres:15-alpine
   - Port: 5432 (internal only)
   - Data persistence via volume

### Volumes

- `postgres-data` - Database persistence
- `dashboard-data` - Application data
- `dashboard-logs` - Application logs
- `dashboard-rrd` - RRD monitoring data

## ⚙️ Konfigurasi

### Environment Variables

Lihat [.env.example](.env.example) untuk konfigurasi lengkap.

**Utama:**
```ini
# Flask
FLASK_PORT=5000
FLASK_DEBUG=False

# Database
DB_TYPE=postgresql
DB_HOST=postgres
DB_PASSWORD=changeme

# Suricata Paths
HOST_SURICATA_CONFIG=/etc/suricata
HOST_SURICATA_LOG=/var/log/suricata
```

### Database Options

#### PostgreSQL (Default)
```ini
DB_TYPE=postgresql
DB_HOST=postgres
DB_PORT=5432
```

#### MySQL/MariaDB
Uncomment MySQL service di `docker-compose.yml` dan set:
```ini
DB_TYPE=mysql
DB_HOST=mysql
DB_PORT=3306
```

## 🔧 Docker Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart dashboard

# View logs
docker-compose logs -f dashboard
docker-compose logs -f postgres

# View status
docker-compose ps
```

### Container Management

```bash
# Access dashboard container
docker exec -it suricata-dashboard bash

# Access database
docker exec -it suricata-postgres psql -U suricata

# Check container health
docker inspect --format='{{.State.Health.Status}}' suricata-dashboard
```

### Data Management

```bash
# Backup database
docker exec suricata-postgres pg_dump -U suricata suricata > backup.sql

# Restore database
docker exec -i suricata-postgres psql -U suricata suricata < backup.sql

# Clean volumes (WARNING: Deletes all data!)
docker-compose down -v
```

## 🔍 Troubleshooting

### Dashboard tidak bisa connect ke database

```bash
# Cek health status
docker-compose ps

# Cek logs database
docker-compose logs postgres

# Test koneksi manual
docker exec -it suricata-dashboard python -c "from config import Config; print(Config.DB_HOST)"
```

### Suricata logs tidak muncul

1. Pastikan path mounting benar:
```bash
# Cek di host
ls -la /var/log/suricata/eve.json

# Cek di container
docker exec suricata-dashboard ls -la /var/log/suricata/
```

2. Periksa permissions:
```bash
# Logs harus readable oleh user id 1000
sudo chmod -R o+r /var/log/suricata/
```

### Port sudah digunakan

Edit `.env` dan ubah `FLASK_PORT`:
```ini
FLASK_PORT=5001
```

Kemudian restart:
```bash
docker-compose down
docker-compose up -d
```

### RRD graphs tidak muncul

RRDtool sudah terinstall di container. Pastikan:
```bash
# Cek RRD directory
docker exec suricata-dashboard ls -la /var/lib/suricata/rrd/

# Cek permission
docker exec suricata-dashboard rrdtool info /var/lib/suricata/rrd/tcp.rrd
```

## 🛡️ Security Best Practices

1. **Ubah default password**
   ```ini
   DB_PASSWORD=generate_strong_password_here
   ```

2. **Jangan expose database port** (comment out di docker-compose.yml)

3. **Gunakan HTTPS untuk production**
   ```ini
   USE_HTTPS=True
   ```
   Mount certificates:
   ```yaml
   volumes:
     - ./certificates:/app/binary/certificates:ro
   ```

4. **Limit resource usage**
   Tambahkan di docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```

5. **Gunakan non-root user** (sudah default di Dockerfile)

## 📊 Monitoring

### Health Checks

Dashboard memiliki built-in health check:
```bash
curl http://localhost:5000/api/status
```

### Prometheus Integration (Optional)

Tambahkan exporter jika diperlukan:
```yaml
# docker-compose.yml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🔄 Updates

### Update aplikasi

```bash
# Pull latest code
git pull

# Rebuild dan restart
docker-compose build dashboard
docker-compose up -d dashboard
```

### Update database

```bash
# Backup dulu
docker-compose exec postgres pg_dump -U suricata suricata > backup.sql

# Update
docker-compose pull postgres
docker-compose up -d postgres
```

## 🧹 Maintenance

### Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (WARNING!)
docker-compose down -v

# Clean unused images
docker image prune -a
```

### Database Maintenance

```bash
# Vacuum database
docker exec suricata-postgres psql -U suricata -c "VACUUM ANALYZE;"

# Check database size
docker exec suricata-postgres psql -U suricata -c "SELECT pg_size_pretty(pg_database_size('suricata'));"
```

## 📚 Resources

- [Dockerfile](Dockerfile) - Image configuration
- [docker-compose.yml](docker-compose.yml) - Service orchestration
- [.env.example](.env.example) - Environment variables
- [Main README](../README.md) - Application documentation

## 🆘 Support

Jika mengalami masalah:

1. Cek logs: `docker-compose logs -f`
2. Cek health: `docker-compose ps`
3. Buat issue di GitHub repository
4. Update wiki dengan solusi yang ditemukan

## 📝 License

Educational and defensive security purposes only.
