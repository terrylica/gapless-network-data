# RPC Provider Research Scripts

Scripts for calculating collection timelines and empirically validating rate limits.

---

## calculate_timeline.py

Calculate collection timeline given rate limits (RPS or compute units).

### Usage (RPS-based)

For providers with RPS-based rate limits (Infura, LlamaRPC):

```bash
python scripts/calculate_timeline.py --blocks 13000000 --rps 5.79
```

**Output**:
```
Timeline: 26.0 days
Blocks per day: 500,000
Sustainable RPS: 5.79
```

### Usage (Compute Unit calculation)

For providers with compute unit limits (Alchemy):

```bash
python scripts/calculate_timeline.py \
  --blocks 13000000 \
  --cu-per-month 300000000 \
  --cu-per-request 20
```

**Output**:
```
Timeline: 26.0 days
Blocks per month: 15,000,000
Blocks per day: 500,000
Sustainable RPS: 5.79
Monthly CU usage: 260,000,000 / 300,000,000 (87%)
```

### Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--blocks` | Total blocks to collect | `13000000` |
| `--rps` | Requests per second (for RPS-based providers) | `5.79` |
| `--cu-per-month` | Compute units per month (for CU-based providers) | `300000000` |
| `--cu-per-request` | CU cost per request method | `20` (eth_getBlockByNumber) |

### Examples

**Alchemy calculation** (300M CU/month free tier):
```bash
python scripts/calculate_timeline.py --blocks 13000000 --cu-per-month 300000000 --cu-per-request 20
# Output: 26.0 days (5.79 RPS sustained)
```

**Infura calculation** (25K archive requests/day limit):
```bash
# 25K requests/day ÷ 86,400 seconds = 0.29 RPS
python scripts/calculate_timeline.py --blocks 13000000 --rps 0.29
# Output: 519 days
```

**LlamaRPC calculation** (1.37 RPS empirically validated):
```bash
python scripts/calculate_timeline.py --blocks 13000000 --rps 1.37
# Output: 110 days
```

---

## test_rpc_rate_limits.py

Template for empirical rate limit testing. Copy and customize for each provider.

### Purpose

Validate rate limits empirically by testing actual RPC calls over 50-100 blocks minimum.

### Configuration

Edit these variables before running:

```python
# RPC endpoint
RPC_ENDPOINT = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

# Rate limit to test
REQUESTS_PER_SECOND = 5.0  # Test different rates

# Calculated delay between requests
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

# Test parameters
START_BLOCK = 21000000  # Recent block or historical
BLOCK_COUNT = 100       # Test minimum 50-100 blocks
```

### Success Criteria

```python
# After running test, check assertions
assert success_rate >= 0.99  # 99%+ success rate
assert rate_limited_count == 0  # Zero 429 errors
```

### Testing Approach

Start aggressive, reduce rate until 100% success rate:

```bash
# Test 1: Aggressive (likely fail)
python test_rpc_rate_limits.py --rps 10 --blocks 100

# Test 2: Moderate (may fail)
python test_rpc_rate_limits.py --rps 5 --blocks 100

# Test 3: Conservative (should work)
python test_rpc_rate_limits.py --rps 2 --blocks 100
```

### Example Output

```
Testing RPC endpoint: https://eth-mainnet.g.alchemy.com/v2/***
Rate: 5.0 RPS (delay: 0.200s between requests)
Blocks: 21000000 - 21000100 (100 blocks)

Progress: 100/100 blocks fetched
Success rate: 100.0% ✅
Rate limited (429): 0 ✅
Other errors: 0 ✅
Avg response time: 245ms
Total time: 20.1s

RESULT: PASS - Sustainable rate validated
```

### Failure Example

```
Testing RPC endpoint: https://eth.llamarpc.com
Rate: 10.0 RPS (delay: 0.100s between requests)
Blocks: 21000000 - 21000100 (100 blocks)

Progress: 100/100 blocks fetched
Success rate: 72.0% ❌
Rate limited (429): 28 ❌
Other errors: 0
Avg response time: 187ms
Total time: 14.3s

RESULT: FAIL - Rate limit exceeded, reduce RPS
```

### Parallel Fetch Testing

Test parallel workers (use with caution on free tiers):

```python
# Configuration for parallel testing
MAX_WORKERS = 3  # Number of parallel workers
test_configs = [
    {"workers": 10, "expected": "likely fail"},
    {"workers": 3, "expected": "may fail"},
    {"workers": 1, "expected": "should work (sequential)"},
]
```

**Warning**: Even 3 workers can trigger rate limits on strict free tiers. Default to sequential with delays unless proven otherwise.
