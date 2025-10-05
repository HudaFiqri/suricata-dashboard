# Suricata Dashboard API

Modular API structure for Suricata Dashboard.

## Structure

```
binary/api/
├── __init__.py          # Module exports
├── routes.py            # Centralized route registration
├── monitor_api.py       # Traffic monitoring & statistics
├── alerts_api.py        # Event processing from eve.json
└── database_api.py      # Database operations
```

## Components

### 1. MonitorAPI (`monitor_api.py`)
Handles traffic monitoring and statistics from eve.json.

**Methods:**
- `get_monitor_data(timespan)` - Get TCP/UDP traffic and alerts count
- `get_debug_info()` - Debug info about eve.json file

**Endpoints:**
- `GET /api/monitor/data?timespan=1h`
- `GET /api/debug/eve`

### 2. AlertsAPI (`alerts_api.py`)
Processes and retrieves all events from eve.json.

**Methods:**
- `get_all_events(limit, category, protocol)` - Get all events with filters

**Endpoints:**
- `GET /api/database/alerts?limit=100&category=HTTP&protocol=TCP`

**Supported Event Types:**
- Alert, HTTP, DNS, TLS, SSH, Flow, Stats, FileInfo

### 3. DatabaseAPI (`database_api.py`)
Handles database connection and operations.

**Methods:**
- `check_connection()` - Check database connection status
- `get_info()` - Get database information
- `get_stats()` - Get latest statistics

**Endpoints:**
- `GET /api/database/check`
- `GET /api/database/info`
- `GET /api/database/stats`

### 4. APIRoutes (`routes.py`)
Centralized route registration for all API endpoints.

**Categories:**
- Status & Control: `/api/status`, `/api/start`, `/api/stop`, `/api/restart`
- Logs: `/api/logs`
- Rules: `/api/rules`
- Config: `/api/config`
- Monitor: `/api/monitor/data`, `/api/monitor/graph/<metric>/<timespan>`
- Database: `/api/database/*`
- Debug: `/api/debug/eve`

## Usage

```python
from binary.api import MonitorAPI, AlertsAPI, DatabaseAPI, APIRoutes

# Initialize API modules
monitor_api = MonitorAPI(Config)
alerts_api = AlertsAPI(Config)
database_api = DatabaseAPI(db_manager)

# Register all routes
api_routes = APIRoutes(app, controller, rrd_manager,
                       monitor_api, alerts_api, database_api)
```

## Benefits

✅ **Modular**: Each API module has a single responsibility
✅ **Maintainable**: Easy to find and modify specific functionality
✅ **Testable**: Each module can be tested independently
✅ **Scalable**: Easy to add new endpoints or features
✅ **Clean**: app.py reduced from 720 lines to 333 lines (54% reduction)
