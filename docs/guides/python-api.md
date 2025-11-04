---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Python API Reference

**Status**: 🚧 Pending Phase 1 implementation

This document will provide comprehensive Python API documentation for programmatic data collection.

## Planned Content

### Core API Functions

#### `fetch_snapshots(chain, start, end, **kwargs)`

Fetch historical blockchain network data snapshots.

```python
import gapless_network_data as gnd
import pandas as pd

# Fetch Ethereum block data (12-second intervals)
df_eth: pd.DataFrame = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01 00:00:00",
    end="2024-01-01 06:00:00"
)

# Returns: DatetimeIndex DataFrame with 6 columns
# (number, timestamp, baseFeePerGas, gasUsed, gasLimit, transactions)
```

**Parameters**:

- `chain` (str): Chain identifier ("ethereum", "bitcoin", "solana", etc.)
- `start` (str | datetime): Start timestamp (ISO 8601 format)
- `end` (str | datetime): End timestamp (ISO 8601 format)
- `output_format` (str, optional): "pandas" (default) or "polars"
- `validate` (bool, optional): Run validation pipeline (default: True)

**Returns**: `pd.DataFrame` with DatetimeIndex

**Raises**:

- `MempoolHTTPException`: API request failed
- `MempoolValidationException`: Data quality check failed
- `ValueError`: Invalid parameters

---

#### `get_latest_snapshot(chain, **kwargs)`

Fetch the most recent snapshot for a blockchain.

```python
# Get latest Ethereum block
block = gnd.get_latest_snapshot(chain="ethereum")

print(f"Block number: {block['number']}")
print(f"Base fee: {block['baseFeePerGas']} wei")
print(f"Gas used: {block['gasUsed']:,}")
print(f"Transactions: {block['transactions']}")
```

**Parameters**:

- `chain` (str): Chain identifier ("ethereum", "bitcoin", "solana", etc.)
- `validate` (bool, optional): Run validation pipeline (default: True)

**Returns**: `dict` with snapshot data

**Raises**:

- `MempoolHTTPException`: API request failed
- `MempoolValidationException`: Data quality check failed

---

### Advanced Features

#### Multi-Chain Collection

```python
# Collect from multiple chains in parallel
import asyncio

async def collect_multi_chain():
    eth_task = gnd.fetch_snapshots_async(chain="ethereum", start="2024-01-01", end="2024-01-02")
    btc_task = gnd.fetch_snapshots_async(chain="bitcoin", start="2024-01-01", end="2024-01-02")

    eth_df, btc_df = await asyncio.gather(eth_task, btc_task)
    return eth_df, btc_df

eth_df, btc_df = asyncio.run(collect_multi_chain())
```

#### Custom Validation Rules

```python
# Define custom validation rules
from gapless_network_data.validation import ValidationRule

custom_rule = ValidationRule(
    name="ethereum_base_fee_spike",
    check=lambda df: df['baseFeePerGas'].pct_change().abs() < 0.5,
    message="Base fee changed more than 50% between blocks"
)

df = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01",
    end="2024-01-02",
    validation_rules=[custom_rule]
)
```

#### Gap Detection and Backfill

```python
# Detect gaps in collected data
from gapless_network_data.validation import detect_gaps

gaps = detect_gaps(
    chain="ethereum",
    data_dir="./data",
    start="2024-01-01",
    end="2024-01-31"
)

print(f"Found {len(gaps)} gaps:")
for gap in gaps:
    print(f"  {gap['start']} to {gap['end']} ({gap['duration']})")

# Automatic backfill
gnd.backfill_gaps(chain="ethereum", data_dir="./data", gaps=gaps)
```

---

### Exception Handling

```python
from gapless_network_data import (
    MempoolHTTPException,
    MempoolValidationException,
    MempoolRateLimitException
)

try:
    df = gnd.fetch_snapshots(
        chain="ethereum",
        start="2024-01-01",
        end="2024-01-02"
    )
except MempoolHTTPException as e:
    print(f"API error: {e.message}")
    print(f"Endpoint: {e.endpoint}")
    print(f"HTTP status: {e.http_status}")
except MempoolValidationException as e:
    print(f"Validation failed: {e.message}")
    print(f"Failed checks: {e.failed_checks}")
except MempoolRateLimitException as e:
    print(f"Rate limited: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
```

---

### Configuration

```python
# Set global configuration
gnd.config.set(
    llamarpc_url="https://eth.llamarpc.com",
    mempool_space_url="https://mempool.space",
    max_retries=3,
    retry_backoff=2.0,
    enable_etag_caching=True,
    validation_level="strict"
)

# Per-request configuration
df = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01",
    end="2024-01-02",
    max_retries=5,
    timeout=30
)
```

---

## Current Quick Start

Until this document is completed, refer to:

- [README.md](/Users/terryli/eon/gapless-network-data/README.md) - Python API quick start (lines 30-64)
- [CLAUDE.md](/Users/terryli/eon/gapless-network-data/CLAUDE.md) - API design patterns
- [src/gapless_network_data/api.py](/Users/terryli/eon/gapless-network-data/src/gapless_network_data/api.py) - Source code

**Example from README.md**:

```python
import gapless_network_data as gnd

# Fetch Ethereum block data (12-second intervals)
df_eth = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01 00:00:00",
    end="2024-01-01 06:00:00"
)

# Get latest Ethereum block
block = gnd.get_latest_snapshot(chain="ethereum")
print(f"Block number: {block['number']}")
print(f"Base fee: {block['baseFeePerGas']} wei")
```

---

**Related Documentation**:

- [Data Collection Guide](/Users/terryli/eon/gapless-network-data/docs/guides/DATA_COLLECTION.md) - CLI usage
- [Feature Engineering Guide](/Users/terryli/eon/gapless-network-data/docs/guides/FEATURE_ENGINEERING.md) - Cross-domain features

**This document will be completed during Phase 1 implementation.**
