# LlamaRPC Historical Ethereum Data Research

**Research Date:** 2025-11-03
**Endpoint:** https://eth.llamarpc.com
**Protocol:** JSON-RPC 2.0

## Executive Summary

LlamaRPC provides **complete historical access** to Ethereum blockchain data from genesis (July 2015) to present. Batch requests are supported with strict rate limiting. Optimal fetching strategy: 10-20 blocks per batch with 1-2 second delays between requests.

---

## 1. Historical Data Depth

### Confirmed Access

✅ **Full historical access back to genesis block (July 30, 2015)**

### Tested Blocks

| Period         | Block Number | Timestamp  | Status       |
| -------------- | ------------ | ---------- | ------------ |
| Genesis        | 0            | 1970-01-01 | ✅ Available |
| Early Ethereum | 100,000      | 2015-08-17 | ✅ Available |
| Homestead      | 1,000,000    | 2016-02-13 | ✅ Available |
| Byzantium      | 5,000,000    | 2018-01-30 | ✅ Available |
| ~2020          | 10,000,000   | 2020-05-04 | ✅ Available |
| The Merge      | 15,537,394   | 2022-09-15 | ✅ Available |
| Recent (2023)  | 18,000,000   | 2023-08-26 | ✅ Available |
| Recent (2024)  | 21,000,000   | 2024-10-19 | ✅ Available |

### Data Completeness

- **No gaps detected** in random sampling across 9+ years
- All tested blocks returned valid data
- Complete transaction counts and metadata

---

## 2. Batch Request Performance

### Batch Request Support

✅ **JSON-RPC batch requests are supported**

### Performance Results

| Batch Size | Sequential Time | Batch Time | Speedup | Status             |
| ---------- | --------------- | ---------- | ------- | ------------------ |
| 5 blocks   | -               | 0.17s      | -       | ✅ Works           |
| 10 blocks  | 1.25s           | 0.20s      | 6.3x    | ✅ Works           |
| 20 blocks  | -               | 0.33s      | -       | ✅ Works           |
| 50 blocks  | -               | -          | -       | ❌ 429 Rate Limit  |
| 100 blocks | -               | -          | -       | ❌ 400 Bad Request |

### Key Findings

- **Optimal batch size:** 10-20 blocks per request
- **Rate limit:** ~50 blocks/batch triggers 429 errors
- **Request limit:** >50 blocks/batch triggers 400 errors
- **Speedup:** 6.3x faster than sequential requests (for small batches)

---

## 3. Rate Limiting Strategy

### Rate Limit Characteristics

- ❌ **Very strict rate limiting** (429 errors on rapid requests)
- ⚠️ **No authentication/API key** to increase limits
- ✅ **Delays between batches prevent errors**

### Recommended Strategy

```python
BATCH_SIZE = 20           # blocks per request
DELAY_BETWEEN_BATCHES = 1.0  # seconds
EXPECTED_RATE = 10-20     # blocks/sec sustained
```

### Sustained Fetching Test Results

- **200 blocks in 13.62 seconds** (14.68 blocks/sec)
- **0 errors** with 20 blocks/batch + 1s delay
- **Stable performance** over 10 consecutive batches

---

## 4. Timestamp to Block Number Mapping

### Strategy: Binary Search with Estimation

```python
# Step 1: Initial estimate
estimated_block = (target_timestamp - reference_timestamp) / avg_block_time

# Step 2: Binary search
search_window = estimated_block +/- 10,000 blocks
max_iterations = 15-20
tolerance = 60 seconds (~5 blocks)
```

### Constants for Estimation

| Era              | Reference Block | Timestamp  | Avg Block Time |
| ---------------- | --------------- | ---------- | -------------- |
| Genesis          | 0               | 1438269973 | -              |
| Pre-Merge (PoW)  | -               | -          | 13.3 seconds   |
| The Merge        | 15,537,394      | 1663224179 | -              |
| Post-Merge (PoS) | -               | -          | 12.0 seconds   |

### Accuracy

- **Typical accuracy:** Within 60 seconds of target
- **Search iterations:** 10-15 on average
- **Search window:** ±10,000 blocks (~1.5 days)

**Note:** For precise date ranges, binary search is required due to variable block times.

---

## 5. Optimal Fetching Strategy

### Recommended Approach

```python
import requests
import time

LLAMARPC_URL = "https://eth.llamarpc.com"
BATCH_SIZE = 20
DELAY = 1.0

def fetch_blocks_batch(block_numbers):
    """Fetch multiple blocks using JSON-RPC batch request."""
    batch_payload = [
        {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(num), False],  # False = no full tx objects
            "id": i
        }
        for i, num in enumerate(block_numbers)
    ]

    response = requests.post(LLAMARPC_URL, json=batch_payload, timeout=30)
    results = response.json()

    return [r["result"] for r in results if "result" in r]

# Collect blocks with rate limiting
for batch_start in range(start_block, end_block, BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE - 1, end_block)
    batch_numbers = list(range(batch_start, batch_end + 1))

    blocks = fetch_blocks_batch(batch_numbers)
    process_blocks(blocks)

    time.sleep(DELAY)  # Rate limiting
```

### Curl Example (Batch Request)

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '[
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e0",false],"id":0},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e1",false],"id":1},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e2",false],"id":2}
  ]'
```

---

## 6. Performance Characteristics

### Throughput

- **Sequential:** ~8 blocks/sec (limited by rate limits)
- **Batch (10 blocks):** ~50 blocks/sec (short bursts)
- **Sustained batch:** ~15 blocks/sec (with delays)

### Bottlenecks

1. **Rate limiting** (429 errors on rapid requests)
2. **Batch size limit** (~50 blocks max)
3. **No burst capacity** (strict per-request limits)

### Comparison with Other RPCs

| RPC Provider | Historical Depth | Batch Support | Rate Limits         |
| ------------ | ---------------- | ------------- | ------------------- |
| LlamaRPC     | Genesis (2015)   | ✅ Yes        | Very strict         |
| Alchemy      | Configurable     | ✅ Yes        | Generous (with key) |
| Infura       | Full history     | ✅ Yes        | Generous (with key) |

**LlamaRPC advantage:** Free, no authentication required
**LlamaRPC limitation:** Strict rate limits, no way to increase

---

## 7. Data Format

### Block Response Structure

```json
{
  "number": "0x148a1e0",           // Block number (hex)
  "timestamp": "0x67769c33",       // Unix timestamp (hex)
  "hash": "0x0b098f4...",          // Block hash
  "parentHash": "0x363d5c...",     // Parent block hash
  "miner": "0x4838b1...",          // Block miner address
  "gasUsed": "0xf84464",           // Gas used (hex)
  "gasLimit": "0x1ca35cc",         // Gas limit (hex)
  "baseFeePerGas": "0x1e8e8ab8a",  // Base fee (hex, post-EIP-1559)
  "transactions": [...]             // Array of tx hashes or objects
}
```

### CSV Export Format

| Column           | Type | Description                 |
| ---------------- | ---- | --------------------------- |
| block_number     | int  | Block number                |
| timestamp        | int  | Unix timestamp              |
| datetime_utc     | str  | ISO 8601 datetime           |
| hash             | str  | Block hash                  |
| parent_hash      | str  | Parent block hash           |
| miner            | str  | Miner address               |
| gas_used         | int  | Gas used                    |
| gas_limit        | int  | Gas limit                   |
| base_fee_per_gas | int  | Base fee per gas (EIP-1559) |
| tx_count         | int  | Transaction count           |

---

## 8. Limitations and Gotchas

### Critical Limitations

1. **Rate Limiting**
   - ❌ No authentication to increase limits
   - ❌ Strict per-request limits
   - ⚠️ Must add delays between batches

2. **Batch Size**
   - ❌ Max ~50 blocks per batch
   - ❌ No way to increase

3. **No Burst Capacity**
   - ❌ Cannot "burst" then slow down
   - ⚠️ Must maintain consistent rate

### Best Practices

✅ **DO:**

- Use batch requests (10-20 blocks)
- Add 1-2 second delays between batches
- Handle 429 errors with exponential backoff
- Use `params: [hex(block), False]` to skip full tx objects

❌ **DON'T:**

- Make rapid sequential requests
- Use batch sizes > 50
- Fetch full transaction objects unless needed
- Expect burst capacity

---

## 9. Use Cases and Recommendations

### Ideal For:

✅ Historical data collection (slow/steady)
✅ Research and analysis
✅ Prototyping and testing
✅ Low-volume applications

### Not Ideal For:

❌ High-throughput ingestion
❌ Real-time streaming
❌ Production data pipelines (rate limits too strict)
❌ Large-scale backfills (too slow)

### Alternative Approaches:

- **Production:** Use Alchemy/Infura with API keys
- **Bulk download:** Consider pre-processed datasets (BigQuery, Dune)
- **Local node:** Run your own Ethereum node for unlimited access

---

## 10. Example Files

### Created Examples

1. **test_historical_blocks.py** - Test blocks across time periods
2. **test_batch_requests.py** - Batch request performance testing
3. **test_optimal_rate.py** - Rate limiting optimization
4. **timestamp_to_block.py** - Timestamp to block number mapping
5. **historical_collector.py** - Complete bulk fetching example
6. **curl_examples.sh** - Curl-based examples
7. **test_data_gaps.py** - Data completeness verification

### Sample Outputs

- **recent_100.csv** - 100 most recent blocks
- **block_range.csv** - Specific block range (21,540,000 to 21,540,200)

---

## 11. Quick Start Guide

### Fetch a Single Block

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0x989680", false],
    "id": 1
  }'
```

### Fetch 100 Recent Blocks (Python)

```python
from historical_collector import collect_recent_blocks

collect_recent_blocks(num_blocks=100, output_file="recent.csv")
```

### Fetch Date Range (Approximate)

```python
from historical_collector import collect_date_range

collect_date_range(
    start_date="2024-01-01",
    end_date="2024-01-02",
    output_file="jan_2024.csv"
)
```

---

## 12. Conclusion

### Summary

| Aspect            | Rating     | Notes                        |
| ----------------- | ---------- | ---------------------------- |
| Historical Depth  | ⭐⭐⭐⭐⭐ | Full history back to genesis |
| Data Completeness | ⭐⭐⭐⭐⭐ | No gaps detected             |
| Batch Support     | ⭐⭐⭐⭐☆  | Works but limited size       |
| Rate Limits       | ⭐⭐☆☆☆    | Very strict, no auth         |
| Performance       | ⭐⭐⭐☆☆   | 10-20 blocks/sec sustained   |
| Ease of Use       | ⭐⭐⭐⭐⭐ | Standard JSON-RPC, no auth   |

### Overall Assessment

**LlamaRPC is excellent for:**

- Learning and prototyping
- Historical research
- Low-volume applications

**Use alternatives for:**

- Production data pipelines
- High-throughput needs
- Real-time applications

### Recommendations

1. **For this project (gapless-network-data):**
   - ⚠️ LlamaRPC rate limits **too strict** for production
   - ✅ Good for testing/prototyping
   - 💡 Consider Alchemy/Infura for production

2. **For historical backfills:**
   - Use batch requests (20 blocks)
   - Add 1s delays between batches
   - Expect ~15 blocks/sec sustained
   - Monitor for 429 errors

3. **For real-time collection:**
   - LlamaRPC not ideal
   - Consider WebSocket subscriptions (Alchemy/Infura)
   - Or run local Ethereum node

---

## Research Artifacts

All test scripts and examples are available in:
`/tmp/llamarpc-historical-research/`

### Files

- RESEARCH_SUMMARY.md (this file)
- test_historical_blocks.py
- test_batch_requests.py
- test_optimal_rate.py
- timestamp_to_block.py
- historical_collector.py
- curl_examples.sh
- test_data_gaps.py
- recent_100.csv (sample output)
- block_range.csv (sample output)
