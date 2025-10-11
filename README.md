# Suricata Web Dashboard

Python Flask-based dashboard to control and monitor Suricata IDS/IPS. Includes process control, rules and config editors, log viewer, traffic monitoring, RRD graphs, and DB-backed statistics.

## Features

- Real-time status (PID, uptime) and service controls
- Rules and configuration management
- Live log viewer with filters
- Traffic monitoring (TCP/UDP/ICMP/alerts) and RRD graphs
- Database storage for alerts/stats (PostgreSQL or MySQL)
- Cross-platform (Windows and Linux)

## Requirements

- Python 3.8+
- Suricata installed and runnable from your host
- Database: PostgreSQL or MySQL (SQLAlchemy is required)
- Optional: RRDtool system libs for graphing (Linux)

Python packages are pinned in `requirements.txt`.

## Quick Start

1) Install dependencies

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) (Linux, optional) Enable RRD graphs

```bash
chmod +x install_rrdtool.sh
./install_rrdtool.sh
```

3) Configure environment (recommended via `.env`)

Create a `.env` file in the repository root. Defaults are sensible per-OS; override what you need.

```ini
# Dashboard
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
DASHBOARD_NAME=Suricata Dashboard

# Suricata paths (Windows defaults auto-detected; Linux shown below)
SURICATA_BINARY_PATH=suricata
SURICATA_CONFIG_PATH=/etc/suricata/suricata.yaml
SURICATA_RULES_DIR=/etc/suricata/rules
SURICATA_LOG_DIR=/var/log/suricata

# RRD (optional; used if rrdtool is installed)
RRD_DIR=/var/lib/suricata/rrd

# Database (REQUIRED)
# Choose one: postgresql or mysql
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=changeme
DB_NAME=suricata

# Optional behavior
DB_RETENTION_DAYS=30
AUTO_RESTART_ENABLED=False
USE_HTTPS=False
SSL_CERT_PATH=binary/certificates/cert.pem
SSL_KEY_PATH=binary/certificates/key.pem
```

Notes:
- Windows paths are inferred automatically; you can still override via `.env`.
- On first run, tables are created in the configured database.

4) Run

```bash
python run.py
```

Open `http://localhost:5000` (or your configured host/port).

## API Endpoints

Process control
- `GET /api/status` – Suricata status
- `POST /api/start` – Start Suricata
- `POST /api/stop` – Stop Suricata
- `POST /api/restart` – Restart Suricata
- `POST /api/reload-rules` – Reload rules

Logs & configuration
- `GET /api/logs` – Recent logs
- `GET /api/rules` – Rules list
- `GET /api/config` – Current config
- `POST /api/config` – Save config

Monitoring & traffic
- `GET /api/monitor/data` – Aggregated traffic and alerts
- `GET /api/monitor/alerts` – Recent alerts from `eve.json`
- `GET /api/monitor/events` – All events from `eve.json`

Database
- `GET /api/database/check` – Connection status
- `GET /api/database/info` – DB information
- `GET /api/database/alerts` – Alerts from DB
- `GET /api/database/traffic/latest` – Latest traffic stats
- `GET /api/database/traffic/recent` – Recent traffic stats

RRD graphs (optional)
- `GET /api/rrd/graph` – Render graph, params: `metric`, `timespan`
  - Metrics: `tcp`, `udp`, `icmp`, `alerts`
  - Timespans: `5m`, `15m`, `30m`, `1h`, `6h`, `24h`, `7d`, `30d`
- `GET /api/rrd/update` – Update RRD metrics from DB

## Configuration Details

- Configuration is managed via environment variables loaded in `config.py`.
- `.env` is supported (loaded via `python-dotenv`).
- Per-OS defaults are applied when variables are not set.

Key variables
- `SURICATA_*` – Paths to Suricata binary, config, rules, and logs
- `DB_*` and `DB_TYPE` – Database connectivity and retention
- `RRD_DIR` – Folder for RRD files when RRDtool is installed
- `FLASK_*` – Host, port, and debug mode
- `USE_HTTPS`, `SSL_CERT_PATH`, `SSL_KEY_PATH` – Enable TLS for the dashboard

## Troubleshooting

- RRDtool not installed: graphs are disabled; install using `install_rrdtool.sh` on Linux.
- Database connection errors: verify `DB_*` values and that the DB is reachable; tables are created automatically on first successful connection.
- Windows paths: escape backslashes in `.env` or use forward slashes.

## Security Notes

- Use only in trusted environments; add authentication for production.
- Run with appropriate privileges and secure file permissions for Suricata paths.

## License

This project is for educational and defensive security purposes only.
