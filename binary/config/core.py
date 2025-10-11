"""Core helpers for Suricata YAML configuration management."""
from __future__ import annotations

import os
from typing import Any, Dict

import yaml

_TRUE_VALUES = {"1", "true", "yes", "on"}


class SuricataDumper(yaml.SafeDumper):
    """Custom dumper that keeps Suricata's yes/no boolean style."""
    pass


def _represent_bool(dumper: yaml.SafeDumper, data: bool):
    return dumper.represent_scalar("tag:yaml.org,2002:bool", "yes" if data else "no")


SuricataDumper.add_representer(bool, _represent_bool)


def to_bool(value: Any) -> bool:
    """Normalize different truthy/falsy representations to a boolean."""
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return bool(value)


class ConfigFile:
    """Thin wrapper responsible for loading and saving Suricata configs."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> Dict[str, Any]:
        """Load YAML configuration from disk."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Config file not found: {self.path}")

        with open(self.path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def save(self, config: Dict[str, Any]) -> bool:
        """Write YAML configuration back to disk."""
        try:
            with open(self.path, "w", encoding="utf-8", newline="\n") as handle:
                yaml.dump(
                    config,
                    handle,
                    Dumper=SuricataDumper,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                    explicit_start=True,
                    version=(1, 1),
                )
            return True
        except Exception as exc:
            print(f"Error saving config: {exc}")
            return False


class ConfigSection:
    """Reusable base for section-specific managers."""

    def __init__(self, config_file: ConfigFile):
        self._file = config_file

    def load(self) -> Dict[str, Any]:
        return self._file.load()

    def save(self, config: Dict[str, Any]) -> bool:
        return self._file.save(config)


__all__ = [
    "ConfigFile",
    "ConfigSection",
    "SuricataDumper",
    "to_bool",
]
