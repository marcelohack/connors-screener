"""
TradingView-specific value screening configurations
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class TradingViewValueConfigs:
    """Value screening configurations for TradingView provider"""

    CONFIGS = {
        "value_low_pe": ScreeningConfig(
            name="value_low_pe",
            provider="tv",
            parameters={
                "max_pe_ratio": 15.0,
                "min_market_cap": 100_000_000,
                "min_volume": 500_000,
            },
            provider_config={"volume_threshold": 500_000},
            filters=[
                {"field": "price_earnings_ttm", "operation": "less", "value": 15.0},
                {
                    "field": "price_earnings_ttm",
                    "operation": "greater",
                    "value": 0,  # Exclude negative P/E
                },
                {
                    "field": "market_cap_basic",
                    "operation": "greater",
                    "value": 100_000_000,
                },
                {"field": "volume", "operation": "greater", "value": 500_000},
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Value screening for stocks with low P/E ratios (< 15) and decent liquidity",
        ),
        "value_undervalued": ScreeningConfig(
            name="value_undervalued",
            provider="tv",
            parameters={
                "max_pe_ratio": 12.0,
                "min_dividend_yield": 2.0,
                "min_market_cap": 1_000_000_000,
            },
            provider_config={"volume_threshold": 1_000_000},
            filters=[
                {"field": "price_earnings_ttm", "operation": "less", "value": 12.0},
                {"field": "price_earnings_ttm", "operation": "greater", "value": 0},
                {
                    "field": "dividend_yield_recent",
                    "operation": "greater",
                    "value": 2.0,
                },
                {
                    "field": "market_cap_basic",
                    "operation": "greater",
                    "value": 1_000_000_000,
                },
                {"field": "volume", "operation": "greater", "value": 1_000_000},
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
            description="Deep value screening for undervalued large-cap dividend stocks",
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
TradingViewValueConfigs.register_all()
