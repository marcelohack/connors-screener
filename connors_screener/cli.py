#!/usr/bin/env python3
"""
CLI for screening stocks using various providers and configurations

Installed as the ``connors-scan`` console script; also runnable via
``python -m connors_screener.cli``.
"""

import argparse
import json
from pathlib import Path

from connors_screener.services.screener_service import ScreenerService


def parse_display_fields(display_fields_str: str, available_fields: dict) -> list[str]:
    """Parse and validate display fields string

    Fields can be either:
    1. Core StockData fields: symbol, name, price, volume, change, market_cap, sector, exchange, currency
    2. Provider-specific fields from --list-fields (stored in raw_data)

    Args:
        display_fields_str: Comma-separated field names
        available_fields: Available fields from provider's get_available_fields()

    Returns:
        List of validated field names
    """
    # Core StockData fields available for all providers
    core_fields = ["symbol", "name", "price", "volume", "change", "market_cap", "sector", "exchange", "currency"]

    # Default fields to display
    default_fields = ["symbol", "name", "price", "volume", "change"]

    if not display_fields_str:
        return default_fields

    # Parse comma-separated fields
    fields = [f.strip() for f in display_fields_str.split(",")]

    # Validate: fields must be either core fields or available provider fields
    valid_fields = set(core_fields) | set(available_fields.keys())
    invalid_fields = [f for f in fields if f not in valid_fields]

    if invalid_fields:
        raise ValueError(
            f"Invalid display fields: {', '.join(invalid_fields)}. "
            f"Valid core fields: {', '.join(core_fields)}. "
            f"Valid provider fields: {', '.join(sorted(available_fields.keys()))}. "
            f"Use --list-fields to see all available provider fields."
        )

    return fields


def format_field_value(field_name: str, value: any) -> str:
    """Format field value for display based on field name and value type

    Handles both core StockData fields and arbitrary provider fields.
    """
    if value is None:
        return "N/A"

    # Core field formatting
    if field_name == "price" or field_name == "close":
        try:
            val = float(value)
            return f"${val:,.2f}" if val > 0 else "N/A"
        except (ValueError, TypeError):
            return str(value)

    elif field_name == "volume" or "vol" in field_name.lower():
        try:
            val = float(value)
            if val >= 1_000_000_000:
                return f"{val/1_000_000_000:.2f}B"
            elif val >= 1_000_000:
                return f"{val/1_000_000:.2f}M"
            elif val > 0:
                return f"{val:,.0f}"
            return "N/A"
        except (ValueError, TypeError):
            return str(value)

    elif field_name == "change" or "change" in field_name.lower():
        try:
            val = float(value)
            return f"{val:+.2f}%" if val != 0 else "0.00%"
        except (ValueError, TypeError):
            return str(value)

    elif field_name == "market_cap" or field_name == "market_cap_basic" or field_name == "market_cap_calc":
        try:
            val = float(value)
            if val >= 1_000_000_000:
                return f"${val/1_000_000_000:.2f}B"
            elif val >= 1_000_000:
                return f"${val/1_000_000:.2f}M"
            elif val > 0:
                return f"${val:,.0f}"
            return "N/A"
        except (ValueError, TypeError):
            return str(value)

    # Try to detect numeric fields and format appropriately
    elif isinstance(value, (int, float)):
        if "ratio" in field_name.lower() or "ttm" in field_name.lower():
            return f"{value:.2f}" if value != 0 else "N/A"
        elif "pct" in field_name.lower() or "percent" in field_name.lower():
            return f"{value:.2f}%"
        elif abs(value) >= 1_000_000:
            # Large numbers
            if value >= 1_000_000_000:
                return f"{value/1_000_000_000:.2f}B"
            else:
                return f"{value/1_000_000:.2f}M"
        elif abs(value) < 1 and value != 0:
            # Small decimals
            return f"{value:.4f}"
        else:
            return f"{value:,.2f}"

    # String fields
    else:
        return str(value) if value else ""


def get_field_display_name(field: str) -> str:
    """Get human-readable field name for display

    Handles both core StockData fields and arbitrary provider fields.
    For unknown fields, creates a readable name from the field name.
    """
    # Known field display names
    field_names = {
        "symbol": "Symbol",
        "name": "Name",
        "price": "Price",
        "volume": "Volume",
        "change": "Change %",
        "market_cap": "Market Cap",
        "sector": "Sector",
        "exchange": "Exchange",
        "currency": "Currency",
        "close": "Close",
        "description": "Description",
        "market_cap_basic": "Market Cap",
        "market_cap_calc": "Market Cap",
        "price_earnings_ttm": "P/E (TTM)",
        "recommendation_mark": "Recommendation",
        "fundamental_currency_code": "Fund. Currency",
        "base_currency": "Base",
        "base_currency_desc": "Name",
        "crypto_total_rank": "Rank",
        "24h_close_change|5": "24h Change %",
        "24h_vol_cmc": "24h Volume",
        "24h_vol_to_market_cap": "Vol/MCap",
        "circulating_supply": "Circ. Supply",
        "socialdominance": "Social Dom.",
        "crypto_common_categories.tr": "Categories",
        "TechRating_1D": "Tech Rating",
        "logoid": "Logo ID",
        "update_mode": "Update Mode",
        "type": "Type",
        "typespecs": "Type Specs",
        "pricescale": "Price Scale",
        "minmov": "Min Move",
        "fractional": "Fractional",
        "minmove2": "Min Move 2"
    }

    if field in field_names:
        return field_names[field]

    # Generate readable name from field name
    # Replace underscores with spaces and title case
    return field.replace("_", " ").replace(".", " ").title()


def get_field_width(field: str) -> int:
    """Get appropriate column width for each field

    Returns appropriate width based on field name and type.
    """
    # Specific field widths
    widths = {
        "symbol": 10,
        "name": 28,
        "description": 30,
        "base_currency_desc": 25,
        "price": 15,
        "close": 15,
        "volume": 14,
        "24h_vol_cmc": 14,
        "change": 12,
        "24h_close_change|5": 14,
        "market_cap": 14,
        "market_cap_basic": 14,
        "market_cap_calc": 14,
        "sector": 20,
        "exchange": 12,
        "currency": 10,
        "price_earnings_ttm": 12,
        "recommendation_mark": 16,
        "crypto_total_rank": 8,
        "circulating_supply": 16,
        "24h_vol_to_market_cap": 12,
        "socialdominance": 14,
        "crypto_common_categories.tr": 20,
        "TechRating_1D": 12,
        "logoid": 15,
        "type": 12,
        "typespecs": 15,
        "pricescale": 12,
        "minmov": 10,
        "fractional": 12,
        "minmove2": 10
    }

    if field in widths:
        return widths[field]

    # Heuristics for unknown fields
    if "desc" in field.lower() or "name" in field.lower():
        return 25
    elif "volume" in field.lower() or "vol" in field.lower():
        return 14
    elif "price" in field.lower() or "close" in field.lower():
        return 15
    elif "cap" in field.lower():
        return 14
    elif "currency" in field.lower():
        return 10
    elif "id" in field.lower():
        return 15
    else:
        # Default width for unknown fields
        return 15


def main() -> None:
    """Main entry point for screening CLI"""

    screener_service = ScreenerService()

    parser = argparse.ArgumentParser(
        prog="connors-scan",
        description="Screen stocks using various providers and criteria.",
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="tv",
        help="Screener provider (e.g., tv for TradingView)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="rsi2",
        help="Screening configuration (e.g., rsi2, rsi2_high_volume)",
    )
    parser.add_argument(
        "--market",
        type=str,
        default="america",
        help="Market to scan (australia, america, brazil)",
    )
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available screener providers",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="List available screening configurations",
    )
    parser.add_argument(
        "--list-markets", action="store_true", help="List available markets"
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="List available data fields for each provider",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Load external configuration file (JSON/YAML)",
    )
    parser.add_argument(
        "--create-example-config",
        type=str,
        default=None,
        help="Create example configuration file at specified path",
    )
    parser.add_argument(
        "--parameters",
        type=str,
        default=None,
        help='Override configuration parameters (format: "key1:value1;key2:value2")',
    )
    parser.add_argument(
        "--show-parameters",
        action="store_true",
        help="Show available parameters for the specified configuration",
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="close",
        help="Field to sort by (close, volume, market_cap_basic, change, etc.)",
    )
    parser.add_argument(
        "--sort-order",
        type=str,
        default="asc",
        choices=["asc", "desc"],
        help="Sort order (asc or desc)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--output-format",
        type=str,
        default="table",
        choices=["table", "json"],
        help="Output format (table or json)",
    )
    parser.add_argument(
        "--display-fields",
        type=str,
        default=None,
        help='Comma-separated list of fields to display (e.g., "symbol,name,price,volume,change,currency,price_earnings_ttm"). Core fields: symbol, name, price, volume, change, market_cap, sector, exchange, currency. Provider-specific fields: Use --list-fields to see all available fields from each provider.',
    )
    parser.add_argument(
        "--post-filter",
        type=str,
        default=None,
        help='Named post-filter to apply client-side after provider returns results (e.g., "elephant_bars"). Use --list-post-filters to see available filters.',
    )
    parser.add_argument(
        "--post-filter-context",
        type=str,
        default=None,
        help='Extra parameters for the post-filter (format: "key1:value1;key2:value2")',
    )
    parser.add_argument(
        "--external-post-filter",
        type=str,
        default=None,
        help="Path to external Python file containing post-filter(s) (must call register_post_filter)",
    )
    parser.add_argument(
        "--list-post-filters",
        action="store_true",
        help="List available named post-filters",
    )

    args = parser.parse_args()

    # Handle utility commands
    if args.create_example_config:
        config_file_path = Path(args.create_example_config)
        format_type = "yaml" if config_file_path.suffix in [".yaml", ".yml"] else "json"
        if screener_service.create_example_config_file(config_file_path, format_type):
            return
        else:
            print(f"❌ Failed to create example config")
            return

    # Load external configuration file if provided
    if args.config_file:
        try:
            config_file_path = Path(args.config_file)
            registered_configs = screener_service.load_external_config_file(
                config_file_path
            )
            print(f"✅ Loaded external configurations: {', '.join(registered_configs)}")
        except Exception as e:
            print(f"❌ Failed to load config file: {e}")
            return

    # Handle list commands
    if args.list_providers:
        print("Available screener providers:")
        for provider in screener_service.get_providers():
            print(f"  - {provider}")
        return

    if args.list_configs:
        print("Available screening configurations by provider:")
        all_configs = screener_service.get_all_configs()
        for provider, config_names in all_configs.items():
            print(f"  {provider}:")
            for config_name in config_names:
                config_info = screener_service.get_config_info(provider, config_name)
                print(f"    - {config_name}: {config_info.get('description', '')}")
        return

    if args.list_markets:
        print("Available markets:")
        for market in screener_service.get_available_markets():
            market_info = screener_service.get_market_info(market)
            print(f"  - {market}: {market_info.get('symbolset', '')}")
        return

    if args.list_post_filters:
        from connors_screener.screening.post_filters import list_post_filters

        print("Available post-filters:")
        for name in list_post_filters():
            print(f"  - {name}")
        return

    if args.list_fields:
        print("Available data fields by provider:")
        print()
        all_fields = screener_service.get_all_provider_fields()
        for provider, fields in all_fields.items():
            provider_info = screener_service.get_provider_info().get(provider, {})
            provider_name = provider_info.get("name", provider)
            print(f"  {provider} ({provider_name}):")
            print(f"  {'-' * 60}")
            for field_name, field_desc in fields.items():
                print(f"    {field_name:<30} {field_desc}")
            print()
        return

    # Show parameters if requested
    if args.show_parameters:
        try:
            config_info = screener_service.get_config_info(args.provider, args.config)
            print(f"Configuration: {args.config} (provider: {args.provider})")
            print(f"Description: {config_info.get('description', '')}")
            print()
            print(screener_service.get_parameter_info(args.provider, args.config))
            return
        except Exception as e:
            print(f"❌ Error retrieving configuration: {e}")
            return

    # Execute screening
    try:
        print(f"🔍 Screening with provider: {args.provider}")
        print(f"📋 Configuration: {args.config}")
        market = (
            "crypto"
            if screener_service.contains_substring(args.config, "crypto")
            or screener_service.contains_substring(args.provider, "crypto")
            else args.market
        )
        print(f"🌍 Market: {market}")

        # Parse parameter overrides if provided
        parameter_overrides = {}
        if args.parameters:
            try:
                from connors_core.core.parameter_override import parse_parameter_string

                parameter_overrides = parse_parameter_string(args.parameters)
                print(f"📝 Parameter overrides: {parameter_overrides}")
            except ValueError as e:
                print(f"❌ Error parsing parameters: {e}")
                print('Expected format: --parameters "key1:value1;key2:value2"')
                return

        # Load external post-filter file if provided
        if args.external_post_filter:
            try:
                loaded = screener_service.load_external_post_filter(
                    args.external_post_filter
                )
                print(f"🔌 Loaded external post-filters: {', '.join(loaded)}")
                # Auto-select if exactly one filter was registered and --post-filter not given
                if not args.post_filter:
                    if len(loaded) == 1:
                        args.post_filter = loaded[0]
                    else:
                        print(
                            f"❌ External file registered {len(loaded)} filters: {', '.join(loaded)}. "
                            "Use --post-filter to select one."
                        )
                        return
            except Exception as e:
                print(f"❌ Failed to load external post-filter: {e}")
                return

        # Parse post-filter context if provided
        post_filter_context = None
        if args.post_filter_context:
            try:
                from connors_core.core.parameter_override import parse_parameter_string

                post_filter_context = parse_parameter_string(args.post_filter_context)
                print(f"🔧 Post-filter context: {post_filter_context}")
            except ValueError as e:
                print(f"❌ Error parsing post-filter context: {e}")
                print('Expected format: --post-filter-context "key1:value1;key2:value2"')
                return

        if args.post_filter:
            print(f"🔎 Post-filter: {args.post_filter}")

        print("-" * 50)

        # Execute screening using service
        result = screener_service.run_screening(
            provider=args.provider,
            config=args.config,
            market=args.market,
            parameters=parameter_overrides,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
            post_filter=args.post_filter,
            post_filter_context=post_filter_context,
        )

        # Get config info for display
        config_info = screener_service.get_config_info(args.provider, args.config)
        print(f"Using config: {config_info.get('name', args.config)}")
        print(f"Parameters: {config_info.get('parameters', {})}")

        if args.verbose:
            print(f"Filters: {config_info.get('filters', [])}")

        print("-" * 50)

        # Get available fields from provider
        provider_fields = screener_service.get_provider_fields(args.provider)

        # Parse display fields
        try:
            display_fields = parse_display_fields(args.display_fields, provider_fields)
        except ValueError as e:
            print(f"❌ {e}")
            print(f"💡 Tip: Use --list-fields to see all available fields for provider '{args.provider}'")
            return

        # Handle JSON output format
        if args.output_format == "json":
            # Filter data based on display_fields
            filtered_data = []
            if result.data:
                for stock in result.data:
                    stock_dict = {}
                    for field in display_fields:
                        stock_dict[field] = stock.get_field(field)
                    filtered_data.append(stock_dict)

            output_data = {
                "provider": result.provider,
                "config_name": result.config_name,
                "timestamp": result.timestamp,
                "market": result.metadata.get("market", ""),
                "filters_applied": result.metadata.get("filters_applied", 0),
                "sort_by": args.sort_by,
                "sort_order": args.sort_order,
                "total_results": len(result.symbols),
                "symbols": result.symbols,
                "data": filtered_data,
                "displayed_fields": display_fields,
                "metadata": result.metadata,
            }
            print(json.dumps(output_data, indent=2))
            return

        # Display results (table format)
        print(f"✅ Screening completed!")
        print(f"📊 Found {len(result.symbols)} symbols (sorted by {args.sort_by} {args.sort_order}):")
        print()

        # Display detailed data table if available
        if result.data and len(result.data) > 0:
            # Build dynamic table based on display_fields
            # Calculate column widths
            col_widths = [get_field_width(field) for field in display_fields]
            num_col_width = 5  # Width for the # column

            # Build header separator
            header_sep_parts = ["─" * num_col_width]
            header_sep_parts.extend(["─" * width for width in col_widths])
            top_border = "┌" + "┬".join(header_sep_parts) + "┐"
            mid_border = "├" + "┼".join(header_sep_parts) + "┤"
            bot_border = "└" + "┴".join(header_sep_parts) + "┘"

            # Build header row
            header_parts = [f"{'#':^{num_col_width}}"]
            for field in display_fields:
                display_name = get_field_display_name(field)
                width = get_field_width(field)
                header_parts.append(f" {display_name:<{width-2}} ")
            header_row = "│".join(header_parts)

            # Print table header
            print(top_border)
            print(f"│{header_row}│")
            print(mid_border)

            # Table rows
            for i, stock in enumerate(result.data, 1):
                row_parts = [f"{i:^{num_col_width}}"]

                for field in display_fields:
                    value = stock.get_field(field)
                    formatted_value = format_field_value(field, value)
                    width = get_field_width(field)

                    # Truncate if too long
                    if len(formatted_value) > width - 2:
                        formatted_value = formatted_value[:width-5] + "..."

                    # Right-align numeric fields, left-align text fields
                    if field in ["price", "volume", "change", "market_cap"]:
                        row_parts.append(f" {formatted_value:>{width-2}} ")
                    else:
                        row_parts.append(f" {formatted_value:<{width-2}} ")

                print(f"│{'│'.join(row_parts)}│")

            print(bot_border)
        else:
            # Fallback to simple list if detailed data not available
            print("-" * 30)
            for i, symbol in enumerate(result.symbols, 1):
                print(f"{i:3d}. {symbol}")
            print("-" * 30)

        print()
        print(f"Provider: {result.provider}")
        print(f"Market: {result.metadata['market']}")
        print(f"Filters applied: {result.metadata['filters_applied']}")
        print(f"Sort: {args.sort_by} ({args.sort_order})")
        print(f"Timestamp: {result.timestamp}")

        if args.verbose:
            print(f"Full metadata: {result.metadata}")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print(
            "\nUse --list-providers, --list-configs, or --list-markets for available options"
        )
    except Exception as e:
        print(f"❌ Screening failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
