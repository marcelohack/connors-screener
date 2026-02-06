"""
TradingView-specific RSI2 screening configurations
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class TradingViewRSI2Configs:
    """RSI2 screening configurations for TradingView provider"""

    CONFIGS = {
        "rsi2": ScreeningConfig(
            name="rsi2",
            provider="tv",
            parameters={"rsi_level": 5, "rsi_period": 2},
            provider_config={"volume_threshold": 1_000_000},
            filters=[
                {"field": "RSI2", "operation": "less", "value": "{rsi_level}"},
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Basic RSI2 < {rsi_level} screening with standard volume filter",
        ),
        "rsi2_high_volume": ScreeningConfig(
            name="rsi2_high_volume",
            provider="tv",
            parameters={"rsi_level": 5, "rsi_period": 2, "volume_threshold": 5_000_000},
            provider_config={"volume_threshold": "{volume_threshold}"},
            filters=[
                {"field": "RSI2", "operation": "less", "value": "{rsi_level}"},
                {
                    "field": "volume",
                    "operation": "greater",
                    "value": "{volume_threshold}",
                },
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="RSI2 < {rsi_level} screening with high volume filter ({volume_threshold:,}+)",
        ),
        "rsi2_relaxed": ScreeningConfig(
            name="rsi2_relaxed",
            provider="tv",
            parameters={"rsi_level": 10, "rsi_period": 2, "volume_threshold": 500_000},
            provider_config={"volume_threshold": "{volume_threshold}"},
            filters=[
                {"field": "RSI2", "operation": "less", "value": "{rsi_level}"},
                {
                    "field": "volume",
                    "operation": "greater",
                    "value": "{volume_threshold}",
                },
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Relaxed RSI2 < {rsi_level} screening with lower volume threshold ({volume_threshold:,}+)",
        ),
    }

    @classmethod
    def register_all(cls) -> None:
        """Register all configurations with the global registry"""
        for config_name, config in cls.CONFIGS.items():
            registry.register_screening_config("tv", config_name, config)

    @classmethod
    def get_config(cls, name: str) -> ScreeningConfig:
        """Get screening configuration by name"""
        if name not in cls.CONFIGS:
            raise ValueError(
                f"Config '{name}' not found. Available: {list(cls.CONFIGS.keys())}"
            )
        return cls.CONFIGS[name]

    @classmethod
    def list_configs(cls) -> list[str]:
        """List all available configuration names"""
        return list(cls.CONFIGS.keys())


# Auto-register configs on import
TradingViewRSI2Configs.register_all()
