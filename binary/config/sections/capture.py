"""Network capture configuration helpers."""
from __future__ import annotations

from typing import Any, Dict, List

from ..core import ConfigSection


class CaptureConfig(ConfigSection):
    """Manage AF-Packet and interface configuration."""

    def get_af_packet_config(self) -> Dict[str, Any]:
        config = self.load()
        af_packet_list = config.get("af-packet", [])
        if isinstance(af_packet_list, list) and af_packet_list:
            first_entry = af_packet_list[0]
            if isinstance(first_entry, dict):
                return first_entry
        return {}

    def update_af_packet_config(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()

            if "af-packet" not in config:
                config["af-packet"] = [{}]

            if isinstance(config["af-packet"], list):
                if config["af-packet"] and isinstance(config["af-packet"][0], dict):
                    config["af-packet"][0].update(settings)
                else:
                    config["af-packet"] = [settings]
            else:
                config["af-packet"] = [settings]

            return self.save(config)
        except Exception as exc:
            print(f"Error updating AF-Packet config: {exc}")
            return False

    def get_interfaces(self) -> List[Dict[str, Any]]:
        config = self.load()
        interfaces: List[Dict[str, Any]] = []

        af_packets = config.get("af-packet")
        if isinstance(af_packets, list):
            for af_packet in af_packets:
                if isinstance(af_packet, dict) and "interface" in af_packet:
                    interfaces.append({
                        "type": "af-packet",
                        "interface": af_packet.get("interface", ""),
                        "threads": af_packet.get("threads", "auto"),
                        "cluster-id": af_packet.get("cluster-id", 99),
                        "cluster-type": af_packet.get("cluster-type", "cluster_flow"),
                        "enabled": True,
                    })

        pcaps = config.get("pcap")
        if isinstance(pcaps, list):
            for pcap in pcaps:
                if isinstance(pcap, dict) and "interface" in pcap:
                    interfaces.append({
                        "type": "pcap",
                        "interface": pcap.get("interface", ""),
                        "enabled": True,
                    })

        return interfaces

    def update_interfaces(self, interfaces: List[Dict[str, Any]]) -> bool:
        try:
            config = self.load()

            af_packet_interfaces = [iface for iface in interfaces if iface.get("type") == "af-packet"]
            pcap_interfaces = [iface for iface in interfaces if iface.get("type") == "pcap"]

            if af_packet_interfaces:
                af_packet_configs: List[Dict[str, Any]] = []
                for iface in af_packet_interfaces:
                    if iface.get("enabled"):
                        af_packet_configs.append({
                            "interface": iface.get("interface", ""),
                            "threads": iface.get("threads", "auto"),
                            "cluster-id": iface.get("cluster-id", 99),
                            "cluster-type": iface.get("cluster-type", "cluster_flow"),
                        })

                config["af-packet"] = af_packet_configs

            if pcap_interfaces:
                pcap_configs: List[Dict[str, Any]] = []
                for iface in pcap_interfaces:
                    if iface.get("enabled"):
                        pcap_configs.append({
                            "interface": iface.get("interface", ""),
                        })

                config["pcap"] = pcap_configs

            return self.save(config)
        except Exception as exc:
            print(f"Error updating interfaces config: {exc}")
            return False


__all__ = ["CaptureConfig"]
