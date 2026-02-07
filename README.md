# connors-screener

> Part of the [Connors Trading System](https://github.com/marcelohack/connors-playground)

## Overview

Stock and cryptocurrency screening system with support for multiple providers (TradingView, Finviz), built-in configurations, runtime parameter overrides, and external configuration files. Provides both a programmatic API and integration with the playground CLI.

## Features

- **Multiple Providers**: TradingView (stocks + crypto) and Finviz screening
- **12 Built-in Configurations**: RSI2, momentum, value, and crypto screening presets
- **Runtime Parameter Overrides**: Customize any configuration parameter at execution time
- **External Configurations**: Load custom screening configs from YAML/JSON files
- **Dynamic Field Display**: Show any provider field in output, not just core fields
- **Market Support**: US, Australian, Brazilian markets plus crypto

## Installation

```bash
pip install connors-screener
```

For development:

```bash
git clone https://github.com/marcelohack/connors-screener.git
cd connors-screener
pip install -e ".[dev]"
```

## Quick Start

### Programmatic API

```python
from connors_screener.services.screener_service import ScreenerService

service = ScreenerService()

# Run screening
result = service.run_screening(
    provider="tv",
    config="rsi2",
    market="america",
    parameter_string="rsi_level:8"
)

# Access results
for stock in result.data:
    print(f"{stock.symbol}: ${stock.price:.2f} (RSI2 oversold)")

# List available providers and configs
print(service.get_providers())           # ['tv', 'tv_crypto', 'finviz']
print(service.get_all_configs())         # {'tv': ['rsi2', ...], ...}
print(service.get_available_markets())   # ['america', 'australia', 'brazil']
```

## CLI Usage

The screening CLI is part of [connors-playground](https://github.com/marcelohack/connors-playground):

```bash
# Basic stock screening
python -m connors.cli.screener --provider tv --config rsi2 --market australia

# High-volume RSI2 screening
python -m connors.cli.screener --provider tv --config rsi2_high_volume --market america

# Momentum breakout screening
python -m connors.cli.screener --provider tv --config momentum_breakout --market america

# Cryptocurrency screening
python -m connors.cli.screener --provider tv_crypto --config crypto_basic
python -m connors.cli.screener --provider tv_crypto --config crypto_high_volume

# Parameter overrides
python -m connors.cli.screener --provider tv --config rsi2 --parameters "rsi_level:10;rsi_period:3"

# Show available parameters for a config
python -m connors.cli.screener --provider tv --config rsi2 --show-parameters

# Custom field display
python -m connors.cli.screener --provider tv --config rsi2 --market australia \
    --display-fields "symbol,price,price_earnings_ttm,recommendation_mark,currency"

# External configuration file
python -m connors.cli.screener --config-file my_config.yaml --provider tv --config custom_momentum

# List available options
python -m connors.cli.screener --list-providers
python -m connors.cli.screener --list-configs
python -m connors.cli.screener --list-markets
python -m connors.cli.screener --list-fields
```

## Built-in Configurations

### TradingView Stock Configs (`--provider tv`)

| Config | Description | Key Parameters |
|--------|-------------|----------------|
| `rsi2` | RSI2 < 5 oversold screening | `rsi_level: 5` |
| `rsi2_high_volume` | RSI2 + high volume (5M+) | `rsi_level: 5`, `volume_threshold: 5M` |
| `rsi2_relaxed` | RSI2 < 10, lower volume | `rsi_level: 10`, `volume_threshold: 500K` |
| `momentum_breakout` | 5%+ daily gain + volume surge | `price_change_pct: 5.0`, `min_price: 5.0` |
| `momentum_strong` | 10%+ gain, large cap | `price_change_pct: 10.0`, `market_cap_min: 500M` |
| `value_low_pe` | P/E < 15, decent liquidity | `max_pe_ratio: 15.0`, `min_volume: 500K` |
| `value_undervalued` | P/E < 12, dividend > 2% | `max_pe_ratio: 12.0`, `min_dividend_yield: 2.0` |

### Finviz Configs (`--provider finviz`)

| Config | Description | Key Parameters |
|--------|-------------|----------------|
| `rsi2` | RSI2 < 5 with market cap filter | `rsi_level: 5` |
| `rsi2_large_cap` | Large-cap (>$2B) RSI2 | `rsi_level: 5`, `focus: large_cap` |

### TradingView Crypto Configs (`--provider tv_crypto`)

| Config | Description | Key Parameters |
|--------|-------------|----------------|
| `crypto_basic` | Basic crypto, 50M+ volume | `min_volume: 50M` |
| `crypto_high_volume` | High volume crypto, 500M+ | `min_volume: 500M` |
| `crypto_top_100` | Top 100 by rank, 100M+ vol | `min_volume: 100M` |

## External Configuration

Create custom screening configurations in YAML or JSON:

```yaml
configurations:
  - name: custom_momentum
    provider: tv
    description: Custom momentum screening
    parameters:
      price_change_pct: 5.0
      volume_multiplier: 2.0
    provider_config:
      volume_threshold: 500000
    filters:
      - field: change
        operation: greater
        value: 5.0
      - field: volume
        operation: greater
        value: 500000
```

```bash
# Generate example config file
python -m connors.cli.screener --create-example-config my_config.yaml

# Use external config
python -m connors.cli.screener --config-file my_config.yaml --provider tv --config custom_momentum
```

## Available Providers

### TradingView (`tv`)
- **Markets**: america, australia, brazil
- **Core fields**: symbol, name, price, volume, change, market_cap, sector, exchange, currency
- **Extended fields**: price_earnings_ttm, recommendation_mark, logoid, type, pricescale

### Finviz (`finviz`)
- **Markets**: america only
- **Core fields**: symbol, name, price, volume, change, market_cap, sector, exchange

### TradingView Crypto (`tv_crypto`)
- **Markets**: crypto (no market parameter needed)
- **Core fields**: symbol, price, volume, change, market_cap
- **Extended fields**: base_currency, crypto_total_rank, 24h_vol_cmc, circulating_supply, socialdominance

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=connors_screener
```

## Related Packages

| Package | Description | Links |
|---------|-------------|-------|
| [connors-playground](https://github.com/marcelohack/connors-playground) | CLI + Streamlit UI (integration hub) | [README](https://github.com/marcelohack/connors-playground#readme) |
| [connors-core](https://github.com/marcelohack/connors-core) | Registry, config, indicators, metrics | [README](https://github.com/marcelohack/connors-core#readme) |
| [connors-backtest](https://github.com/marcelohack/connors-backtest) | Backtesting service + built-in strategies | [README](https://github.com/marcelohack/connors-backtest#readme) |
| [connors-strategies](https://github.com/marcelohack/connors-strategies) | Trading strategy collection (private) | — |
| [connors-datafetch](https://github.com/marcelohack/connors-datafetch) | Multi-source data downloader | [README](https://github.com/marcelohack/connors-datafetch#readme) |
| [connors-sr](https://github.com/marcelohack/connors-sr) | Support & Resistance calculator | [README](https://github.com/marcelohack/connors-sr#readme) |
| [connors-regime](https://github.com/marcelohack/connors-regime) | Market regime detection | [README](https://github.com/marcelohack/connors-regime#readme) |
| [connors-bots](https://github.com/marcelohack/connors-bots) | Automated trading bots | [README](https://github.com/marcelohack/connors-bots#readme) |

## License

MIT
