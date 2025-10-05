# Suricata Web Dashboard

A Python Flask-based web dashboard for controlling and monitoring Suricata IDS/IPS.

## Features

- **Real-time Status Monitoring**: View Suricata process status, PID, and uptime
- **Process Control**: Start, stop, restart Suricata with web interface
- **Rule Management**: View, edit, and manage Suricata rules files
- **Log Viewing**: Real-time log monitoring with filtering capabilities
- **Configuration Management**: Edit Suricata configuration through web interface
- **Cross-platform**: Works on Windows and Linux

## Installation

1. Install Python 3.7+ and pip
2. Clone or download this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit the paths in `app.py` to match your Suricata installation:

```python
controller = SuricataController(
    binary_path="suricata.exe",  # Path to Suricata executable
    config_path="C:\\Program Files\\Suricata\\suricata.yaml",  # Config file path
    rules_directory="C:\\Program Files\\Suricata\\rules",  # Rules directory
    log_directory="C:\\Program Files\\Suricata\\log"  # Log directory
)
```

## Usage

1. Start the dashboard:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to: `http://localhost:5000`

3. Use the web interface to:
   - Monitor Suricata status
   - Start/stop/restart Suricata
   - View and manage rules
   - Monitor logs in real-time
   - Edit configuration files

## API Endpoints

### Process Control
- `GET /api/status` - Get Suricata status
- `POST /api/start` - Start Suricata
- `POST /api/stop` - Stop Suricata
- `POST /api/restart` - Restart Suricata
- `POST /api/reload-rules` - Reload rules

### Logs & Configuration
- `GET /api/logs` - Get recent logs
- `GET /api/rules` - Get rules files
- `GET /api/config` - Get configuration
- `POST /api/config` - Save configuration

### Monitoring & Traffic
- `GET /api/monitor/data` - Get traffic monitoring data (TCP, UDP, ICMP, Alerts)
- `GET /api/monitor/alerts` - Get recent alerts from eve.json
- `GET /api/monitor/events` - Get all events from eve.json

### Database
- `GET /api/database/check` - Check database connection status
- `GET /api/database/info` - Get database information
- `GET /api/database/alerts` - Get alerts from database
- `GET /api/database/traffic/latest` - Get latest traffic statistics
- `GET /api/database/traffic/recent` - Get recent traffic statistics

### RRD Graphs
- `GET /api/rrd/graph` - Generate RRD graph (params: metric, timespan)
  - Metrics: `tcp`, `udp`, `icmp`, `alerts`
  - Timespans: `5m`, `15m`, `30m`, `1h`, `6h`, `24h`, `7d`, `30d`
- `GET /api/rrd/update` - Update RRD metrics from database

## Security Notes

- This dashboard should only be used in trusted environments
- Consider adding authentication for production use
- Ensure proper file permissions for Suricata directories
- Run with appropriate user privileges

## Requirements

- Python 3.7+
- Flask 2.3.3+
- psutil 5.9.5+
- PyYAML 6.0.1+
- Suricata IDS/IPS installed

## License

This project is for educational and defensive security purposes only.
