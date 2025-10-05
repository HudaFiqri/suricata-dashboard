from typing import Dict, Any
from ..suricata_config import SuricataConfig
from ..suricata_rule_manager import SuricataRuleManager
from ..suricata_log_manager import SuricataLogManager
from .backend import SuricataBackendController
from config import Config

class SuricataFrontendController:
    """Frontend controller that aggregates backend service control with config, rules, and logs management"""

    def __init__(self,
                 binary_path: str = "suricata",
                 config_path: str = "/etc/suricata/suricata.yaml",
                 rules_directory: str = "/etc/suricata/rules",
                 log_directory: str = "/var/log/suricata"):

        # Initialize backend controller
        self.backend = SuricataBackendController(binary_path, config_path)

        # Initialize managers
        self.config = SuricataConfig(config_path)
        self.rule_manager = SuricataRuleManager(rules_directory)
        self.log_manager = SuricataLogManager(log_directory)

    def get_status(self) -> Dict[str, Any]:
        """Get service status from backend and enrich with database info"""
        status = self.backend.get_status()

        db_type = (Config.DB_TYPE or '').strip().lower()
        db_label_map = {
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL'
        }
        if db_type:
            status['database'] = {
                'type': db_type,
                'label': db_label_map.get(db_type, db_type.upper()),
                'host': Config.DB_HOST,
                'port': Config.DB_PORT,
                'name': Config.DB_NAME
            }
        else:
            status['database'] = None

        return status

    def start(self) -> Dict[str, Any]:
        """Start service via backend"""
        return self.backend.start()

    def stop(self) -> Dict[str, Any]:
        """Stop service via backend"""
        return self.backend.stop()

    def restart(self) -> Dict[str, Any]:
        """Restart service via backend"""
        return self.backend.restart()

    def reload_rules(self) -> Dict[str, Any]:
        """Reload rules via backend"""
        return self.backend.reload_rules()

    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration via backend"""
        return self.backend.validate_config()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated dashboard data"""
        try:
            status = self.get_status()

            # Get stats
            alerts_count = 0
            rules_count = len(self.rule_manager.get_rule_files())

            # Try to get alerts from logs
            try:
                logs = self.log_manager.get_fast_log(100)
                alerts_count = len(logs)
            except:
                pass

            return {
                'status': status,
                'stats': {
                    'alerts': alerts_count,
                    'rules': rules_count,
                    'uptime': status.get('uptime', '-')
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts from logs"""
        try:
            logs = self.log_manager.get_fast_log(limit)
            return logs
        except Exception as e:
            return []

    def get_all_rules(self) -> list:
        """Get all rule files"""
        try:
            return self.rule_manager.get_rule_files()
        except Exception as e:
            return []

    def get_config_yaml(self) -> str:
        """Get configuration as YAML string"""
        try:
            import yaml
            config_data = self.config.load()
            return yaml.dump(config_data, default_flow_style=False, indent=2)
        except Exception as e:
            return f"Error loading config: {str(e)}"

    def save_config_yaml(self, yaml_string: str) -> Dict[str, Any]:
        """Save configuration from YAML string"""
        try:
            import yaml
            config_data = yaml.safe_load(yaml_string)
            self.config.save(config_data)
            return {'success': True, 'message': 'Configuration saved successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
