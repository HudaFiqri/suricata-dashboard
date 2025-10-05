from __future__ import annotations

from typing import Any, Dict, Tuple
from urllib.parse import quote_plus, urlencode

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DEFAULT_MYSQL_PORT = 3306


def _coerce_port(value: Any, default: int) -> int:
    """Attempt to coerce the provided port value to an integer."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_query_string(params: Any) -> str:
    """Build a query string portion for the SQLAlchemy URL."""
    if not params:
        return ''

    if isinstance(params, str):
        return params if params.startswith('?') else f'?{params}'

    if isinstance(params, dict):
        return '?' + urlencode(params, doseq=True)

    return ''


def create_mysql_engine(config: Dict[str, Any]) -> Tuple[str, Engine]:
    """Create a SQLAlchemy engine for MySQL and return the URL and engine."""
    host = config.get('host') or 'localhost'
    port = _coerce_port(config.get('port'), DEFAULT_MYSQL_PORT)
    user = config.get('user') or 'root'
    password = config.get('password')
    database = config.get('database') or 'suricata'
    options = config.get('options') or config.get('query')

    user_part = quote_plus(str(user))
    if password is None or password == '':
        auth_part = user_part
    else:
        auth_part = f"{user_part}:{quote_plus(str(password))}"

    query_string = _build_query_string(options)

    url = f"mysql+pymysql://{auth_part}@{host}:{port}/{database}{query_string or '?charset=utf8mb4'}"

    if query_string:
        if 'charset=' not in query_string.lower():
            url += ('&' if '?' in query_string else '?') + 'charset=utf8mb4'
    else:
        # ensured above by default suffix
        pass

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=bool(config.get('echo', False)),
    )

    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))

    return url, engine
