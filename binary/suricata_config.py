import yaml
import os
from typing import Dict, List, Any

class SuricataConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config_data = None
    
    def load(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
            return self._config_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def save(self, config_data: Dict[str, Any]) -> None:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            self._config_data = config_data
        except Exception as e:
            raise IOError(f"Failed to save config: {e}")
    
    def get_interfaces(self) -> List[str]:
        if not self._config_data:
            self.load()
        
        interfaces = []
        af_packet = self._config_data.get('af-packet', [])
        for interface_config in af_packet:
            if 'interface' in interface_config:
                interfaces.append(interface_config['interface'])
        return interfaces
    
    def get_rule_files(self) -> List[str]:
        if not self._config_data:
            self.load()
        
        rule_files = []
        rule_config = self._config_data.get('rule-files', [])
        for rule_file in rule_config:
            rule_files.append(rule_file)
        return rule_files