# Suricata Dashboard Application Core

Core application engine and background tasks.

## Structure

```
binary/app/
├── __init__.py           # Module exports
├── engine.py             # Core app initialization (103 lines)
├── background_tasks.py   # Background daemon threads (241 lines)
└── web_routes.py         # HTML page routes (51 lines)
```

## Components

### 1. AppEngine (`engine.py`)
Core application initialization and setup.

**Responsibilities:**
- Initialize application directories
- Setup Suricata controller
- Setup RRD manager
- Setup database manager
- Initialize API modules
- Register API routes

**Usage:**
```python
from binary.app import AppEngine

engine = AppEngine(Config)
engine.register_routes(app)
```

### 2. BackgroundTasks (`background_tasks.py`)
Manages all background daemon threads.

**Background Tasks:**
- **RRD Metrics Update** - Every 60 seconds
- **Alert Sync** - eve.json → Database (Every 5 seconds)
- **Stats Sync** - stats.log → Database (Every 10 seconds)
- **Database Retention** - Cleanup old records (Every 1 hour)
- **Auto-Restart Monitor** - Restart crashed Suricata (Configurable interval)

**Usage:**
```python
from binary.app import BackgroundTasks

tasks = BackgroundTasks(engine, Config)
tasks.start_all()
```

### 3. WebRoutes (`web_routes.py`)
HTML page route registration.

**Routes:**
- `/` - Home page
- `/logs` - Logs viewer
- `/rules` - Rules management
- `/config` - Configuration editor
- `/services` - Services status
- `/monitor` - Traffic monitoring

**Usage:**
```python
from binary.app import WebRoutes

web_routes = WebRoutes(app, controller)
```

## Complete Integration

**Before (720 lines in app.py):**
```python
# Massive app.py with everything mixed together
```

**After (35 lines in app.py):**
```python
from flask import Flask
from config import Config
from binary.app import AppEngine, BackgroundTasks, WebRoutes

app = Flask(__name__)
engine = AppEngine(Config)
web_routes = WebRoutes(app, engine.controller)
api_routes = engine.register_routes(app)
background_tasks = BackgroundTasks(engine, Config)
background_tasks.start_all()

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG,
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT)
```

## Benefits

✅ **Ultra Clean**: app.py only 35 lines (95% reduction)
✅ **TypeScript-like**: Modular structure similar to TS/NestJS
✅ **Separation of Concerns**: Engine, Tasks, Routes separated
✅ **Easy Testing**: Each module testable independently
✅ **Maintainable**: Clear responsibility for each component
✅ **Scalable**: Easy to add new features
