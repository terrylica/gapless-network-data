# Historical Data Collection Strategy

## 5-Year Backfill Architecture

**Critical Requirement Change**: Initial goal is HISTORICAL data (5 years back), NOT real-time collection

**Date**: 2025-11-04
**Impact**: Fundamental architecture change from forward-only to historical backfill

---

## 🚨 KEY CHANGES FROM ORIGINAL PLAN

### What Changed

❌ **REMOVED**: Forward-collection-only constraint  
❌ **REMOVED**: "Start time must be within 5 minutes of now" validation  
❌ **REMOVED**: Continuous polling/daemon mode

✅ **ADDED**: Historical backfill (2020-2025, 5 years)  
✅ **ADDED**: Batch fetching with progress tracking  
✅ **ADDED**: Resume capability for multi-day fetches  
✅ **ADDED**: Rate limit management for large-scale collection

---

## 📊 HISTORICAL DATA AVAILABILITY

### Ethereum - EXCELLENT (PRIMARY)

- **Timespan**: 2015-07-30 (genesis) to present = **9.5 years available**
- **Granularity**: 12-second blocks (~2.6M blocks/year)
- **5-year estimate**: Jan 2020 - Jan 2025 = **~13 million blocks**
- **Data source**: LlamaRPC archive nodes
- **Quality**: Complete block data, all 26 fields available

**Time Estimates** (5 years, empirically validated 2025-11-04):

- At 5.5-6.85 blocks/sec (validated sustained rate): **530-650 hours** (22-27 days)
- Conservative estimate (1 req/sec): **150 hours** (6-7 days) - UNDERESTIMATE
- Aggressive (10 req/sec): **15 hours** (~1 day) - NOT TESTED

**Validation**: LlamaRPC archive access confirmed (scratch/llamarpc-archive-validation/)

### Bitcoin - LIMITED (SECONDARY)

- **Timespan**: 2016+ available
- **Recent data** (< 1 month): M5 granularity (5-minute intervals) = **8,640 snapshots/month**
- **Historical data** (> 1 month): **H24 granularity (24-hour intervals, NOT H12)** = **365 snapshots/year**
- **5-year estimate**: 365 × 5 = **1,825 snapshots** (vs 525,600 if 5-minute)

**CRITICAL LIMITATION**: Bitcoin historical data loses 99.65% granularity (5-min → 24-hour)

**Validation**: Empirically confirmed H24 (not H12) via scratch/bitcoin-historical-validation/

**Alternative sources**:

- blockchain.info: H29 (29-hour) mempool size from 2009+
- Consider: Just use recent 1-month M5 data for Bitcoin, skip historical

---

## 🏗️ UPDATED ARCHITECTURE

### Collection Modes

**Mode 1: Historical Backfill** (PRIMARY)

```python
df = fetch_snapshots(
    chain="ethereum",
    start="2020-01-01 00:00:00",  # 5 years ago
    end="2025-01-01 00:00:00",    # Present
    mode="historical",  # NEW parameter
    batch_size=1000,  # Fetch 1000 blocks at a time
    checkpoint_interval=10000,  # Save progress every 10K blocks
)
```

**Mode 2: Real-Time Collection** (Optional, future)

```python
df = fetch_snapshots(
    chain="ethereum",
    start="now",
    end="now+1hour",
    mode="realtime",  # Continuous polling
    interval=12,  # 12-second polling
)
```

---

## 🛠️ IMPLEMENTATION STRATEGY

### Phase 1A: Ethereum Historical Backfill (20-30 hours)

**Task 1: EthereumHistoricalCollector (6 hours)**

```python
class EthereumHistoricalCollector:
    def __init__(self, checkpoint_file="ethereum_progress.json", db_path="~/.cache/gapless-network-data/data.duckdb"):
        self.w3 = Web3(HTTPProvider("https://eth.llamarpc.com"))
        self.checkpoint_file = checkpoint_file
        self.db_path = db_path
        self.last_block = self._load_checkpoint()
        self.conn = duckdb.connect(db_path)

    def collect_range(self, start_block: int, end_block: int, batch_size=100) -> pd.DataFrame:
        """Fetch historical blocks with progress tracking."""
        blocks = []

        # Resume from checkpoint
        current_block = max(start_block, self.last_block + 1)

        while current_block <= end_block:
            batch_end = min(current_block + batch_size, end_block)

            # Fetch batch (parallel requests)
            batch_blocks = self._fetch_batch(current_block, batch_end)
            blocks.extend(batch_blocks)

            # Save checkpoint every 1000 blocks
            if len(blocks) % 1000 == 0:
                self._save_checkpoint(batch_end)
                self._write_duckdb_batch(blocks)
                blocks = []  # Clear memory

            current_block = batch_end + 1
            time.sleep(0.1)  # Rate limit: 10 req/sec

        return pd.DataFrame(blocks)

    def _fetch_batch(self, start, end):
        """Fetch multiple blocks concurrently."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.w3.eth.get_block, block_num)
                for block_num in range(start, end + 1)
            ]
            return [f.result() for f in futures]

    def _write_duckdb_batch(self, blocks):
        """Write blocks to DuckDB with batch INSERT."""
        df = pd.DataFrame(blocks)
        self.conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")
        # CRITICAL: Call CHECKPOINT for durability (crash-tested requirement)
        self.conn.execute("CHECKPOINT")  # Empirically validated: scratch/duckdb-batch-validation/
```

**Features**:

- ✅ Checkpoint-based resume (survive crashes)
- ✅ Batch fetching (10-100 concurrent requests)
- ✅ Memory-efficient (write to DuckDB every 1000 blocks)
- ✅ Progress logging (ETA, blocks/sec)
- ✅ Rate limit compliance

**Task 2: Block Number Resolution (2 hours)**

```python
def _resolve_block_number(self, timestamp: str) -> int:
    """Convert timestamp to block number (binary search)."""
    # Ethereum blocks have timestamps
    # Binary search to find block closest to timestamp
    # Cache timestamp→block mapping
    pass
```

**Why needed**: User provides dates ("2020-01-01"), need to convert to block numbers

**Task 3: Progress Tracking UI (2 hours)**

```python
# CLI output:
# Ethereum Historical Backfill
# ============================
# Range: Block 11,560,000 - 21,000,000 (9.44M blocks)
# Progress: [████████░░] 45% (4.25M / 9.44M blocks)
# Speed: 125 blocks/sec
# Elapsed: 9h 25m
# ETA: 11h 15m
# Last checkpoint: Block 15,810,000 (saved 2025-11-04 15:23:45)
```

**Task 4: Retry & Error Handling (3 hours)**

- Exponential backoff for failed blocks
- Skip blocks that consistently fail (log to errors.csv)
- Handle rate limit 429 errors (back off 60 seconds)
- Connection errors (retry 3 times)

**Task 5: Testing (4 hours)**

- Unit tests with mocked web3.py
- Integration test: Fetch 1000 real blocks
- Load test: Verify rate limits not exceeded
- Resume test: Stop mid-fetch, restart, verify continuation

---

### Phase 1B: Bitcoin Historical Collection (8-12 hours)

**Decision Point**: Given H12 (12-hour) granularity for historical data:

**Option A: Collect Bitcoin Historical Data**

- 5 years = 3,650 snapshots (very sparse)
- Use mempool.space historical API
- **Pros**: Some historical context
- **Cons**: 99.3% data loss vs 5-minute granularity

**Option B: Bitcoin Recent Data Only**

- Collect only last 1-2 months (M5 granularity)
- **Pros**: High-quality 5-minute data
- **Cons**: No 5-year history

**Recommendation**: Start with Option A (collect H12 historical), add recent M5 later

---

## ⏱️ UPDATED TIMELINE

### Phase 1: Historical Data Collection (3-4 weeks)

**Week 1: Ethereum Historical Collector (20 hours)**

- Implement historical backfill
- Block number resolution
- Progress tracking
- Checkpoint/resume
- Testing

**Week 2-4: Run 5-Year Ethereum Backfill (530-650 hours machine time, 10-20 hours human time)**

- Start backfill (monitor first 24 hours)
- Verify checkpoints working
- Handle errors as they arise
- **Machine runs continuously for 22-27 days at 5.5-6.85 blocks/sec** (empirically validated)

**Week 5: Bitcoin Historical + Multi-Chain API (15 hours) - DEFERRED TO PHASE 2+**

- Bitcoin H24 historical collector (SECONDARY priority)
- Multi-chain API updates
- CLI updates
- Testing

**Week 6: Validation & Release (10 hours)**

- Data quality validation
- Documentation
- v0.2.0 release

**Total**: 4-6 weeks **PLUS** 22-27 days machine runtime for Ethereum backfill (empirically validated)

---

## 🎯 SUCCESS CRITERIA (UPDATED)

### Ethereum Historical Collection

- ✅ Collect 5 years (2020-2025) = ~13M blocks
- ✅ All 6 fields present and valid
- ✅ < 0.01% missing blocks (allow ~1,300 failures)
- ✅ Data stored in DuckDB ethereum_blocks table (~1.5 GB, 76-100 bytes/block empirically validated)
- ✅ Resume capability works (checkpoint/resume crash-tested with 0 data loss)

### Bitcoin Historical Collection (DEFERRED TO PHASE 2+)

- ✅ Collect 5 years H24 data = 1,825 snapshots (empirically validated: H24 not H12)
- ✅ Document granularity limitation clearly (99.65% data loss: 5-min → 24-hour)
- ✅ Option to add recent M5 data (last 1-2 months)
- ⚠️ SECONDARY priority - deferred after Ethereum PRIMARY collection

### Multi-Chain API

- ✅ Supports both historical and realtime modes
- ✅ `fetch_snapshots(chain, start, end, mode="historical")`
- ✅ Progress tracking for long-running fetches

---

## 📋 NEXT STEPS (RIGHT NOW)

1. **Confirm Bitcoin historical approach**:
   - Do you want H12 (12-hour) Bitcoin data for 5 years?
   - Or focus on Ethereum only + recent Bitcoin M5?

2. **Confirm Ethereum time range**:
   - Exactly 5 years? (2020-01-01 to 2025-01-01)
   - Or all available? (2015-07-30 to present = 9.5 years)

3. **Confirm rate limit strategy**:
   - Start conservative (1 req/sec = 7 days)?
   - Or test aggressive (10 req/sec = 15 hours)?

4. **Update specifications** once confirmed:
   - Remove forward-only constraints
   - Add historical backfill tasks
   - Update time estimates

---

## ⚠️ CRITICAL QUESTIONS FOR YOU

Before I update all specifications, please confirm:

1. **Time range**: Exactly 5 years (2020-2025) or all available (2015-2025)?

2. **Bitcoin historical**: Accept H24 (24-hour, NOT H12) granularity or skip historical Bitcoin? (DEFERRED TO PHASE 2+)

3. **Urgency**: Need data ASAP (test aggressive rate limits) or safety first (conservative 5.5-6.85 blocks/sec)?

4. **Storage**: ~13M Ethereum blocks = ~1.5 GB DuckDB (76-100 bytes/block empirically validated). Storage OK? (ANSWERED: Yes, negligible)

5. **Runtime**: OK with 22-27 day continuous machine runtime for Ethereum backfill? (EMPIRICALLY VALIDATED)

Let me know your answers and I'll update all the specifications accordingly!
