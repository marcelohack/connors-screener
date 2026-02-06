"""
Configuration loader for screening configurations
Supports built-in and external configuration loading
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class ScreeningConfigLoader:
    """Loads screening configurations from various sources"""

    def __init__(self) -> None:
        self.supported_formats = {".json", ".yaml", ".yml"}

    def load_from_file(self, file_path: Union[str, Path]) -> List[ScreeningConfig]:
        """Load screening configurations from a file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        if file_path.suffix not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. Supported: {self.supported_formats}"
            )

        # Load raw data
        with open(file_path, "r") as f:
            if file_path.suffix == ".json":
                data = json.load(f)
            else:  # .yaml or .yml
                data = yaml.safe_load(f)

        return self._parse_config_data(data)

    def load_from_dict(self, config_data: Dict[str, Any]) -> List[ScreeningConfig]:
        """Load screening configurations from a dictionary"""
        return self._parse_config_data(config_data)

    def _parse_config_data(self, data: Dict[str, Any]) -> List[ScreeningConfig]:
        """Parse configuration data into ScreeningConfig objects"""
        configs = []

        # Support both single config and multiple configs
        if "configurations" in data:
            # Multiple configurations format
            for config_data in data["configurations"]:
                config = self._create_config_from_dict(config_data)
                configs.append(config)
        else:
            # Single configuration format
            config = self._create_config_from_dict(data)
            configs.append(config)

        return configs

    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> ScreeningConfig:
        """Create ScreeningConfig from dictionary data"""
        required_fields = ["name", "provider", "filters"]

        # Validate required fields
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field '{field}' in configuration")

        return ScreeningConfig(
            name=config_data["name"],
            provider=config_data["provider"],
            parameters=config_data.get("parameters", {}),
            provider_config=config_data.get("provider_config", {}),
            filters=config_data["filters"],
            description=config_data.get("description", ""),
        )

    def register_configs_from_file(self, file_path: Union[str, Path]) -> List[str]:
        """Load and register configurations from a file"""
        configs = self.load_from_file(file_path)
        registered_names = []

        for config in configs:
            registry.register_screening_config(config.provider, config.name, config)
            registered_names.append(f"{config.provider}:{config.name}")

        return registered_names

    def create_example_config_file(
        self, file_path: Union[str, Path], format_type: str = "yaml"
    ) -> None:
        """Create an example configuration file"""
        example_config = {
            "configurations": [
                {
                    "name": "custom_rsi_oversold",
                    "provider": "tv",
                    "description": "Custom RSI oversold screening with specific parameters",
                    "parameters": {
                        "rsi_level": 30,
                        "rsi_period": 14,
                        "volume_min": 1000000,
                    },
                    "provider_config": {
                        "volume_threshold": 1000000,
                        "market_cap_min": 50000000,
                    },
                    "filters": [
                        {"field": "RSI", "operation": "less", "value": 30},
                        {"field": "volume", "operation": "greater", "value": 1000000},
                        {
                            "field": "is_blacklisted",
                            "operation": "equal",
                            "value": False,
                        },
                    ],
                },
                {
                    "name": "momentum_breakout",
                    "provider": "tv",
                    "description": "Momentum breakout screening configuration",
                    "parameters": {"price_change_pct": 5.0, "volume_multiplier": 2.0},
                    "provider_config": {"volume_threshold": 500000},
                    "filters": [
                        {"field": "change", "operation": "greater", "value": 5.0},
                        {"field": "volume", "operation": "greater", "value": 500000},
                    ],
                },
            ]
        }

        file_path = Path(file_path)

        with open(file_path, "w") as f:
            if format_type.lower() == "json":
                json.dump(example_config, f, indent=2)
            else:  # yaml
                yaml.dump(example_config, f, default_flow_style=False, indent=2)

        print(f"Example configuration file created: {file_path}")


# Global instance
config_loader = ScreeningConfigLoader()
