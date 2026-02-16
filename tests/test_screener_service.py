"""
Unit tests for ScreenerService
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

from connors_screener.screening.post_filters import _post_filters

import pytest

from connors_screener.config.screening import MarketScreeningConfig
from connors_screener.core.screener import ScreeningConfig, ScreeningResult, StockData
from connors_screener.services.screener_service import PostFilter, ScreenerService


class TestScreenerService:
    """Test suite for ScreenerService"""

    @pytest.fixture
    def service(self):
        """Create a ScreenerService instance for testing"""
        return ScreenerService()

    @pytest.fixture
    def mock_screening_config(self):
        """Mock screening configuration"""
        filters = [
            {"field": "rsi", "operation": "less_than", "value": 30},
            {"field": "volume", "operation": "greater_than", "value": 1000000},
        ]
        return ScreeningConfig(
            name="test_config",
            description="Test configuration",
            provider="tv",
            parameters={"rsi_level": 30, "volume_threshold": 1000000},
            filters=filters,
            provider_config={"test": "config"},
        )

    @pytest.fixture
    def mock_screening_result(self):
        """Mock screening result"""
        stock_data = [
            StockData(symbol="AAPL", name="Apple Inc.", price=150.0),
            StockData(symbol="GOOGL", name="Alphabet Inc.", price=140.0),
            StockData(symbol="MSFT", name="Microsoft Corp.", price=300.0)
        ]
        return ScreeningResult(
            symbols=["AAPL", "GOOGL", "MSFT"],
            data=stock_data,
            provider="tv",
            config_name="test_config",
            timestamp="2024-01-01T00:00:00Z",
            metadata={"market": "america", "filters_applied": 2, "total_scanned": 1000},
        )

    @pytest.fixture
    def mock_market_config(self):
        """Mock market configuration"""
        return MarketScreeningConfig(
            name="test_market",
            symbolset="TEST:MARKET",
            default_volume=1000000,
            market_identifier="test",
        )

    def test_init(self, service):
        """Test service initialization"""
        assert service is not None
        assert hasattr(service, "registry")
        assert hasattr(service, "screening_config_manager")
        assert hasattr(service, "logger")

    def test_get_providers(self, service):
        """Test getting available providers"""
        with patch.object(
            service.registry,
            "list_screener_providers",
            return_value=["tv", "finviz", "tv_crypto"],
        ) as mock_method:
            providers = service.get_providers()

            assert providers == ["tv", "finviz", "tv_crypto"]
            mock_method.assert_called_once()

    def test_get_providers_error(self, service):
        """Test getting providers when an error occurs"""
        with patch.object(
            service.registry,
            "list_screener_providers",
            side_effect=Exception("Registry error"),
        ):
            providers = service.get_providers()

            assert providers == []

    def test_get_provider_info(self, service):
        """Test getting provider information"""
        with patch.object(service, "get_providers", return_value=["tv", "finviz"]):
            provider_info = service.get_provider_info()

            assert "tv" in provider_info
            assert "finviz" in provider_info
            assert "tv_crypto" not in provider_info  # Not in available providers

            assert provider_info["tv"]["name"] == "TradingView"
            assert provider_info["finviz"]["asset_types"] == "US Stocks"

    def test_get_configs_for_provider(self, service):
        """Test getting configurations for a provider"""
        with patch.object(
            service.registry,
            "list_screening_configs",
            return_value={"tv": ["rsi2", "momentum"]},
        ) as mock_method:
            configs = service.get_configs_for_provider("tv")

            assert configs == ["rsi2", "momentum"]
            mock_method.assert_called_once_with("tv")

    def test_get_config_info(self, service, mock_screening_config):
        """Test getting configuration information"""
        with patch.object(
            service.registry, "get_screening_config", return_value=mock_screening_config
        ):
            config_info = service.get_config_info("tv", "test_config")

            assert config_info["name"] == "test_config"
            assert config_info["description"] == "Test configuration"
            assert config_info["provider"] == "tv"
            assert config_info["parameters"] == {
                "rsi_level": 30,
                "volume_threshold": 1000000,
            }
            assert len(config_info["filters"]) == 2
            assert config_info["filters"][0]["field"] == "rsi"

    def test_get_available_markets(self, service):
        """Test getting available markets"""
        with patch.object(
            service.screening_config_manager,
            "list_markets",
            return_value=["america", "australia", "brazil"],
        ):
            markets = service.get_available_markets()

            assert markets == ["america", "australia", "brazil"]

    def test_get_market_info(self, service, mock_market_config):
        """Test getting market information"""
        with patch.object(
            service.screening_config_manager,
            "get_market_config",
            return_value=mock_market_config,
        ):
            market_info = service.get_market_info("test_market")

            assert market_info["name"] == "test_market"
            assert market_info["symbolset"] == "TEST:MARKET"
            assert market_info["default_volume"] == 1000000
            assert market_info["market_identifier"] == "test"

    def test_get_all_configs(self, service):
        """Test getting all configurations"""
        mock_configs = {"tv": ["rsi2", "momentum"], "finviz": ["value"]}
        with patch.object(
            service.registry, "list_screening_configs", return_value=mock_configs
        ):
            configs = service.get_all_configs()

            assert configs == mock_configs

    def test_get_parameter_info(self, service, mock_screening_config):
        """Test getting parameter information"""
        with (
            patch.object(
                service.registry,
                "get_screening_config",
                return_value=mock_screening_config,
            ),
            patch(
                "connors_screener.services.screener_service.get_parameter_info",
                return_value="Parameter info string",
            ),
        ):
            param_info = service.get_parameter_info("tv", "test_config")

            assert param_info == "Parameter info string"

    @patch("connors_screener.services.screener_service.config_loader")
    def test_create_example_config_file(self, mock_config_loader, service):
        """Test creating example configuration file"""
        mock_config_loader.create_example_config_file.return_value = None

        result = service.create_example_config_file(Path("/tmp/test.json"), "json")

        assert result is True
        mock_config_loader.create_example_config_file.assert_called_once_with(
            Path("/tmp/test.json"), "json"
        )

    @patch("connors_screener.services.screener_service.config_loader")
    def test_create_example_config_file_error(self, mock_config_loader, service):
        """Test creating example configuration file with error"""
        mock_config_loader.create_example_config_file.side_effect = Exception(
            "File error"
        )

        result = service.create_example_config_file(Path("/tmp/test.json"), "json")

        assert result is False

    @patch("connors_screener.services.screener_service.config_loader")
    def test_load_external_config_file(self, mock_config_loader, service):
        """Test loading external configuration file"""
        mock_config_loader.register_configs_from_file.return_value = ["custom_config"]

        configs = service.load_external_config_file(Path("/tmp/config.json"))

        assert configs == ["custom_config"]
        mock_config_loader.register_configs_from_file.assert_called_once_with(
            Path("/tmp/config.json")
        )

    def test_contains_substring(self, service):
        """Test substring checking utility"""
        assert service.contains_substring("crypto_basic", "crypto") is True
        assert service.contains_substring("CRYPTO_BASIC", "crypto") is True
        assert service.contains_substring("rsi2", "crypto") is False

    def test_run_screening_basic(
        self, service, mock_screening_config, mock_screening_result
    ):
        """Test basic screening execution"""
        mock_provider = Mock()
        mock_provider.scan.return_value = mock_screening_result

        with (
            patch.object(
                service.registry, "create_screener_provider", return_value=mock_provider
            ),
            patch.object(
                service.registry,
                "get_screening_config",
                return_value=mock_screening_config,
            ),
            patch(
                "connors_screener.services.screener_service.apply_parameter_overrides",
                return_value=mock_screening_config,
            ),
        ):
            result = service.run_screening("tv", "test_config", "america")

            assert result == mock_screening_result
            # scan is called with config, market, sort_by, sort_order
            mock_provider.scan.assert_called_once_with(mock_screening_config, "america", "close", "asc")

    def test_run_screening_with_parameters(
        self, service, mock_screening_config, mock_screening_result
    ):
        """Test screening with parameter overrides"""
        mock_provider = Mock()
        mock_provider.scan.return_value = mock_screening_result

        with (
            patch.object(
                service.registry, "create_screener_provider", return_value=mock_provider
            ),
            patch.object(
                service.registry,
                "get_screening_config",
                return_value=mock_screening_config,
            ),
            patch(
                "connors_screener.services.screener_service.apply_parameter_overrides",
                return_value=mock_screening_config,
            ) as mock_apply,
        ):
            parameters = {"rsi_level": 25, "volume_threshold": 2000000}
            result = service.run_screening(
                "tv", "test_config", "america", parameters=parameters
            )

            assert result == mock_screening_result
            mock_apply.assert_called_once_with(mock_screening_config, parameters)

    def test_run_screening_with_parameter_string(
        self, service, mock_screening_config, mock_screening_result
    ):
        """Test screening with parameter string"""
        mock_provider = Mock()
        mock_provider.scan.return_value = mock_screening_result

        with (
            patch.object(
                service.registry, "create_screener_provider", return_value=mock_provider
            ),
            patch.object(
                service.registry,
                "get_screening_config",
                return_value=mock_screening_config,
            ),
            patch(
                "connors_screener.services.screener_service.parse_parameter_string",
                return_value={"rsi_level": 25},
            ) as mock_parse,
            patch(
                "connors_screener.services.screener_service.apply_parameter_overrides",
                return_value=mock_screening_config,
            ) as mock_apply,
        ):
            result = service.run_screening(
                "tv", "test_config", "america", parameter_string="rsi_level:25"
            )

            assert result == mock_screening_result
            mock_parse.assert_called_once_with("rsi_level:25")
            mock_apply.assert_called_once_with(mock_screening_config, {"rsi_level": 25})

    def test_run_screening_error(self, service):
        """Test screening with error"""
        with patch.object(
            service.registry,
            "create_screener_provider",
            side_effect=Exception("Provider error"),
        ):
            with pytest.raises(Exception) as exc_info:
                service.run_screening("invalid", "test_config")

            assert "Provider error" in str(exc_info.value)

    def test_create_external_config_template(self, service):
        """Test creating external configuration template"""
        template = service.create_external_config_template()

        assert "configurations" in template
        assert len(template["configurations"]) == 1
        config = template["configurations"][0]
        assert config["name"] == "custom_momentum"
        assert config["provider"] == "tv"
        assert "parameters" in config
        assert "filters" in config

    def test_load_external_config(self, service):
        """Test loading external configuration"""
        config_data = {
            "configurations": [
                {
                    "name": "test_config",
                    "provider": "tv",
                    "description": "Test config",
                    "parameters": {"test": "value"},
                }
            ]
        }

        with patch(
            "connors_screener.screening.config_loader.ScreeningConfigLoader.register_configs_from_file"
        ):
            result = service.load_external_config(config_data, "test_config")

            assert result is not None
            assert result["name"] == "test_config"
            assert result["provider"] == "tv"

    def test_load_external_config_not_found(self, service):
        """Test loading external configuration that doesn't exist"""
        config_data = {"configurations": []}

        with patch(
            "connors_screener.screening.config_loader.ScreeningConfigLoader.register_configs_from_file"
        ):
            result = service.load_external_config(config_data, "missing_config")

            assert result is None

    def test_parameter_validation(self, service):
        """Test parameter validation in various methods"""
        # Test missing provider
        with pytest.raises(ValueError) as exc_info:
            service.get_configs_for_provider("")
        assert "Missing required parameters" in str(exc_info.value)

        # Test missing config
        with pytest.raises(ValueError) as exc_info:
            service.get_config_info("tv", "")
        assert "Missing required parameters" in str(exc_info.value)

        # Test missing parameters for run_screening
        with pytest.raises(ValueError) as exc_info:
            service.run_screening("", "test_config")
        assert "Missing required parameters" in str(exc_info.value)


class TestScreenerServiceIntegration:
    """Integration tests that use real components where possible"""

    @pytest.fixture
    def service(self):
        """Create a ScreenerService instance for integration testing"""
        return ScreenerService()

    def test_service_initialization_integration(self, service):
        """Test that service initializes with real components"""
        # These should work with the actual registry and config manager
        providers = service.get_providers()
        assert isinstance(providers, list)

        markets = service.get_available_markets()
        assert isinstance(markets, list)
        assert len(markets) > 0

    def test_provider_info_integration(self, service):
        """Test provider info with real providers"""
        provider_info = service.get_provider_info()
        assert isinstance(provider_info, dict)

        # Should contain info for available providers only
        for provider, info in provider_info.items():
            assert "name" in info
            assert "description" in info

    def test_config_template_creation(self, service):
        """Test creating config template"""
        template = service.create_external_config_template()

        # Validate template structure
        assert "configurations" in template
        assert isinstance(template["configurations"], list)
        assert len(template["configurations"]) > 0

        config = template["configurations"][0]
        required_fields = ["name", "provider", "description", "parameters", "filters"]
        for field in required_fields:
            assert field in config

    @patch("connors_screener.services.screener_service.tempfile.NamedTemporaryFile")
    @patch(
        "connors_screener.screening.config_loader.ScreeningConfigLoader.register_configs_from_file"
    )
    @patch("pathlib.Path.unlink")
    def test_external_config_loading_integration(
        self, mock_unlink, mock_register_configs, mock_temp_file, service
    ):
        """Test external config loading process"""
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.json"

        config_data = {
            "configurations": [
                {
                    "name": "integration_test",
                    "provider": "tv",
                    "description": "Integration test config",
                    "parameters": {"test_param": "value"},
                }
            ]
        }

        result = service.load_external_config(config_data, "integration_test")

        assert result is not None
        assert result["name"] == "integration_test"
        mock_register_configs.assert_called_once()


class TestPostFilter:
    """Tests for the post_filter feature in run_screening"""

    @pytest.fixture
    def service(self):
        return ScreenerService()

    @pytest.fixture
    def screening_config(self):
        return ScreeningConfig(
            name="test_config",
            description="Test",
            provider="tv",
            parameters={"rsi_level": 30, "min_price": 100},
            filters=[],
            provider_config={},
        )

    @pytest.fixture
    def screening_result(self):
        stock_data = [
            StockData(symbol="AAPL", name="Apple", price=150.0, raw_data={"RSI2": 10}),
            StockData(symbol="GOOGL", name="Alphabet", price=140.0, raw_data={"RSI2": 25}),
            StockData(symbol="MSFT", name="Microsoft", price=300.0, raw_data={"RSI2": 50}),
        ]
        return ScreeningResult(
            symbols=["AAPL", "GOOGL", "MSFT"],
            data=stock_data,
            provider="tv",
            config_name="test_config",
            timestamp="2024-01-01T00:00:00Z",
            metadata={"market": "america"},
        )

    def _patch_service(self, service, screening_config, screening_result):
        """Return a context manager that patches registry + apply_parameter_overrides."""
        mock_provider = Mock()
        mock_provider.scan.return_value = screening_result
        return (
            patch.object(
                service.registry, "create_screener_provider", return_value=mock_provider
            ),
            patch.object(
                service.registry, "get_screening_config", return_value=screening_config
            ),
            patch(
                "connors_screener.services.screener_service.apply_parameter_overrides",
                return_value=screening_config,
            ),
        )

    def test_run_screening_no_post_filter(
        self, service, screening_config, screening_result
    ):
        """No filter passed -> result unchanged, no post-filter metadata"""
        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening("tv", "test_config")

        assert result.symbols == ["AAPL", "GOOGL", "MSFT"]
        assert len(result.data) == 3
        assert "post_filter_applied" not in result.metadata

    def test_run_screening_with_post_filter_filters_data(
        self, service, screening_config, screening_result
    ):
        """Filter by price -> correct subset, metadata counts correct"""

        def price_above_145(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return stock.price > 145

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter=price_above_145
            )

        assert result.symbols == ["AAPL", "MSFT"]
        assert len(result.data) == 2
        assert result.metadata["post_filter_applied"] is True
        assert result.metadata["pre_filter_count"] == 3
        assert result.metadata["post_filter_count"] == 2

    def test_run_screening_post_filter_receives_screening_parameters(
        self, service, screening_config, screening_result
    ):
        """Filter context contains ScreeningConfig.parameters"""
        received_contexts: list = []

        def capture_context(stock: StockData, ctx: Dict[str, Any]) -> bool:
            received_contexts.append(dict(ctx))
            return True

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            service.run_screening("tv", "test_config", post_filter=capture_context)

        assert len(received_contexts) == 3
        for ctx in received_contexts:
            assert ctx["rsi_level"] == 30
            assert ctx["min_price"] == 100

    def test_run_screening_post_filter_receives_custom_context(
        self, service, screening_config, screening_result
    ):
        """post_filter_context values are available in context dict"""
        received_contexts: list = []

        def capture_context(stock: StockData, ctx: Dict[str, Any]) -> bool:
            received_contexts.append(dict(ctx))
            return True

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            service.run_screening(
                "tv",
                "test_config",
                post_filter=capture_context,
                post_filter_context={"watchlist": ["AAPL", "MSFT"]},
            )

        for ctx in received_contexts:
            assert ctx["watchlist"] == ["AAPL", "MSFT"]
            # screening params still present
            assert ctx["rsi_level"] == 30

    def test_run_screening_post_filter_context_overrides_parameters(
        self, service, screening_config, screening_result
    ):
        """post_filter_context keys override parameters keys"""
        received_contexts: list = []

        def capture_context(stock: StockData, ctx: Dict[str, Any]) -> bool:
            received_contexts.append(dict(ctx))
            return True

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            service.run_screening(
                "tv",
                "test_config",
                post_filter=capture_context,
                post_filter_context={"rsi_level": 99},
            )

        for ctx in received_contexts:
            assert ctx["rsi_level"] == 99  # overridden

    def test_run_screening_post_filter_removes_all(
        self, service, screening_config, screening_result
    ):
        """Filter returns all False -> empty result, count=0"""

        def reject_all(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return False

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter=reject_all
            )

        assert result.symbols == []
        assert result.data == []
        assert result.metadata["post_filter_count"] == 0
        assert result.metadata["pre_filter_count"] == 3

    def test_run_screening_post_filter_removes_none(
        self, service, screening_config, screening_result
    ):
        """Filter returns all True -> all records kept"""

        def keep_all(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return True

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter=keep_all
            )

        assert result.symbols == ["AAPL", "GOOGL", "MSFT"]
        assert len(result.data) == 3
        assert result.metadata["post_filter_applied"] is True
        assert result.metadata["pre_filter_count"] == 3
        assert result.metadata["post_filter_count"] == 3

    def test_run_screening_post_filter_uses_raw_data(
        self, service, screening_config, screening_result
    ):
        """Filter accesses stock.get_field('RSI2') from raw_data"""

        def rsi2_below_30(stock: StockData, ctx: Dict[str, Any]) -> bool:
            rsi = stock.get_field("RSI2")
            return rsi is not None and rsi < 30

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter=rsi2_below_30
            )

        assert result.symbols == ["AAPL", "GOOGL"]
        assert len(result.data) == 2
        assert result.data[0].get_field("RSI2") == 10
        assert result.data[1].get_field("RSI2") == 25

    def test_run_screening_with_string_post_filter(
        self, service, screening_config
    ):
        """Test passing post_filter as a string name resolves from registry"""
        elephant_raw = {
            "open": 100.0, "high": 120.0, "low": 99.0,
            "ATR": 3.0, "average_volume_30d_calc": 500_000,
        }
        elephant_result = ScreeningResult(
            symbols=["AAPL", "GOOGL", "MSFT"],
            data=[
                StockData(symbol="AAPL", name="Apple", price=118.0,
                          volume=5_000_000, raw_data={**elephant_raw}),
                StockData(symbol="GOOGL", name="Alphabet", price=119.0,
                          volume=4_000_000, raw_data={**elephant_raw}),
                StockData(symbol="MSFT", name="Microsoft", price=118.0,
                          volume=6_000_000, raw_data={**elephant_raw}),
            ],
            provider="tv",
            config_name="test_config",
            timestamp="2024-01-01T00:00:00Z",
            metadata={"market": "america"},
        )
        p1, p2, p3 = self._patch_service(service, screening_config, elephant_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter="elephant_bars"
            )

        assert result.symbols == ["AAPL", "GOOGL", "MSFT"]
        assert len(result.data) == 3
        assert result.metadata["post_filter_applied"] is True

    def test_run_screening_with_unknown_string_post_filter_raises(
        self, service, screening_config, screening_result
    ):
        """Test that unknown string post_filter raises ValueError"""
        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            with pytest.raises(ValueError, match="Post-filter 'nonexistent' not found"):
                service.run_screening(
                    "tv", "test_config", post_filter="nonexistent"
                )

    def test_run_screening_callable_post_filter_still_works(
        self, service, screening_config, screening_result
    ):
        """Test that passing a callable post_filter still works (backward compat)"""

        def price_filter(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return stock.price > 145

        p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
        with p1, p2, p3:
            result = service.run_screening(
                "tv", "test_config", post_filter=price_filter
            )

        assert result.symbols == ["AAPL", "MSFT"]
        assert len(result.data) == 2

    def test_run_screening_string_post_filter_receives_context(
        self, service, screening_config, screening_result
    ):
        """Test that string-based post_filter receives post_filter_context"""
        received_contexts: list = []

        def capture_filter(stock: StockData, ctx: Dict[str, Any]) -> bool:
            received_contexts.append(dict(ctx))
            return True

        _post_filters["test_capture"] = capture_filter

        try:
            p1, p2, p3 = self._patch_service(service, screening_config, screening_result)
            with p1, p2, p3:
                service.run_screening(
                    "tv",
                    "test_config",
                    post_filter="test_capture",
                    post_filter_context={"volume_multiplier": 3.0},
                )

            assert len(received_contexts) == 3
            for ctx in received_contexts:
                assert ctx["volume_multiplier"] == 3.0
                assert ctx["rsi_level"] == 30  # from screening_config.parameters
        finally:
            _post_filters.pop("test_capture", None)


class TestLoadExternalPostFilter:
    """Tests for load_external_post_filter()"""

    @pytest.fixture
    def service(self):
        return ScreenerService()

    def test_load_valid_external_post_filter(self, service, tmp_path):
        """Test loading a valid external post-filter file"""
        filter_file = tmp_path / "my_filter.py"
        filter_file.write_text(
            "def my_filter(stock, ctx):\n"
            "    return stock.price > 100\n"
            "\n"
            "register_post_filter('ext_test_filter', my_filter)\n"
        )

        try:
            names = service.load_external_post_filter(str(filter_file))
            assert names == ["ext_test_filter"]
            assert "ext_test_filter" in _post_filters
        finally:
            _post_filters.pop("ext_test_filter", None)

    def test_load_external_post_filter_multiple(self, service, tmp_path):
        """Test loading a file that registers multiple filters"""
        filter_file = tmp_path / "multi_filter.py"
        filter_file.write_text(
            "def filter_a(stock, ctx):\n"
            "    return True\n"
            "\n"
            "def filter_b(stock, ctx):\n"
            "    return False\n"
            "\n"
            "register_post_filter('ext_multi_a', filter_a)\n"
            "register_post_filter('ext_multi_b', filter_b)\n"
        )

        try:
            names = service.load_external_post_filter(str(filter_file))
            assert sorted(names) == ["ext_multi_a", "ext_multi_b"]
        finally:
            _post_filters.pop("ext_multi_a", None)
            _post_filters.pop("ext_multi_b", None)

    def test_load_external_post_filter_file_not_found(self, service):
        """Test that missing file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError, match="not found"):
            service.load_external_post_filter("/nonexistent/filter.py")

    def test_load_external_post_filter_not_python(self, service, tmp_path):
        """Test that non-.py file raises ValueError"""
        filter_file = tmp_path / "filter.txt"
        filter_file.write_text("not python")

        with pytest.raises(ValueError, match="Python"):
            service.load_external_post_filter(str(filter_file))

    def test_load_external_post_filter_no_registration(self, service, tmp_path):
        """Test that file with no register_post_filter calls raises ValueError"""
        filter_file = tmp_path / "empty_filter.py"
        filter_file.write_text(
            "def my_filter(stock, ctx):\n"
            "    return True\n"
        )

        with pytest.raises(ValueError, match="No post-filters were registered"):
            service.load_external_post_filter(str(filter_file))

    def test_loaded_filter_works_with_run_screening(self, service, tmp_path):
        """Test that externally loaded filter can be used by name in run_screening"""
        filter_file = tmp_path / "price_filter.py"
        filter_file.write_text(
            "def price_filter(stock, ctx):\n"
            "    threshold = ctx.get('min_price', 0)\n"
            "    return stock.price > threshold\n"
            "\n"
            "register_post_filter('ext_price', price_filter)\n"
        )

        try:
            service.load_external_post_filter(str(filter_file))

            stock_data = [
                StockData(symbol="AAPL", price=150.0),
                StockData(symbol="PENNY", price=2.0),
            ]
            mock_result = ScreeningResult(
                symbols=["AAPL", "PENNY"],
                data=stock_data,
                provider="tv",
                config_name="test",
                timestamp="2024-01-01T00:00:00Z",
                metadata={"market": "america"},
            )

            mock_config = ScreeningConfig(
                name="test",
                description="Test",
                provider="tv",
                parameters={},
                filters=[],
                provider_config={},
            )
            mock_provider = Mock()
            mock_provider.scan.return_value = mock_result

            with (
                patch.object(
                    service.registry,
                    "create_screener_provider",
                    return_value=mock_provider,
                ),
                patch.object(
                    service.registry,
                    "get_screening_config",
                    return_value=mock_config,
                ),
                patch(
                    "connors_screener.services.screener_service.apply_parameter_overrides",
                    return_value=mock_config,
                ),
            ):
                result = service.run_screening(
                    "tv",
                    "test",
                    post_filter="ext_price",
                    post_filter_context={"min_price": 100},
                )

            assert result.symbols == ["AAPL"]
            assert len(result.data) == 1
        finally:
            _post_filters.pop("ext_price", None)
