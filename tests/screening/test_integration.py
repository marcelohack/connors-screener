"""
Integration tests for the complete screening system
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from connors_core.core.registry import registry
from connors_screener.screening.configs.finviz_rsi2 import FinvizRSI2Configs
from connors_screener.screening.configs.tradingview_rsi2 import TradingViewRSI2Configs


class TestScreeningSystemIntegration:
    """Test complete screening system integration"""

    def test_configs_auto_registered_on_import(self) -> None:
        """Test that configs are automatically registered when modules are imported"""
        # Configs should be auto-registered via module imports
        tv_configs = registry.list_screening_configs("tv")
        finviz_configs = registry.list_screening_configs("finviz")

        assert "tv" in tv_configs
        assert "finviz" in finviz_configs
        assert len(tv_configs["tv"]) >= 3  # rsi2, rsi2_high_volume, rsi2_relaxed
        assert len(finviz_configs["finviz"]) >= 2  # rsi2, rsi2_large_cap

    def test_provider_config_relationship(self) -> None:
        """Test that providers can only use their own configurations"""
        # Get TradingView provider and Finviz config
        tv_provider = registry.create_screener_provider("tv")
        finviz_config = registry.get_screening_config("finviz", "rsi2")

        # Should raise error when using wrong provider's config
        with pytest.raises(
            ValueError,
            match="Config provider 'finviz' is not compatible with TradingView provider",
        ):
            tv_provider.scan(finviz_config)

    def test_cross_provider_config_isolation(self) -> None:
        """Test that same strategy configs are isolated by provider"""
        tv_rsi2 = registry.get_screening_config("tv", "rsi2")
        finviz_rsi2 = registry.get_screening_config("finviz", "rsi2")

        # Same config name, different providers
        assert tv_rsi2.name == finviz_rsi2.name == "rsi2"
        assert tv_rsi2.provider == "tv"
        assert finviz_rsi2.provider == "finviz"

        # Different implementations
        assert tv_rsi2.provider_config != finviz_rsi2.provider_config
        assert tv_rsi2.filters != finviz_rsi2.filters

    @patch("connors_screener.screening.providers.tradingview.requests.post")
    def test_end_to_end_screening_flow(self, mock_post: Mock) -> None:
        """Test complete screening flow from registry to results"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"d": ["TEST1", "desc1", "logo1", "update", "stock"]},
                {"d": ["TEST2", "desc2", "logo2", "update", "stock"]},
            ]
        }
        mock_post.return_value = mock_response

        # Get provider and config from registry
        provider = registry.create_screener_provider("tv")
        config = registry.get_screening_config("tv", "rsi2")

        # Execute screening
        result = provider.scan(config, "australia")

        # Verify results
        assert result.symbols == ["TEST1", "TEST2"]
        assert result.provider == "TradingView"
        assert result.config_name == "rsi2"
        assert result.metadata["total_results"] == 2

    def test_registry_list_all_configs(self) -> None:
        """Test listing all configurations across providers"""
        all_configs = registry.list_screening_configs()

        assert isinstance(all_configs, dict)
        assert "tv" in all_configs
        assert "finviz" in all_configs

        # Each provider should have multiple configs
        assert len(all_configs["tv"]) >= 3
        assert len(all_configs["finviz"]) >= 2

    def test_config_naming_convention(self) -> None:
        """Test that RSI2 config names follow rsi2 prefix convention (not lcrsi2)"""
        tv_configs = registry.list_screening_configs("tv")["tv"]
        finviz_configs = registry.list_screening_configs("finviz")["finviz"]

        # RSI2 config names should start with 'rsi2', not 'lcrsi2'
        rsi2_configs = [name for name in tv_configs if "rsi2" in name]
        for config_name in rsi2_configs:
            assert config_name.startswith("rsi2")
            assert not config_name.startswith("lcrsi2")

        finviz_rsi2_configs = [name for name in finviz_configs if "rsi2" in name]
        for config_name in finviz_rsi2_configs:
            assert config_name.startswith("rsi2")
            assert not config_name.startswith("lcrsi2")

        # Verify we have other types of configs too
        assert any("momentum" in name for name in tv_configs)
        assert any("value" in name for name in tv_configs)

    def test_provider_specific_field_names(self) -> None:
        """Test that providers use their own field naming conventions"""
        tv_config = registry.get_screening_config("tv", "rsi2")
        finviz_config = registry.get_screening_config("finviz", "rsi2")

        # TradingView uses "RSI2" field
        tv_fields = [f["field"] for f in tv_config.filters]
        assert "RSI2" in tv_fields

        # Finviz uses "ta_rsi" field
        finviz_fields = [f["field"] for f in finviz_config.filters]
        assert "ta_rsi" in finviz_fields

        # Fields should be different
        assert set(tv_fields) != set(finviz_fields)

    def test_provider_specific_operations(self) -> None:
        """Test that providers use their own operation conventions"""
        tv_config = registry.get_screening_config("tv", "rsi2")
        finviz_config = registry.get_screening_config("finviz", "rsi2")

        # Find RSI filters
        tv_rsi_filter = next(
            (f for f in tv_config.filters if "RSI" in f["field"]), None
        )
        finviz_rsi_filter = next(
            (f for f in finviz_config.filters if "rsi" in f["field"]), None
        )

        assert tv_rsi_filter is not None
        assert finviz_rsi_filter is not None

        # TradingView uses "less", Finviz uses "under"
        assert tv_rsi_filter["operation"] == "less"
        assert finviz_rsi_filter["operation"] == "under"

    def test_error_handling_consistency(self) -> None:
        """Test consistent error handling across the system"""
        # Test non-existent provider
        with pytest.raises(
            ValueError, match="Screener provider 'nonexistent' not found"
        ):
            registry.create_screener_provider("nonexistent")

        # Test non-existent config for existing provider
        with pytest.raises(
            ValueError, match="Config 'nonexistent' not found for provider 'tv'"
        ):
            registry.get_screening_config("tv", "nonexistent")

        # Test non-existent provider for config
        with pytest.raises(
            ValueError, match="No configs registered for provider 'nonexistent'"
        ):
            registry.get_screening_config("nonexistent", "rsi2")


class TestConfigDescriptions:
    """Test that all configurations have meaningful descriptions"""

    def test_all_tv_configs_have_descriptions(self) -> None:
        """Test that all TradingView configs have non-empty descriptions"""
        for config_name in TradingViewRSI2Configs.list_configs():
            config = TradingViewRSI2Configs.get_config(config_name)
            assert (
                config.description != ""
            ), f"Config '{config_name}' missing description"
            assert (
                len(config.description) > 10
            ), f"Config '{config_name}' description too short"

    def test_all_finviz_configs_have_descriptions(self) -> None:
        """Test that all Finviz configs have non-empty descriptions"""
        for config_name in FinvizRSI2Configs.list_configs():
            config = FinvizRSI2Configs.get_config(config_name)
            assert (
                config.description != ""
            ), f"Config '{config_name}' missing description"
            assert (
                len(config.description) > 10
            ), f"Config '{config_name}' description too short"
