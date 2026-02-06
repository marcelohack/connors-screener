"""
Unit tests for screening configurations
"""

import pytest

from connors_screener.core.screener import ScreeningConfig
from connors_screener.screening.configs.finviz_rsi2 import FinvizRSI2Configs
from connors_screener.screening.configs.tradingview_rsi2 import TradingViewRSI2Configs


class TestTradingViewRSI2Configs:
    """Test TradingView RSI2 configurations"""

    def test_get_basic_rsi2_config(self) -> None:
        """Test getting basic RSI2 configuration"""
        config = TradingViewRSI2Configs.get_config("rsi2")

        assert isinstance(config, ScreeningConfig)
        assert config.name == "rsi2"
        assert config.provider == "tv"
        assert config.parameters["rsi_level"] == 5
        assert config.parameters["rsi_period"] == 2
        assert config.provider_config["volume_threshold"] == 1_000_000
        assert len(config.filters) == 2
        assert config.description != ""

    def test_get_high_volume_config(self) -> None:
        """Test getting high volume RSI2 configuration"""
        config = TradingViewRSI2Configs.get_config("rsi2_high_volume")

        assert config.name == "rsi2_high_volume"
        assert config.provider == "tv"
        assert config.parameters["rsi_level"] == 5
        assert config.parameters["volume_threshold"] == 5_000_000
        assert config.provider_config["volume_threshold"] == "{volume_threshold}"
        assert len(config.filters) == 3  # RSI2, volume, blacklisted

    def test_get_relaxed_config(self) -> None:
        """Test getting relaxed RSI2 configuration"""
        config = TradingViewRSI2Configs.get_config("rsi2_relaxed")

        assert config.name == "rsi2_relaxed"
        assert config.provider == "tv"
        assert config.parameters["rsi_level"] == 10  # Relaxed threshold
        assert (
            config.parameters["volume_threshold"] == 500_000
        )  # Lower volume parameter
        assert (
            config.provider_config["volume_threshold"] == "{volume_threshold}"
        )  # Placeholder

    def test_get_nonexistent_config(self) -> None:
        """Test getting non-existent configuration"""
        with pytest.raises(ValueError, match="Config 'nonexistent' not found"):
            TradingViewRSI2Configs.get_config("nonexistent")

    def test_list_configs(self) -> None:
        """Test listing all available configurations"""
        configs = TradingViewRSI2Configs.list_configs()

        assert isinstance(configs, list)
        assert len(configs) == 3
        assert "rsi2" in configs
        assert "rsi2_high_volume" in configs
        assert "rsi2_relaxed" in configs

    def test_all_configs_have_required_fields(self) -> None:
        """Test that all configs have required fields"""
        for config_name in TradingViewRSI2Configs.list_configs():
            config = TradingViewRSI2Configs.get_config(config_name)

            # Check required fields
            assert config.name is not None
            assert config.provider == "tv"
            assert isinstance(config.parameters, dict)
            assert isinstance(config.provider_config, dict)
            assert isinstance(config.filters, list)
            assert len(config.filters) > 0


class TestFinvizRSI2Configs:
    """Test Finviz RSI2 configurations"""

    def test_get_basic_rsi2_config(self) -> None:
        """Test getting basic Finviz RSI2 configuration"""
        config = FinvizRSI2Configs.get_config("rsi2")

        assert isinstance(config, ScreeningConfig)
        assert config.name == "rsi2"
        assert config.provider == "finviz"
        assert config.parameters["rsi_level"] == 5
        assert config.parameters["rsi_period"] == 2
        assert config.provider_config["market_cap_min"] == 100_000_000
        assert config.provider_config["price_min"] == 5.0

    def test_get_large_cap_config(self) -> None:
        """Test getting large cap Finviz configuration"""
        config = FinvizRSI2Configs.get_config("rsi2_large_cap")

        assert config.name == "rsi2_large_cap"
        assert config.provider == "finviz"
        assert config.parameters["focus"] == "large_cap"
        assert config.provider_config["market_cap_min"] == 2_000_000_000  # $2B
        assert config.provider_config["price_min"] == 10.0

    def test_finviz_filters_different_from_tv(self) -> None:
        """Test that Finviz filters use different field names than TradingView"""
        config = FinvizRSI2Configs.get_config("rsi2")

        # Finviz uses different field names
        filter_fields = [f["field"] for f in config.filters]
        assert "ta_rsi" in filter_fields  # Not "RSI2" like TradingView
        assert "sh_price" in filter_fields  # Finviz-specific field
        assert "sh_curvol" in filter_fields  # Finviz-specific field

    def test_finviz_operations_different_from_tv(self) -> None:
        """Test that Finviz uses different operations than TradingView"""
        config = FinvizRSI2Configs.get_config("rsi2")

        # Find RSI filter
        rsi_filter = next(f for f in config.filters if f["field"] == "ta_rsi")
        assert rsi_filter["operation"] == "under"  # Not "less" like TradingView

    def test_list_configs(self) -> None:
        """Test listing all available Finviz configurations"""
        configs = FinvizRSI2Configs.list_configs()

        assert isinstance(configs, list)
        assert len(configs) == 2
        assert "rsi2" in configs
        assert "rsi2_large_cap" in configs

    def test_provider_specific_differences(self) -> None:
        """Test that provider-specific configurations are truly different"""
        tv_config = TradingViewRSI2Configs.get_config("rsi2")
        finviz_config = FinvizRSI2Configs.get_config("rsi2")

        # Same config name, different providers
        assert tv_config.name == finviz_config.name == "rsi2"
        assert tv_config.provider != finviz_config.provider

        # Different provider-specific configurations
        assert tv_config.provider_config != finviz_config.provider_config

        # Different filter implementations
        tv_fields = {f["field"] for f in tv_config.filters}
        finviz_fields = {f["field"] for f in finviz_config.filters}
        assert tv_fields != finviz_fields
