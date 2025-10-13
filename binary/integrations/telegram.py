from typing import Any, Dict

from .utils import coerce_bool

NAME = 'telegram'

DEFAULTS: Dict[str, Any] = {
    'enabled': False,
    'bot_token': '',
    'chat_id': '',
    'message_template': '',
    'rate_limit_messages': 20,  # Max messages per interval
    'rate_limit_interval': 60   # Interval in seconds (default: 20 messages per 60 seconds)
}


def sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = payload or {}
    sanitized: Dict[str, Any] = {
        'enabled': coerce_bool(payload.get('enabled')),
        'bot_token': str(payload.get('bot_token') or '').strip(),
        'chat_id': str(payload.get('chat_id') or '').strip(),
        'message_template': str(payload.get('message_template') or '').strip(),
        'rate_limit_messages': int(payload.get('rate_limit_messages', 20)),
        'rate_limit_interval': int(payload.get('rate_limit_interval', 60))
    }
    return sanitized
