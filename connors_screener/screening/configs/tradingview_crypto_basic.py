"""
TradingView Crypto-specific screening configurations
"""

from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningConfig


class TradingViewCryptoConfigs:
    """Basic screening configurations for TradingView Crypto provider"""

    CONFIGS = {
        "crypto_top_100": ScreeningConfig(
            name="crypto_top_100",
            provider="tv_crypto",
            parameters={"min_volume": 100_000_000},
            provider_config={"volume_threshold": "{min_volume}"},
            filters=[
                {
                    "field": "24h_vol_cmc",
                    "operation": "egreater",
                    "value": "{min_volume}",
                }
            ],
            description="Top 100 crypto by rank with minimum volume of ${min_volume:,}",
        ),
        "crypto_high_volume": ScreeningConfig(
            name="crypto_high_volume",
            provider="tv_crypto",
            parameters={"min_volume": 500_000_000},
            provider_config={"volume_threshold": "{min_volume}"},
            filters=[
                {
                    "field": "24h_vol_cmc",
                    "operation": "egreater",
                    "value": "{min_volume}",
                }
            ],
            description="High volume crypto (${min_volume:,}+)",
        ),
        "crypto_basic": ScreeningConfig(
            name="crypto_basic",
            provider="tv_crypto",
            parameters={"min_volume": 50_000_000},
            provider_config={"volume_threshold": "{min_volume}"},
            filters=[
                {
                    "field": "24h_vol_cmc",
                    "operation": "egreater",
                    "value": "{min_volume}",
                }
            ],
            description="Basic crypto screening with minimum volume of ${min_volume:,}",
        ),
    }

    @classmethod
    def register_all(cls) -> None:
        """Register all configurations with the global registry"""
        for config_name, config in cls.CONFIGS.items():
            registry.register_screening_config("tv_crypto", config_name, config)

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
TradingViewCryptoConfigs.register_all()
