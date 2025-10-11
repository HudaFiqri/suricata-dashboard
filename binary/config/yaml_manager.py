"""High-level YAML configuration manager composed of modular sections."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .core import ConfigFile, SuricataDumper
from .sections import AppLayerConfig, CaptureConfig, EngineConfig, IPSConfig, SystemConfig


class YAMLConfigManager:
    """Facade that exposes a stable API while delegating to section managers."""

    def __init__(self, config_path: str):
        self._file = ConfigFile(config_path)
        self.app_layer = AppLayerConfig(self._file)
        self.capture = CaptureConfig(self._file)
        self.engine = EngineConfig(self._file)
        self.system = SystemConfig(self._file)
        self.ips = IPSConfig(self._file)

    @property
    def config_path(self) -> str:
        return self._file.path

    # Shared IO helpers --------------------------------------------------
    def load(self) -> Dict[str, Any]:
        return self._file.load()

    def save(self, config: Dict[str, Any]) -> bool:
        return self._file.save(config)

    # App-layer ---------------------------------------------------------
    def get_app_layer_protocols(self) -> Dict[str, Any]:
        return self.app_layer.get_protocols()

    def update_app_layer_protocol(
        self,
        protocol: str,
        enabled: bool,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return self.app_layer.update_protocol(protocol, enabled, settings)

    # Capture -----------------------------------------------------------
    def get_packet_capture_config(self, capture_type: str = "af-packet") -> Dict[str, Any]:
        """Get packet capture configuration for a specific capture type."""
        return self.capture.get_packet_capture_config(capture_type)

    def update_packet_capture_config(self, capture_type: str, settings: Dict[str, Any]) -> bool:
        """Update packet capture configuration for a specific capture type."""
        return self.capture.update_packet_capture_config(capture_type, settings)

    # Backward compatibility for AF-Packet
    def get_af_packet_config(self) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.capture.get_af_packet_config()

    def update_af_packet_config(self, settings: Dict[str, Any]) -> bool:
        """Legacy method for backward compatibility."""
        return self.capture.update_af_packet_config(settings)

    def get_interfaces(self) -> List[Dict[str, Any]]:
        return self.capture.get_interfaces()

    def update_interfaces(self, interfaces: List[Dict[str, Any]]) -> bool:
        return self.capture.update_interfaces(interfaces)

    # Engine ------------------------------------------------------------
    def get_stream(self) -> Dict[str, Any]:
        return self.engine.get_stream()

    def update_stream(self, settings: Dict[str, Any]) -> bool:
        return self.engine.update_stream(settings)

    def get_detection(self) -> Dict[str, Any]:
        return self.engine.get_detection()

    def update_detection(self, settings: Dict[str, Any]) -> bool:
        return self.engine.update_detection(settings)

    # System ------------------------------------------------------------
    def get_vars(self) -> Dict[str, Any]:
        return self.system.get_vars()

    def update_vars(self, variables: Dict[str, Any]) -> bool:
        return self.system.update_vars(variables)

    def update_var(self, var_name: str, value: str) -> bool:
        return self.system.update_var(var_name, value)

    def get_outputs(self) -> Dict[str, Any]:
        return self.system.get_outputs()

    def update_output(
        self,
        output_name: str,
        enabled: bool,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return self.system.update_output(output_name, enabled, settings)

    def get_logging(self) -> Dict[str, Any]:
        return self.system.get_logging()

    def update_logging(self, settings: Dict[str, Any]) -> bool:
        return self.system.update_logging(settings)

    def get_host(self) -> Dict[str, Any]:
        return self.system.get_host()

    def update_host(self, settings: Dict[str, Any]) -> bool:
        return self.system.update_host(settings)

    # IPS ---------------------------------------------------------------
    def get_ips(self) -> Dict[str, Any]:
        return self.ips.get_ips()

    def update_ips(self, settings: Dict[str, Any]) -> bool:
        return self.ips.update_ips(settings)


__all__ = ["YAMLConfigManager", "SuricataDumper"]
