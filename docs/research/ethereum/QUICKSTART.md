# Quick Start Guide: Collecting Ethereum High-Frequency Data

## TL;DR

**Best Free Option for M1/M5/M15 Data**: JSON-RPC Archive Nodes (LlamaRPC, Alchemy, Infura)

Ethereum block time averages **~12 seconds**, which means native blockchain data IS already high-frequency. You just need to aggregate blocks to your desired intervals.

---

## Option 1: LlamaRPC (No Signup, Instant Access)

### Pros

- ✅ No authentication required
- ✅ Full archive access (2015-present)
- ✅ Generous rate limits
- ✅ Works immediately

### Cons

- ❌ No SLA guarantees (free public endpoint)
- ❌ May have occasional downtime

### Example: Fetch Block Data

```bash
curl -s -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_getBlockByNumber",
    "params":["0xD59F80", false],
    "id":1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    baseFeePerGas: .result.baseFeePerGas,
    gasUsed: .result.gasUsed,
    gasLimit: .result.gasLimit
  }'
```

**Output**:

```json
{
  "number": "0xd59f80", // 14,000,000
  "timestamp": "0x61e0aeeb", // 2022-01-13 14:59:55 UTC
  "baseFeePerGas": "0x207d533808", // 139.54 Gwei
  "gasUsed": "0x7be612", // 8,119,826
  "gasLimit": "0x1caa841" // 30,058,561
}
```

### Block-to-M1/M5/M15 Strategy

1. **Fetch blocks sequentially** (start_block → end_block)
2. **Group by time intervals**:
   - M1: Group every ~5 blocks (60 seconds ÷ 12s block time)
   - M5: Group every ~25 blocks
   - M15: Group every ~75 blocks
3. **Calculate OHLC metrics**:
   - Open: First block's baseFeePerGas
   - High: Max baseFeePerGas
   - Low: Min baseFeePerGas
   - Close: Last block's baseFeePerGas
   - Volume: Sum gasUsed

---

## Option 2: Dune Analytics (Best for Bulk Historical Queries)

### Pros

- ✅ SQL-based queries (familiar interface)
- ✅ Built-in aggregation (`DATE_TRUNC`)
- ✅ 2,500 free credits/month
- ✅ Can query YEARS of data in one query

### Cons

- ❌ Requires signup + API key
- ❌ Credit consumption limits large queries

### Example: M1 Gas Prices for Jan 2022

```sql
SELECT
  DATE_TRUNC('minute', time) as minute,
  AVG(CAST(base_fee_per_gas AS DOUBLE) / 1e9) as avg_base_fee_gwei,
  MAX(CAST(base_fee_per_gas AS DOUBLE) / 1e9) as max_base_fee_gwei,
  MIN(CAST(base_fee_per_gas AS DOUBLE) / 1e9) as min_base_fee_gwei,
  SUM(gas_used) as total_gas_used,
  AVG(CAST(gas_used AS DOUBLE) / CAST(gas_limit AS DOUBLE)) as avg_utilization
FROM ethereum.blocks
WHERE time >= TIMESTAMP '2022-01-01'
  AND time < TIMESTAMP '2022-02-01'
GROUP BY DATE_TRUNC('minute', time)
ORDER BY minute
```

**Python SDK**:

```bash
pip install dune-client
export DUNE_API_KEY="your_api_key"
```

```python
from dune_client.client import DuneClient

dune = DuneClient.from_env()
query = dune.create_query(name="ETH M1 Gas Jan 2022", query_sql=sql)
results = dune.get_result(query.query_id)
```

---

## Option 3: The Graph (Best for DeFi Protocol Data)

### Pros

- ✅ Protocol-specific subgraphs (Uniswap, Aave, etc.)
- ✅ Event-level granularity
- ✅ 100K free queries/month

### Cons

- ❌ Requires signup + API key
- ❌ Not suitable for general on-chain metrics
- ❌ Subgraph-specific schemas

### Example: Uniswap V3 Swaps

```bash
curl -X POST \
  https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ swaps(first: 100, orderBy: timestamp, where: {timestamp_gte: 1640995200}) { timestamp amountUSD token0 { symbol } token1 { symbol } } }"
  }'
```

---

## Comparison: Which Source to Use?

| Use Case                     | Recommended Source | Reason                                 |
| ---------------------------- | ------------------ | -------------------------------------- |
| **Quick prototype**          | LlamaRPC           | No signup, instant access              |
| **Production pipeline**      | Alchemy            | Reliable SLA, 300M compute units/month |
| **Bulk historical analysis** | Dune Analytics     | SQL queries can fetch years of data    |
| **DeFi protocol data**       | The Graph          | Protocol-specific subgraphs            |
| **Real-time monitoring**     | LlamaRPC + Alchemy | Low latency                            |

---

## Block Number ↔ Date Conversion

### Finding Block Number for Specific Date

**Method 1: Etherscan**
Visit: https://etherscan.io/block/countdown/14000000

**Method 2: Binary Search**

1. Get latest block number: `eth_blockNumber`
2. Fetch block timestamp: `eth_getBlockByNumber`
3. Binary search to target date

**Reference Points**:
| Date | Block Number | Timestamp |
|------|-------------|-----------|
| 2022-01-01 00:00:00 UTC | ~13916166 | 1640995200 |
| 2022-01-13 14:59:55 UTC | 14000000 | 1642114795 |
| 2023-01-01 00:00:00 UTC | ~16308190 | 1672531200 |
| 2024-01-01 00:00:00 UTC | ~18885000 | 1704067200 |

---

## Rate Limit Strategy

### Free-Tier Daily Limits

| Source   | Requests/Day        | Equivalent Blocks | Historical Coverage |
| -------- | ------------------- | ----------------- | ------------------- |
| LlamaRPC | ~Unlimited          | ~200K+            | ~27 days/day        |
| Alchemy  | 300M CU/month       | ~1M blocks/month  | ~12 days/month      |
| Infura   | 100K req/day        | 100K blocks/day   | ~14 days/day        |
| Dune     | 2,500 credits/month | Unlimited (SQL)   | Full history        |

### Recommended Collection Schedule

**Scenario 1: Backfill 2022-2025 (3 years)**

- Use **Dune Analytics** for bulk query
- Single SQL query can fetch all M1 data for 3 years
- Export to Parquet for local storage

**Scenario 2: Real-Time Updates**

- Use **LlamaRPC** or **Alchemy** for latest blocks
- Poll every 15 seconds for new blocks
- Aggregate to M1/M5/M15 locally

**Scenario 3: Hybrid Approach**

1. Bulk download historical data via Dune (one-time)
2. Switch to LlamaRPC for incremental updates
3. Store locally to avoid repeated API calls

---

## Data Storage Format

### Recommended: Parquet with Snappy Compression

```python
import pandas as pd

# Assume you've fetched block data into a list
df = pd.DataFrame(blocks)
df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
df.set_index('datetime', inplace=True)

# Aggregate to M1
m1_data = df.resample('1min').agg({
    'baseFeePerGas': ['first', 'max', 'min', 'last'],
    'gasUsed': 'sum',
    'gasLimit': 'mean'
})

# Flatten column names
m1_data.columns = ['open', 'high', 'low', 'close', 'gasUsed', 'gasLimit']

# Save to Parquet
m1_data.to_parquet('eth_m1_gas_2022.parquet', compression='snappy')
```

**File Naming Convention**:

- `eth_m1_gas_YYYYMMDD.parquet` - Daily files
- `eth_m5_gas_YYYYMM.parquet` - Monthly files
- `eth_m15_gas_YYYY.parquet` - Yearly files

---

## Next Steps

1. **Test LlamaRPC**: Run `/tmp/ethereum-research/test_llamarpc_curl.sh`
2. **Sign up for Dune**: Get free API key at https://dune.com/
3. **Read full findings**: See `/tmp/ethereum-research/FINDINGS.md`
4. **Build data pipeline**: Choose source based on your use case

---

## Additional Resources

- **Full Research Report**: `/tmp/ethereum-research/FINDINGS.md`
- **LlamaRPC Test Script**: `/tmp/ethereum-research/test_llamarpc_curl.sh`
- **Ethereum JSON-RPC Docs**: https://ethereum.org/en/developers/docs/apis/json-rpc/
- **Dune Docs**: https://docs.dune.com/
- **The Graph Docs**: https://thegraph.com/docs/

---

## FAQs

**Q: Can I get OHLCV data for Ethereum price?**
A: No. Archive nodes provide **on-chain data** (gas prices, transactions, blocks), not **market price data**. For ETH/USD OHLCV, use CEX APIs (Binance, Coinbase, etc.) or `gapless-crypto-data`.

**Q: What's the finest granularity available?**
A: **Block-level** (~12 seconds average). This is native blockchain granularity.

**Q: Can I get data older than 2022?**
A: Yes! Archive nodes have full history back to **genesis block (July 2015)**.

**Q: Which source is most reliable for production?**
A: **Alchemy** (free tier: 300M compute units/month) or **Infura** (100K requests/day). Both have SLAs and dedicated infrastructure.

**Q: How do I handle rate limits?**
A: Implement exponential backoff, use multiple free-tier accounts (with different email addresses), or upgrade to paid tiers.

**Q: Can I combine multiple sources?**
A: Yes! Use Dune for historical bulk downloads, then switch to LlamaRPC/Alchemy for real-time updates.
