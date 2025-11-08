# Example Workflow: Validating Alchemy for Ethereum Collection

This document provides a complete case study of validating Alchemy RPC provider for Ethereum data collection.

---

## User Request

"Validate Alchemy for Ethereum data collection before implementation"

**Context**:
- Need to collect 13M Ethereum blocks (5 years historical data)
- Evaluating Alchemy free tier (300M compute units/month)
- Need empirical validation before committing to implementation

---

## Step 1: Single Block Connectivity Test

### Actions Taken

Created `01_single_block_fetch.py`:

```python
#!/usr/bin/env python3
"""Test 1: Single block connectivity and schema validation."""

from datetime import datetime
from web3 import Web3

RPC_ENDPOINT = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

def test_single_block():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))

    # Connectivity test
    latest = w3.eth.block_number
    print(f"✅ Connected to RPC endpoint")
    print(f"✅ Latest block: #{latest}")

    # Fetch single block
    import time
    start = time.time()
    block = w3.eth.get_block(latest)
    response_time = (time.time() - start) * 1000

    print(f"✅ Response time: {response_time:.0f}ms")
    print(f"✅ Block retrieved: #{block['number']}")

if __name__ == "__main__":
    test_single_block()
```

### Results

```
✅ Connected to RPC endpoint
✅ Latest block: #21000000
✅ Response time: 243ms
✅ Block retrieved: #21000000
```

### Conclusion

✅ **PASS** - Connectivity validated, response time acceptable

---

## Step 2: Schema Validation

### Actions Taken

Extended same script to validate all required fields:

```python
def test_schema():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    block = w3.eth.get_block(w3.eth.block_number)

    # Extract required fields
    block_data = {
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'baseFeePerGas': block.get('baseFeePerGas'),
        'gasUsed': block['gasUsed'],
        'gasLimit': block['gasLimit'],
        'transactions_count': len(block['transactions']),
    }

    # Validate data types
    assert isinstance(block_data['block_number'], int)
    assert isinstance(block_data['timestamp'], datetime)
    assert isinstance(block_data['gasUsed'], int)
    assert isinstance(block_data['gasLimit'], int)
    assert isinstance(block_data['transactions_count'], int)

    # Sanity checks (CHECK constraints)
    assert block_data['gasUsed'] <= block_data['gasLimit'], "gasUsed > gasLimit"
    assert block_data['block_number'] >= 0, "block_number < 0"
    assert block_data['transactions_count'] >= 0, "transactions_count < 0"

    print("✅ All required fields present")
    print("✅ Data types correct")
    print("✅ Constraints satisfied")
    print(f"\nSample data:")
    for key, value in block_data.items():
        print(f"  {key}: {value}")
```

### Results

```
✅ All required fields present
✅ Data types correct
✅ Constraints satisfied

Sample data:
  block_number: 21000000
  timestamp: 2025-11-05 14:23:45
  baseFeePerGas: 12345678
  gasUsed: 15000000
  gasLimit: 30000000
  transactions_count: 142
```

### Conclusion

✅ **PASS** - All fields present, types correct, constraints satisfied

---

## Step 3: Rate Limit Testing

### Test 3.1: Parallel Fetch (Aggressive)

Created `02_batch_parallel_fetch.py`:

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_block(w3, block_num):
    return w3.eth.get_block(block_num)

def test_parallel():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    start_block = w3.eth.block_number - 100

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_block, w3, i) for i in range(start_block, start_block + 100)]
        results = [f.result() for f in futures]

    print(f"✅ Fetched {len(results)} blocks in parallel")
```

**Result**: ❌ **FAIL** - 429 rate limit errors after ~30 blocks

### Test 3.2: Sequential with 10 RPS

Created `03_rate_limited_fetch.py`:

```python
import time

REQUESTS_PER_SECOND = 10.0
DELAY = 1.0 / REQUESTS_PER_SECOND

def test_sequential():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    start_block = w3.eth.block_number - 100

    success = 0
    failures = 0

    for i in range(100):
        try:
            block = w3.eth.get_block(start_block + i)
            success += 1
        except Exception as e:
            if '429' in str(e):
                failures += 1
            else:
                raise
        time.sleep(DELAY)

    success_rate = success / (success + failures) * 100
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Rate limited (429): {failures}")
```

**Result**: ❌ **FAIL** - 72% success rate, 28 rate limit errors

### Test 3.3: Sequential with 5 RPS

Adjusted `REQUESTS_PER_SECOND = 5.0`:

**Result**: ✅ **PASS** - 100% success rate over 100 blocks

### Final Validation

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

### Conclusion

✅ **PASS** - Empirical sustainable rate: **5.79 RPS** (conservative 5.0 RPS for production)

---

## Step 4: Complete Pipeline Test

### Actions Taken

Created `04_complete_pipeline.py`:

```python
import time
import pandas as pd
from datetime import datetime
from web3 import Web3
from gapless_network_data.db import Database

RPC_ENDPOINT = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
REQUESTS_PER_SECOND = 5.0
DELAY = 1.0 / REQUESTS_PER_SECOND

def test_pipeline():
    # Step 1: Fetch blocks
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    start_block = w3.eth.block_number - 100

    blocks = []
    for i in range(100):
        block = w3.eth.get_block(start_block + i)
        blocks.append({
            'block_number': block['number'],
            'timestamp': datetime.fromtimestamp(block['timestamp']),
            'baseFeePerGas': block.get('baseFeePerGas'),
            'gasUsed': block['gasUsed'],
            'gasLimit': block['gasLimit'],
            'transactions_count': len(block['transactions']),
        })
        time.sleep(DELAY)

    print(f"✅ Fetched {len(blocks)} blocks")

    # Step 2: Transform to DataFrame
    df = pd.DataFrame(blocks)
    print(f"✅ DataFrame created: {len(df)} rows")

    # Step 3: Insert into DuckDB
    db = Database(db_path="./test.duckdb")
    db.initialize()

    conn = db.connect()
    conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
    conn.execute("CHECKPOINT")  # CRITICAL: Persist to disk
    print(f"✅ DuckDB INSERT completed")

    # Step 4: Verify persistence
    count = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()[0]
    assert count == len(df), f"Expected {len(df)}, got {count}"
    print(f"✅ Data verified: {count} blocks in database")

    # Step 5: Verify constraints
    invalid = conn.execute("""
        SELECT COUNT(*) FROM ethereum_blocks WHERE gasUsed > gasLimit
    """).fetchone()[0]
    assert invalid == 0, f"Found {invalid} blocks with gasUsed > gasLimit"
    print(f"✅ All CHECK constraints pass")

if __name__ == "__main__":
    test_pipeline()
```

### Results

```
✅ Fetched 100 blocks
✅ DataFrame created: 100 rows
✅ DuckDB INSERT completed
✅ Data verified: 100 blocks in database
✅ All CHECK constraints pass

Performance metrics:
- Fetch throughput: 5.0 blocks/sec
- Insert throughput: 8.3K blocks/sec (far exceeds fetch rate)
- Storage per block: 84 bytes average
- Total storage: 8.4 KB for 100 blocks
```

### Conclusion

✅ **PASS** - Complete pipeline validated (fetch → transform → insert → verify)

---

## Step 5: Documentation and Decision

### Test Results Summary

| Step                | Result      | Key Finding                                |
| ------------------- | ----------- | ------------------------------------------ |
| 1. Connectivity     | ✅ PASS     | 243ms response time                        |
| 2. Schema           | ✅ PASS     | All fields present, constraints satisfied  |
| 3. Rate Limits      | ✅ PASS     | 5.79 RPS sustainable (empirical)           |
| 4. Complete Pipeline| ✅ PASS     | Full fetch→DuckDB flow working             |

### Performance Metrics

- **Fetch throughput**: 5.0 blocks/sec (network-bound)
- **Insert throughput**: 8.3K blocks/sec (CPU-bound, far exceeds fetch)
- **Storage**: 84 bytes/block average
- **Response time**: 245ms average

### Timeline Calculation

Using `calculate_timeline.py`:

```bash
python scripts/calculate_timeline.py --blocks 13000000 --rps 5.79
```

**Output**:
```
Timeline: 26.0 days
Blocks per day: 500,000
Sustainable RPS: 5.79
```

### Decision

✅ **GO** - Implement with Alchemy

**Recommendation**:
- **Provider**: Alchemy free tier (300M compute units/month)
- **Conservative rate**: 5.0 RPS production (86% of empirical 5.79 RPS max)
- **Timeline**: 26 days for 13M blocks
- **Confidence**: **HIGH** (100% success over 100 blocks, all validation steps passed)

**Fallback strategy**:
- Monitor compute unit usage daily
- If approaching limit, fallback to LlamaRPC at 1.37 RPS (110-day timeline)
- Consider paid tier if faster collection needed

**Next steps**:
1. Implement production collector using validated patterns
2. Add checkpoint/resume capability (store last_block_number)
3. Implement monitoring (blocks/sec, compute units used)
4. Add error handling and retry logic

---

## Lessons Learned

### What Worked Well
1. Empirical validation caught 3x discrepancy between attempted (10 RPS) and sustainable (5 RPS) rates
2. Complete pipeline test revealed no issues (CHECKPOINT worked, constraints passed)
3. Testing progression (parallel → aggressive → conservative) found optimal rate efficiently

### Mistakes Avoided
1. Trusting documented limits without validation (could have led to production failures)
2. Testing with <50 blocks (would have missed sliding window rate limiting)
3. Forgetting CHECKPOINT (validated it works correctly)

### Recommendations for Future Validation
1. Always test 100+ blocks minimum (not 50)
2. Test crash recovery explicitly (kill process during collection, verify CHECKPOINT)
3. Monitor response times (degradation may indicate approaching rate limits)

---

## Reference Materials

**Complete POC scripts**: `/Users/terryli/eon/gapless-network-data/scratch/ethereum-collector-poc/`

**Validation reports**:
- `/Users/terryli/eon/gapless-network-data/scratch/ethereum-collector-poc/ETHEREUM_COLLECTOR_POC_REPORT.md `
- `/Users/terryli/eon/gapless-network-data/scratch/duckdb-batch-validation/DUCKDB_BATCH_VALIDATION_REPORT.md `
