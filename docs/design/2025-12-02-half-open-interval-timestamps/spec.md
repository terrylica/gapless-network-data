---
version: "1.0.0"
last_updated: "2025-12-02"
supersedes: []
---

# Design Spec: Half-Open Interval Timestamp Handling

**ADR**: [Adopt Half-Open Interval for Date Range Queries](/docs/adr/2025-12-02-half-open-interval-timestamps.md)

## Problem

`fetch_blocks(start='2024-03-13', end='2024-03-13')` raises:

```
DatabaseException: Failed to query blocks: 'number' [start=2024-03-13, end=2024-03-13, limit=None]
```

## Root Cause (Empirically Validated)

**TWO separate issues:**

1. **Date interpretation**: ClickHouse interprets `'2024-03-13'` as `'2024-03-13 00:00:00'`, making same-day = exact timestamp (0 matches)
2. **Empty result handling**: clickhouse-connect returns empty `column_names: ()` when 0 rows, causing KeyError

---

## Industry Research: Half-Open Interval Standard

### Best Practice: `[start, end)` (Inclusive Start, Exclusive End)

| Source                                                                                                      | Pattern        | Evidence                                           |
| ----------------------------------------------------------------------------------------------------------- | -------------- | -------------------------------------------------- |
| [PostgreSQL ranges](https://www.postgresql.org/docs/current/rangetypes.html)                                | `[start, end)` | "Default is from start inclusive to end exclusive" |
| [BigQuery time series](https://cloud.google.com/bigquery/docs/reference/standard-sql/time-series-functions) | `[start, end)` | "`end_timestamp` is exclusive"                     |
| [yfinance](https://marketxls.com/blog/yahoo-finance-api-the-ultimate-guide-for-2024)                        | `[start, end)` | "Similar to Python's range()"                      |
| [pandas](https://pandas.pydata.org/docs/reference/api/pandas.date_range.html)                               | Configurable   | `inclusive='left'` for half-open                   |
| SQL BETWEEN                                                                                                 | Inclusive both | **Not recommended for time series**                |

**Rationale**:

- Prevents boundary overlap between consecutive ranges
- Makes consecutive time windows non-overlapping
- Critical for financial aggregations
- Aligns with Python's `range()` semantics

### Current State vs Best Practice

| Component                 | Current       | Standard       | Aligned? |
| ------------------------- | ------------- | -------------- | -------- |
| BigQuery Sync (cloud-run) | `>=` and `<`  | `[start, end)` | Yes      |
| Historical Migration      | `>=` and `<`  | `[start, end)` | Yes      |
| **SDK API**               | `>=` and `<=` | `[start, end)` | **No**   |

---

## Solution: Align with Industry Standard

**Design Decision**: Change SDK API to use **half-open interval** `[start, end)`:

- `start`: Inclusive (`>=`)
- `end`: Exclusive (`<`)

With **date expansion** for date-only inputs:

- `start='2024-03-13'` → `>= 2024-03-13 00:00:00.000000`
- `end='2024-03-13'` → `< 2024-03-14 00:00:00.000000` (next day, exclusive)

### Behavior Matrix

| Input                                              | Start Boundary           | End Boundary            | Blocks Included    |
| -------------------------------------------------- | ------------------------ | ----------------------- | ------------------ |
| `start='2024-03-13', end='2024-03-13'`             | `>= 2024-03-13 00:00:00` | `< 2024-03-14 00:00:00` | All of March 13    |
| `start='2024-03-13', end='2024-03-14'`             | `>= 2024-03-13 00:00:00` | `< 2024-03-15 00:00:00` | All of March 13-14 |
| `start='2024-03-13 12:00', end='2024-03-13 18:00'` | `>= 2024-03-13 12:00:00` | `< 2024-03-13 18:00:00` | 12:00-17:59:59     |

**Note**: This is a **behavioral change** but aligns with industry standards and our own cloud jobs.

---

## Comprehensive Audit Findings

### Scope Assessment (No Pipeline Impact)

| Component               | Affected? | Reason                   |
| ----------------------- | --------- | ------------------------ |
| `api.py`                | YES       | Query string building    |
| `realtime_collector.py` | NO        | Direct ClickHouse insert |
| `cloud-run/main.py`     | NO        | Already uses `<`         |
| `gap-monitor/main.py`   | NO        | Raw SQL, no date ranges  |

### Documentation Updates Required

| File               | Current Example    | Needs Update           |
| ------------------ | ------------------ | ---------------------- |
| `README.md`        | `end='2024-01-31'` | Clarify exclusive end  |
| `CLAUDE.md`        | `end='2024-01-31'` | Clarify exclusive end  |
| `llms.txt`         | `end='2024-01-31'` | Clarify exclusive end  |
| `probe.py`         | `end='2024-01-31'` | Clarify exclusive end  |
| `api.py` docstring | No mention         | Add boundary semantics |

### Schema Discrepancy

| Location            | Documented | Actual          |
| ------------------- | ---------- | --------------- |
| CLAUDE.md           | `DateTime` | -               |
| create_schema.py:65 | -          | `DateTime64(3)` |

**Action**: Update CLAUDE.md to `DateTime64(3)`.

---

## Files to Modify

### Primary (Bug Fix + Standard Alignment)

1. **`src/gapless_network_data/api.py`** (lines 286-318)

### Secondary (Documentation)

2. **`CLAUDE.md`** - Schema + boundary semantics
3. **`README.md`** - Clarify exclusive end
4. **`llms.txt`** - Update for AI agents
5. **`src/gapless_network_data/probe.py`** - Example code
6. **`tests/test_api.py`** - Add timestamp tests

---

## Implementation

### Step 1: Add timestamp normalization helper (api.py)

```python
def _normalize_timestamp(ts_str: str, is_end: bool = False) -> str:
    """
    Normalize timestamp string for half-open interval queries.

    Following industry standard [start, end):
    - Date-only strings expand to day boundaries
    - Explicit times are preserved with ms precision
    - End timestamps: date-only → next day start (exclusive)

    Args:
        ts_str: Timestamp string (various formats)
        is_end: If True, expand date-only to next day start

    Returns:
        Formatted timestamp string with millisecond precision
    """
    ts = pd.to_datetime(ts_str)

    # Detect date-only input (no time component specified)
    is_date_only = (
        ts.hour == 0 and ts.minute == 0 and ts.second == 0
        and ts.microsecond == 0
        and 'T' not in str(ts_str) and ':' not in str(ts_str)
    )

    if is_date_only and is_end:
        # Expand to next day start for exclusive end
        ts = ts + pd.Timedelta(days=1)

    return ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Milliseconds (DateTime64(3))
```

### Step 2: Update query building (api.py lines 286-295)

```python
# Build query with half-open interval [start, end)
# Industry standard: PostgreSQL, BigQuery, yfinance
conditions = []
if start:
    start_ts = _normalize_timestamp(start, is_end=False)
    conditions.append(f"timestamp >= '{start_ts}'")

if end:
    end_ts = _normalize_timestamp(end, is_end=True)
    conditions.append(f"timestamp < '{end_ts}'")  # Exclusive end
```

### Step 3: Handle empty column_names (api.py lines 311-314)

```python
try:
    result = client.query(query)
    # Handle clickhouse-connect returning empty column_names when 0 rows
    if not result.column_names:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(result.result_rows, columns=result.column_names)
```

### Step 4: Update docstring (api.py)

```python
def fetch_blocks(
    start: str | None = None,
    end: str | None = None,
    ...
) -> pd.DataFrame:
    """
    Fetch Ethereum block data optimized for alpha feature engineering.

    Date Range Semantics (half-open interval [start, end)):
        - start: Inclusive (blocks >= start)
        - end: Exclusive (blocks < end)
        - Date-only strings expand to full day boundaries
        - Example: start='2024-03-13', end='2024-03-13' returns all blocks on March 13

    This follows industry standards used by PostgreSQL, BigQuery, and yfinance.
    ...
    """
```

### Step 5: Update CLAUDE.md schema

```sql
CREATE TABLE ethereum_mainnet.blocks (
    timestamp DateTime64(3) NOT NULL,  -- Millisecond precision
    number UInt64,
    ...
```

### Step 6: Add test cases

```python
class TestFetchBlocksTimestampHandling:
    """Test half-open interval timestamp handling."""

    def test_same_day_returns_full_day(self):
        """Same-day query returns all blocks for that day."""
        df = gmd.fetch_blocks(start='2024-03-13', end='2024-03-13', limit=10)
        assert len(df) > 0
        assert all(df['timestamp'].dt.date == pd.Timestamp('2024-03-13').date())

    def test_exclusive_end_boundary(self):
        """End boundary is exclusive (standard [start, end) interval)."""
        df = gmd.fetch_blocks(
            start='2024-03-13 12:00:00',
            end='2024-03-13 12:00:01',  # 1 second window
            limit=100
        )
        # All timestamps should be < end
        assert all(df['timestamp'] < pd.Timestamp('2024-03-13 12:00:01', tz='UTC'))

    def test_empty_result_returns_schema(self):
        """Empty result returns DataFrame with correct columns."""
        df = gmd.fetch_blocks(
            start='2024-03-13 00:00:00.000',
            end='2024-03-13 00:00:00.001',
        )
        assert isinstance(df, pd.DataFrame)
        assert 'number' in df.columns
        assert len(df) == 0
```

---

## Test Verification

```bash
# Before fix - fails
uv run python -c "import gapless_network_data as gmd; gmd.fetch_blocks(start='2024-03-13', end='2024-03-13')"
# DatabaseException: 'number'

# After fix - works (half-open interval)
uv run python -c "
import gapless_network_data as gmd
df = gmd.fetch_blocks(start='2024-03-13', end='2024-03-13', limit=5)
print(f'Rows: {len(df)}')
print(df[['timestamp', 'number']].head())
"
# Returns all blocks from 2024-03-13 00:00:00 to 2024-03-13 23:59:59
```

---

## Risk Assessment

| Risk                      | Likelihood | Impact | Mitigation                                         |
| ------------------------- | ---------- | ------ | -------------------------------------------------- |
| Breaking existing queries | Low        | Medium | Exclusive end is industry standard, more intuitive |
| User confusion            | Low        | Low    | Document clearly, add examples                     |
| Pipeline impact           | None       | N/A    | Pipelines don't use SDK API                        |

---

## Release

- Version bump: 4.7.0 → 4.7.1 (patch - bug fix with behavioral alignment)
- Changelog: "fix: adopt half-open interval [start, end) for date range queries (industry standard)"

## Sources

- [PostgreSQL Range Types](https://www.postgresql.org/docs/current/rangetypes.html)
- [BigQuery Time Series Functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/time-series-functions)
- [pandas.date_range](https://pandas.pydata.org/docs/reference/api/pandas.date_range.html)
- [yfinance API Guide](https://marketxls.com/blog/yahoo-finance-api-the-ultimate-guide-for-2024)
