"""Inspection engine configuration helpers."""
from __future__ import annotations

from typing import Any, Dict

from ..core import ConfigSection


class EngineConfig(ConfigSection):
    """Manage stream and detection engine configuration."""

    def get_stream(self) -> Dict[str, Any]:
        config = self.load()
        stream_config = config.get("stream", {})
        if not isinstance(stream_config, dict):
            return {}

        reassembly = stream_config.get("reassembly")
        if not isinstance(reassembly, dict):
            stream_config["reassembly"] = {}

        return stream_config

    def update_stream(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()
            existing_stream = config.get("stream", {})
            if not isinstance(existing_stream, dict):
                existing_stream = {}

            updated_stream = dict(existing_stream)

            reassembly_settings = settings.get("reassembly")
            if isinstance(reassembly_settings, dict):
                existing_reassembly = existing_stream.get("reassembly", {})
                if not isinstance(existing_reassembly, dict):
                    existing_reassembly = {}
                updated_stream["reassembly"] = {**existing_reassembly, **reassembly_settings}

            for key, value in settings.items():
                if key == "reassembly":
                    continue
                updated_stream[key] = value

            config["stream"] = updated_stream
            return self.save(config)
        except Exception as exc:
            print(f"Error updating stream config: {exc}")
            return False

    def get_detection(self) -> Dict[str, Any]:
        config = self.load()
        detection: Dict[str, Any] = {}

        if "detect" in config:
            detection["detect"] = config["detect"]
        if "threading" in config:
            detection["threading"] = config["threading"]
        if "profiling" in config:
            detection["profiling"] = config["profiling"]
        if "mpm-algo" in config:
            detection["mpm-algo"] = config["mpm-algo"]
        if "sgh-mpm-context" in config:
            detection["sgh-mpm-context"] = config["sgh-mpm-context"]

        return detection

    def update_detection(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()
            for key, value in settings.items():
                config[key] = value
            return self.save(config)
        except Exception as exc:
            print(f"Error updating detection config: {exc}")
            return False


__all__ = ["EngineConfig"]
