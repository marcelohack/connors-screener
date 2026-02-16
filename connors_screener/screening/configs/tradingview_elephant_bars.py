"""
TradingView elephant_bars screening configuration.

Reproduces a TradingView scan that returns the top stocks by market cap
with no API-level filters, no symbolset restriction, and extra columns
for volume/ATR analysis (used by the elephant_bars post-filter).
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class TradingViewElephantBarsConfigs:
    """Elephant bars screening configurations for TradingView provider"""

    CONFIGS = {
        "elephant_bars": ScreeningConfig(
            name="elephant_bars",
            provider="tv",
            parameters={},
            provider_config={
                "extra_columns": ["average_volume_30d_calc", "ATR", "high", "low", "open"],
                "use_symbolset": False,
                "skip_default_volume_filter": True,
            },
            filters=[],
            description="Top stocks by market cap with volume/ATR data for elephant bar detection",
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
TradingViewElephantBarsConfigs.register_all()
