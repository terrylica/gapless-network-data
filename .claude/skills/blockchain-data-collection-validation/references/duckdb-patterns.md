# DuckDB Integration Patterns for Blockchain Data Collection

**Empirically validated from**: `scratch/duckdb-batch-validation/`
**Last updated**: 2025-11-05

---

## Critical Pattern: CHECKPOINT for Durability

**Problem**: Without `CHECKPOINT`, data inserted into DuckDB stays in-memory and is lost on crash.

**Empirical Evidence**:
- Tested 4 crash scenarios (kill -9, reboot, exception, timeout)
- Without CHECKPOINT: 100% data loss
- With CHECKPOINT: 0% data loss

**Solution**:
```python
# After batch INSERT
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")

# CRITICAL: Call CHECKPOINT to persist to disk
conn.execute("CHECKPOINT")
```

**From**: `scratch/duckdb-batch-validation/test_checkpoint_resume.py`

**Performance Impact**: Minimal (< 10ms for 1K blocks)

---

## Batch INSERT from DataFrame

**Pattern**: DuckDB can read pandas DataFrame directly in SQL

```python
import pandas as pd

# Create DataFrame from blocks list
blocks = [
    {'block_number': 100, 'timestamp': '2024-01-01', ...},
    {'block_number': 101, 'timestamp': '2024-01-01', ...},
]
df = pd.DataFrame(blocks)

# DuckDB reads DataFrame directly (no intermediate CSV)
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
conn.execute("CHECKPOINT")
```

**Performance** (empirically validated):
- Batch size 1K: 124,356 blocks/sec
- Batch size 10K: Similar performance
- Batch size 100K: No significant improvement

**Recommendation**: Use 1K batch size (simple, fast enough, far exceeds RPC limits)

**From**: `scratch/duckdb-batch-validation/test_batch_performance.py`

---

## Schema with CHECK Constraints

**Purpose**: Catch data corruption at insertion time

```sql
CREATE TABLE ethereum_blocks (
    block_number BIGINT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    baseFeePerGas BIGINT,
    gasUsed BIGINT NOT NULL,
    gasLimit BIGINT NOT NULL,
    transactions_count INTEGER NOT NULL,

    -- Sanity constraints
    CHECK (gasUsed <= gasLimit),
    CHECK (block_number >= 0),
    CHECK (transactions_count >= 0)
)
```

**Benefits**:
- Detects invalid data immediately (exception thrown)
- No silent corruption in database
- Aligns with exception-only failure philosophy

**Testing**:
```python
# This will fail with constraint violation
conn.execute("""
    INSERT INTO ethereum_blocks VALUES (
        100, '2024-01-01', 1000, 5000, 4000, 10  -- gasUsed > gasLimit
    )
""")
# DuckDB.ConstraintException: CHECK constraint failed
```

**From**: `scratch/duckdb-batch-validation/test_batch_insert.py`

---

## Storage Estimates

**Empirically measured** (76-100 bytes/block):

| Dataset | Rows | Size | Bytes/Row |
|---------|------|------|-----------|
| Ethereum test | 1,000 | 88 KB | 90 bytes |
| Ethereum test | 10,000 | 873 KB | 89 bytes |
| Ethereum test | 100,000 | 7.6 MB | 80 bytes |

**Projection**:
- 13M Ethereum blocks: 1.0-1.2 GB
- 3.6K Bitcoin snapshots: ~300 KB

**Storage location**: `~/.cache/gapless-network-data/data.duckdb`

**From**: `scratch/duckdb-batch-validation/test_batch_performance.py`

---

## Checkpoint/Resume Pattern

**Use case**: Resume collection after crash or interruption

```python
from gapless_network_data.db import Database

db = Database(db_path="./collection.duckdb")
db.initialize()

# Load checkpoint
last_block = db.get_checkpoint("last_ethereum_block")
if last_block:
    start_block = int(last_block) + 1
else:
    start_block = 11_560_000  # Genesis for our collection

# Collect blocks
for block_num in range(start_block, end_block):
    block_data = fetch_block(block_num)
    df = pd.DataFrame([block_data])

    # Insert + checkpoint
    db.insert_ethereum_blocks(df)

    # Save progress every 1000 blocks
    if block_num % 1000 == 0:
        db.save_checkpoint("last_ethereum_block", str(block_num))
```

**Benefits**:
- Resume from last saved block after crash
- No duplicate data (PRIMARY KEY prevents)
- Progress tracking

**From**: `scratch/duckdb-batch-validation/test_checkpoint_resume.py`

---

## Database Initialization Pattern

```python
from gapless_network_data.db import Database
from pathlib import Path

# Use standard cache directory
cache_dir = Path.home() / ".cache" / "gapless-network-data"
cache_dir.mkdir(parents=True, exist_ok=True)
db_path = cache_dir / "data.duckdb"

# Initialize database
db = Database(db_path=db_path)
db.initialize()  # Creates tables if not exist

# Use database
conn = db.connect()
# ... queries ...

# Close when done
db.close()
```

**Benefits**:
- Standard XDG cache location
- Idempotent initialization (safe to call multiple times)
- Connection pooling handled by Database class

---

## Performance Benchmarks

From empirical validation (`scratch/duckdb-batch-validation/`):

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Batch INSERT | 124,356 blocks/sec | Far exceeds RPC rates (1-10 blocks/sec) |
| CHECKPOINT | < 10ms | Negligible overhead |
| SELECT COUNT(*) | < 1ms | Even for millions of rows |
| Full table scan | 0.15ms per 1M rows | DuckDB columnar storage |
| CHECK constraint | Inline | No measurable overhead |

**Conclusion**: DuckDB is never the bottleneck. RPC fetching is always the limiting factor.

---

## Common Mistakes to Avoid

### 1. Forgetting CHECKPOINT

❌ **Wrong**:
```python
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
# Data lost on crash!
```

✅ **Correct**:
```python
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
conn.execute("CHECKPOINT")  # Persist to disk
```

### 2. Not Using CHECK Constraints

❌ **Wrong**:
```sql
CREATE TABLE ethereum_blocks (
    gasUsed BIGINT,
    gasLimit BIGINT
    -- No constraints, invalid data possible
)
```

✅ **Correct**:
```sql
CREATE TABLE ethereum_blocks (
    gasUsed BIGINT NOT NULL,
    gasLimit BIGINT NOT NULL,
    CHECK (gasUsed <= gasLimit)  -- Catch corruption
)
```

### 3. Manual CSV Export/Import

❌ **Wrong**:
```python
df.to_csv("temp.csv")
conn.execute("COPY ethereum_blocks FROM 'temp.csv'")
```

✅ **Correct**:
```python
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
# DuckDB reads DataFrame directly
```

---

## References

- **Full Investigation**: `/Users/terryli/eon/gapless-network-data/scratch/duckdb-batch-validation/DUCKDB_BATCH_VALIDATION_REPORT.md `
- **Test Scripts**: `/Users/terryli/eon/gapless-network-data/scratch/duckdb-batch-validation/test_*.py `
- **Performance Data**: Empirically measured over 100K+ blocks
