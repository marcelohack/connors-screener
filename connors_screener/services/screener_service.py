"""
Screener Service

Provides high-level interface for stock screening operations,
integrating with the screening providers and configurations.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, cast

import connors_screener.screening.configs.finviz_rsi2
import connors_screener.screening.configs.tradingview_crypto_basic
import connors_screener.screening.configs.tradingview_momentum
import connors_screener.screening.configs.tradingview_rsi2
import connors_screener.screening.configs.tradingview_elephant_bars
import connors_screener.screening.configs.tradingview_value
import connors_screener.screening.providers.finviz

# Import all screening providers to ensure registration
import connors_screener.screening.providers.tradingview
import connors_screener.screening.providers.tradingview_crypto  # noqa: F401
from connors_screener.config.screening import ScreeningConfigManager
from connors_core.core.parameter_override import (
    apply_parameter_overrides,
    get_parameter_info,
    parse_parameter_string,
)
from connors_core.core.registry import registry
from connors_screener.core.screener import ScreeningResult, StockData
from connors_screener.screening.config_loader import config_loader
from connors_screener.screening.post_filters import get_post_filter
from connors_core.services.base import BaseService

PostFilter = Callable[[StockData, Dict[str, Any]], bool]


class ScreenerService(BaseService):
    """Service for stock and crypto screening operations"""

    def __init__(self) -> None:
        super().__init__()
        self.registry = registry
        self.screening_config_manager = ScreeningConfigManager()

    def get_providers(self) -> List[str]:
        """Get list of available screening providers"""
        try:
            return self.registry.list_screener_providers()
        except Exception as e:
            self.logger.error(f"Failed to get providers: {e}")
            return []

    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about each provider"""
        providers_info = {
            "tv": {
                "name": "TradingView",
                "description": "Traditional stock screening via TradingView",
                "supports_markets": True,
                "asset_types": "Stocks",
            },
            "tv_crypto": {
                "name": "TradingView Crypto",
                "description": "Cryptocurrency screening via TradingView",
                "supports_markets": False,
                "asset_types": "Cryptocurrencies",
            },
            "finviz": {
                "name": "Finviz",
                "description": "Stock screening via Finviz platform",
                "supports_markets": True,
                "asset_types": "US Stocks",
            },
        }

        available_providers = self.get_providers()
        return {
            provider: info
            for provider, info in providers_info.items()
            if provider in available_providers
        }

    def get_configs_for_provider(self, provider: str) -> List[str]:
        """Get available configurations for a specific provider"""
        try:
            self._validate_required_params({"provider": provider}, ["provider"])
            configs_dict = self.registry.list_screening_configs(provider)
            return configs_dict.get(provider, [])
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Failed to get configs for provider {provider}: {e}")
            return []

    def get_config_info(self, provider: str, config: str) -> Dict[str, Any]:
        """Get detailed information about a screening configuration"""
        try:
            self._validate_required_params(
                {"provider": provider, "config": config}, ["provider", "config"]
            )

            screening_config = self.registry.get_screening_config(provider, config)

            return {
                "name": screening_config.name,
                "description": screening_config.description,
                "provider": screening_config.provider,
                "parameters": screening_config.parameters,
                "filters": screening_config.filters,
            }
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Failed to get config info for {provider}/{config}: {e}")
            return {}

    def get_available_markets(self) -> List[str]:
        """Get list of available markets for stock screening"""
        return self.screening_config_manager.list_markets()

    def get_market_info(self, market: str) -> Dict[str, Any]:
        """Get detailed information about a specific market"""
        try:
            market_config = self.screening_config_manager.get_market_config(market)
            return {
                "name": market_config.name,
                "symbolset": market_config.symbolset,
                "default_volume": market_config.default_volume,
                "market_identifier": market_config.market_identifier,
            }
        except Exception as e:
            self.logger.error(f"Failed to get market info for {market}: {e}")
            return {}

    def get_all_configs(self) -> Dict[str, List[str]]:
        """Get all available configurations organized by provider"""
        try:
            return self.registry.list_screening_configs()
        except Exception as e:
            self.logger.error(f"Failed to get all configs: {e}")
            return {}

    def get_provider_fields(self, provider: str) -> Dict[str, str]:
        """Get available data fields for a specific provider"""
        try:
            self._validate_required_params({"provider": provider}, ["provider"])
            provider_instance = self.registry.create_screener_provider(provider)
            return provider_instance.get_available_fields()
        except Exception as e:
            self.logger.error(f"Failed to get fields for provider {provider}: {e}")
            return {}

    def get_all_provider_fields(self) -> Dict[str, Dict[str, str]]:
        """Get available data fields for all providers"""
        try:
            providers = self.get_providers()
            fields_by_provider = {}
            for provider in providers:
                fields_by_provider[provider] = self.get_provider_fields(provider)
            return fields_by_provider
        except Exception as e:
            self.logger.error(f"Failed to get all provider fields: {e}")
            return {}

    def get_config_parameters(self, provider: str, config: str) -> Dict[str, Any]:
        """Get customizable parameters for a configuration with their current values"""
        try:
            config_info = self.get_config_info(provider, config)
            parameters = config_info.get("parameters", {})
            return parameters if isinstance(parameters, dict) else {}
        except Exception as e:
            self.logger.error(f"Failed to get parameters for {provider}/{config}: {e}")
            return {}

    def get_parameter_info(self, provider: str, config: str) -> str:
        """Get detailed parameter information for a configuration"""
        try:
            screening_config = self.registry.get_screening_config(provider, config)
            param_info = get_parameter_info(screening_config)
            return (
                str(param_info)
                if param_info is not None
                else "No parameter information available"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to get parameter info for {provider}/{config}: {e}"
            )
            return f"Error retrieving parameter information: {e}"

    def create_example_config_file(
        self, file_path: Path, format_type: str = "json"
    ) -> bool:
        """Create an example configuration file"""
        try:
            config_loader.create_example_config_file(file_path, format_type)
            self.logger.info(f"Created example config file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create example config: {e}")
            return False

    def load_external_config_file(self, config_file_path: Path) -> List[str]:
        """Load external configuration file and return list of registered config names"""
        try:
            registered_configs = config_loader.register_configs_from_file(
                config_file_path
            )
            self.logger.info(
                f"Loaded external configurations: {', '.join(registered_configs)}"
            )
            return registered_configs
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file_path}: {e}")
            raise

    def contains_substring(self, text: str, substring: str) -> bool:
        """Helper method to check if text contains substring (case-insensitive)"""
        return substring.lower() in text.lower()

    def run_screening(
        self,
        provider: str,
        config: str,
        market: str = "america",
        parameters: Optional[Dict[str, Any]] = None,
        parameter_string: Optional[str] = None,
        sort_by: str = "close",
        sort_order: str = "asc",
        post_filter: Union[PostFilter, str, None] = None,
        post_filter_context: Optional[Dict[str, Any]] = None,
    ) -> ScreeningResult:
        """
        Run screening with specified configuration

        Args:
            provider: Provider name (tv, tv_crypto, finviz)
            config: Configuration name
            market: Market name (ignored for crypto providers)
            parameters: Parameter overrides as dict
            parameter_string: Parameter overrides as string ("key1:value1;key2:value2")
            sort_by: Field to sort by (close, volume, market_cap_basic, etc.)
            sort_order: Sort order ('asc' or 'desc')
            post_filter: Optional filter for results. Can be a callable
                (stock, context) -> bool, a string name of a registered post-filter
                (e.g. "elephant_bars"), or None.
            post_filter_context: Optional dict merged into the filter context
                (overrides keys from ScreeningConfig.parameters).

        Returns:
            ScreeningResult object with symbols and metadata
        """
        try:
            self._validate_required_params(
                {"provider": provider, "config": config}, ["provider", "config"]
            )

            # Parse parameter string if provided
            parsed_params = {}
            if parameter_string:
                parsed_params = parse_parameter_string(parameter_string)

            # Merge with dict parameters (dict takes precedence)
            if parameters:
                parsed_params.update(parameters)

            # Get the screening provider and configuration
            provider_instance = self.registry.create_screener_provider(provider)
            screening_config = self.registry.get_screening_config(provider, config)

            # Apply parameter overrides (or substitute default values if no overrides provided)
            screening_config = apply_parameter_overrides(
                screening_config, parsed_params
            )

            # Run the screening
            # Try to pass sort parameters if provider supports them
            try:
                result = cast(
                    ScreeningResult, provider_instance.scan(
                        screening_config, market, sort_by, sort_order
                    )
                )
            except TypeError:
                # Provider doesn't support sort parameters, fall back to basic scan
                result = cast(
                    ScreeningResult, provider_instance.scan(screening_config, market)
                )

            # Resolve string-based post_filter to callable
            resolved_post_filter: Optional[PostFilter] = None
            if isinstance(post_filter, str):
                resolved_post_filter = get_post_filter(post_filter)
            elif post_filter is not None:
                resolved_post_filter = post_filter

            if resolved_post_filter is not None:
                pre_filter_count = len(result.data)
                filter_context: Dict[str, Any] = dict(screening_config.parameters)
                if post_filter_context:
                    filter_context.update(post_filter_context)

                filtered_data = [
                    stock for stock in result.data
                    if resolved_post_filter(stock, filter_context)
                ]
                filtered_symbols = [stock.symbol for stock in filtered_data]

                result = ScreeningResult(
                    symbols=filtered_symbols,
                    data=filtered_data,
                    metadata={
                        **result.metadata,
                        "post_filter_applied": True,
                        "pre_filter_count": pre_filter_count,
                        "post_filter_count": len(filtered_data),
                    },
                    provider=result.provider,
                    config_name=result.config_name,
                    timestamp=result.timestamp,
                )

            self.logger.info(
                f"Screening completed: {len(result.symbols)} symbols found"
            )
            return result

        except Exception as e:
            self.logger.error(f"Screening failed: {e}")
            raise

    def create_external_config_template(self) -> Dict[str, Any]:
        """Create a template for external configuration files"""
        return {
            "configurations": [
                {
                    "name": "custom_momentum",
                    "provider": "tv",
                    "description": "Custom momentum screening configuration",
                    "parameters": {"price_change_pct": 5.0, "volume_multiplier": 2.0},
                    "provider_config": {"volume_threshold": 500000},
                    "filters": [
                        {"field": "change", "operation": "greater", "value": 5.0},
                        {"field": "volume", "operation": "greater", "value": 500000},
                    ],
                }
            ]
        }

    def load_external_config(
        self, config_data: Dict[str, Any], config_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load external configuration and return config info for UI

        Args:
            config_data: Parsed JSON/YAML configuration data
            config_name: Name of configuration to load

        Returns:
            Configuration info dict or None if not found
        """
        try:
            # Create temporary file for external config
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(config_data, f)
                temp_file = f.name

            # Load external configurations
            from connors_screener.screening.config_loader import ScreeningConfigLoader

            loader = ScreeningConfigLoader()
            loader.register_configs_from_file(temp_file)

            # Find the requested configuration
            configurations = config_data.get("configurations", [])
            if isinstance(configurations, list):
                for config in configurations:
                    if isinstance(config, dict) and config.get("name") == config_name:
                        return config

            return None

        except Exception as e:
            self.logger.error(f"Failed to load external config: {e}")
            return None
        finally:
            # Clean up temp file
            try:
                Path(temp_file).unlink()
            except Exception:
                pass
