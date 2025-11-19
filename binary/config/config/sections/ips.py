"""IPS configuration helpers."""
from __future__ import annotations

from typing import Any, Dict

from ..core import ConfigSection


class IPSConfig(ConfigSection):
    """Manage IPS-related configuration entries."""

    def get_ips(self) -> Dict[str, Any]:
        config = self.load()
        ips_config: Dict[str, Any] = {}

        if "action-order" in config:
            ips_config["action-order"] = config["action-order"]
        if "default-rule-action" in config:
            ips_config["default-rule-action"] = config["default-rule-action"]
        if "nfq" in config:
            ips_config["nfq"] = config["nfq"]
        if "netmap" in config:
            ips_config["netmap"] = config["netmap"]

        af_packets = config.get("af-packet")
        if isinstance(af_packets, list) and af_packets:
            for af_packet in af_packets:
                if isinstance(af_packet, dict) and af_packet.get("copy-mode"):
                    ips_config["af-packet-copy-mode"] = af_packet.get("copy-mode")
                    ips_config["af-packet-copy-iface"] = af_packet.get("copy-iface", "")
                    break

        return ips_config

    def update_ips(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()

            if "action-order" in settings:
                config["action-order"] = settings["action-order"]
            if "default-rule-action" in settings:
                config["default-rule-action"] = settings["default-rule-action"]
            if "nfq" in settings:
                config["nfq"] = settings["nfq"]
            if "netmap" in settings:
                config["netmap"] = settings["netmap"]

            if "af-packet-copy-mode" in settings:
                if "af-packet" not in config:
                    config["af-packet"] = [{}]

                if isinstance(config["af-packet"], list) and config["af-packet"]:
                    af_packet_entry = config["af-packet"][0]
                    if not isinstance(af_packet_entry, dict):
                        af_packet_entry = {}
                        config["af-packet"][0] = af_packet_entry
                    af_packet_entry["copy-mode"] = settings["af-packet-copy-mode"]
                    if "af-packet-copy-iface" in settings:
                        af_packet_entry["copy-iface"] = settings["af-packet-copy-iface"]

            return self.save(config)
        except Exception as exc:
            print(f"Error updating IPS config: {exc}")
            return False


__all__ = ["IPSConfig"]
