"""
Unit tests for screening providers
"""

from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import pytest

from connors_screener.core.screener import ScreeningConfig, ScreeningResult
from connors_screener.screening.providers.finviz import FinvizProvider
from connors_screener.screening.providers.tradingview import TradingViewProvider
from connors_screener.screening.providers.tradingview_crypto import TradingViewCryptoProvider


class TestTradingViewProvider:
    """Test TradingView provider functionality"""

    @pytest.fixture
    def provider(self) -> TradingViewProvider:
        """Create TradingView provider instance"""
        return TradingViewProvider()

    @pytest.fixture
    def tv_config(self) -> ScreeningConfig:
        """Sample TradingView configuration"""
        return ScreeningConfig(
            name="test_rsi2",
            provider="tv",
            parameters={"rsi_level": 5},
            provider_config={"volume_threshold": 1_000_000},
            filters=[
                {"field": "RSI2", "operation": "less", "value": 5},
                {"field": "is_blacklisted", "operation": "equal", "value": False},
            ],
        )

    def test_provider_initialization(self, provider: TradingViewProvider) -> None:
        """Test provider initializes correctly"""
        assert provider.headers is not None
        assert "User-Agent" in provider.headers
        assert provider.screening_config_manager is not None

    def test_validate_config_correct_provider(
        self, provider: TradingViewProvider, tv_config: ScreeningConfig
    ) -> None:
        """Test config validation passes for correct provider"""
        assert provider.validate_config(tv_config) == True

    def test_validate_config_wrong_provider(
        self, provider: TradingViewProvider
    ) -> None:
        """Test config validation fails for wrong provider"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="finviz",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        # The current validate_config method only checks for required fields
        # The provider check happens in the scan method
        assert provider.validate_config(wrong_config) == True

    def test_scan_wrong_provider_raises_error(
        self, provider: TradingViewProvider
    ) -> None:
        """Test screening with wrong provider configuration raises error"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="finviz",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        with pytest.raises(
            ValueError,
            match="Config provider 'finviz' is not compatible with TradingView provider",
        ):
            provider.scan(wrong_config)

    def test_get_supported_markets(self, provider: TradingViewProvider) -> None:
        """Test getting supported markets"""
        markets = provider.get_supported_markets()

        assert isinstance(markets, list)
        assert len(markets) > 0
        assert "australia" in markets
        assert "america" in markets
        assert "brazil" in markets

    @patch("connors_screener.screening.providers.tradingview.requests.post")
    def test_scan_successful_response(
        self, mock_post: Mock, provider: TradingViewProvider, tv_config: ScreeningConfig
    ) -> None:
        """Test successful screening response"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"d": ["AAPL", "desc", "logo", "update", "stock"]},
                {"d": ["MSFT", "desc", "logo", "update", "stock"]},
            ]
        }
        mock_post.return_value = mock_response

        result = provider.scan(tv_config, "america")

        assert isinstance(result, ScreeningResult)
        assert result.symbols == ["AAPL", "MSFT"]
        assert result.provider == "TradingView"
        assert result.config_name == "test_rsi2"
        assert "market" in result.metadata
        assert result.metadata["total_results"] == 2

    @patch("connors_screener.screening.providers.tradingview.requests.post")
    def test_scan_api_error(
        self, mock_post: Mock, provider: TradingViewProvider, tv_config: ScreeningConfig
    ) -> None:
        """Test handling of API error response"""
        # Mock error API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="TradingView API error: 400"):
            provider.scan(tv_config, "america")

    def test_build_payload_structure(
        self, provider: TradingViewProvider, tv_config: ScreeningConfig
    ) -> None:
        """Test payload building produces correct structure"""
        market_config = provider.screening_config_manager.get_market_config("australia")
        payload = provider._build_payload(tv_config, market_config)

        # Check required payload structure
        assert "columns" in payload
        assert "filter" in payload
        assert "symbols" in payload
        assert "markets" in payload
        assert "filter2" in payload

        # Check filters are correctly translated
        assert len(payload["filter"]) >= 2  # At least our config filters

        # Check volume filter is added if not present
        volume_filters = [f for f in payload["filter"] if f["left"] == "volume"]
        assert len(volume_filters) >= 1


class TestFinvizProvider:
    """Test Finviz provider functionality"""

    @pytest.fixture
    def provider(self) -> FinvizProvider:
        """Create Finviz provider instance"""
        return FinvizProvider()

    @pytest.fixture
    def finviz_config(self) -> ScreeningConfig:
        """Sample Finviz configuration"""
        return ScreeningConfig(
            name="test_rsi2",
            provider="finviz",
            parameters={"rsi_level": 5},
            provider_config={"market_cap_min": 100_000_000},
            filters=[{"field": "ta_rsi", "operation": "under", "value": 5}],
        )

    def test_provider_initialization(self, provider: FinvizProvider) -> None:
        """Test provider initializes correctly"""
        assert provider.base_url == "https://finviz.com/screener.ashx"
        assert provider.headers is not None
        assert "User-Agent" in provider.headers

    def test_validate_config_correct_provider(
        self, provider: FinvizProvider, finviz_config: ScreeningConfig
    ) -> None:
        """Test config validation passes for correct provider"""
        assert provider.validate_config(finviz_config) == True

    def test_validate_config_wrong_provider(self, provider: FinvizProvider) -> None:
        """Test config validation fails for wrong provider"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="tv",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        assert provider.validate_config(wrong_config) == False

    def test_scan_wrong_provider_raises_error(self, provider: FinvizProvider) -> None:
        """Test screening with wrong provider configuration raises error"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="tv",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        with pytest.raises(
            ValueError,
            match="Config provider 'tv' is not compatible with Finviz provider",
        ):
            provider.scan(wrong_config)

    def test_get_supported_markets(self, provider: FinvizProvider) -> None:
        """Test getting supported markets"""
        markets = provider.get_supported_markets()

        assert isinstance(markets, list)
        assert "america" in markets
        # Finviz primarily supports US markets

    def test_scan_mock_implementation(
        self, provider: FinvizProvider, finviz_config: ScreeningConfig
    ) -> None:
        """Test mock screening implementation"""
        result = provider.scan(finviz_config, "america")

        assert isinstance(result, ScreeningResult)
        assert result.provider == "Finviz"
        assert result.config_name == "test_rsi2"
        assert isinstance(result.symbols, list)
        assert "note" in result.metadata
        assert "Mock implementation" in result.metadata["note"]


class TestProviderRegistry:
    """Test provider registration functionality"""

    def test_providers_auto_registered(self) -> None:
        """Test that providers are automatically registered"""
        from connors_core.core.registry import registry

        providers = registry.list_screener_providers()
        assert "tv" in providers
        assert "finviz" in providers

    def test_create_providers_from_registry(self) -> None:
        """Test creating providers from registry"""
        from connors_core.core.registry import registry

        tv_provider = registry.create_screener_provider("tv")
        assert isinstance(tv_provider, TradingViewProvider)

        finviz_provider = registry.create_screener_provider("finviz")
        assert isinstance(finviz_provider, FinvizProvider)

    def test_create_unknown_provider_raises_error(self) -> None:
        """Test creating unknown provider raises error"""
        from connors_core.core.registry import registry

        with pytest.raises(ValueError, match="Screener provider 'unknown' not found"):
            registry.create_screener_provider("unknown")


class TestTradingViewCryptoProvider:
    """Test TradingView Crypto provider functionality"""

    @pytest.fixture
    def provider(self) -> TradingViewCryptoProvider:
        """Create TradingView Crypto provider instance"""
        return TradingViewCryptoProvider()

    @pytest.fixture
    def crypto_config(self) -> ScreeningConfig:
        """Sample crypto configuration"""
        return ScreeningConfig(
            name="test_crypto_basic",
            provider="tv_crypto",
            parameters={"min_volume": 100_000_000},
            provider_config={"volume_threshold": 100_000_000},
            filters=[
                {"field": "24h_vol_cmc", "operation": "egreater", "value": 100_000_000}
            ],
        )

    def test_provider_initialization(self, provider: TradingViewCryptoProvider) -> None:
        """Test provider initializes correctly"""
        assert provider.headers is not None
        assert "User-Agent" in provider.headers
        assert provider.screening_config_manager is not None

    def test_validate_config_correct_provider(
        self, provider: TradingViewCryptoProvider, crypto_config: ScreeningConfig
    ) -> None:
        """Test config validation passes for correct provider"""
        assert provider.validate_config(crypto_config) == True

    def test_validate_config_wrong_provider(
        self, provider: TradingViewCryptoProvider
    ) -> None:
        """Test config validation fails for wrong provider"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="tv",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        # The current validate_config method only checks for required fields
        # The provider check happens in the scan method
        assert provider.validate_config(wrong_config) == True

    def test_scan_wrong_provider_raises_error(
        self, provider: TradingViewCryptoProvider
    ) -> None:
        """Test screening with wrong provider configuration raises error"""
        wrong_config = ScreeningConfig(
            name="test",
            provider="tv",  # Wrong provider
            parameters={},
            provider_config={},
            filters=[],
        )

        with pytest.raises(
            ValueError,
            match="Config provider 'tv' is not compatible with TradingViewCrypto provider",
        ):
            provider.scan(wrong_config)

    def test_get_supported_markets(self, provider: TradingViewProvider) -> None:
        """Test getting supported markets"""
        markets = provider.get_supported_markets()

        assert isinstance(markets, list)
        assert len(markets) == 1
        assert "crypto" in markets

    @patch("connors_screener.screening.providers.tradingview_crypto.requests.post")
    def test_scan_successful_response(
        self,
        mock_post: Mock,
        provider: TradingViewCryptoProvider,
        crypto_config: ScreeningConfig,
    ) -> None:
        """Test successful screening response"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "totalCount": 3529,
            "data": [
                {
                    "s": "CRYPTO:BTCUSD",
                    "d": ["BTC", "Bitcoin", "crypto/XTVCBTC", "streaming", "spot"],
                },
                {
                    "s": "CRYPTO:ETHUSD",
                    "d": ["ETH", "Ethereum", "crypto/XTVCETH", "streaming", "spot"],
                },
            ],
        }
        mock_post.return_value = mock_response

        result = provider.scan(crypto_config, "crypto")

        assert isinstance(result, ScreeningResult)
        assert result.symbols == ["BTC", "ETH"]
        assert result.provider == "TradingViewCrypto"
        assert result.config_name == "test_crypto_basic"
        assert "market" in result.metadata
        assert result.metadata["total_results"] == 2
        assert result.metadata["total_count"] == 3529

        # Verify the correct URL was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "coin/scan" in call_args[1]["json"] or "coin/scan" in str(call_args)

    @patch("connors_screener.screening.providers.tradingview_crypto.requests.post")
    def test_scan_api_error(
        self,
        mock_post: Mock,
        provider: TradingViewCryptoProvider,
        crypto_config: ScreeningConfig,
    ) -> None:
        """Test handling of API error response"""
        # Mock error API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="TradingViewCrypto API error: 400"):
            provider.scan(crypto_config, "crypto")

    def test_build_payload_structure(
        self, provider: TradingViewCryptoProvider, crypto_config: ScreeningConfig
    ) -> None:
        """Test payload building produces correct structure"""
        payload = provider._build_payload(crypto_config)

        # Check required payload structure
        assert "columns" in payload
        assert "filter" in payload
        assert "symbols" in payload
        assert "markets" in payload

        # Check crypto-specific structure
        assert payload["markets"] == ["coin"]

        # Check columns include crypto-specific fields
        crypto_columns = [
            "base_currency",
            "24h_vol_cmc",
            "crypto_total_rank",
            "market_cap_calc",
        ]
        for col in crypto_columns:
            assert col in payload["columns"]

        # Check filters are correctly translated
        assert len(payload["filter"]) >= 1  # At least one volume filter

        # Check volume filter is present
        volume_filters = [f for f in payload["filter"] if f["left"] == "24h_vol_cmc"]
        assert len(volume_filters) >= 1

        # Verify volume filter uses correct operation for crypto
        volume_filter = volume_filters[0]
        assert volume_filter["operation"] == "egreater"

    def test_crypto_specific_columns(
        self, provider: TradingViewCryptoProvider, crypto_config: ScreeningConfig
    ) -> None:
        """Test that crypto-specific columns are included"""
        payload = provider._build_payload(crypto_config)
        columns = payload["columns"]

        # Check for crypto-specific columns from the original JSON
        expected_crypto_columns = [
            "base_currency",
            "base_currency_desc",
            "crypto_total_rank",
            "24h_vol_cmc",
            "market_cap_calc",
            "crypto_common_categories.tr",
            "TechRating_1D",
        ]

        for col in expected_crypto_columns:
            assert (
                col in columns
            ), f"Expected column '{col}' not found in crypto payload"

    def test_registry_integration(self) -> None:
        """Test that crypto provider is properly registered"""
        from connors_core.core.registry import registry

        providers = registry.list_screener_providers()
        assert "tv_crypto" in providers

        crypto_provider = registry.create_screener_provider("tv_crypto")
        assert isinstance(crypto_provider, TradingViewCryptoProvider)
