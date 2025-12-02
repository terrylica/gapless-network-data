# Blockchain Data Collection Validation Workflow

This document provides the complete 5-step empirical validation workflow for blockchain data collection pipelines.

---

## Step 1: Single Block Connectivity Test

**Purpose**: Verify basic connectivity and response format

**Create**: `01_single_block_fetch.py`

**What to validate**:

- RPC endpoint connectivity (no authentication errors)
- Response time (< 500ms acceptable)
- Block retrieval works (eth_getBlockByNumber or equivalent)
- Basic data structure returned

**Success criteria**:

- ✅ Successful block fetch
- ✅ Response time reasonable
- ✅ No connection errors

**Example output**:

```
✅ Connected to RPC endpoint
✅ Response time: 243ms
✅ Block retrieved: #21000000
```

**Next step**: If passed → Step 2 (Schema Validation)

---

## Step 2: Schema Validation

**Purpose**: Verify all required fields are present and correctly typed

**Extend**: Same script as Step 1

**What to validate**:

- All required fields present in response
- Data types match expectations (int, string, timestamp)
- Field values are reasonable (non-negative, within ranges)
- Calculated fields work (e.g., transactions_count = len(transactions))

**For Ethereum blocks, validate**:

```python
required_fields = {
    'number': int,           # block_number
    'timestamp': int,        # Unix timestamp
    'baseFeePerGas': int,    # Can be None for pre-EIP-1559
    'gasUsed': int,
    'gasLimit': int,
    'transactions': list,    # Extract len() for transactions_count
}
```

**Constraints to check**:

- `gasUsed <= gasLimit` (CHECK constraint)
- `block_number >= 0`
- `timestamp > 0`
- `transactions_count >= 0`

**Success criteria**:

- ✅ All required fields present
- ✅ Data types correct
- ✅ Values pass sanity checks
- ✅ Constraints satisfied

**Next step**: If passed → Step 3 (Rate Limit Testing)

---

## Step 3: Rate Limit Testing

**Purpose**: Find sustainable request rate without triggering 429 errors

**Create**: `02_batch_fetch.py` and `03_rate_limited_fetch.py`

**Testing progression**:

### 3.1 Test Parallel Fetching (Likely to Fail)

```python
# 02_batch_parallel_fetch.py
with ThreadPoolExecutor(max_workers=10) as executor:
    # Fetch blocks in parallel
```

**Expected**: 429 rate limit errors

**Purpose**: Understand burst limit behavior

### 3.2 Test Sequential with Delays

```python
# 03_rate_limited_fetch.py
REQUESTS_PER_SECOND = 5.0  # Adjust based on provider
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

for block_num in range(start, end):
    block = fetch_block(block_num)
    time.sleep(DELAY_BETWEEN_REQUESTS)
```

**Rate testing pattern**:

- Start at documented limit (e.g., 10 RPS)
- If fails → reduce by 50% and retry
- If succeeds → try slightly higher to find limit
- Goal: 100% success rate over 50-100 blocks

**Success criteria**:

- ✅ 100% success rate (no 429 errors)
- ✅ Tested over minimum 50 blocks
- ✅ Sustainable rate documented

**Output**: Empirically validated RPS (e.g., "1.37 RPS sustainable")

**Next step**: If passed → Step 4 (Complete Pipeline)

---

## Step 4: Complete Pipeline Test (Fetch → DuckDB)

**Purpose**: Validate end-to-end data flow from RPC to DuckDB storage

**Create**: `04_complete_pipeline.py`

**What to validate**:

### 4.1 Fetch Blocks

Using validated rate limit from Step 3

### 4.2 Transform to DataFrame

```python
import pandas as pd
df = pd.DataFrame(blocks)
```

### 4.3 Insert into DuckDB

```python
from gapless_network_data.db import Database
db = Database(db_path="./test.duckdb")
db.initialize()
db.insert_ethereum_blocks(df)
```

### 4.4 Verify Persistence

```python
conn = db.connect()
count = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()[0]
assert count == len(df)
```

**DuckDB patterns to use** (see `duckdb-patterns.md`):

```python
# Batch INSERT from DataFrame
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")

# CRITICAL: Call CHECKPOINT for durability
conn.execute("CHECKPOINT")

# Verify constraints
invalid = conn.execute("""
    SELECT COUNT(*) FROM ethereum_blocks WHERE gasUsed > gasLimit
""").fetchone()[0]
assert invalid == 0
```

**Success criteria**:

- ✅ Fetch works at validated rate
- ✅ DataFrame conversion successful
- ✅ DuckDB INSERT works
- ✅ CHECKPOINT persists data
- ✅ All CHECK constraints pass
- ✅ Data verifiable in database

**Performance benchmarks** (from empirical validation):

- Fetch: Network-bound (1-10 blocks/sec depending on RPC)
- Insert: CPU-bound (124K+ blocks/sec, far exceeds fetch rate)
- Storage: 76-100 bytes/block

**Next step**: If passed → Step 5 (Documentation)

---

## Step 5: Documentation and Decision

**Purpose**: Document findings and make go/no-go decision

**Create**: `VALIDATION_REPORT.md` (see `validation-report-template.md`)

**Document**:

### 5.1 Executive Summary

- Provider tested
- Sustainable rate found
- Timeline estimate
- Go/No-Go recommendation

### 5.2 Test Results

- Each step's outcome (Pass/Fail)
- Rate limit findings (documented vs empirical)
- Performance metrics

### 5.3 Pipeline Validation

- Fetch throughput
- Insert performance
- Storage estimates

### 5.4 Decision

- Primary RPC provider choice
- Conservative rate limit for production
- Fallback strategy
- Next steps

**Success criteria**:

- ✅ All 4 validation steps passed
- ✅ Sustainable rate documented
- ✅ Timeline calculated
- ✅ Go decision with confidence level

**Example decision**:

```
✅ GO: Alchemy validated at 5.79 RPS sustained
   Timeline: 26 days for 13M blocks
   Confidence: HIGH (100% success over 100 blocks)
   Fallback: LlamaRPC at 1.37 RPS
```

---

## Complete Testing Flow

```
Step 1: Connectivity Test
    ↓ (if passed)
Step 2: Schema Validation
    ↓ (if passed)
Step 3: Rate Limit Testing
    ├─ 3.1: Parallel fetch (expect failure)
    └─ 3.2: Sequential with delays (find sustainable rate)
    ↓ (if passed)
Step 4: Complete Pipeline
    ├─ Fetch → Transform → Insert → Verify
    └─ Validate CHECKPOINT and constraints
    ↓ (if passed)
Step 5: Documentation
    └─ Create validation report with Go/No-Go decision
```

---

## Script Templates

All script templates are available in `scripts/README.md`:

- `poc_single_block.py` - Steps 1-2
- `poc_batch_parallel_fetch.py` - Step 3.1
- `poc_rate_limited_fetch.py` - Step 3.2
- `poc_complete_pipeline.py` - Step 4
