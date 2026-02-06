from datetime import datetime
from typing import Any, Dict, List

import requests

from connors_screener.config.screening import ScreeningConfigManager
from connors_core.core.registry import registry
from connors_screener.core.screener import ScreenerProvider, ScreeningConfig, ScreeningResult, StockData


@registry.register_screener_provider("tv_crypto")
class TradingViewCryptoProvider:
    """TradingView Crypto screener provider implementation"""

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        self.screening_config_manager = ScreeningConfigManager()

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Normalize API values that might be lists to strings

        TradingView API can return lists for some fields (e.g., categories).
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
        self, config: ScreeningConfig, market: str = "crypto",
        sort_by: str = "crypto_total_rank", sort_order: str = "asc"
    ) -> ScreeningResult:
        """Execute crypto screening using TradingView API

        Args:
            config: Screening configuration
            market: Market to scan (default: crypto)
            sort_by: Field to sort by (crypto_total_rank, close, 24h_vol_cmc, market_cap_calc, etc.)
            sort_order: Sort order ('asc' or 'desc')
        """

        # Validate provider compatibility
        if config.provider != "tv_crypto":
            raise ValueError(
                f"Config provider '{config.provider}' is not compatible with TradingViewCrypto provider"
            )

        print(f"#### Scanning Cryptocurrencies with config {config.name} ####")

        url = "https://scanner.tradingview.com/coin/scan?label-product=screener-coin"
        print(f"URL: {url}")

        payload = self._build_payload(config, sort_by, sort_order)

        response = requests.post(url, json=payload, headers=self.headers)
        symbols: List[str] = []
        crypto_data: List[StockData] = []

        if response.status_code == 200:
            json_response = response.json()
            parsed_data = json_response["data"]

            # Build column index map for easy access
            columns = payload["columns"]
            col_idx = {col: i for i, col in enumerate(columns)}

            # Extract data for each crypto
            for item in parsed_data:
                d = item["d"]
                symbol = d[col_idx["base_currency"]] if col_idx["base_currency"] < len(d) else ""

                # Build raw_data dictionary with all available fields
                raw_data = {}
                for col_name, col_index in col_idx.items():
                    if col_index < len(d) and d[col_index] is not None:
                        raw_data[col_name] = d[col_index]

                # Extract core fields for backward compatibility
                crypto = StockData(
                    symbol=symbol,
                    name=self._normalize_value(d[col_idx["base_currency_desc"]] if col_idx.get("base_currency_desc") is not None and col_idx["base_currency_desc"] < len(d) and d[col_idx["base_currency_desc"]] is not None else ""),
                    price=float(d[col_idx["close"]]) if col_idx.get("close") is not None and col_idx["close"] < len(d) and d[col_idx["close"]] is not None else 0.0,
                    volume=float(d[col_idx["24h_vol_cmc"]]) if col_idx.get("24h_vol_cmc") is not None and col_idx["24h_vol_cmc"] < len(d) and d[col_idx["24h_vol_cmc"]] is not None else 0.0,
                    change=float(d[col_idx["24h_close_change|5"]]) if col_idx.get("24h_close_change|5") is not None and col_idx["24h_close_change|5"] < len(d) and d[col_idx["24h_close_change|5"]] is not None else 0.0,
                    market_cap=float(d[col_idx["market_cap_calc"]]) if col_idx.get("market_cap_calc") is not None and col_idx["market_cap_calc"] < len(d) and d[col_idx["market_cap_calc"]] is not None else 0.0,
                    sector=self._normalize_value(d[col_idx["crypto_common_categories.tr"]] if col_idx.get("crypto_common_categories.tr") is not None and col_idx["crypto_common_categories.tr"] < len(d) and d[col_idx["crypto_common_categories.tr"]] is not None else ""),
                    exchange=self._normalize_value(d[col_idx["exchange"]] if col_idx.get("exchange") is not None and col_idx["exchange"] < len(d) and d[col_idx["exchange"]] is not None else ""),
                    currency=self._normalize_value(d[col_idx["currency"]] if col_idx.get("currency") is not None and col_idx["currency"] < len(d) and d[col_idx["currency"]] is not None else ""),
                    raw_data=raw_data  # Store all provider fields
                )

                symbols.append(symbol)
                crypto_data.append(crypto)

            print(f"Found {len(symbols)} crypto symbols matching criteria")

            return ScreeningResult(
                symbols=symbols,
                data=crypto_data,
                metadata={
                    "market": "crypto",
                    "symbolset": "coin",
                    "filters_applied": len(config.filters),
                    "response_status": response.status_code,
                    "total_results": len(symbols),
                    "total_count": json_response.get("totalCount", 0),
                },
                provider="TradingViewCrypto",
                config_name=config.name,
                timestamp=datetime.now().isoformat(),
            )
        else:
            print(f"Error: {response.status_code}")
            raise Exception(f"TradingViewCrypto API error: {response.status_code}")

    def validate_config(self, config: ScreeningConfig) -> bool:
        """Validate if the configuration is compatible with TradingViewCrypto"""
        required_fields = ["filters", "provider_config"]
        return all(hasattr(config, field) for field in required_fields)

    def get_supported_markets(self) -> List[str]:
        """Get list of supported markets"""
        return ["crypto"]

    def get_available_fields(self) -> Dict[str, str]:
        """Get available data fields returned by TradingViewCrypto API

        Includes both:
        - Core standardized fields (symbol, name, price, etc.)
        - Raw TradingView Crypto API fields (base_currency, base_currency_desc, etc.)
        """
        return {
            # Core standardized fields (available for all providers)
            "symbol": "Cryptocurrency symbol/ticker (core field, maps to API 'base_currency')",
            "name": "Cryptocurrency name (core field, maps to API 'base_currency_desc')",
            "price": "Current price (core field, maps to API 'close')",
            "volume": "24-hour trading volume (core field, maps to API '24h_vol_cmc')",
            "change": "24-hour price change percentage (core field, maps to API '24h_close_change|5')",
            "market_cap": "Market capitalization (core field, maps to API 'market_cap_calc')",
            "sector": "Cryptocurrency categories (core field, maps to API 'crypto_common_categories.tr')",
            "exchange": "Exchange where traded (core field)",
            "currency": "Quote currency (core field)",

            # Raw TradingView Crypto API fields
            "base_currency": "Cryptocurrency base currency code (raw API field)",
            "base_currency_desc": "Cryptocurrency full name (raw API field)",
            "base_currency_logoid": "Logo identifier",
            "close": "Current price (raw API field)",
            "crypto_total_rank": "Overall crypto ranking",
            "24h_close_change|5": "24-hour price change percentage (raw API field)",
            "market_cap_calc": "Calculated market capitalization (raw API field)",
            "24h_vol_cmc": "24-hour trading volume (CoinMarketCap, raw API field)",
            "circulating_supply": "Circulating token supply",
            "24h_vol_to_market_cap": "Volume to market cap ratio",
            "socialdominance": "Social media dominance score",
            "crypto_common_categories.tr": "Cryptocurrency categories (raw API field)",
            "TechRating_1D": "1-day technical rating",
            "TechRating_1D.tr": "1-day technical rating (translated)",
            "fundamental_currency_code": "Fundamental currency code",
            "update_mode": "Update mode",
            "type": "Asset type",
            "typespecs": "Type specifications",
            "pricescale": "Price scale factor",
            "minmov": "Minimum price movement",
            "fractional": "Fractional pricing flag",
            "minmove2": "Alternative minimum movement"
        }

    def _build_payload(
        self, config: ScreeningConfig,
        sort_by: str = "crypto_total_rank", sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Build TradingViewCrypto API payload from screening config

        Args:
            config: Screening configuration
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
        """

        # Crypto-specific columns based on the provided JSON structure
        columns = [
            "base_currency",
            "base_currency_desc",
            "base_currency_logoid",
            "update_mode",
            "type",
            "typespecs",
            "exchange",
            "crypto_total_rank",
            "close",
            "pricescale",
            "minmov",
            "fractional",
            "minmove2",
            "currency",
            "24h_close_change|5",
            "market_cap_calc",
            "fundamental_currency_code",
            "24h_vol_cmc",
            "circulating_supply",
            "24h_vol_to_market_cap",
            "socialdominance",
            "crypto_common_categories.tr",
            "TechRating_1D",
            "TechRating_1D.tr",
        ]

        # Build filters from config
        filters = []

        # Default volume filter for crypto (100M USD volume)
        default_volume_threshold = config.provider_config.get(
            "volume_threshold", 100000000
        )

        for filter_def in config.filters:
            if filter_def["field"] == "24h_vol_cmc" and "value" not in filter_def:
                # Use configured volume threshold if not specified
                filter_def = filter_def.copy()
                filter_def["value"] = default_volume_threshold

            filters.append(
                {
                    "left": filter_def["field"],
                    "operation": filter_def["operation"],
                    "right": filter_def["value"],
                }
            )

        # Add default volume filter if not already present
        if not any(f["field"] == "24h_vol_cmc" for f in config.filters):
            filters.append(
                {
                    "left": "24h_vol_cmc",
                    "operation": "egreater",
                    "right": default_volume_threshold,
                }
            )

        return {
            "columns": columns,
            "filter": filters,
            "ignore_unknown_fields": False,
            "options": {"lang": "en"},
            "range": [0, 100],
            "sort": {"sortBy": sort_by, "sortOrder": sort_order},
            "symbols": {},
            "markets": ["coin"],
        }
