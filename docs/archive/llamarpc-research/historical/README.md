# LlamaRPC Historical Ethereum Data Research

Research conducted on **2025-11-03** to evaluate LlamaRPC for historical Ethereum block data collection.

## Quick Links

- **[RESEARCH_SUMMARY.md](/docs/archive/llamarpc-research/historical/RESEARCH_SUMMARY.md)** - Complete findings and recommendations

## TL;DR

✅ **Historical Depth:** Full access back to genesis (July 2015)
✅ **Batch Requests:** Supported (10-20 blocks per request)
⚠️ **Rate Limits:** Very strict - 1-2 second delays required
📊 **Performance:** ~15 blocks/sec sustained throughput
❌ **Production Use:** Not recommended due to strict rate limits

## Key Findings

### 1. Confirmed Historical Depth

- Genesis block (2015-07-30): ✅ Available
- All tested historical blocks: ✅ No gaps detected
- Complete transaction data: ✅ Available

### 2. Optimal Fetching Strategy

```
Batch size: 20 blocks per request
Delay: 1-2 seconds between batches
Expected rate: 10-20 blocks/sec
```

### 3. Rate Limiting

- **429 errors** on rapid sequential requests
- **400 errors** on batches > 50 blocks
- No authentication to increase limits
- Must maintain consistent delays

### 4. Timestamp to Block Mapping

- Use binary search with estimation
- Average block time: 12s (post-merge), 13.3s (pre-merge)
- Typical accuracy: Within 60 seconds

## Test Scripts

### 1. Historical Access Test

```bash
uv run test_historical_blocks.py
```

Tests blocks from different time periods (genesis to recent).

### 2. Batch Request Test

```bash
uv run test_batch_requests.py
```

Tests JSON-RPC batch requests with different sizes.

### 3. Rate Limiting Test

```bash
uv run test_optimal_rate.py
```

Finds optimal batch size and delay settings.

### 4. Timestamp Mapping Test

```bash
uv run timestamp_to_block.py
```

Tests timestamp to block number conversion.

### 5. Data Gaps Test

```bash
uv run test_data_gaps.py
```

Checks for missing blocks across history.

### 6. Historical Collector

```bash
uv run historical_collector.py
```

Complete example: bulk historical block fetching with CSV export.

### 7. Curl Examples

```bash
./curl_examples.sh
```

Basic curl commands for LlamaRPC interaction.

## Sample Output Files

- **block_range.csv** - 201 blocks from specific range
- Sample columns: block_number, timestamp, datetime_utc, hash, gas_used, tx_count

## Recommendations

### For gapless-network-data Project

⚠️ **LlamaRPC rate limits too strict for production**

**Alternatives:**

1. Use Alchemy/Infura with API keys (generous rate limits)
2. Run local Ethereum node (unlimited access)
3. Use LlamaRPC for prototyping only

### For Historical Backfills

If using LlamaRPC:

- Expect ~15 blocks/sec sustained
- Use batch requests (20 blocks)
- Add 1s delays between batches
- Implement retry logic for 429 errors
- Budget ~2 hours per 100,000 blocks

### For Real-time Collection

❌ **Not recommended**

- Use WebSocket subscriptions instead (Alchemy/Infura)
- Or run local node with IPC connection

## Performance Summary

| Metric             | Value                 |
| ------------------ | --------------------- |
| Historical depth   | Genesis (July 2015)   |
| Data completeness  | 100% (no gaps)        |
| Batch support      | Yes (max ~50 blocks)  |
| Sequential rate    | ~8 blocks/sec         |
| Batch rate (burst) | ~50 blocks/sec        |
| Sustained rate     | ~15 blocks/sec        |
| Rate limit errors  | 429 on rapid requests |
| Authentication     | None required (free)  |

## Files in This Directory

```
.
├── README.md                      (this file)
├── RESEARCH_SUMMARY.md            (detailed findings)
├── test_historical_blocks.py      (historical access test)
├── test_batch_requests.py         (batch performance test)
├── test_optimal_rate.py           (rate limiting test)
├── timestamp_to_block.py          (timestamp mapping)
├── test_data_gaps.py              (data completeness check)
├── historical_collector.py        (bulk fetching example)
├── curl_examples.sh               (curl examples)
├── block_range.csv                (sample output)
└── recent_100.csv                 (sample output - if generated)
```

## Quick Start

### Fetch Latest Block

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### Fetch Specific Block

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x989680",false],"id":1}'
```

### Fetch 100 Recent Blocks (Python)

```python
from historical_collector import collect_recent_blocks

collect_recent_blocks(num_blocks=100, output_file="blocks.csv")
```

## Conclusion

**LlamaRPC is suitable for:**

- ✅ Learning and prototyping
- ✅ Historical research
- ✅ Low-volume applications
- ✅ Testing without API keys

**Not suitable for:**

- ❌ Production data pipelines
- ❌ High-throughput ingestion
- ❌ Real-time streaming
- ❌ Large-scale backfills

**Bottom line:** Great free option for research and prototyping, but production use requires paid alternatives (Alchemy/Infura) or local node.
