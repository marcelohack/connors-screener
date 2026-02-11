"""
Post-filter registry for screening results.

Post-filters run client-side after the provider returns data.
They can be registered by name so callers can pass a string
instead of a callable to run_screening().
"""

from typing import Any, Callable, Dict, List

from connors_screener.core.screener import StockData

PostFilter = Callable[[StockData, Dict[str, Any]], bool]

_post_filters: Dict[str, PostFilter] = {}


def register_post_filter(name: str, fn: PostFilter) -> None:
    """Register a named post-filter function."""
    if name in _post_filters:
        raise ValueError(f"Post-filter '{name}' is already registered")
    _post_filters[name] = fn


def get_post_filter(name: str) -> PostFilter:
    """Retrieve a post-filter by name."""
    if name not in _post_filters:
        available = list(_post_filters.keys())
        raise ValueError(
            f"Post-filter '{name}' not found. Available: {available}"
        )
    return _post_filters[name]


def list_post_filters() -> List[str]:
    """Return names of all registered post-filters."""
    return list(_post_filters.keys())


# Import sub-modules to trigger auto-registration
import connors_screener.screening.post_filters.elephant_bars  # noqa: E402, F401
