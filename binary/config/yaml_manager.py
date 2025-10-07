"""
YAML Config Manager - Parse and update Suricata YAML configuration
"""
import os
from typing import Dict, Any, Optional

import yaml

_TRUE_VALUES = {"1", "true", "yes", "on"}


class SuricataDumper(yaml.SafeDumper):
    """Custom dumper that keeps Suricata's yes/no boolean style."""
    pass


def _represent_bool(dumper: yaml.SafeDumper, data: bool):
    return dumper.represent_scalar("tag:yaml.org,2002:bool", "yes" if data else "no")


SuricataDumper.add_representer(bool, _represent_bool)


def _to_bool(value: Any) -> bool:
    """Normalize different truthy/falsy representations to a boolean."""
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return bool(value)


class YAMLConfigManager:
    """Manage Suricata YAML configuration file"""

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def save(self, config: Dict[str, Any]) -> bool:
        """Save YAML configuration"""
        try:
            with open(self.config_path, "w", encoding="utf-8", newline="\n") as f:
                yaml.dump(
                    config,
                    f,
                    Dumper=SuricataDumper,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                    explicit_start=True,
                    version=(1, 1),
                )
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_app_layer_protocols(self) -> Dict[str, Any]:
        """Get app-layer protocols configuration"""
        config = self.load()
        app_layer = config.get("app-layer", {})
        protocols = app_layer.get("protocols", {})
        return protocols

    def update_app_layer_protocol(self, protocol: str, enabled: bool, settings: Optional[Dict] = None) -> bool:
        """
        Update app-layer protocol configuration

        Args:
            protocol: Protocol name (e.g., 'http', 'dns', 'tls')
            enabled: Enable or disable protocol
            settings: Additional protocol-specific settings

        Returns:
            True if update successful
        """
        try:
            config = self.load()

            # Ensure app-layer structure exists
            if "app-layer" not in config:
                config["app-layer"] = {}
            if "protocols" not in config["app-layer"]:
                config["app-layer"]["protocols"] = {}

            protocols = config["app-layer"]["protocols"]

            # Update protocol
            if protocol not in protocols:
                protocols[protocol] = {}

            protocols[protocol]["enabled"] = _to_bool(enabled)

            # Update additional settings if provided
            if settings:
                for key, value in settings.items():
                    protocols[protocol][key] = value

            return self.save(config)

        except Exception as e:
            print(f"Error updating protocol {protocol}: {e}")
            return False

    def get_af_packet_config(self) -> Dict[str, Any]:
        """Get AF-Packet configuration"""
        config = self.load()
        af_packet_list = config.get("af-packet", [])
        if isinstance(af_packet_list, list) and len(af_packet_list) > 0:
            return af_packet_list[0]
        return {}

    def update_af_packet_config(self, settings: Dict[str, Any]) -> bool:
        """Update AF-Packet configuration"""
        try:
            config = self.load()

            if "af-packet" not in config:
                config["af-packet"] = [{}]

            if isinstance(config["af-packet"], list):
                config["af-packet"][0].update(settings)
            else:
                config["af-packet"] = [settings]

            return self.save(config)

        except Exception as e:
            print(f"Error updating AF-Packet config: {e}")
            return False

    def get_stream(self) -> Dict[str, Any]:
        """Get stream configuration"""
        config = self.load()
        stream_config = config.get("stream", {})
        if not isinstance(stream_config, dict):
            return {}

        reassembly = stream_config.get("reassembly")
        if reassembly is None or not isinstance(reassembly, dict):
            stream_config["reassembly"] = {}

        return stream_config

    def update_stream(self, settings: Dict[str, Any]) -> bool:
        """Update stream configuration"""
        try:
            config = self.load()
            existing_stream = config.get("stream", {})
            if not isinstance(existing_stream, dict):
                existing_stream = {}

            updated_stream = {**existing_stream}

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

        except Exception as e:
            print(f"Error updating stream config: {e}")
            return False


    def get_vars(self) -> Dict[str, Any]:
        """Get variables configuration"""
        config = self.load()
        return config.get("vars", {})

    def update_vars(self, variables: Dict[str, Any]) -> bool:
        """Replace entire vars configuration"""
        try:
            config = self.load()
            config["vars"] = variables or {}
            return self.save(config)

        except Exception as e:
            print(f"Error updating vars: {e}")
            return False


    def update_var(self, var_name: str, value: str) -> bool:
        """Update a specific variable"""
        try:
            config = self.load()

            if "vars" not in config:
                config["vars"] = {}

            config["vars"][var_name] = value

            return self.save(config)

        except Exception as e:
            print(f"Error updating variable {var_name}: {e}")
            return False

    def get_outputs(self) -> Dict[str, Any]:
        """Get outputs configuration"""
        config = self.load()
        outputs_list = config.get("outputs", [])

        # Convert list to dict for easier processing
        outputs_dict = {}
        if isinstance(outputs_list, list):
            for output in outputs_list:
                if isinstance(output, dict):
                    for key, value in output.items():
                        outputs_dict[key] = value

        return outputs_dict

    def update_output(self, output_name: str, enabled: bool, settings: Optional[Dict] = None) -> bool:
        """
        Update output configuration

        Args:
            output_name: Output type (e.g., 'eve-log', 'unified2-alert', 'fast', 'stats')
            enabled: Enable or disable output
            settings: Additional output-specific settings

        Returns:
            True if update successful
        """
        try:
            config = self.load()

            if "outputs" not in config:
                config["outputs"] = []

            outputs = config["outputs"]

            enabled_flag = _to_bool(enabled)

            # Find output in list
            output_found = False
            for output in outputs:
                if output_name in output:
                    # Update enabled status
                    if isinstance(output[output_name], dict):
                        output[output_name]["enabled"] = enabled_flag
                        # Update additional settings
                        if settings:
                            output[output_name].update(settings)
                    else:
                        # Simple format: just enabled/no
                        output[output_name] = enabled_flag
                    output_found = True
                    break

            # If output not found, add it
            if not output_found:
                new_output = {output_name: {"enabled": enabled_flag}}
                if settings:
                    new_output[output_name].update(settings)
                outputs.append(new_output)

            return self.save(config)

        except Exception as e:
            print(f"Error updating output {output_name}: {e}")
            return False

    def get_logging(self) -> Dict[str, Any]:
        """Get logging configuration"""
        config = self.load()
        return config.get("logging", {})

    def update_logging(self, settings: Dict[str, Any]) -> bool:
        """Update logging configuration"""
        try:
            config = self.load()

            if "logging" not in config:
                config["logging"] = {}

            # Update logging settings
            config["logging"].update(settings)

            return self.save(config)

        except Exception as e:
            print(f"Error updating logging config: {e}")
            return False

    def get_detection(self) -> Dict[str, Any]:
        """Get detection engine configuration"""
        config = self.load()
        detect_config = {}

        # Collect detection-related settings
        if "detect" in config:
            detect_config["detect"] = config["detect"]
        if "threading" in config:
            detect_config["threading"] = config["threading"]
        if "profiling" in config:
            detect_config["profiling"] = config["profiling"]
        if "mpm-algo" in config:
            detect_config["mpm-algo"] = config["mpm-algo"]
        if "sgh-mpm-context" in config:
            detect_config["sgh-mpm-context"] = config["sgh-mpm-context"]

        return detect_config

    def update_detection(self, settings: Dict[str, Any]) -> bool:
        """Update detection engine configuration"""
        try:
            config = self.load()

            # Update detection settings at root level
            for key, value in settings.items():
                config[key] = value

            return self.save(config)

        except Exception as e:
            print(f"Error updating detection config: {e}")
            return False

    def get_host(self) -> Dict[str, Any]:
        """Get host configuration"""
        config = self.load()
        return config.get("host", {})

    def update_host(self, settings: Dict[str, Any]) -> bool:
        """Update host configuration"""
        try:
            config = self.load()

            if "host" not in config:
                config["host"] = {}

            # Update host settings
            config["host"].update(settings)

            return self.save(config)

        except Exception as e:
            print(f"Error updating host config: {e}")
            return False

    def get_ips(self) -> Dict[str, Any]:
        """Get IPS/Preventive configuration"""
        config = self.load()
        ips_config = {}

        # Collect IPS-related settings from various sections
        # Action order defines what actions can be taken
        if "action-order" in config:
            ips_config["action-order"] = config["action-order"]

        # Default action for rules without explicit action
        if "default-rule-action" in config:
            ips_config["default-rule-action"] = config["default-rule-action"]

        # NFQ (NFQUEUE) configuration for inline mode
        if "nfq" in config:
            ips_config["nfq"] = config["nfq"]

        # Netmap configuration
        if "netmap" in config:
            ips_config["netmap"] = config["netmap"]

        # AF-Packet can run in IPS mode too
        if "af-packet" in config:
            af_packets = config["af-packet"]
            if isinstance(af_packets, list) and len(af_packets) > 0:
                # Check if any af-packet interface is in copy mode (IPS)
                for af in af_packets:
                    if isinstance(af, dict) and af.get("copy-mode"):
                        ips_config["af-packet-copy-mode"] = af.get("copy-mode")
                        ips_config["af-packet-copy-iface"] = af.get("copy-iface", "")
                        break

        return ips_config

    def update_ips(self, settings: Dict[str, Any]) -> bool:
        """Update IPS/Preventive configuration"""
        try:
            config = self.load()

            # Update action-order if provided
            if "action-order" in settings:
                config["action-order"] = settings["action-order"]

            # Update default-rule-action if provided
            if "default-rule-action" in settings:
                config["default-rule-action"] = settings["default-rule-action"]

            # Update NFQ settings if provided
            if "nfq" in settings:
                config["nfq"] = settings["nfq"]

            # Update Netmap settings if provided
            if "netmap" in settings:
                config["netmap"] = settings["netmap"]

            # Update AF-Packet copy mode if provided
            if "af-packet-copy-mode" in settings:
                if "af-packet" not in config:
                    config["af-packet"] = [{}]

                if isinstance(config["af-packet"], list) and len(config["af-packet"]) > 0:
                    config["af-packet"][0]["copy-mode"] = settings["af-packet-copy-mode"]
                    if "af-packet-copy-iface" in settings:
                        config["af-packet"][0]["copy-iface"] = settings["af-packet-copy-iface"]

            return self.save(config)

        except Exception as e:
            print(f"Error updating IPS config: {e}")
            return False

    def get_interfaces(self) -> list:
        """Get configured interfaces from af-packet or pcap sections"""
        config = self.load()
        interfaces = []

        # Check af-packet interfaces
        if "af-packet" in config:
            af_packets = config["af-packet"]
            if isinstance(af_packets, list):
                for af in af_packets:
                    if isinstance(af, dict) and "interface" in af:
                        interfaces.append({
                            'type': 'af-packet',
                            'interface': af.get('interface', ''),
                            'threads': af.get('threads', 'auto'),
                            'cluster-id': af.get('cluster-id', 99),
                            'cluster-type': af.get('cluster-type', 'cluster_flow'),
                            'enabled': True
                        })

        # Check pcap interfaces
        if "pcap" in config:
            pcaps = config["pcap"]
            if isinstance(pcaps, list):
                for pcap in pcaps:
                    if isinstance(pcap, dict) and "interface" in pcap:
                        interfaces.append({
                            'type': 'pcap',
                            'interface': pcap.get('interface', ''),
                            'enabled': True
                        })

        return interfaces

    def update_interfaces(self, interfaces: list) -> bool:
        """Update interfaces configuration"""
        try:
            config = self.load()

            # Separate interfaces by type
            af_packet_interfaces = [i for i in interfaces if i.get('type') == 'af-packet']
            pcap_interfaces = [i for i in interfaces if i.get('type') == 'pcap']

            # Update af-packet interfaces
            if af_packet_interfaces:
                af_packet_configs = []
                for iface in af_packet_interfaces:
                    if iface.get('enabled'):
                        af_config = {
                            'interface': iface.get('interface', ''),
                            'threads': iface.get('threads', 'auto'),
                            'cluster-id': iface.get('cluster-id', 99),
                            'cluster-type': iface.get('cluster-type', 'cluster_flow')
                        }
                        af_packet_configs.append(af_config)

                config["af-packet"] = af_packet_configs

            # Update pcap interfaces
            if pcap_interfaces:
                pcap_configs = []
                for iface in pcap_interfaces:
                    if iface.get('enabled'):
                        pcap_configs.append({
                            'interface': iface.get('interface', '')
                        })

                config["pcap"] = pcap_configs

            return self.save(config)

        except Exception as e:
            print(f"Error updating interfaces config: {e}")
            return False
