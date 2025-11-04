# Blockstream Esplora API Analysis

## Summary

Real-time Bitcoin explorer API with NO built-in historical time-series endpoints.

## Base URL

`https://blockstream.info/api/`

## Available Endpoints (Real-time only)

### 1. Current Mempool

- **URL**: `https://blockstream.info/api/mempool`
- **Returns**: Current mempool state (count, vsize, total_fee, fee_histogram)
- **Frequency**: Real-time snapshot (on-demand)

### 2. Fee Estimates

- **URL**: `https://blockstream.info/api/fee-estimates`
- **Returns**: Fee estimates for different confirmation targets (blocks)
- **Format**: `{blocks: fee_rate_sat_vB}`

### 3. Block Data

- **URL**: `https://blockstream.info/api/blocks/{start_height}`
- **Returns**: 10 blocks per request
- **Fields**: height, timestamp, tx_count, size, weight
- **Can be used to construct historical**: YES (by iterating block heights)

### 4. Block by Height

- **URL**: `https://blockstream.info/api/block-height/{height}`
- **Returns**: Block hash for given height
- **Historical Access**: YES (back to genesis block)

### 5. Transaction History

- **URL**: `https://blockstream.info/api/address/{address}/txs`
- **Returns**: Up to 50 mempool + 25 confirmed txs per page
- **Pagination**: Available via last_seen_txid parameter

## Data Format Examples

```json
// Mempool
{
  "count": 40503,
  "vsize": 21152108,
  "total_fee": 5866355,
  "fee_histogram": [[5.01, 51181], ...]
}

// Fee Estimates
{
  "1": 3.15,
  "2": 3.15,
  "3": 2.134,
  "144": 1.012,
  "504": 0.706,
  "1008": 0.706
}
```

## Historical Data Capabilities

- ❌ No built-in time-series statistics endpoints
- ❌ No historical charts API
- ✅ Can reconstruct historical data by:
  - Iterating through block heights
  - Polling at regular intervals (requires self-hosting)
- ✅ Block data back to genesis (2009)

## Rate Limits

- **Not officially documented**
- **Public API**: Appears to have rate limiting
- **Self-hosted**: No limits (open source)

## Monitoring/Time Series

- **Prometheus exporter available** for self-hosted instances
- **Grafana integration** for time-series visualization
- **Requires self-hosting** for historical time-series collection

## Data Types

- ✅ Real-time mempool state
- ✅ Fee estimates (next 1-1008 blocks)
- ✅ Block data (height, timestamp, tx count)
- ✅ Transaction history (address-based)
- ❌ No historical time-series charts
- ❌ No OHLCV price data

## Verdict

**NOT SUITABLE** for high-frequency historical data research. Real-time API only.
Suitable for current state queries, but requires self-polling for time-series.
Use mempool.space or blockchain.info for historical time-series instead.
