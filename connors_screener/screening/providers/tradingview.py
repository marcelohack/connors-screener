from datetime import datetime
from typing import Any, Dict, List

import requests

from connors_screener.config.screening import ScreeningConfigManager
from connors_core.core.registry import registry
from connors_screener.core.screener import ScreenerProvider, ScreeningConfig, ScreeningResult, StockData


@registry.register_screener_provider("tv")
class TradingViewProvider:
    """TradingView screener provider implementation"""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        self.screening_config_manager = ScreeningConfigManager()

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Normalize API values that might be lists to strings

        TradingView API can return lists for some fields (e.g., sectors).
        This converts lists to comma-separated strings for compatibility with
        DataFrames and PyArrow.
        """
        if value is None:
            return ""
        if isinstance(value, list):
            # Convert list to comma-separated string
            return ", ".join(str(v) for v in value if v is not None)
        return value

    def scan(
        self, config: ScreeningConfig, market: str = "australia",
        sort_by: str = "close", sort_order: str = "asc"
    ) -> ScreeningResult:
        """Execute screening using TradingView API

        Args:
            config: Screening configuration
            market: Market to scan
            sort_by: Field to sort by (close, volume, market_cap_basic, change, etc.)
            sort_order: Sort order ('asc' or 'desc')
        """

        # Validate provider compatibility
        if config.provider != "tv":
            raise ValueError(
                f"Config provider '{config.provider}' is not compatible with TradingView provider"
            )

        market_config = self.screening_config_manager.get_market_config(market)

        print(f"#### Scanning {market_config.name} with config {config.name} ####")

        url = f"https://scanner.tradingview.com/{market_config.market_identifier}/scan"
        print(f"URL: {url}")

        payload = self._build_payload(config, market_config, sort_by, sort_order)

        response = requests.post(url, json=payload, headers=self.headers)
        symbols: List[str] = []
        stock_data: List[StockData] = []

        if response.status_code == 200:
            json_response = response.json()
            parsed_data = json_response["data"]

            # Build column index map for easy access
            columns = payload["columns"]
            col_idx = {col: i for i, col in enumerate(columns)}

            # Extract data for each stock
            for item in parsed_data:
                d = item["d"]
                symbol = d[col_idx["name"]] if col_idx["name"] < len(d) else ""

                # Build raw_data dictionary with all available fields
                raw_data = {}
                for col_name, col_index in col_idx.items():
                    if col_index < len(d) and d[col_index] is not None:
                        raw_data[col_name] = d[col_index]

                # Extract core fields for backward compatibility
                stock = StockData(
                    symbol=symbol,
                    name=self._normalize_value(d[col_idx["description"]] if col_idx.get("description") is not None and col_idx["description"] < len(d) else ""),
                    price=float(d[col_idx["close"]]) if col_idx.get("close") is not None and col_idx["close"] < len(d) and d[col_idx["close"]] is not None else 0.0,
                    volume=float(d[col_idx["volume"]]) if col_idx.get("volume") is not None and col_idx["volume"] < len(d) and d[col_idx["volume"]] is not None else 0.0,
                    change=float(d[col_idx["change"]]) if col_idx.get("change") is not None and col_idx["change"] < len(d) and d[col_idx["change"]] is not None else 0.0,
                    market_cap=float(d[col_idx["market_cap_basic"]]) if col_idx.get("market_cap_basic") is not None and col_idx["market_cap_basic"] < len(d) and d[col_idx["market_cap_basic"]] is not None else 0.0,
                    sector=self._normalize_value(d[col_idx["sector"]] if col_idx.get("sector") is not None and col_idx["sector"] < len(d) and d[col_idx["sector"]] is not None else ""),
                    exchange=self._normalize_value(d[col_idx["exchange"]] if col_idx.get("exchange") is not None and col_idx["exchange"] < len(d) and d[col_idx["exchange"]] is not None else ""),
                    currency=self._normalize_value(d[col_idx["currency"]] if col_idx.get("currency") is not None and col_idx["currency"] < len(d) and d[col_idx["currency"]] is not None else ""),
                    raw_data=raw_data  # Store all provider fields
                )

                symbols.append(symbol)
                stock_data.append(stock)

            print(f"Found {len(symbols)} symbols matching criteria")

            return ScreeningResult(
                symbols=symbols,
                data=stock_data,
                metadata={
                    "market": market_config.name,
                    "symbolset": market_config.symbolset,
                    "filters_applied": len(config.filters),
                    "response_status": response.status_code,
                    "total_results": len(symbols),
                },
                provider="TradingView",
                config_name=config.name,
                timestamp=datetime.now().isoformat(),
            )
        else:
            print(f"Error: {response.status_code}")
            raise Exception(f"TradingView API error: {response.status_code}")

    def validate_config(self, config: ScreeningConfig) -> bool:
        """Validate if the configuration is compatible with TradingView"""
        required_fields = ["filters", "provider_config"]
        return all(hasattr(config, field) for field in required_fields)

    def get_supported_markets(self) -> List[str]:
        """Get list of supported markets"""
        return self.screening_config_manager.list_markets()

    def get_available_fields(self) -> Dict[str, str]:
        """Get available data fields returned by TradingView API

        Includes both:
        - Core standardized fields (symbol, name, price, etc.)
        - Raw TradingView API fields (description, close, market_cap_basic, etc.)
        """
        return {
            # Core standardized fields (available for all providers)
            "symbol": "Stock symbol/ticker (core field, maps to API 'name')",
            "name": "Company name (core field, maps to API 'description')",
            "price": "Current/closing price (core field, maps to API 'close')",
            "volume": "Trading volume (core field)",
            "change": "Price change percentage (core field)",
            "market_cap": "Market capitalization (core field, maps to API 'market_cap_basic')",
            "sector": "Industry sector (core field)",
            "exchange": "Stock exchange (core field)",
            "currency": "Currency code (core field)",

            # Raw TradingView API fields
            "description": "Company name/description (raw API field)",
            "close": "Current/closing price (raw API field)",
            "market_cap_basic": "Market capitalization (raw API field)",
            "price_earnings_ttm": "P/E ratio (trailing twelve months)",
            "recommendation_mark": "Analyst recommendation score",
            "fundamental_currency_code": "Fundamental currency",
            "market": "Market identifier",
            "logoid": "Logo identifier",
            "update_mode": "Update mode",
            "type": "Security type",
            "typespecs": "Type specifications",
            "pricescale": "Price scale factor",
            "minmov": "Minimum price movement",
            "fractional": "Fractional pricing flag",
            "minmove2": "Alternative minimum movement"
        }

    def _build_payload(
        self, config: ScreeningConfig, market_config: Any,
        sort_by: str = "close", sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Build TradingView API payload from screening config

        Args:
            config: Screening configuration
            market_config: Market configuration
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
        """

        # Base columns to retrieve
        columns = [
            "name",
            "description",
            "logoid",
            "update_mode",
            "type",
            "typespecs",
            "close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "change",
            "volume",
            "market_cap_basic",
            "fundamental_currency_code",
            "price_earnings_ttm",
            "sector.tr",
            "market",
            "sector",
            "recommendation_mark",
            "exchange",
        ]

        # Build filters from config
        filters = []
        volume_threshold = config.provider_config.get(
            "volume_threshold", market_config.default_volume
        )

        for filter_def in config.filters:
            if filter_def["field"] == "volume" and "value" not in filter_def:
                # Use configured volume threshold if not specified
                filter_def = filter_def.copy()
                filter_def["value"] = volume_threshold

            filters.append(
                {
                    "left": filter_def["field"],
                    "operation": filter_def["operation"],
                    "right": filter_def["value"],
                }
            )

        # Add volume filter if not already present
        if not any(f["field"] == "volume" for f in config.filters):
            filters.append(
                {"left": "volume", "operation": "greater", "right": volume_threshold}
            )

        return {
            "columns": columns,
            "filter": filters,
            "ignore_unknown_fields": False,
            "options": {"lang": "en"},
            "range": [0, 100],
            "sort": {"sortBy": sort_by, "sortOrder": sort_order},
            "symbols": {"symbolset": [market_config.symbolset]},
            "markets": [market_config.market_identifier],
            "filter2": self._get_stock_type_filter(),
        }

    def _get_stock_type_filter(self) -> Dict[str, Any]:
        """Get the complex stock type filter used by TradingView"""
        return {
            "operator": "and",
            "operands": [
                {
                    "operation": {
                        "operator": "or",
                        "operands": [
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "stock",
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has",
                                                "right": ["common"],
                                            }
                                        },
                                    ],
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "stock",
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has",
                                                "right": ["preferred"],
                                            }
                                        },
                                    ],
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "dr",
                                            }
                                        }
                                    ],
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "fund",
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has_none_of",
                                                "right": ["etf"],
                                            }
                                        },
                                    ],
                                }
                            },
                        ],
                    }
                }
            ],
        }
