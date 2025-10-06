from typing import Any, Dict

from .utils import coerce_bool

NAME = 'discord'

DEFAULTS: Dict[str, Any] = {
    'enabled': False,
    'webhook_url': '',
    'message_template': '',
    'rate_limit_messages': 30,  # Max messages per interval
    'rate_limit_interval': 60   # Interval in seconds (default: 30 messages per 60 seconds)
}


def sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = payload or {}
    sanitized: Dict[str, Any] = {
        'enabled': coerce_bool(payload.get('enabled')),
        'webhook_url': str(payload.get('webhook_url') or '').strip(),
        'message_template': str(payload.get('message_template') or '').strip(),
        'rate_limit_messages': int(payload.get('rate_limit_messages', 30)),
        'rate_limit_interval': int(payload.get('rate_limit_interval', 60))
    }
    return sanitized
