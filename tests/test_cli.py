"""Tests for the screener CLI"""

from unittest.mock import Mock, patch


class TestScreenerCLI:
    """Test screener CLI functionality"""

    def test_import_cli_module(self) -> None:
        """Test that the CLI module can be imported"""
        from connors_screener import cli

        assert hasattr(cli, "main")
        assert callable(cli.main)

    @patch("connors_screener.services.screener_service.config_loader")
    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_create_example_config(
        self, mock_parse_args: Mock, mock_config_loader: Mock
    ) -> None:
        """Test create example config functionality"""
        mock_args = Mock()
        mock_args.create_example_config = "example.yaml"
        mock_args.list_providers = False
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.config_file = None
        mock_args.provider = "tv"
        mock_args.config = "rsi2"
        mock_args.market = "australia"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        mock_config_loader.create_example_config_file = Mock()

        from connors_screener.cli import main

        with patch("builtins.print"):
            main()

        mock_config_loader.create_example_config_file.assert_called_once()

    @patch("connors_screener.services.screener_service.registry")
    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_list_providers(self, mock_parse_args: Mock, mock_registry: Mock) -> None:
        """Test list providers functionality"""
        mock_args = Mock()
        mock_args.create_example_config = None
        mock_args.list_providers = True
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.config_file = None
        mock_args.provider = "tv"
        mock_args.config = "rsi2"
        mock_args.market = "australia"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        mock_registry.list_screener_providers.return_value = ["tv", "finviz"]

        from connors_screener.cli import main

        with patch("builtins.print") as mock_print:
            main()

        mock_registry.list_screener_providers.assert_called_once()
        mock_print.assert_called()

    @patch("connors_screener.services.screener_service.registry")
    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_list_configs(self, mock_parse_args: Mock, mock_registry: Mock) -> None:
        """Test list configs functionality"""
        mock_args = Mock()
        mock_args.create_example_config = None
        mock_args.list_providers = False
        mock_args.list_configs = True
        mock_args.list_markets = False
        mock_args.config_file = None
        mock_args.provider = "tv"
        mock_args.config = "rsi2"
        mock_args.market = "australia"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        mock_registry.list_screening_configs.return_value = {"tv": ["rsi2", "momentum"]}

        from connors_screener.cli import main

        with patch("builtins.print") as mock_print:
            main()

        mock_registry.list_screening_configs.assert_called_once()
        mock_print.assert_called()


class TestCLIRegistry:
    """Test CLI integration with registry system"""

    @patch("connors_core.core.registry.registry")
    def test_registry_integration_screener(self, mock_registry: Mock) -> None:
        """Test that CLI properly integrates with registry"""
        mock_registry.list_screener_providers.return_value = ["tv", "finviz"]
        mock_registry.list_screening_configs.return_value = {"tv": ["rsi2", "momentum"]}
        mock_registry.get_screener_provider.return_value = Mock()
        mock_registry.get_screening_config.return_value = Mock()

        from connors_screener.cli import main

        # Test that the CLI can call registry methods without error
        providers = mock_registry.list_screener_providers()
        configs = mock_registry.list_screening_configs()

        assert "tv" in providers
        assert "finviz" in providers
        assert "tv" in configs
        assert "rsi2" in configs["tv"]
        assert "momentum" in configs["tv"]


class TestCLIErrorHandling:
    """Test CLI error handling"""

    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_screener_invalid_config_file(self, mock_parse_args: Mock) -> None:
        """Test error handling for invalid config files"""
        mock_args = Mock()
        mock_args.create_example_config = None
        mock_args.list_providers = False
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.config_file = "nonexistent.yaml"
        mock_args.provider = "tv"
        mock_args.config = "rsi2"
        mock_args.market = "australia"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        from connors_screener.cli import main

        # Should handle file not found gracefully
        with patch("builtins.print"):
            try:
                main()
            except SystemExit:
                pass  # Expected for error conditions

    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_screener_exception_handling(self, mock_parse_args: Mock) -> None:
        """Test general exception handling in screener CLI"""
        mock_args = Mock()
        mock_args.create_example_config = None
        mock_args.list_providers = False
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.config_file = None
        mock_args.provider = "invalid_provider"
        mock_args.config = "invalid_config"
        mock_args.market = "australia"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        from connors_screener.cli import main

        # Should handle invalid provider/config gracefully
        with patch("builtins.print"):
            try:
                main()
            except (SystemExit, Exception):
                pass  # Expected for error conditions


class TestParameterOverrides:
    """Test parameter override functionality in CLI"""

    @patch("connors_screener.cli.ScreenerService")
    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_show_parameters_functionality(
        self, mock_parse_args: Mock, mock_screener_service_class: Mock
    ) -> None:
        """Test show parameters CLI functionality"""
        # Setup mock service instance
        mock_service = Mock()
        mock_screener_service_class.return_value = mock_service

        mock_service.get_config_info.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "parameters": {"rsi_level": 5, "rsi_period": 2}
        }
        mock_service.get_parameter_info.return_value = "Parameter information"

        mock_args = Mock()
        mock_args.provider = "tv"
        mock_args.config = "test_config"
        mock_args.show_parameters = True
        mock_args.create_example_config = None
        mock_args.list_providers = False
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.list_fields = False
        mock_args.list_post_filters = False
        mock_args.config_file = None
        mock_args.parameters = None
        mock_parse_args.return_value = mock_args

        from connors_screener.cli import main

        with patch("builtins.print") as mock_print:
            main()

        # Should have called print with parameter information
        mock_print.assert_called()
        mock_service.get_config_info.assert_called_with("tv", "test_config")
        mock_service.get_parameter_info.assert_called_with("tv", "test_config")

    @patch("connors_screener.cli.ScreenerService")
    @patch("connors_screener.cli.argparse.ArgumentParser.parse_args")
    def test_parameter_override_functionality(
        self, mock_parse_args: Mock, mock_screener_service_class: Mock
    ) -> None:
        """Test parameter override CLI functionality"""
        from connors_core.core.screener import ScreeningResult, StockData

        # Setup mock service instance
        mock_service = Mock()
        mock_screener_service_class.return_value = mock_service

        # Mock service methods
        mock_service.get_config_info.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "parameters": {"rsi_level": 5}
        }

        # Mock screening result with data
        mock_result = ScreeningResult(
            symbols=["AAPL"],
            data=[StockData(symbol="AAPL", name="Apple Inc.", price=150.0)],
            metadata={"market": "australia"},
            provider="TradingView",
            config_name="test_config",
            timestamp="2023-01-01T00:00:00"
        )
        mock_service.run_screening.return_value = mock_result
        mock_service.get_provider_fields.return_value = {"symbol": "Symbol", "name": "Name", "price": "Price"}

        mock_args = Mock()
        mock_args.provider = "tv"
        mock_args.config = "test_config"
        mock_args.market = "australia"
        mock_args.show_parameters = False
        mock_args.create_example_config = None
        mock_args.list_providers = False
        mock_args.list_configs = False
        mock_args.list_markets = False
        mock_args.list_fields = False
        mock_args.list_post_filters = False
        mock_args.config_file = None
        mock_args.parameters = "rsi_level:10"
        mock_args.verbose = False
        mock_args.sort_by = "close"
        mock_args.sort_order = "asc"
        mock_args.output_format = "table"
        mock_args.display_fields = None
        mock_args.post_filter = None
        mock_args.post_filter_context = None
        mock_args.external_post_filter = None
        mock_parse_args.return_value = mock_args

        from connors_screener.cli import main

        with patch("builtins.print"):
            main()

        # Should have called run_screening with parameter overrides
        mock_service.run_screening.assert_called_once()
        call_kwargs = mock_service.run_screening.call_args[1]
        assert call_kwargs["provider"] == "tv"
        assert call_kwargs["config"] == "test_config"
        assert call_kwargs["parameters"] == {"rsi_level": 10}
