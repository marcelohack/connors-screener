"""
Unit tests for screening core functionality
"""

from dataclasses import dataclass
from typing import Any

import pytest

from connors_core.core.registry import ComponentRegistry
from connors_screener.core.screener import ScreeningConfig, ScreeningResult, StockData


class TestScreeningConfig:
    """Test ScreeningConfig dataclass"""

    def test_screening_config_creation(self) -> None:
        """Test creation of ScreeningConfig"""
        config = ScreeningConfig(
            name="test_config",
            provider="tv",
            parameters={"rsi_level": 5},
            provider_config={"volume_threshold": 1000000},
            filters=[{"field": "RSI2", "operation": "less", "value": 5}],
            description="Test configuration",
        )

        assert config.name == "test_config"
        assert config.provider == "tv"
        assert config.parameters["rsi_level"] == 5
        assert config.provider_config["volume_threshold"] == 1000000
        assert len(config.filters) == 1
        assert config.description == "Test configuration"

    def test_screening_config_defaults(self) -> None:
        """Test ScreeningConfig with default description"""
        config = ScreeningConfig(
            name="test_config",
            provider="tv",
            parameters={},
            provider_config={},
            filters=[],
        )

        assert config.description == ""


class TestScreeningResult:
    """Test ScreeningResult dataclass"""

    def test_screening_result_creation(self) -> None:
        """Test creation of ScreeningResult"""
        stock_data = [
            StockData(symbol="AAPL", name="Apple Inc.", price=150.0),
            StockData(symbol="MSFT", name="Microsoft Corp.", price=300.0)
        ]

        result = ScreeningResult(
            symbols=["AAPL", "MSFT"],
            data=stock_data,
            metadata={"market": "america", "filters_applied": 2},
            provider="TradingView",
            config_name="rsi2",
            timestamp="2023-01-01T00:00:00",
        )

        assert result.symbols == ["AAPL", "MSFT"]
        assert len(result.data) == 2
        assert result.data[0].symbol == "AAPL"
        assert result.data[1].symbol == "MSFT"
        assert result.metadata["market"] == "america"
        assert result.provider == "TradingView"
        assert result.config_name == "rsi2"
        assert result.timestamp == "2023-01-01T00:00:00"


class TestComponentRegistryScreening:
    """Test ComponentRegistry screening functionality"""

    @pytest.fixture
    def registry(self) -> ComponentRegistry:
        """Create a fresh registry for each test"""
        return ComponentRegistry()

    @pytest.fixture
    def sample_config(self) -> ScreeningConfig:
        """Sample screening configuration"""
        return ScreeningConfig(
            name="test_rsi2",
            provider="tv",
            parameters={"rsi_level": 5},
            provider_config={"volume_threshold": 1000000},
            filters=[{"field": "RSI2", "operation": "less", "value": 5}],
        )

    def test_register_screening_config(
        self, registry: ComponentRegistry, sample_config: ScreeningConfig
    ) -> None:
        """Test registering screening configuration"""
        registry.register_screening_config("tv", "test_rsi2", sample_config)

        retrieved_config = registry.get_screening_config("tv", "test_rsi2")
        assert retrieved_config.name == "test_rsi2"
        assert retrieved_config.provider == "tv"

    def test_get_screening_config_provider_not_found(
        self, registry: ComponentRegistry
    ) -> None:
        """Test getting config for non-existent provider"""
        with pytest.raises(
            ValueError, match="No configs registered for provider 'unknown'"
        ):
            registry.get_screening_config("unknown", "test_config")

    def test_get_screening_config_config_not_found(
        self, registry: ComponentRegistry, sample_config: ScreeningConfig
    ) -> None:
        """Test getting non-existent config for existing provider"""
        registry.register_screening_config("tv", "existing_config", sample_config)

        with pytest.raises(
            ValueError, match="Config 'unknown_config' not found for provider 'tv'"
        ):
            registry.get_screening_config("tv", "unknown_config")

    def test_list_screening_configs_all(
        self, registry: ComponentRegistry, sample_config: ScreeningConfig
    ) -> None:
        """Test listing all screening configurations"""
        registry.register_screening_config("tv", "rsi2", sample_config)
        registry.register_screening_config("finviz", "momentum", sample_config)

        configs = registry.list_screening_configs()

        assert "tv" in configs
        assert "finviz" in configs
        assert "rsi2" in configs["tv"]
        assert "momentum" in configs["finviz"]

    def test_list_screening_configs_by_provider(
        self, registry: ComponentRegistry, sample_config: ScreeningConfig
    ) -> None:
        """Test listing configs for specific provider"""
        registry.register_screening_config("tv", "rsi2", sample_config)
        registry.register_screening_config("tv", "rsi2_relaxed", sample_config)

        configs = registry.list_screening_configs("tv")

        assert len(configs) == 1
        assert "tv" in configs
        assert len(configs["tv"]) == 2
        assert "rsi2" in configs["tv"]
        assert "rsi2_relaxed" in configs["tv"]

    def test_list_screening_configs_empty_provider(
        self, registry: ComponentRegistry
    ) -> None:
        """Test listing configs for provider with no configs"""
        configs = registry.list_screening_configs("empty_provider")

        assert configs == {"empty_provider": []}

    def test_multiple_configs_same_provider(self, registry: ComponentRegistry) -> None:
        """Test registering multiple configs for same provider"""
        config1 = ScreeningConfig(
            name="rsi2",
            provider="tv",
            parameters={"rsi_level": 5},
            provider_config={},
            filters=[],
        )

        config2 = ScreeningConfig(
            name="rsi2_relaxed",
            provider="tv",
            parameters={"rsi_level": 10},
            provider_config={},
            filters=[],
        )

        registry.register_screening_config("tv", "rsi2", config1)
        registry.register_screening_config("tv", "rsi2_relaxed", config2)

        retrieved1 = registry.get_screening_config("tv", "rsi2")
        retrieved2 = registry.get_screening_config("tv", "rsi2_relaxed")

        assert retrieved1.parameters["rsi_level"] == 5
        assert retrieved2.parameters["rsi_level"] == 10
