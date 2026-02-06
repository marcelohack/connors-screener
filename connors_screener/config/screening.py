import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MarketScreeningConfig:
    """Market-specific screening configuration"""

    name: str
    symbolset: str
    default_volume: int
    market_identifier: str


class ScreeningConfigManager:
    """Manager for screening configurations across different markets"""

    def __init__(self) -> None:
        self.market_configs = {
            "brazil": MarketScreeningConfig(
                name="brazil",
                symbolset="SYML:BMFBOVESPA;IBOV",
                default_volume=1_000_000,
                market_identifier="brazil",
            ),
            "australia": MarketScreeningConfig(
                name="australia",
                symbolset="SYML:ASX;XKO",
                default_volume=1_000_000,
                market_identifier="australia",
            ),
            "america": MarketScreeningConfig(
                name="america",
                symbolset="SYML:SP;SPX",
                default_volume=10_000_000,
                market_identifier="america",
            ),
        }

        # Legacy config mapping for backward compatibility
        self.legacy_configs = {
            "brazil-bmfbovespa-ibov": "brazil",
            "australia-asx-xko": "australia",
            "america-nasdaq-xnas": "america",
            "america-sp-spx": "america",
        }

        self.default_config = os.getenv("SCREENING_CONFIG", "america-sp-spx")

    def get_market_config(self, config_name: str) -> MarketScreeningConfig:
        """Get market configuration, handling legacy names"""
        # Handle legacy config names
        if config_name in self.legacy_configs:
            config_name = self.legacy_configs[config_name]

        if config_name not in self.market_configs:
            raise ValueError(
                f"Unknown market config: {config_name}. Available: {list(self.market_configs.keys())}"
            )

        return self.market_configs[config_name]

    def list_markets(self) -> list[str]:
        """List all available market configurations"""
        return list(self.market_configs.keys())

    def list_legacy_configs(self) -> list[str]:
        """List all legacy configuration names"""
        return list(self.legacy_configs.keys())
