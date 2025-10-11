import json
import os
import threading
from typing import Any, Callable, Dict, Optional, Tuple

from . import discord, telegram

Sanitizer = Callable[[Dict[str, Any]], Dict[str, Any]]
RegistryEntry = Tuple[Dict[str, Any], Sanitizer]


class IntegrationManager:
    """Manage integration configuration for external services."""

    _FILENAME = 'integration_settings.json'

    def __init__(self, data_dir: str, db_manager: Optional[Any] = None, filename: Optional[str] = None):
        self.data_dir = data_dir
        self.db_manager = db_manager
        self.file_path = os.path.join(self.data_dir, filename or self._FILENAME)
        self._lock = threading.Lock()
        self._registry: Dict[str, RegistryEntry] = {
            discord.NAME: (discord.DEFAULTS, discord.sanitize),
            telegram.NAME: (telegram.DEFAULTS, telegram.sanitize)
        }
        self._ensure_storage()

    def _default_payload(self) -> Dict[str, Dict[str, Any]]:
        return {name: defaults.copy() for name, (defaults, _) in self._registry.items()}

    def _ensure_storage(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.file_path):
            payload = self._default_payload()
            self._write(payload)
            self._sync_to_database(payload)
            return

        try:
            current = self._read()
        except (json.JSONDecodeError, OSError, ValueError):
            current = {}

        merged = self._merge_with_defaults(current)
        self._write(merged)
        self._sync_to_database(merged)

    def _merge_with_defaults(self, current: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        current = current or {}

        for name, (defaults, sanitizer) in self._registry.items():
            existing = current.get(name, {})
            if not isinstance(existing, dict):
                existing = {}

            sanitized = sanitizer(existing)
            for key, default_value in defaults.items():
                if key not in sanitized:
                    sanitized[key] = default_value
            merged[name] = sanitized

        return merged

    def _read(self) -> Dict[str, Any]:
        with open(self.file_path, 'r', encoding='utf-8') as handle:
            return json.load(handle)

    def _write(self, data: Dict[str, Any]) -> None:
        tmp_path = f"{self.file_path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, self.file_path)

    def _sync_to_database(self, payload: Dict[str, Dict[str, Any]]) -> None:
        if not self.db_manager:
            return

        for name, settings in payload.items():
            self._persist_to_database(name, settings)

    def _persist_to_database(self, name: str, settings: Dict[str, Any]) -> None:
        if not self.db_manager:
            return

        try:
            self.db_manager.upsert_integration_settings(name, settings)
        except Exception as exc:
            print(f"[IntegrationManager] Warning: failed to persist '{name}' integration to database: {exc}")

    def get_settings(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            data = self._read()
            return self._merge_with_defaults(data)

    def get_integration(self, name: str) -> Dict[str, Any]:
        normalized = (name or '').lower()
        if normalized not in self._registry:
            raise ValueError(f"Unsupported integration: {normalized}")

        settings = self.get_settings()
        return settings[normalized]

    def update_integration(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = (name or '').lower()
        if normalized not in self._registry:
            raise ValueError(f"Unsupported integration: {normalized}")

        defaults, sanitizer = self._registry[normalized]
        sanitized = sanitizer(payload or {})
        for key, default_value in defaults.items():
            if key not in sanitized:
                sanitized[key] = default_value

        with self._lock:
            current = self._read()
            merged = self._merge_with_defaults(current)
            merged[normalized] = sanitized
            self._write(merged)

        self._persist_to_database(normalized, sanitized)
        return sanitized

    def get_hashes(self) -> Dict[str, Dict[str, Any]]:
        if not self.db_manager:
            return {}
        try:
            return self.db_manager.get_integration_hashes()
        except Exception:
            return {}

    def get_hash(self, name: str) -> Optional[Dict[str, Any]]:
        if not self.db_manager:
            return None
        try:
            return self.db_manager.get_integration_hash(name)
        except Exception:
            return None

    def available_integrations(self) -> Tuple[str, ...]:
        return tuple(self._registry.keys())
