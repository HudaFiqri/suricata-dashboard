from typing import Any


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        return lowered in {'1', 'true', 'yes', 'on'}
    if isinstance(value, (int, float)):
        return bool(value)
    return False
