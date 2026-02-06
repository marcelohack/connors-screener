from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import pandas as pd


@dataclass
class ScreeningConfig:
    """Configuration for screening criteria, specific to a provider"""

    name: str
    provider: str  # Provider this config belongs to (e.g., 'tv', 'finviz')
    parameters: Dict[str, Any]
    provider_config: Dict[str, Any]
    filters: List[Dict[str, Any]]
    description: str = ""


@dataclass
class StockData:
    """Detailed data for a single stock from screening

    Core fields are commonly used across all providers.
    Provider-specific fields are stored in raw_data dictionary.
    """

    symbol: str
    name: str = ""
    price: float = 0.0
    volume: float = 0.0
    change: float = 0.0
    market_cap: float = 0.0
    sector: str = ""
    exchange: str = ""
    currency: str = ""
    raw_data: Optional[Dict[str, Any]] = None  # All raw provider data

    def __post_init__(self):
        """Convert None values to defaults"""
        if self.name is None:
            self.name = ""
        if self.price is None:
            self.price = 0.0
        if self.volume is None:
            self.volume = 0.0
        if self.change is None:
            self.change = 0.0
        if self.market_cap is None:
            self.market_cap = 0.0
        if self.sector is None:
            self.sector = ""
        if self.exchange is None:
            self.exchange = ""
        if self.currency is None:
            self.currency = ""
        if self.raw_data is None:
            self.raw_data = {}

    def get_field(self, field_name: str) -> Any:
        """Get field value from either core fields or raw_data

        Args:
            field_name: Name of the field to retrieve

        Returns:
            Field value if found, None otherwise
        """
        # Check core fields first
        core_fields = ['symbol', 'name', 'price', 'volume', 'change',
                       'market_cap', 'sector', 'exchange', 'currency']
        if field_name in core_fields:
            return getattr(self, field_name, None)

        # Check raw_data for provider-specific fields
        if self.raw_data:
            return self.raw_data.get(field_name)

        return None


@dataclass
class ScreeningResult:
    """Result of a screening operation"""

    symbols: List[str]  # Keep for backward compatibility
    data: List[StockData]  # Detailed stock data
    metadata: Dict[str, Any]
    provider: str
    config_name: str
    timestamp: str


class ScreenerProvider(Protocol):
    """Protocol for screener providers (TradingView, Finviz, etc.)"""

    def scan(self, config: ScreeningConfig) -> ScreeningResult: ...

    def validate_config(self, config: ScreeningConfig) -> bool: ...

    def get_supported_markets(self) -> List[str]: ...

    def get_available_fields(self) -> Dict[str, str]: ...
