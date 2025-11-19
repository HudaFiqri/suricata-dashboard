"""Network capture configuration helpers."""
from __future__ import annotations

from typing import Any, Dict, List

from ..core import ConfigSection


class CaptureConfig(ConfigSection):
    """Manage Packet Capture configuration (AF-Packet, AF-XDP, DPDK, PCAP)."""

    def get_packet_capture_config(self, capture_type: str = "af-packet") -> Dict[str, Any]:
        """
        Get packet capture configuration for a specific capture type.

        Args:
            capture_type: Type of capture (af-packet, af-xdp, dpdk, pcap)

        Returns:
            Dictionary with capture configuration
        """
        config = self.load()
        capture_list = config.get(capture_type, [])
        if isinstance(capture_list, list) and capture_list:
            first_entry = capture_list[0]
            if isinstance(first_entry, dict):
                return first_entry
        return {}

    def update_packet_capture_config(self, capture_type: str, settings: Dict[str, Any]) -> bool:
        """
        Update packet capture configuration for a specific capture type.

        Args:
            capture_type: Type of capture (af-packet, af-xdp, dpdk, pcap)
            settings: Configuration settings to update

        Returns:
            True if successful, False otherwise
        """
        try:
            config = self.load()

            if capture_type not in config:
                config[capture_type] = [{}]

            if isinstance(config[capture_type], list):
                if config[capture_type] and isinstance(config[capture_type][0], dict):
                    config[capture_type][0].update(settings)
                else:
                    config[capture_type] = [settings]
            else:
                config[capture_type] = [settings]

            return self.save(config)
        except Exception as exc:
            print(f"Error updating {capture_type} config: {exc}")
            return False

    # Backward compatibility methods
    def get_af_packet_config(self) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.get_packet_capture_config("af-packet")

    def update_af_packet_config(self, settings: Dict[str, Any]) -> bool:
        """Legacy method for backward compatibility."""
        return self.update_packet_capture_config("af-packet", settings)

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get all configured capture interfaces across all capture types."""
        config = self.load()
        interfaces: List[Dict[str, Any]] = []

        # AF-Packet interfaces
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

        # AF-XDP interfaces
        af_xdp = config.get("af-xdp")
        if isinstance(af_xdp, list):
            for xdp in af_xdp:
                if isinstance(xdp, dict) and "interface" in xdp:
                    interfaces.append({
                        "type": "af-xdp",
                        "interface": xdp.get("interface", ""),
                        "threads": xdp.get("threads", "auto"),
                        "enabled": True,
                    })

        # DPDK interfaces
        dpdk = config.get("dpdk")
        if isinstance(dpdk, dict) and "interfaces" in dpdk:
            dpdk_interfaces = dpdk.get("interfaces", [])
            if isinstance(dpdk_interfaces, list):
                for dpdk_iface in dpdk_interfaces:
                    if isinstance(dpdk_iface, dict) and "interface" in dpdk_iface:
                        interfaces.append({
                            "type": "dpdk",
                            "interface": dpdk_iface.get("interface", ""),
                            "threads": dpdk_iface.get("threads", "auto"),
                            "enabled": True,
                        })

        # PCAP interfaces
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
        """Update all capture interfaces configuration."""
        try:
            config = self.load()

            # Group interfaces by type
            af_packet_interfaces = [iface for iface in interfaces if iface.get("type") == "af-packet"]
            af_xdp_interfaces = [iface for iface in interfaces if iface.get("type") == "af-xdp"]
            dpdk_interfaces = [iface for iface in interfaces if iface.get("type") == "dpdk"]
            pcap_interfaces = [iface for iface in interfaces if iface.get("type") == "pcap"]

            # Update AF-Packet
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

            # Update AF-XDP
            if af_xdp_interfaces:
                af_xdp_configs: List[Dict[str, Any]] = []
                for iface in af_xdp_interfaces:
                    if iface.get("enabled"):
                        af_xdp_configs.append({
                            "interface": iface.get("interface", ""),
                            "threads": iface.get("threads", "auto"),
                        })
                config["af-xdp"] = af_xdp_configs

            # Update DPDK
            if dpdk_interfaces:
                dpdk_iface_configs: List[Dict[str, Any]] = []
                for iface in dpdk_interfaces:
                    if iface.get("enabled"):
                        dpdk_iface_configs.append({
                            "interface": iface.get("interface", ""),
                            "threads": iface.get("threads", "auto"),
                        })
                if "dpdk" not in config:
                    config["dpdk"] = {}
                config["dpdk"]["interfaces"] = dpdk_iface_configs

            # Update PCAP
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
