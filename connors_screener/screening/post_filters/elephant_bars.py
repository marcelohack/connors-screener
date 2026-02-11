"""
Elephant Bars post-filter.

An "elephant bar" is a price bar with unusually large range and/or volume
relative to recent history. The user will implement the actual detection
logic; this module provides the registration and function signature.

Required raw_data fields (requested via extra_columns in the config):
    - average_volume_30d_calc: 30-day average volume
    - ATR: Average True Range

Suggested context keys (passed via post_filter_context):
    - volume_multiplier: min ratio of volume to avg volume (e.g. 3.0)
    - atr_multiplier: min ratio of bar range to ATR (e.g. 2.0)
"""

from typing import Any, Dict

from connors_screener.core.screener import StockData
from connors_screener.screening.post_filters import register_post_filter


def elephant_bars_filter(stock: StockData, context: Dict[str, Any]) -> bool:
    """Determine whether a stock's current bar qualifies as an elephant bar.

    Args:
        stock: StockData with raw_data containing ATR, average_volume_30d_calc, etc.
        context: Merged dict of ScreeningConfig.parameters + post_filter_context.

    Returns:
        True to keep the stock (it IS an elephant bar), False to discard.
    """
    # TODO: Implement elephant bar detection logic.
    #
    # Example approach:
    #   volume = stock.volume
    #   avg_volume = stock.get_field("average_volume_30d_calc")
    #   atr = stock.get_field("ATR")
    #   volume_mult = context.get("volume_multiplier", 2.0)
    #   atr_mult = context.get("atr_multiplier", 1.5)
    #   return volume > volume_mult * avg_volume and ...
    #
    # For now, pass everything through (no filtering).
    return True


register_post_filter("elephant_bars", elephant_bars_filter)
