"""
Suricata Dashboard API Module
"""

# Import main routes handler
from binary.api.routes import APIRoutes

# Import individual API modules
from binary.api.alerts import AlertsAPI
from binary.api.config import ConfigAPI
from binary.api.database import DatabaseAPI
from binary.api.debug import DebugAPI
from binary.api.integrations import IntegrationsAPI
from binary.api.logging import LoggingAPI
from binary.api.monitor import MonitorAPI
from binary.api.rules import RulesAPI
from binary.api.status_controll import StatusControlAPI
from binary.api.suricata import SuricataConfigAPI

__all__ = [
    'APIRoutes',
    'AlertsAPI',
    'ConfigAPI',
    'DatabaseAPI',
    'DebugAPI',
    'IntegrationsAPI',
    'LoggingAPI',
    'MonitorAPI',
    'RulesAPI',
    'StatusControlAPI',
    'SuricataConfigAPI',
]
