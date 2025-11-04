# Ethereum to Bitcoin Mempool Metric Mapping

**Purpose**: Map Ethereum network metrics to equivalent Bitcoin mempool metrics for `gapless-network-data` implementation

## Conceptual Mapping

### Network Congestion Metrics

| Ethereum Metric          | Calculation                                | Bitcoin Mempool Equivalent       | Notes                            |
| ------------------------ | ------------------------------------------ | -------------------------------- | -------------------------------- |
| Gas Utilization          | `gasUsed / gasLimit`                       | Mempool size / typical size      | Lower granularity on Bitcoin     |
| Base Fee (Gwei)          | `baseFeePerGas / 1e9`                      | N/A                              | No base fee in Bitcoin           |
| Priority Fee Percentiles | `reward[i][percentile]`                    | Fee rate percentiles (sat/vB)    | Similar concept                  |
| Congestion Level         | <50% = low, 50-80% = moderate, >80% = high | Based on mempool size & tx count | Classification thresholds differ |

### Transaction Volume Metrics

| Ethereum Metric   | Calculation                  | Bitcoin Mempool Equivalent    | Notes                              |
| ----------------- | ---------------------------- | ----------------------------- | ---------------------------------- |
| Transaction Count | `len(block['transactions'])` | Unconfirmed transaction count | Per-block vs snapshot              |
| Avg Gas/Tx        | `gasUsed / txCount`          | N/A                           | Gas model doesn't exist in Bitcoin |
| Block Size (KB)   | `size / 1024`                | Mempool vsize (MB)            | Different units                    |

### Fee Market Metrics

| Ethereum Metric            | Calculation                         | Bitcoin Mempool Equivalent | Notes            |
| -------------------------- | ----------------------------------- | -------------------------- | ---------------- |
| Base Fee Trend             | `(current - oldest) / oldest * 100` | Fee rate trend             | Similar analysis |
| Recommended Gas (Slow)     | `baseFee + priority_25th`           | Economy fee rate           | 25th percentile  |
| Recommended Gas (Standard) | `baseFee + priority_50th`           | Hour fee rate              | 50th percentile  |
| Recommended Gas (Fast)     | `baseFee + priority_75th`           | Fastest fee rate           | 75th percentile  |

### Time-Series Metrics

| Ethereum Metric | Calculation                  | Bitcoin Mempool Equivalent | Notes              |
| --------------- | ---------------------------- | -------------------------- | ------------------ |
| Block Time      | `timestamp - prev_timestamp` | N/A (1-minute snapshots)   | Different cadence  |
| Timestamp       | Unix seconds                 | Unix seconds               | Likely same format |

## Ethereum-Specific Metrics (No Bitcoin Equivalent)

### Blob Transactions (EIP-4844)

- `blobGasUsed / maxBlobGas` - Blob utilization
- `baseFeePerBlobGas` - Blob-specific fee market
- Estimated blob count

**Note**: No equivalent in Bitcoin. L2 rollups use Ethereum blobs.

### Validator Withdrawals (EIP-4895)

- Withdrawal count per block
- Total ETH withdrawn
- Validator index tracking

**Note**: No equivalent in Bitcoin. PoS-specific.

### Builder Information

- Builder address (`miner` field)
- Builder tag (`extraData` field)

**Note**: Bitcoin has mining pools, but not exposed in mempool.space API.

## Bitcoin-Specific Metrics (No Ethereum Equivalent)

### Expected from mempool.space

Based on mempool.space documentation and gapless-network-data schema:

| Bitcoin Metric         | Expected Field      | Description                |
| ---------------------- | ------------------- | -------------------------- |
| Unconfirmed TX Count   | `unconfirmed_count` | Total pending transactions |
| Mempool Size (MB)      | `vsize_mb`          | Virtual size of mempool    |
| Total Fees (BTC)       | `total_fee_btc`     | Sum of all pending tx fees |
| Fastest Fee (sat/vB)   | `fastest_fee`       | Next block inclusion       |
| Half-hour Fee (sat/vB) | `half_hour_fee`     | ~30 min confirmation       |
| Hour Fee (sat/vB)      | `hour_fee`          | ~1 hour confirmation       |
| Economy Fee (sat/vB)   | `economy_fee`       | Low priority               |
| Minimum Fee (sat/vB)   | `minimum_fee`       | Minimum relay fee          |

**Note**: These are point-in-time snapshots at 1-minute intervals, unlike Ethereum's per-block data.

## Data Model Differences

### Ethereum (LlamaRPC)

```python
{
  "number": "0x16a00e1",           # Hex string
  "timestamp": "0x6909a133",       # Hex string (seconds)
  "gasUsed": "0x13892e4",          # Hex string
  "baseFeePerGas": "0x3b35c053",   # Hex string (wei)
  "transactions": [...]            # Array of hashes or objects
}
```

**Characteristics**:

- All numbers as hex strings
- Conversion: `int(value, 16)`
- Per-block granularity (~12 seconds)

### Bitcoin Mempool (Expected)

```python
{
  "timestamp": "2024-01-01T00:00:00Z",  # ISO 8601 string?
  "unconfirmed_count": 12345,            # Integer (likely decimal)
  "vsize_mb": 123.45,                    # Float (likely decimal)
  "fastest_fee": 25.5                    # Float (sat/vB, likely decimal)
}
```

**Characteristics** (to be verified):

- Numbers as integers/floats (likely decimal, not hex)
- Timestamp format TBD (ISO 8601 vs Unix)
- Snapshot granularity (1-minute intervals)

## Metric Calculation Examples

### Ethereum: Gas Utilization

```python
gas_limit = int(block["gasLimit"], 16)
gas_used = int(block["gasUsed"], 16)
utilization = gas_used / gas_limit  # 0.0 - 1.0
```

### Bitcoin: Mempool Congestion (Proposed)

```python
# Assuming historical baseline
baseline_vsize_mb = 50  # Historical average
current_vsize_mb = snapshot["vsize_mb"]
congestion = current_vsize_mb / baseline_vsize_mb  # >1.0 = congested
```

### Ethereum: Fee Trend

```python
fees = [int(f, 16) / 1e9 for f in fee_history["baseFeePerGas"]]
change = (fees[-1] - fees[0]) / fees[0] * 100
```

### Bitcoin: Fee Trend (Proposed)

```python
# Across multiple snapshots
fee_rates = [s["fastest_fee"] for s in snapshots]
change = (fee_rates[-1] - fee_rates[0]) / fee_rates[0] * 100
```

### Ethereum: Recommended Gas Price

```python
base_fee = int(fee_history["baseFeePerGas"][-1], 16)
priority = int(fee_history["reward"][-1][1], 16)  # 50th percentile
recommended = (base_fee + priority) / 1e9  # Gwei
```

### Bitcoin: Recommended Fee (Already Provided)

```python
# mempool.space provides this directly
recommended = snapshot["hour_fee"]  # sat/vB for ~1 hour confirmation
```

## Feature Engineering Alignment

### For OHLCV + Mempool Cross-Domain Features

**Ethereum Pattern** (this research):

```python
# 1. Collect OHLCV
df_ohlcv = gcd.get_data("BTCUSDT", "1m", start, end)  # DatetimeIndex

# 2. Collect block data (synthetic for demonstration)
df_blocks = pd.DataFrame({
    "gas_utilization": [...],
    "base_fee_gwei": [...]
}, index=DatetimeIndex)

# 3. Align via reindex
df_blocks_aligned = df_blocks.reindex(df_ohlcv.index, method='ffill')

# 4. Join
df = df_ohlcv.join(df_blocks_aligned)
```

**Bitcoin Pattern** (for gapless-network-data):

```python
# 1. Collect OHLCV (same)
df_ohlcv = gcd.get_data("BTCUSDT", "1m", start, end)  # DatetimeIndex

# 2. Collect mempool snapshots (1-minute)
df_mempool = gmd.fetch_snapshots(start, end)  # DatetimeIndex

# 3. Align via reindex (forward-fill for live trading)
df_mempool_aligned = df_mempool.reindex(df_ohlcv.index, method='ffill')

# 4. Join
df = df_ohlcv.join(df_mempool_aligned)

# 5. Engineer cross-domain features
df['fee_pressure'] = df['fastest_fee'] / (df['economy_fee'] + 1e-10)
df['congestion_z'] = (df['unconfirmed_count'] - df['unconfirmed_count'].rolling(60).mean()) / \
                     (df['unconfirmed_count'].rolling(60).std() + 1e-10)
```

**Key Insight**: Same DatetimeIndex alignment strategy works for both Ethereum and Bitcoin mempool data.

## Validation Rules Comparison

### Ethereum (Observed)

```python
# Range checks
assert 0 <= gasUsed <= gasLimit
assert baseFeePerGas >= 1  # Wei (very low)
assert 0 <= gasUsedRatio <= 1

# Sanity checks
assert len(transactions) >= 0
assert timestamp > previous_timestamp
assert difficulty == 0  # Post-Merge

# Fee hierarchy (EIP-1559)
assert effectiveGasPrice >= baseFeePerGas
```

### Bitcoin Mempool (Proposed)

```python
# Range checks (from gapless-network-data schema)
assert unconfirmed_count >= 0
assert vsize_mb >= 0
assert total_fee_btc >= 0
assert 1 <= fastest_fee <= 1000  # Sat/vB (reasonable range)

# Sanity checks
assert fastest_fee >= half_hour_fee >= hour_fee >= economy_fee >= minimum_fee

# Temporal checks
assert timestamp > previous_timestamp  # No gaps
```

## Hex vs Decimal Conversion

### Ethereum (All Hex)

```python
# Block number
block_num = int("0x16a00e1", 16)  # 23,593,185

# Gas price
gwei = int("0x3b35c053", 16) / 1e9  # 0.995 gwei

# Timestamp
timestamp = int("0x6909a133", 16)  # 1762017587
```

### Bitcoin Mempool (Likely Decimal, TBD)

```python
# Transaction count (likely already decimal)
count = data["unconfirmed_count"]  # 12345 (no conversion)

# Fee rate (likely already decimal)
fee = data["fastest_fee"]  # 25.5 sat/vB (no conversion)

# Timestamp (format TBD)
# Option A: ISO 8601
timestamp = datetime.fromisoformat(data["timestamp"])

# Option B: Unix seconds
timestamp = int(data["timestamp"])  # No hex conversion
```

**Action Item**: Verify mempool.space numeric format (hex vs decimal).

## API Call Patterns

### Ethereum

```python
# Single block
payload = {
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["latest", False],
    "id": 1
}

# Fee history (bulk)
payload = {
    "jsonrpc": "2.0",
    "method": "eth_feeHistory",
    "params": ["0x14", "latest", [25, 50, 75]],
    "id": 1
}
```

### Bitcoin Mempool (Expected)

```python
# GET request to REST API
url = "https://mempool.space/api/v1/mempool"
response = requests.get(url)
data = response.json()

# Or for historical data (if available)
url = f"https://mempool.space/api/v1/mempool/history?timestamp={ts}"
```

**Note**: mempool.space uses REST, not JSON-RPC like Ethereum.

## Rate Limiting

### Ethereum (LlamaRPC)

- No explicit limit observed
- Error code 1015 seen on transaction receipt query
- Best practice: Exponential backoff on errors

### Bitcoin Mempool (mempool.space)

- Documented: 10 requests/second
- No authentication required
- Best practice: Same exponential backoff + rate limiter

## Recommended Implementation Strategy

1. **Verify Schema First**

   ```python
   # Fetch one snapshot and inspect
   response = requests.get("https://mempool.space/api/v1/mempool")
   print(json.dumps(response.json(), indent=2))
   ```

2. **Check Numeric Format**

   ```python
   # Are values hex or decimal?
   data = response.json()
   print(type(data.get("unconfirmed_count")))  # int or str?
   ```

3. **Verify Timestamp Format**

   ```python
   # ISO 8601, Unix seconds, or Unix milliseconds?
   print(data.get("timestamp"))
   ```

4. **Implement Conversion Utilities**

   ```python
   # Only if hex encoding is used
   def convert_hex(value):
       return int(value, 16) if isinstance(value, str) and value.startswith("0x") else value
   ```

5. **Define Validation Rules**
   ```python
   def validate_snapshot(data):
       assert data["fastest_fee"] >= data["half_hour_fee"]
       assert data["half_hour_fee"] >= data["hour_fee"]
       # ... etc
   ```

## Next Research Steps

1. Fetch mempool.space API snapshot
2. Document actual field names and types
3. Compare with gapless-network-data schema assumptions
4. Verify timestamp format (seconds vs milliseconds)
5. Check numeric encoding (hex vs decimal)
6. Test rate limiting behavior
7. Document any undocumented fields

## References

- **This Research**: Ethereum schema via LlamaRPC
- **Target Schema**: `/Users/terryli/eon/gapless-network-data/docs/architecture/DATA_FORMAT.md` (pending)
- **mempool.space API**: https://mempool.space/docs/api
- **gapless-network-data**: `/Users/terryli/eon/gapless-network-data/CLAUDE.md`
