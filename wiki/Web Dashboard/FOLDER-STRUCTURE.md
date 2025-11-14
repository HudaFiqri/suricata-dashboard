# Folder Structure

Struktur folder Suricata Multi-Agent Dashboard setelah reorganisasi.

## 📁 Root Directory

```
suricata-dashboard/
├── binary/                     # All application code
│   ├── dashboard/              # Dashboard application (NEW)
│   │   ├── api/                # REST API endpoints (11 modules)
│   │   ├── websocket/          # WebSocket server (3 modules)
│   │   ├── web/                # Web UI (templates & routes)
│   │   ├── processing/         # Event processing pipeline
│   │   ├── database.py         # Database connections
│   │   ├── models.py           # SQLAlchemy models
│   │   └── __init__.py         # App factory
│   │
│   ├── tools/                  # Tools & utilities (NEW)
│   │   ├── agent/              # Python agent for remote servers
│   │   │   ├── core/           # Core agent modules
│   │   │   ├── transport/      # WebSocket & HTTP clients
│   │   │   ├── config.py       # Configuration loader
│   │   │   └── agent.py        # Main agent daemon
│   │   │
│   │   ├── migrations/         # Database migrations
│   │   │   ├── postgresql/     # PostgreSQL schemas
│   │   │   ├── mongodb/        # MongoDB collections & indexes
│   │   │   └── migrate.py      # Migration runner
│   │   │
│   │   └── create_user.py      # User creation script
│   │
│   ├── app/                    # OLD: Legacy local monitoring
│   ├── api/                    # OLD: Legacy API
│   ├── web/                    # OLD: Legacy web UI
│   ├── static_old/             # OLD: Legacy static files
│   └── templates_old/          # OLD: Legacy templates
│
├── container/                  # Container configurations (OLD)
├── k8s/                        # Kubernetes manifests (NEW)
├── wiki/                       # Documentation & planning
│
├── app.py                      # OLD: Legacy entry point
├── run.py                      # NEW: Development server runner
├── wsgi.py                     # NEW: Production WSGI entry
├── config.py                   # OLD: Legacy config
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
│
└── Documentation files:
    ├── README.md               # Main documentation
    ├── README-REMOTE.md        # Remote monitoring guide
    ├── QUICKSTART.md           # 5-minute setup guide
    ├── FOLDER-STRUCTURE.md     # This file
    ├── SUMMARY.md              # Implementation summary
    ├── FINAL-STATUS.md         # Final project status
    └── IMPLEMENTATION-STATUS.md # Detailed progress
```

## 📂 Detailed Breakdown

### `binary/dashboard/` - Dashboard Application (NEW)

**Main application untuk multi-agent dashboard.**

#### `api/` - REST API (11 modules)
- `__init__.py` - API blueprint
- `auth.py` - JWT authentication
- `agents.py` - **Multi-agent management**
- `events.py` - Event ingestion
- `logs.py` - Log ingestion
- `configs.py` - Configuration management
- `commands.py` - Command execution
- `stats.py` - Statistics
- `query.py` - MongoDB queries
- `installer.py` - **Agent installer generator dengan embedded code**
- `health.py` - Health checks

#### `websocket/` - WebSocket Server (3 modules)
- `__init__.py` - Socket.IO initialization
- `agent_handlers.py` - Agent connection handlers
- `ui_handlers.py` - UI connection handlers
- `sessions.py` - Session management

#### `web/` - Web UI
- `__init__.py` - Web blueprint
- `routes.py` - Route definitions
- `templates/` - HTML templates
  - `base.html` - Base template dengan WebSocket
  - `dashboard.html` - **Multi-agent dashboard**
  - `agents.html` - **Agent management page**
  - `login.html` - Login page

#### `processing/` - Event Processing Pipeline (NEW)
- `__init__.py` - Processing module
- `enrichment.py` - Event enrichment (GeoIP, threat intel)
- `aggregator.py` - Event aggregation & analytics
- `alerts.py` - Alert engine dengan rules

#### Core Files
- `database.py` - Database connection manager (PostgreSQL + MongoDB)
- `models.py` - SQLAlchemy models (Agent, User, Config, Command, etc.)
- `__init__.py` - Flask app factory dengan auto-initialization

### `binary/tools/` - Tools & Utilities (NEW)

**Command-line tools dan agent.**

#### `agent/` - Python Agent
Complete agent untuk run di remote Suricata servers.

- **Core Modules** (`core/`)
  - `tailer.py` - File monitoring dengan inotify
  - `parser.py` - Event & log parsing
  - `buffer.py` - SQLite offline buffer
  - `auth.py` - Token encryption
  - `health.py` - System health metrics

- **Transport** (`transport/`)
  - `websocket_client.py` - WebSocket streaming
  - `http_client.py` - HTTP fallback

- **Main Files**
  - `config.py` - Configuration loader
  - `agent.py` - Main agent daemon
  - `requirements.txt` - Agent dependencies

#### `migrations/` - Database Migrations
- `migrate.py` - Migration runner script
- `postgresql/001_initial_schema.sql` - PostgreSQL schema
- `mongodb/001_create_collections.js` - MongoDB collections
- `mongodb/002_create_indexes.js` - MongoDB indexes

#### `create_user.py` - User Creation Script
CLI tool untuk create admin/user accounts.

### `k8s/` - Kubernetes Deployment (NEW)

Production-ready Kubernetes manifests.

- `namespace.yaml` - Kubernetes namespace
- `postgresql.yaml` - PostgreSQL StatefulSet + PVC
- `mongodb.yaml` - MongoDB StatefulSet + PVC
- `dashboard.yaml` - Dashboard Deployment + Service + Ingress
- `README.md` - Deployment guide

### `wiki/` - Documentation

Planning documents dan specifications.

- `00-refactor-overview.md` - Architecture overview
- `01-database-schema.md` - Database design
- `02-api-specification.md` - Complete API docs
- `03-agent-protocol.md` - Agent communication protocol
- `04-file-structure.md` - File organization
- `05-agent-installer.md` - Installer design
- `06-migration-guide.md` - Migration from local to remote
- `07-websocket-real-time.md` - WebSocket protocol details
- `08-ui-mockups.md` - UI/UX design

### Legacy Files (OLD - For Reference)

**Kode lama untuk local monitoring** (tidak dipakai di remote multi-agent mode):

- `binary/app/` - Legacy application logic
- `binary/api/` - Legacy API
- `binary/web/` - Legacy web interface
- `binary/static_old/` - Old static assets
- `binary/templates_old/` - Old HTML templates
- `app.py` - Old entry point
- `config.py` - Old configuration
- `container/` - Old container configs

## 🎯 Import Paths

### OLD (Before Reorganization)
```python
from apps.api import api
from apps.database import get_pg_session
from apps.models import Agent
```

### NEW (After Reorganization)
```python
from binary.dashboard.api import api
from binary.dashboard.database import get_pg_session
from binary.dashboard.models import Agent
```

## 🚀 Entry Points

### Development
```bash
python run.py
```
Imports: `from binary.dashboard import create_app`

### Production (WSGI)
```bash
gunicorn wsgi:app
```
File: `wsgi.py` imports `from binary.dashboard import create_app`

### Docker
```bash
docker-compose up
```
Uses: `Dockerfile` → runs `wsgi.py`

### Kubernetes
```bash
kubectl apply -f k8s/
```
Deploys: Docker image built from `Dockerfile`

## 📊 File Counts

```
NEW Architecture:
├── binary/dashboard/     38 Python files (API, WebSocket, Web, Processing)
├── binary/tools/agent/   9 Python files (Agent daemon)
├── binary/tools/         4 files (Migrations, utilities)
├── k8s/                  5 YAML files (Kubernetes)
└── Documentation:        15 Markdown files

Total NEW files: 70+
Lines of Code: 10,000+
```

## 🔄 Why This Structure?

### Benefits:
1. **Clean Separation** - All new code di `binary/dashboard/` dan `binary/tools/`
2. **Legacy Preserved** - Kode lama tetap di `binary/app/`, `binary/api/`, `binary/web/`
3. **Consistent** - Semua di folder `binary/` seperti yang user mau
4. **Modular** - Dashboard, Agent, Tools terpisah jelas
5. **Scalable** - Mudah ditambah module baru

### Folder Purpose:
- **`binary/dashboard/`** → Dashboard application (API, WebSocket, Web UI, Processing)
- **`binary/tools/`** → CLI tools, agent, migrations
- **`k8s/`** → Kubernetes deployment
- **`wiki/`** → Documentation
- **Root files** → Entry points (run.py, wsgi.py, docker-compose.yml)

## 📝 Quick Reference

**Jalankan Dashboard:**
```bash
python run.py
```

**Create User:**
```bash
python binary/tools/create_user.py admin password admin
```

**Run Migrations:**
```bash
cd binary/tools/migrations && python migrate.py up
```

**Deploy Docker:**
```bash
docker-compose up -d
```

**Deploy Kubernetes:**
```bash
kubectl apply -f k8s/
```

---

**Structure Status: REORGANIZED & CLEAN** ✅

Semua code baru sudah di `binary/` dengan struktur yang rapi dan modular.
