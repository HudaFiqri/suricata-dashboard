from typing import Any, Dict

from .utils import coerce_bool

NAME = 'discord'

DEFAULTS: Dict[str, Any] = {
    'enabled': False,
    'webhook_url': '',
    'message_template': ''
}


def sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = payload or {}
    sanitized: Dict[str, Any] = {
        'enabled': coerce_bool(payload.get('enabled')),
        'webhook_url': str(payload.get('webhook_url') or '').strip(),
        'message_template': str(payload.get('message_template') or '').strip()
    }
    return sanitized
