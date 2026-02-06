"""
TradingView-specific momentum screening configurations
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class TradingViewMomentumConfigs:
    """Momentum screening configurations for TradingView provider"""

    CONFIGS = {
        "momentum_breakout": ScreeningConfig(
            name="momentum_breakout",
            provider="tv",
            parameters={
                "price_change_pct": 5.0,
                "volume_threshold": 1_000_000,
                "min_price": 5.0,
            },
            provider_config={"volume_threshold": "{volume_threshold}"},
            filters=[
                {
                    "field": "change",
                    "operation": "greater",
                    "value": "{price_change_pct}",
                },
                {
                    "field": "volume",
                    "operation": "greater",
                    "value": "{volume_threshold}",
                },
                {"field": "close", "operation": "greater", "value": "{min_price}"},
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Momentum breakout screening for stocks with {price_change_pct:g}%+ daily gain, volume >{volume_threshold:,}, and price >${min_price:g}",
        ),
        "momentum_strong": ScreeningConfig(
            name="momentum_strong",
            provider="tv",
            parameters={
                "price_change_pct": 10.0,
                "volume_multiplier": 3.0,
                "market_cap_min": 500_000_000,
            },
            provider_config={"volume_threshold": 2_000_000},
            filters=[
                {"field": "change", "operation": "greater", "value": 10.0},
                {"field": "volume", "operation": "greater", "value": 2_000_000},
                {
                    "field": "market_cap_basic",
                    "operation": "greater",
                    "value": 500_000_000,
                },
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Strong momentum screening for stocks with 10%+ daily gain, high volume, and large market cap",
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
TradingViewMomentumConfigs.register_all()
