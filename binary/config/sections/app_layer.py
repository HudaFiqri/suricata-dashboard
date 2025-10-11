"""App-layer protocol configuration helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..core import ConfigSection, to_bool


class AppLayerConfig(ConfigSection):
    """Manage app-layer protocol entries."""

    def get_protocols(self) -> Dict[str, Any]:
        config = self.load()
        app_layer = config.get("app-layer", {})
        return app_layer.get("protocols", {})

    def update_protocol(self, protocol: str, enabled: bool, settings: Optional[Dict[str, Any]] = None) -> bool:
        try:
            config = self.load()

            app_layer = config.setdefault("app-layer", {})
            protocols = app_layer.setdefault("protocols", {})
            protocol_config = protocols.setdefault(protocol, {})

            protocol_config["enabled"] = to_bool(enabled)
            if settings:
                protocol_config.update(settings)

            return self.save(config)
        except Exception as exc:
            print(f"Error updating protocol {protocol}: {exc}")
            return False


__all__ = ["AppLayerConfig"]
