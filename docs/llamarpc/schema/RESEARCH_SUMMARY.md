# Ethereum/LlamaRPC Research Summary

**Research Date**: 2025-11-04
**Working Directory**: `/tmp/llamarpc-schema-research`
**Data Source**: LlamaRPC (https://eth.llamarpc.com)

## Executive Summary

This research documents the complete schema and available network metrics from Ethereum block data via LlamaRPC. The research covers block structure, transaction format, fee history API, and derivable metrics for network monitoring and analysis.

## Key Findings

### 1. Complete Block Schema (26 Fields)

**Core Fields**:

- `baseFeePerGas`, `gasLimit`, `gasUsed` - Gas market data
- `blobGasUsed`, `excessBlobGas` - EIP-4844 blob transaction data (Cancun fork)
- `withdrawals`, `withdrawalsRoot` - Validator withdrawals (Shanghai fork)
- `parentBeaconBlockRoot` - Consensus layer link (Cancun fork)
- `timestamp`, `number`, `hash`, `parentHash` - Block identification

**Post-Merge Changes**:

- `difficulty` = always `0x0`
- `nonce` = always `0x0000000000000000`
- `uncles` = always empty array `[]`

**Builder Information**:

- `miner` - Builder address
- `extraData` - Builder tag/signature (e.g., "Titan (titanbuilder.xyz)")

### 2. Transaction Schema (24 Fields)

**Transaction Types**:

- Type 0: Legacy transactions (pre-EIP-2718)
- Type 1: EIP-2930 (with access lists)
- Type 2: EIP-1559 (dynamic fees) - **Most common**
- Type 3: EIP-4844 (blob transactions)

**EIP-1559 Fee Fields**:

- `maxFeePerGas` - Maximum total fee willing to pay
- `maxPriorityFeePerGas` - Maximum tip to builder
- `gasPrice` - Effective gas price paid

**Gas Price Calculation**:

```python
effective_priority = min(maxPriorityFeePerGas, maxFeePerGas - baseFeePerGas)
effective_gas_price = baseFeePerGas + effective_priority
```

### 3. Fee History API

**Method**: `eth_feeHistory`
**Parameters**: `[blockCount, newestBlock, rewardPercentiles]`

**Response Fields**:

- `baseFeePerGas` - Array of base fees (length = blockCount + 1, includes next block prediction)
- `baseFeePerBlobGas` - Array of blob base fees (length = blockCount + 1)
- `gasUsedRatio` - Array of gas utilization ratios (length = blockCount)
- `blobGasUsedRatio` - Array of blob utilization ratios (length = blockCount)
- `reward` - Array of arrays containing priority fee percentiles (length = blockCount)

**Important**: The `baseFeePerGas` array has one extra element (next block prediction).

### 4. Withdrawal Schema

**Fields**:

- `address` - Recipient address
- `amount` - **In Gwei, not wei!** (1 Gwei = 10^9 wei)
- `index` - Global withdrawal counter
- `validatorIndex` - Beacon chain validator ID

**Conversion**:

```python
eth_amount = int(withdrawal["amount"], 16) / 1e9  # Gwei to ETH
```

## Derivable Network Metrics

### Block-Level Metrics

| Metric              | Calculation                        | Example Value |
| ------------------- | ---------------------------------- | ------------- |
| Gas Utilization     | `gasUsed / gasLimit * 100`         | 42.36%        |
| Base Fee (Gwei)     | `int(baseFeePerGas, 16) / 1e9`     | 0.914 gwei    |
| Transaction Count   | `len(transactions)`                | 200 txs       |
| Avg Gas/Tx          | `gasUsed / len(transactions)`      | 95,208 gas    |
| Block Size (KB)     | `int(size, 16) / 1024`             | 159.50 KB     |
| Block Size (MB)     | `int(size, 16) / 1,048,576`        | 0.16 MB       |
| Blob Utilization    | `blobGasUsed / (6 * 131072) * 100` | 100.00%       |
| Blob Count          | `blobGasUsed // 131072`            | ~6 blobs      |
| Withdrawal Count    | `len(withdrawals)`                 | 16            |
| Total Withdrawn ETH | `sum(amounts) / 1e9`               | 0.332 ETH     |

### Fee Market Metrics

| Metric                   | Source                          | Description                                |
| ------------------------ | ------------------------------- | ------------------------------------------ |
| Base Fee Trend           | `eth_feeHistory`                | Percentage change over N blocks            |
| Priority Fee Percentiles | `eth_feeHistory.reward`         | 25th/50th/75th percentile tips             |
| Network Congestion       | `eth_feeHistory.gasUsedRatio`   | Low (<50%), Moderate (50-80%), High (>80%) |
| Recommended Gas Prices   | `baseFee + priority_percentile` | Slow/Standard/Fast options                 |

### Timestamp Metrics

```python
block_time = current_timestamp - previous_timestamp  # Typically ~12 seconds
datetime_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
```

### Efficiency Metrics

```python
gas_efficiency = gasUsed / gasLimit  # How full is the block
bytes_per_gas = blockSize / gasUsed  # Data density
tx_density = txCount / gasUsed * 1000  # Txs per 1000 gas units
```

## Working Examples

### 1. Simple Metrics Collection

See `/tmp/llamarpc-schema-research/simple_metrics.py`:

- Uses only Python standard library (no external dependencies)
- Demonstrates 10+ key metrics
- Includes gas prices, congestion, withdrawals, blobs
- **Verified working** on 2025-11-04

**Sample Output**:

```
📦 Block #23,724,279
   Utilization: 42.36%
   Base Fee: 0.914 gwei
   Transactions: 200
   Blob Utilization: 100.00%
   Withdrawals: 16 (0.332 ETH)
   Congestion: LOW

⚡ Recommended Gas Prices:
   🐢 Slow:     0.946 gwei
   🚶 Standard: 0.996 gwei
   🚀 Fast:     1.896 gwei
```

### 2. Full-Featured Class

See `/tmp/llamarpc-schema-research/examples.py`:

- Complete `EthereumMetricsCollector` class
- 15+ metric calculation methods
- Comprehensive reporting functions
- Requires `requests` library

## Hex Value Conversion Reference

All numeric values are returned as hexadecimal strings with `0x` prefix.

```python
# Block number
block_num = int("0x16a00e1", 16)  # 23,593,185

# Gas values (in gas units)
gas_used = int("0x13892e4", 16)  # 20,456,676

# Fee values (in wei)
base_fee_wei = int("0x3b35c053", 16)  # 995,074,643 wei
base_fee_gwei = base_fee_wei / 1e9    # 0.995 gwei

# ETH values (wei to ETH)
value_eth = int("0x10fa186", 16) / 1e18  # For transaction values

# Withdrawal amounts (Gwei to ETH)
withdrawal_eth = int("0x10fa186", 16) / 1e9  # NOTE: Withdrawals are in Gwei!

# Timestamps (seconds, not milliseconds)
timestamp = int("0x6909a133", 16)  # 1762017587
dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
```

## Undocumented/Interesting Findings

### 1. Builder Tags in `extraData`

The `extraData` field contains builder signatures and vanity text:

- "Titan (titanbuilder.xyz)"
- "Builder+ www.btcs.com/builder"
- Can be decoded from hex to UTF-8 (with error handling)

### 2. Blob Market Activity (EIP-4844)

- Max 6 blobs per block (6 × 131,072 gas = 786,432 gas)
- `blobGasUsedRatio` provides pre-calculated utilization
- Observed 100% utilization during research period
- `baseFeePerBlobGas` tracks blob-specific fee market

### 3. Fee History Array Lengths

**Critical**: Different arrays have different lengths:

- `baseFeePerGas`: length = N + 1 (includes next block prediction)
- `baseFeePerBlobGas`: length = N + 1 (includes next block prediction)
- `gasUsedRatio`: length = N
- `blobGasUsedRatio`: length = N
- `reward`: length = N

This asymmetry is intentional - base fee arrays include a prediction for the next block.

### 4. Withdrawal Amounts Are in Gwei

**Important**: Unlike all other values (which are in wei), withdrawal amounts are in **Gwei**.

Conversion:

```python
# WRONG - treats as wei
wrong_eth = int(withdrawal["amount"], 16) / 1e18  # Off by 1e9!

# CORRECT - treats as gwei
correct_eth = int(withdrawal["amount"], 16) / 1e9
```

### 5. Priority Fee Percentiles

The `reward` array in `eth_feeHistory` provides percentile data for priority fees:

- Lower percentiles (25th) = slower confirmation, cheaper
- Higher percentiles (75th) = faster confirmation, more expensive
- Can be used to build gas price estimators

### 6. Network Congestion Patterns

From 20-block sample (2025-11-04 06:50 UTC):

- Average gas utilization: 48.91% (LOW congestion)
- Base fee trend: -7.81% (decreasing)
- Median priority fee: 0.100 gwei
- Blob utilization: Variable (0% to 100%)

## File Inventory

| File                       | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| `ETHEREUM_BLOCK_SCHEMA.md` | Complete field documentation (26 block fields, 24 tx fields) |
| `schemas.json`             | JSON Schema definitions for validation                       |
| `simple_metrics.py`        | Working Python example (stdlib only)                         |
| `examples.py`              | Full-featured metrics collector class                        |
| `RESEARCH_SUMMARY.md`      | This file                                                    |
| `block_without_txs.json`   | Sample block data (tx hashes only)                           |
| `full_block_with_txs.json` | Sample block data (full tx objects, 624KB)                   |
| `transaction_detail.json`  | Sample transaction object                                    |
| `fee_history.json`         | Sample fee history response                                  |

## Comparison with Bitcoin Mempool Data

**For gapless-network-data implementation**:

### Similarities

- Both use REST APIs with JSON responses
- Both require hex-to-decimal conversion
- Both track network congestion metrics
- Both have timestamp-based data points

### Key Differences

| Aspect             | Ethereum (This Research)   | Bitcoin Mempool (Target)   |
| ------------------ | -------------------------- | -------------------------- |
| **Block Time**     | ~12 seconds (consistent)   | ~10 minutes (variable)     |
| **Fee Model**      | EIP-1559 (base + priority) | Sat/vB (auction)           |
| **Data Frequency** | Per-block snapshots        | 1-minute snapshots         |
| **API Complexity** | Multiple transaction types | Single fee rate model      |
| **Data Size**      | ~160KB per block           | Unknown (to be determined) |
| **Hex Encoding**   | All numeric values         | Unknown (to be determined) |

### Architectural Insights

1. **Validation Approach**: Similar to gapless-crypto-data, validation should be exception-only
2. **Timestamp Handling**: Ethereum uses seconds (not milliseconds) - check mempool.space API
3. **Hex Conversion**: All numeric values need `int(value, 16)` conversion
4. **Schema Evolution**: EIP-based upgrades add new fields - mempool.space may have similar versioning
5. **Rate Limiting**: LlamaRPC appears generous - mempool.space allows 10 req/sec (no auth)

## Next Steps for gapless-network-data

1. **Verify mempool.space Schema**:
   - Check if values are hex or decimal
   - Verify timestamp format (seconds vs milliseconds)
   - Document all available fields

2. **Design Data Collection**:
   - 1-minute intervals (vs Ethereum's per-block)
   - ETag caching for bandwidth optimization
   - Retry logic with exponential backoff

3. **Define Validation Rules**:
   - Fee rate sanity checks (1-1000 sat/vB)
   - Gap detection (missing 1-minute intervals)
   - Anomaly detection (z-score on vsize, fee spikes)

4. **Implement Metric Calculations**:
   - Fee pressure: `fastest_fee / economy_fee`
   - Congestion z-score: `(count - mean) / std`
   - Temporal alignment with OHLCV data (DatetimeIndex join)

## References

- **LlamaRPC**: https://eth.llamarpc.com
- **EIP-1559**: Base fee mechanism (London fork)
- **EIP-4844**: Blob transactions (Cancun fork)
- **EIP-4895**: Beacon chain withdrawals (Shanghai fork)
- **Ethereum JSON-RPC Spec**: https://ethereum.org/en/developers/docs/apis/json-rpc/

## Conclusion

This research provides a complete reference for Ethereum block and transaction schemas via LlamaRPC. All documented fields have been verified with real data, and working Python examples demonstrate practical metric calculations. The schema is stable post-Merge with incremental additions via EIPs.

**Key Takeaway**: Ethereum's RPC API provides rich, structured data suitable for time-series analysis, congestion monitoring, and fee estimation. The fee history API is particularly valuable for real-time gas price recommendations.
