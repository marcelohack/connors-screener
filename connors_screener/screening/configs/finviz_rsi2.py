"""
Finviz-specific RSI2 screening configurations
Example of how different providers can have different implementations
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class FinvizRSI2Configs:
    """RSI2 screening configurations for Finviz provider"""

    CONFIGS = {
        "rsi2": ScreeningConfig(
            name="rsi2",
            provider="finviz",
            parameters={"rsi_level": 5, "rsi_period": 2},
            provider_config={
                "market_cap_min": 100_000_000,  # Finviz-specific: $100M min market cap
                "price_min": 5.0,  # Min stock price
                "sector": "any",
            },
            filters=[
                {
                    "field": "ta_rsi",  # Finviz uses different field names
                    "operation": "under",  # Finviz uses different operations
                    "value": 5,
                },
                {"field": "sh_price", "operation": "over", "value": 5.0},
                {"field": "sh_curvol", "operation": "over", "value": 1000},
            ],
            description="Finviz RSI2 < 5 screening with market cap and price filters",
        ),
        "rsi2_large_cap": ScreeningConfig(
            name="rsi2_large_cap",
            provider="finviz",
            parameters={"rsi_level": 5, "rsi_period": 2, "focus": "large_cap"},
            provider_config={
                "market_cap_min": 2_000_000_000,  # $2B min market cap
                "price_min": 10.0,
                "sector": "any",
            },
            filters=[
                {"field": "ta_rsi", "operation": "under", "value": 5},
                {"field": "sh_price", "operation": "over", "value": 10.0},
                {
                    "field": "cap_megalarge",  # Finviz market cap category
                    "operation": "any",
                    "value": True,
                },
            ],
            description="Finviz RSI2 < 5 screening focused on large-cap stocks",
        ),
    }

    @classmethod
    def register_all(cls) -> None:
        """Register all configurations with the global registry"""
        for config_name, config in cls.CONFIGS.items():
            registry.register_screening_config("finviz", config_name, config)

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
FinvizRSI2Configs.register_all()
