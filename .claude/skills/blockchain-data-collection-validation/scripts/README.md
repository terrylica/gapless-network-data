# Blockchain Data Collection Validation Scripts

POC template scripts for empirical validation of blockchain data collection pipelines.

---

## Overview

These scripts follow the 5-step validation workflow. Each builds on the previous step.

**Testing progression**:
1. `poc_single_block.py` - Connectivity and schema validation (Steps 1-2)
2. `poc_batch_parallel_fetch.py` - Parallel fetch testing (Step 3, expect failures)
3. `poc_rate_limited_fetch.py` - Rate-limited sequential fetch (Step 3, find sustainable rate)
4. `poc_complete_pipeline.py` - Complete fetch→DuckDB pipeline (Step 4)

---

## poc_single_block.py

**Purpose**: Test connectivity and schema validation (Steps 1-2)

**What it validates**:
- RPC endpoint connectivity
- Response time (<500ms acceptable)
- All required fields present
- Data types correct
- CHECK constraints satisfied

**Usage**:

```bash
python scripts/poc_single_block.py
```

**Template**:

```python
#!/usr/bin/env python3
"""Test 1: Single block connectivity and schema validation."""

from datetime import datetime
from web3 import Web3

RPC_ENDPOINT = "https://eth.llamarpc.com"  # Change to your provider

def test_single_block():
    """Test connectivity and schema validation."""
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

    # Validate schema
    block_data = {
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'baseFeePerGas': block.get('baseFeePerGas'),
        'gasUsed': block['gasUsed'],
        'gasLimit': block['gasLimit'],
        'transactions_count': len(block['transactions']),
    }

    # Validate data types
    assert isinstance(block_data['block_number'], int), "block_number not int"
    assert isinstance(block_data['timestamp'], datetime), "timestamp not datetime"
    assert isinstance(block_data['gasUsed'], int), "gasUsed not int"
    assert isinstance(block_data['gasLimit'], int), "gasLimit not int"
    assert isinstance(block_data['transactions_count'], int), "transactions_count not int"
    print("✅ All data types correct")

    # Sanity checks (CHECK constraints)
    assert block_data['gasUsed'] <= block_data['gasLimit'], "gasUsed > gasLimit"
    assert block_data['block_number'] >= 0, "block_number < 0"
    assert block_data['transactions_count'] >= 0, "transactions_count < 0"
    print("✅ All constraints satisfied")

    print(f"\n✅ PASS - Connectivity and schema validated")
    print(f"\nSample data:")
    for key, value in block_data.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_single_block()
```

**Expected output**:

```
✅ Connected to RPC endpoint
✅ Latest block: #21000000
✅ Response time: 243ms
✅ All data types correct
✅ All constraints satisfied

✅ PASS - Connectivity and schema validated

Sample data:
  block_number: 21000000
  timestamp: 2025-11-05 14:23:45
  baseFeePerGas: 12345678
  gasUsed: 15000000
  gasLimit: 30000000
  transactions_count: 142
```

**Next step**: If passed → `poc_batch_parallel_fetch.py`

---

## poc_batch_parallel_fetch.py

**Purpose**: Test parallel fetching (Step 3.1, expect failures)

**What it validates**:
- Burst limit behavior
- Whether parallel fetching is viable
- Rate limiting response (429 errors)

**Usage**:

```bash
python scripts/poc_batch_parallel_fetch.py
```

**Template**:

```python
#!/usr/bin/env python3
"""Test 2: Parallel batch fetch (expect 429 errors)."""

import time
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3

RPC_ENDPOINT = "https://eth.llamarpc.com"
MAX_WORKERS = 10  # Aggressive parallel fetching
BLOCK_COUNT = 100

def fetch_block(w3, block_num):
    """Fetch single block, return (block_num, success, error)."""
    try:
        block = w3.eth.get_block(block_num)
        return (block_num, True, None)
    except Exception as e:
        error_type = "429" if "429" in str(e) else "other"
        return (block_num, False, error_type)

def test_parallel():
    """Test parallel fetching (expect failures)."""
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    start_block = w3.eth.block_number - BLOCK_COUNT

    print(f"Testing parallel fetch: {MAX_WORKERS} workers")
    print(f"Blocks: {start_block} - {start_block + BLOCK_COUNT} ({BLOCK_COUNT} blocks)\n")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_block, w3, start_block + i)
            for i in range(BLOCK_COUNT)
        ]
        results = [f.result() for f in futures]

    elapsed = time.time() - start_time

    # Analyze results
    success = sum(1 for _, ok, _ in results if ok)
    failures = BLOCK_COUNT - success
    rate_limited = sum(1 for _, _, err in results if err == "429")

    success_rate = success / BLOCK_COUNT * 100

    print(f"Progress: {BLOCK_COUNT}/{BLOCK_COUNT} blocks fetched")
    print(f"Success rate: {success_rate:.1f}% {'✅' if success_rate == 100 else '❌'}")
    print(f"Rate limited (429): {rate_limited} {'✅' if rate_limited == 0 else '❌'}")
    print(f"Other errors: {failures - rate_limited}")
    print(f"Total time: {elapsed:.1f}s")

    if success_rate == 100:
        print(f"\n✅ PASS - Parallel fetching viable at {MAX_WORKERS} workers")
    else:
        print(f"\n❌ FAIL - Rate limit exceeded, use sequential approach")

if __name__ == "__main__":
    test_parallel()
```

**Expected output** (typical failure):

```
Testing parallel fetch: 10 workers
Blocks: 21000000 - 21000100 (100 blocks)

Progress: 100/100 blocks fetched
Success rate: 72.0% ❌
Rate limited (429): 28 ❌
Other errors: 0
Total time: 14.3s

❌ FAIL - Rate limit exceeded, use sequential approach
```

**Next step**: If failed → `poc_rate_limited_fetch.py`

---

## poc_rate_limited_fetch.py

**Purpose**: Find sustainable request rate (Step 3.2)

**What it validates**:
- Sustainable RPS without 429 errors
- 100% success rate over 50+ blocks
- Empirical rate limit discovery

**Usage**:

```bash
python scripts/poc_rate_limited_fetch.py
```

**Template**:

```python
#!/usr/bin/env python3
"""Test 3: Rate-limited sequential fetch."""

import time
from web3 import Web3

RPC_ENDPOINT = "https://eth.llamarpc.com"
REQUESTS_PER_SECOND = 5.0  # Start conservative, adjust as needed
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND
BLOCK_COUNT = 100  # Test minimum 50, ideally 100+

def test_rate_limited():
    """Test sequential fetch with rate limiting."""
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    start_block = w3.eth.block_number - BLOCK_COUNT

    print(f"Testing RPC endpoint: {RPC_ENDPOINT}")
    print(f"Rate: {REQUESTS_PER_SECOND} RPS (delay: {DELAY_BETWEEN_REQUESTS:.3f}s between requests)")
    print(f"Blocks: {start_block} - {start_block + BLOCK_COUNT} ({BLOCK_COUNT} blocks)\n")

    success = 0
    rate_limited = 0
    other_errors = 0
    response_times = []

    start_time = time.time()

    for i in range(BLOCK_COUNT):
        block_num = start_block + i

        try:
            req_start = time.time()
            block = w3.eth.get_block(block_num)
            req_time = (time.time() - req_start) * 1000
            response_times.append(req_time)
            success += 1

            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{BLOCK_COUNT} blocks fetched")

        except Exception as e:
            if "429" in str(e):
                rate_limited += 1
            else:
                other_errors += 1
                print(f"Error at block {block_num}: {e}")

        time.sleep(DELAY_BETWEEN_REQUESTS)

    elapsed = time.time() - start_time
    success_rate = success / BLOCK_COUNT * 100
    avg_response = sum(response_times) / len(response_times) if response_times else 0

    print(f"\nProgress: {BLOCK_COUNT}/{BLOCK_COUNT} blocks fetched")
    print(f"Success rate: {success_rate:.1f}% {'✅' if success_rate == 100 else '❌'}")
    print(f"Rate limited (429): {rate_limited} {'✅' if rate_limited == 0 else '❌'}")
    print(f"Other errors: {other_errors} {'✅' if other_errors == 0 else '❌'}")
    print(f"Avg response time: {avg_response:.0f}ms")
    print(f"Total time: {elapsed:.1f}s")

    if success_rate == 100 and rate_limited == 0:
        print(f"\n✅ PASS - Sustainable rate validated at {REQUESTS_PER_SECOND} RPS")
    else:
        print(f"\n❌ FAIL - Reduce RPS and retry")

if __name__ == "__main__":
    test_rate_limited()
```

**Expected output** (success):

```
Testing RPC endpoint: https://eth.llamarpc.com
Rate: 5.0 RPS (delay: 0.200s between requests)
Blocks: 21000000 - 21000100 (100 blocks)

Progress: 10/100 blocks fetched
Progress: 20/100 blocks fetched
...
Progress: 100/100 blocks fetched

Progress: 100/100 blocks fetched
Success rate: 100.0% ✅
Rate limited (429): 0 ✅
Other errors: 0 ✅
Avg response time: 245ms
Total time: 20.1s

✅ PASS - Sustainable rate validated at 5.0 RPS
```

**Next step**: If passed → `poc_complete_pipeline.py`

---

## poc_complete_pipeline.py

**Purpose**: Test complete fetch→DuckDB pipeline (Step 4)

**What it validates**:
- End-to-end data flow (fetch → transform → insert → verify)
- DuckDB integration (INSERT, CHECKPOINT, constraints)
- Data persistence and integrity

**Usage**:

```bash
python scripts/poc_complete_pipeline.py
```

**Template**:

```python
#!/usr/bin/env python3
"""Test 4: Complete fetch → DuckDB pipeline."""

import time
import pandas as pd
from datetime import datetime
from web3 import Web3
from gapless_network_data.db import Database

RPC_ENDPOINT = "https://eth.llamarpc.com"
REQUESTS_PER_SECOND = 1.37  # From Step 3 validation
DELAY = 1.0 / REQUESTS_PER_SECOND
BLOCK_COUNT = 100

def test_pipeline():
    """Test complete fetch → DuckDB pipeline."""
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))

    # Step 1: Fetch blocks
    print(f"Step 1: Fetching {BLOCK_COUNT} blocks at {REQUESTS_PER_SECOND} RPS...")
    start_block = w3.eth.block_number - BLOCK_COUNT
    blocks = []

    fetch_start = time.time()

    for i in range(BLOCK_COUNT):
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

    fetch_elapsed = time.time() - fetch_start
    print(f"✅ Fetched {len(blocks)} blocks in {fetch_elapsed:.1f}s ({len(blocks)/fetch_elapsed:.2f} blocks/sec)")

    # Step 2: Transform to DataFrame
    print(f"\nStep 2: Transforming to DataFrame...")
    df = pd.DataFrame(blocks)
    print(f"✅ DataFrame created: {len(df)} rows × {len(df.columns)} columns")

    # Step 3: Insert into DuckDB
    print(f"\nStep 3: Inserting into DuckDB...")
    db = Database(db_path="./test.duckdb")
    db.initialize()

    conn = db.connect()

    insert_start = time.time()
    conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
    conn.execute("CHECKPOINT")  # CRITICAL: Persist to disk
    insert_elapsed = time.time() - insert_start

    blocks_per_sec = len(df) / insert_elapsed if insert_elapsed > 0 else 0
    print(f"✅ DuckDB INSERT completed in {insert_elapsed:.3f}s ({blocks_per_sec:.0f} blocks/sec)")

    # Step 4: Verify persistence
    print(f"\nStep 4: Verifying data persistence...")
    count = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()[0]
    assert count == len(df), f"Expected {len(df)}, got {count}"
    print(f"✅ Data verified: {count} blocks in database")

    # Step 5: Verify constraints
    print(f"\nStep 5: Verifying CHECK constraints...")
    invalid = conn.execute("""
        SELECT COUNT(*) FROM ethereum_blocks WHERE gasUsed > gasLimit
    """).fetchone()[0]
    assert invalid == 0, f"Found {invalid} blocks with gasUsed > gasLimit"
    print(f"✅ All CHECK constraints pass (gasUsed <= gasLimit)")

    # Storage analysis
    import os
    db_size = os.path.getsize("./test.duckdb")
    bytes_per_block = db_size / count if count > 0 else 0
    print(f"\n📊 Storage metrics:")
    print(f"  Database size: {db_size:,} bytes ({db_size/1024:.1f} KB)")
    print(f"  Bytes per block: {bytes_per_block:.0f} bytes")

    print(f"\n✅ PASS - Complete pipeline validated")

if __name__ == "__main__":
    test_pipeline()
```

**Expected output**:

```
Step 1: Fetching 100 blocks at 1.37 RPS...
✅ Fetched 100 blocks in 73.0s (1.37 blocks/sec)

Step 2: Transforming to DataFrame...
✅ DataFrame created: 100 rows × 6 columns

Step 3: Inserting into DuckDB...
✅ DuckDB INSERT completed in 0.012s (8333 blocks/sec)

Step 4: Verifying data persistence...
✅ Data verified: 100 blocks in database

Step 5: Verifying CHECK constraints...
✅ All CHECK constraints pass (gasUsed <= gasLimit)

📊 Storage metrics:
  Database size: 8,400 bytes (8.2 KB)
  Bytes per block: 84 bytes

✅ PASS - Complete pipeline validated
```

**Next step**: If passed → Step 5 (Documentation and Decision)

---

## Testing Progression Guide

### Progressive Testing Strategy

1. **Start with single block** (`poc_single_block.py`)
   - Validates connectivity and schema
   - Fast feedback (< 1 second)
   - If fails: Check RPC endpoint, API key, network

2. **Try parallel fetch** (`poc_batch_parallel_fetch.py`)
   - Tests burst limits
   - Expect failures on free tiers
   - If passes: Lucky! Can use parallel fetching
   - If fails: Normal, proceed to sequential

3. **Find sustainable rate** (`poc_rate_limited_fetch.py`)
   - Start at documented limit (e.g., 10 RPS)
   - If fails: Reduce by 50%, retry
   - If succeeds: Try slightly higher to find max
   - Goal: 100% success rate over 100 blocks

4. **Validate complete pipeline** (`poc_complete_pipeline.py`)
   - Tests end-to-end flow
   - Verifies DuckDB integration
   - Confirms data persistence
   - If passes: Ready for production implementation

### Rate Testing Tips

**Finding the optimal rate**:
```
10 RPS → 72% success → Too high
5 RPS → 100% success → Good
7 RPS → 95% success → Too risky
5.5 RPS → 100% success → Optimal
```

**Conservative production rate**:
- Use 80-90% of empirical max
- Example: 5.79 RPS max → 5.0 RPS production
- Safety margin for network variability

### Common Issues

**Issue**: "Connection refused" or "Name or service not known"
- **Cause**: Invalid RPC endpoint or network issue
- **Fix**: Check endpoint URL, test with curl first

**Issue**: "Unauthorized" or "Invalid API key"
- **Cause**: Missing or incorrect API key
- **Fix**: Check RPC_ENDPOINT includes valid API key

**Issue**: 429 errors even at 1 RPS
- **Cause**: API key rate limit exhausted or IP banned
- **Fix**: Wait for rate limit reset, try different provider

**Issue**: Pipeline test fails with "Table not found"
- **Cause**: Database not initialized
- **Fix**: Ensure `db.initialize()` is called before INSERT

---

## Related Documentation

- **Workflow steps**: `references/validation-workflow.md` - Complete 5-step workflow guide
- **Common pitfalls**: `references/common-pitfalls.md` - Mistakes to avoid
- **Example walkthrough**: `references/example-workflow.md` - Complete Alchemy case study
- **DuckDB patterns**: `references/duckdb-patterns.md` - CHECKPOINT, constraints, performance
