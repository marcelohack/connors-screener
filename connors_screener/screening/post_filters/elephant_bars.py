"""
Elephant Bars post-filter.

An "elephant bar" is a price bar with unusually large range and/or volume
relative to recent history. The user will implement the actual detection
logic; this module provides the registration and function signature.

Required raw_data fields (requested via extra_columns in the config):
    - average_volume_30d_calc: 30-day average volume
    - ATR: Average True Range

Suggested context keys (passed via post_filter_context):
    - volume_factor: min ratio of volume to avg volume (e.g. 3.0)
    - atr_factor: min ratio of bar range to ATR (e.g. 2.0)
    - candle_body_pct: min body as % of total range (e.g. 80.0)
"""

import logging
from typing import Any, Dict

from connors_screener.core.screener import StockData
from connors_screener.screening.post_filters import register_post_filter

logger = logging.getLogger(__name__)


def elephant_bars_filter(stock: StockData, context: Dict[str, Any]) -> bool:
    """Determine whether a stock's current bar qualifies as an elephant bar.

    Args:
        stock: StockData with raw_data containing ATR, average_volume_30d_calc, etc.
        context: Merged dict of ScreeningConfig.parameters + post_filter_context.

    Returns:
        True to keep the stock (it IS an elephant bar), False to discard.
    """

    # Implement elephant bar detection logic.
    #
    # OHLCV
    open_price = stock.get_field("open")
    high = stock.get_field("high")
    close_price = stock.price
    low = stock.get_field("low")
    volume = stock.volume

    atr_factor = context.get("atr_factor", 2.5) # Multiplier for elephant bar amplitude threshold
    atr = stock.get_field("ATR") # Average True Range value from raw_data

    avg_volume = stock.get_field("average_volume_30d_calc") # 30-day average volume from raw_data
    volume_factor = context.get("volume_factor", 2.0) # Volume comparison multiplier

    candle_body_pct = context.get("candle_body_pct", 80.0) # Minimum body percentage of total range
    # use_financial_volume = context.get("use_financial_volume", False) # If True, use Close*Volume instead of Volume

    amplitude = high - low
    atr_adjusted = atr * atr_factor
    volume_adjusted = volume * volume_factor
    body = abs(close_price - open_price) if amplitude > 0 else 0.0
    body_pct = (body / amplitude) * 100 if amplitude > 0 else 0.0
    direction = "bullish" if close_price > open_price else "bearish" if close_price < open_price else "doji"

    logger.debug(
        "[elephant_bars] %s | O=%.2f H=%.2f L=%.2f C=%.2f | vol=%,.0f avg_vol=%,.0f | "
        "ATR=%.2f atr_factor=%.1f atr_adj=%.2f | vol_factor=%.1f vol_adj=%,.0f | "
        "amplitude=%.2f body=%.2f body_pct=%.1f%% (min=%.1f%%) | direction=%s | "
        "amp>atr_adj=%s vol_adj>avg_vol=%s body_pct>min=%s",
        stock.symbol,
        open_price, high, low, close_price,
        volume, avg_volume,
        atr, atr_factor, atr_adjusted,
        volume_factor, volume_adjusted,
        amplitude, body, body_pct, candle_body_pct,
        direction,
        amplitude > atr_adjusted,
        volume_adjusted > avg_volume,
        body_pct > candle_body_pct,
    )

    signal = ""

    if amplitude > atr_adjusted and volume_adjusted > avg_volume:
        if open_price < close_price:
            if body_pct > candle_body_pct:
                signal = "buy"

        elif open_price > close_price:
            if body_pct > candle_body_pct:
                signal = "sell"

    logger.debug("[elephant_bars] %s -> %s", stock.symbol, signal or "REJECTED")
    return bool(signal)


register_post_filter("elephant_bars", elephant_bars_filter)
