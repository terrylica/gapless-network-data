"""Database initialization and management for gapless-network-data.

This module provides:
- DuckDB database initialization with schema creation
- Checkpoint save/load for crash recovery
- Database connection management
- Batch insert operations with durability guarantees

Architecture: DuckDB PRIMARY for raw data storage
Storage: ~/.cache/gapless-network-data/data.duckdb
Size: ~1.5 GB for 13M Ethereum blocks (76-100 bytes/block empirically validated)

Empirical Validation: 2025-11-04 (scratch/duckdb-batch-validation/)
- Batch INSERT: 124K blocks/sec
- CHECKPOINT required after each batch for durability (crash-tested)
- Resume capability: 0 data loss across 4 crash scenarios
"""

import json
from pathlib import Path
from typing import Any, Optional

import duckdb
import pandas as pd

from .exceptions import DatabaseException


# Default storage location (follows XDG Base Directory Specification)
DEFAULT_DB_PATH = Path.home() / ".cache" / "gapless-network-data" / "data.duckdb"


# DDL statements from duckdb-schema-specification.yaml
CREATE_ETHEREUM_BLOCKS = """
CREATE TABLE IF NOT EXISTS ethereum_blocks (
    block_number BIGINT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    baseFeePerGas BIGINT CHECK (baseFeePerGas >= 0),
    gasUsed BIGINT CHECK (gasUsed >= 0),
    gasLimit BIGINT CHECK (gasLimit >= 0),
    transactions_count INTEGER CHECK (transactions_count >= 0),
    CHECK (gasUsed <= gasLimit)
);

CREATE INDEX IF NOT EXISTS idx_ethereum_timestamp
ON ethereum_blocks(timestamp);
"""

CREATE_BITCOIN_MEMPOOL = """
CREATE TABLE IF NOT EXISTS bitcoin_mempool (
    snapshot_id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL UNIQUE,
    unconfirmed_count INTEGER CHECK (unconfirmed_count >= 0),
    vsize_mb DOUBLE CHECK (vsize_mb >= 0),
    total_fee_btc DOUBLE CHECK (total_fee_btc >= 0),
    fastest_fee DOUBLE CHECK (fastest_fee >= 1 AND fastest_fee <= 10000),
    half_hour_fee DOUBLE CHECK (half_hour_fee >= 1 AND half_hour_fee <= 10000),
    hour_fee DOUBLE CHECK (hour_fee >= 1 AND hour_fee <= 10000),
    economy_fee DOUBLE CHECK (economy_fee >= 1 AND economy_fee <= 10000),
    minimum_fee DOUBLE CHECK (minimum_fee >= 1),
    granularity VARCHAR CHECK (granularity IN ('M5', 'H24'))
);

CREATE INDEX IF NOT EXISTS idx_bitcoin_timestamp
ON bitcoin_mempool(timestamp);
"""

CREATE_METADATA = """
CREATE TABLE IF NOT EXISTS metadata (
    key VARCHAR PRIMARY KEY,
    value VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize collection progress checkpoints
INSERT OR IGNORE INTO metadata VALUES
    ('ethereum_last_block', '0', CURRENT_TIMESTAMP),
    ('bitcoin_last_snapshot', '0', CURRENT_TIMESTAMP),
    ('ethereum_start_date', '', CURRENT_TIMESTAMP),
    ('ethereum_end_date', '', CURRENT_TIMESTAMP),
    ('collection_version', '0.2.0', CURRENT_TIMESTAMP);
"""


class Database:
    """DuckDB database manager for blockchain network data.

    Provides database initialization, connection management, and checkpoint operations.

    Empirical validation (scratch/duckdb-batch-validation/):
    - CHECKPOINT required after batch INSERT for durability
    - Without CHECKPOINT: data stays in-memory, lost on crash
    - Performance: 124,356 blocks/sec at 1K batch size

    Example:
        >>> db = Database()
        >>> db.initialize()
        >>>
        >>> # Batch insert with durability
        >>> df = pd.DataFrame([...])  # 1000 blocks
        >>> db.insert_ethereum_blocks(df)
        >>> # CHECKPOINT called automatically for durability
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager.

        Args:
            db_path: Path to DuckDB file. Defaults to ~/.cache/gapless-network-data/data.duckdb
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def initialize(self) -> None:
        """Initialize database with schema creation.

        Creates:
        - ethereum_blocks table with constraints and indexes
        - bitcoin_mempool table (deferred to Phase 2+)
        - metadata table for checkpoint tracking

        Creates parent directories if they don't exist.
        Safe to call multiple times (CREATE TABLE IF NOT EXISTS).

        Raises:
            DatabaseException: If schema creation fails
        """
        try:
            # Create parent directory if doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Connect and create schema
            self.conn = duckdb.connect(str(self.db_path))

            # Create tables (idempotent)
            self.conn.execute(CREATE_ETHEREUM_BLOCKS)
            self.conn.execute(CREATE_BITCOIN_MEMPOOL)
            self.conn.execute(CREATE_METADATA)

            # Ensure changes persisted
            self.conn.execute("CHECKPOINT")

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to initialize database: {e}",
                context={
                    "db_path": str(self.db_path),
                    "operation": "initialize",
                }
            ) from e

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Get database connection (creates if doesn't exist).

        Returns:
            DuckDB connection object

        Raises:
            DatabaseException: If connection fails
        """
        if self.conn is None:
            try:
                self.conn = duckdb.connect(str(self.db_path))
            except Exception as e:
                raise DatabaseException(
                    message=f"Failed to connect to database: {e}",
                    context={"db_path": str(self.db_path)}
                ) from e
        return self.conn

    def close(self) -> None:
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def insert_ethereum_blocks(self, df: pd.DataFrame) -> None:
        """Insert Ethereum blocks with durability guarantee.

        Uses batch INSERT + CHECKPOINT pattern (empirically validated).

        Args:
            df: DataFrame with columns: block_number, timestamp, baseFeePerGas,
                gasUsed, gasLimit, transactions_count

        Raises:
            DatabaseException: If insert or checkpoint fails
        """
        try:
            conn = self.connect()

            # Batch INSERT from DataFrame
            conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")

            # CRITICAL: Call CHECKPOINT for durability
            # Empirically validated: scratch/duckdb-batch-validation/
            # Without this: data stays in-memory, lost on crash
            conn.execute("CHECKPOINT")

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to insert Ethereum blocks: {e}",
                context={
                    "operation": "insert_ethereum_blocks",
                    "num_blocks": len(df),
                    "db_path": str(self.db_path),
                }
            ) from e

    def insert_bitcoin_snapshots(self, df: pd.DataFrame) -> None:
        """Insert Bitcoin mempool snapshots with durability guarantee.

        Args:
            df: DataFrame with Bitcoin mempool columns

        Raises:
            DatabaseException: If insert or checkpoint fails
        """
        try:
            conn = self.connect()
            conn.execute("INSERT INTO bitcoin_mempool SELECT * FROM df")
            conn.execute("CHECKPOINT")  # Durability guarantee

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to insert Bitcoin snapshots: {e}",
                context={
                    "operation": "insert_bitcoin_snapshots",
                    "num_snapshots": len(df),
                }
            ) from e

    def save_checkpoint(self, key: str, value: Any) -> None:
        """Save checkpoint to metadata table.

        Args:
            key: Checkpoint key (e.g., 'ethereum_last_block')
            value: Checkpoint value (serialized as JSON if dict/list)

        Raises:
            DatabaseException: If checkpoint save fails
        """
        try:
            conn = self.connect()

            # Serialize complex types as JSON
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)

            # Upsert checkpoint
            conn.execute(
                """
                INSERT INTO metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                [key, value_str]
            )

            # Persist checkpoint immediately
            conn.execute("CHECKPOINT")

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to save checkpoint: {e}",
                context={"key": key, "value": value_str}
            ) from e

    def load_checkpoint(self, key: str, default: Any = None) -> Any:
        """Load checkpoint from metadata table.

        Args:
            key: Checkpoint key
            default: Default value if checkpoint doesn't exist

        Returns:
            Checkpoint value (JSON-parsed if applicable) or default

        Raises:
            DatabaseException: If checkpoint load fails
        """
        try:
            conn = self.connect()

            result = conn.execute(
                "SELECT value FROM metadata WHERE key = ?",
                [key]
            ).fetchone()

            if result is None:
                return default

            value_str = result[0]

            # Try to parse as JSON
            try:
                return json.loads(value_str)
            except (json.JSONDecodeError, TypeError):
                return value_str

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to load checkpoint: {e}",
                context={"key": key}
            ) from e

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with row counts, latest blocks, data age
        """
        try:
            conn = self.connect()

            stats = {}

            # Ethereum stats
            eth_count = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()[0]
            stats["ethereum_blocks_count"] = eth_count

            if eth_count > 0:
                latest = conn.execute(
                    "SELECT MAX(timestamp), MAX(block_number) FROM ethereum_blocks"
                ).fetchone()
                stats["ethereum_latest_timestamp"] = latest[0]
                stats["ethereum_latest_block"] = latest[1]

            # Bitcoin stats (if table has data)
            btc_count = conn.execute("SELECT COUNT(*) FROM bitcoin_mempool").fetchone()[0]
            stats["bitcoin_snapshots_count"] = btc_count

            # Database file size
            if self.db_path.exists():
                stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)

            return stats

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get database stats: {e}",
                context={"operation": "get_stats"}
            ) from e

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
