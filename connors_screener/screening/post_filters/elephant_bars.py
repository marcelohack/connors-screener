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

_context_printed = False


def elephant_bars_filter(stock: StockData, context: Dict[str, Any]) -> bool:
    """Determine whether a stock's current bar qualifies as an elephant bar.

    Args:
        stock: StockData with raw_data containing ATR, average_volume_30d_calc, etc.
        context: Merged dict of ScreeningConfig.parameters + post_filter_context.

    Returns:
        True to keep the stock (it IS an elephant bar), False to discard.
    """

    global _context_printed
    if not _context_printed:
        atr_f = context.get("atr_factor", 2.5)
        vol_f = context.get("volume_factor", 2.0)
        body_min = context.get("candle_body_pct", 80.0)
        print(f"  [elephant_bars] Context: atr_factor={atr_f}, volume_factor={vol_f}, candle_body_pct={body_min}")
        print(f"  [elephant_bars] Full context: {context}")
        print()
        _context_printed = True

    # OHLCV — reject early if required fields are missing
    open_price = stock.get_field("open")
    high = stock.get_field("high")
    low = stock.get_field("low")
    close_price = stock.price
    volume = stock.volume
    atr = stock.get_field("ATR")
    avg_volume = stock.get_field("average_volume_30d_calc")

    required = {"open": open_price, "high": high, "low": low, "close": close_price,
                "volume": volume, "ATR": atr, "average_volume_30d_calc": avg_volume}
    missing = [k for k, v in required.items() if v is None]
    if missing:
        print(f"  [elephant_bars] {stock.symbol} SKIP — missing fields: {missing}")
        return False

    atr_factor = context.get("atr_factor", 2.5)
    volume_factor = context.get("volume_factor", 2.0)

    candle_body_pct = context.get("candle_body_pct", 80.0) # Minimum body percentage of total range
    # use_financial_volume = context.get("use_financial_volume", False) # If True, use Close*Volume instead of Volume

    amplitude = high - low
    atr_adjusted = atr * atr_factor
    volume_adjusted = volume * volume_factor
    body = abs(close_price - open_price) if amplitude > 0 else 0.0
    body_pct = (body / amplitude) * 100 if amplitude > 0 else 0.0
    direction = "bullish" if close_price > open_price else "bearish" if close_price < open_price else "doji"

    print(
        f"  [elephant_bars] {stock.symbol} | O={open_price:.4f} H={high:.4f} L={low:.4f} C={close_price:.4f} | "
        f"vol={volume:,.0f} avg_vol={avg_volume:,.0f} | "
        f"ATR={atr:.4f} atr_adj={atr_adjusted:.4f} | "
        f"amp={amplitude:.4f} body={body:.4f} body_pct={body_pct:.1f}% (min={candle_body_pct:.1f}%) | "
        f"{direction} | amp>atr={amplitude > atr_adjusted} vol_adj>avg={volume_adjusted > avg_volume} body>min={body_pct > candle_body_pct}"
    )

    signal = ""

    if amplitude > atr_adjusted and volume_adjusted > avg_volume:
        if open_price < close_price:
            if body_pct > candle_body_pct:
                signal = "buy"

        elif open_price > close_price:
            if body_pct > candle_body_pct:
                signal = "sell"

    print(f"  [elephant_bars] {stock.symbol} -> {signal or 'REJECTED'}")
    return bool(signal)


register_post_filter("elephant_bars", elephant_bars_filter)
