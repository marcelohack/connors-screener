"""
Unit tests for post-filter registry
"""

from typing import Any, Dict

import pytest

from connors_screener.core.screener import StockData
from connors_screener.screening.post_filters import (
    _post_filters,
    get_post_filter,
    list_post_filters,
    register_post_filter,
)


class TestPostFilterRegistry:
    """Test the post-filter registry functions"""

    def test_elephant_bars_auto_registered(self) -> None:
        """Test that elephant_bars filter is auto-registered on import"""
        assert "elephant_bars" in list_post_filters()

    def test_get_registered_filter(self) -> None:
        """Test retrieving a registered filter by name"""
        fn = get_post_filter("elephant_bars")
        assert callable(fn)

    def test_get_unregistered_filter_raises(self) -> None:
        """Test that requesting unknown filter raises ValueError"""
        with pytest.raises(ValueError, match="Post-filter 'nonexistent' not found"):
            get_post_filter("nonexistent")

    def test_register_custom_filter(self) -> None:
        """Test registering a custom filter"""

        def my_filter(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return stock.price > 100

        register_post_filter("test_custom", my_filter)

        try:
            assert "test_custom" in list_post_filters()
            fn = get_post_filter("test_custom")
            assert fn is my_filter
        finally:
            _post_filters.pop("test_custom", None)

    def test_register_duplicate_raises(self) -> None:
        """Test that registering a duplicate name raises ValueError"""

        def dummy(stock: StockData, ctx: Dict[str, Any]) -> bool:
            return True

        register_post_filter("test_dup", dummy)

        try:
            with pytest.raises(ValueError, match="already registered"):
                register_post_filter("test_dup", dummy)
        finally:
            _post_filters.pop("test_dup", None)

    def test_list_post_filters(self) -> None:
        """Test listing all registered filters"""
        filters = list_post_filters()
        assert isinstance(filters, list)
        assert "elephant_bars" in filters

    def test_elephant_bars_detects_bullish_bar(self) -> None:
        """Test that the elephant_bars filter detects a bullish elephant bar"""
        fn = get_post_filter("elephant_bars")
        stock = StockData(
            symbol="AAPL",
            price=160.0,  # close
            volume=5_000_000,
            raw_data={
                "open": 140.0,
                "high": 162.0,
                "low": 138.0,
                "ATR": 5.0,
                "average_volume_30d_calc": 1_000_000,
            },
        )
        ctx = {"atr_factor": 2.0, "volume_factor": 2.0, "candle_body_pct": 70.0}
        assert fn(stock, ctx) is True

    def test_elephant_bars_rejects_small_bar(self) -> None:
        """Test that the elephant_bars filter rejects a normal-sized bar"""
        fn = get_post_filter("elephant_bars")
        stock = StockData(
            symbol="AAPL",
            price=151.0,  # close
            volume=500_000,
            raw_data={
                "open": 150.0,
                "high": 151.5,
                "low": 149.5,
                "ATR": 5.0,
                "average_volume_30d_calc": 1_000_000,
            },
        )
        assert fn(stock, {}) is False
