from __future__ import annotations

from typing import Any, Dict, Tuple
from urllib.parse import quote_plus, urlencode

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DEFAULT_POSTGRES_PORT = 5432


def _coerce_port(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_query_string(params: Any) -> str:
    if not params:
        return ''

    if isinstance(params, str):
        return params if params.startswith('?') else f'?{params}'

    if isinstance(params, dict):
        return '?' + urlencode(params, doseq=True)

    return ''


def create_postgresql_engine(config: Dict[str, Any]) -> Tuple[str, Engine]:
    """Create a SQLAlchemy engine for PostgreSQL and return the URL and engine."""
    host = config.get('host') or 'localhost'
    port = _coerce_port(config.get('port'), DEFAULT_POSTGRES_PORT)
    user = config.get('user') or 'postgres'
    password = config.get('password')
    database = config.get('database') or 'suricata'
    options = config.get('options') or config.get('query')

    user_part = quote_plus(str(user))
    if password is None or password == '':
        auth_part = user_part
    else:
        auth_part = f"{user_part}:{quote_plus(str(password))}"

    query_string = _build_query_string(options)

    url = f"postgresql+psycopg2://{auth_part}@{host}:{port}/{database}{query_string}"

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=bool(config.get('echo', False)),
    )

    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))

    return url, engine
