"""System-level configuration helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..core import ConfigSection, to_bool


class SystemConfig(ConfigSection):
    """Manage variables, outputs, logging, and host sections."""

    def get_vars(self) -> Dict[str, Any]:
        config = self.load()
        return config.get("vars", {})

    def update_vars(self, variables: Dict[str, Any]) -> bool:
        try:
            config = self.load()
            config["vars"] = variables or {}
            return self.save(config)
        except Exception as exc:
            print(f"Error updating vars: {exc}")
            return False

    def update_var(self, var_name: str, value: str) -> bool:
        try:
            config = self.load()

            if "vars" not in config:
                config["vars"] = {}

            config["vars"][var_name] = value
            return self.save(config)
        except Exception as exc:
            print(f"Error updating variable {var_name}: {exc}")
            return False

    def get_outputs(self) -> Dict[str, Any]:
        config = self.load()
        outputs_list = config.get("outputs", [])
        outputs_dict: Dict[str, Any] = {}

        if isinstance(outputs_list, list):
            for output in outputs_list:
                if isinstance(output, dict):
                    for key, value in output.items():
                        outputs_dict[key] = value

        return outputs_dict

    def update_output(self, output_name: str, enabled: bool, settings: Optional[Dict[str, Any]] = None) -> bool:
        try:
            config = self.load()

            if "outputs" not in config:
                config["outputs"] = []

            outputs = config["outputs"]
            enabled_flag = to_bool(enabled)
            output_found = False

            for output in outputs:
                if output_name in output:
                    if isinstance(output[output_name], dict):
                        output[output_name]["enabled"] = enabled_flag
                        if settings:
                            output[output_name].update(settings)
                    else:
                        output[output_name] = enabled_flag
                    output_found = True
                    break

            if not output_found:
                new_output = {output_name: {"enabled": enabled_flag}}
                if settings:
                    new_output[output_name].update(settings)
                outputs.append(new_output)

            return self.save(config)
        except Exception as exc:
            print(f"Error updating output {output_name}: {exc}")
            return False

    def get_logging(self) -> Dict[str, Any]:
        config = self.load()
        return config.get("logging", {})

    def update_logging(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()

            if "logging" not in config:
                config["logging"] = {}

            config["logging"].update(settings)
            return self.save(config)
        except Exception as exc:
            print(f"Error updating logging config: {exc}")
            return False

    def get_host(self) -> Dict[str, Any]:
        config = self.load()
        return config.get("host", {})

    def update_host(self, settings: Dict[str, Any]) -> bool:
        try:
            config = self.load()

            if "host" not in config:
                config["host"] = {}

            config["host"].update(settings)
            return self.save(config)
        except Exception as exc:
            print(f"Error updating host config: {exc}")
            return False


__all__ = ["SystemConfig"]
