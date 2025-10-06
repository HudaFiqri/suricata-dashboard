"""
YAML Config Manager - Parse and update Suricata YAML configuration
"""
import yaml
from typing import Dict, Any, Optional
import os


class YAMLConfigManager:
    """Manage Suricata YAML configuration file"""

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def save(self, config: Dict[str, Any]) -> bool:
        """Save YAML configuration"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_app_layer_protocols(self) -> Dict[str, Any]:
        """Get app-layer protocols configuration"""
        config = self.load()
        app_layer = config.get('app-layer', {})
        protocols = app_layer.get('protocols', {})
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
            if 'app-layer' not in config:
                config['app-layer'] = {}
            if 'protocols' not in config['app-layer']:
                config['app-layer']['protocols'] = {}

            protocols = config['app-layer']['protocols']

            # Update protocol
            if protocol not in protocols:
                protocols[protocol] = {}

            protocols[protocol]['enabled'] = 'yes' if enabled else 'no'

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
        af_packet_list = config.get('af-packet', [])
        if isinstance(af_packet_list, list) and len(af_packet_list) > 0:
            return af_packet_list[0]
        return {}

    def update_af_packet_config(self, settings: Dict[str, Any]) -> bool:
        """Update AF-Packet configuration"""
        try:
            config = self.load()

            if 'af-packet' not in config:
                config['af-packet'] = [{}]

            if isinstance(config['af-packet'], list):
                config['af-packet'][0].update(settings)
            else:
                config['af-packet'] = [settings]

            return self.save(config)

        except Exception as e:
            print(f"Error updating AF-Packet config: {e}")
            return False

    def get_vars(self) -> Dict[str, Any]:
        """Get variables configuration"""
        config = self.load()
        return config.get('vars', {})

    def update_var(self, var_name: str, value: str) -> bool:
        """Update a specific variable"""
        try:
            config = self.load()

            if 'vars' not in config:
                config['vars'] = {}

            config['vars'][var_name] = value

            return self.save(config)

        except Exception as e:
            print(f"Error updating variable {var_name}: {e}")
            return False

    def get_outputs(self) -> Dict[str, Any]:
        """Get outputs configuration"""
        config = self.load()
        outputs_list = config.get('outputs', [])

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

            if 'outputs' not in config:
                config['outputs'] = []

            outputs = config['outputs']

            # Find output in list
            output_found = False
            for i, output in enumerate(outputs):
                if output_name in output:
                    # Update enabled status
                    if isinstance(output[output_name], dict):
                        output[output_name]['enabled'] = 'yes' if enabled else 'no'
                        # Update additional settings
                        if settings:
                            output[output_name].update(settings)
                    else:
                        # Simple format: just enabled/no
                        output[output_name] = 'yes' if enabled else 'no'
                    output_found = True
                    break

            # If output not found, add it
            if not output_found:
                new_output = {output_name: {'enabled': 'yes' if enabled else 'no'}}
                if settings:
                    new_output[output_name].update(settings)
                outputs.append(new_output)

            return self.save(config)

        except Exception as e:
            print(f"Error updating output {output_name}: {e}")
            return False
