#!/usr/bin/env python3
"""Test database initialization and basic operations.

Demonstrates:
1. Database initialization with schema creation
2. Checkpoint save/load operations
3. Database statistics

Run with: uv run test_db_init.py
"""

from pathlib import Path
from src.gapless_network_data.db import Database

def main():
    """Test database initialization."""
    print("=== DuckDB Database Initialization Test ===\n")

    # Use test database path
    test_db_path = Path("./test_data.duckdb")

    # Clean up if exists
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"Removed existing test database: {test_db_path}\n")

    # Initialize database
    print(f"Initializing database at: {test_db_path}")
    db = Database(db_path=test_db_path)
    db.initialize()
    print("✅ Database initialized successfully\n")

    # Test checkpoint save/load
    print("Testing checkpoint operations:")
    db.save_checkpoint("ethereum_last_block", 12345678)
    db.save_checkpoint("ethereum_start_date", "2020-01-01")
    db.save_checkpoint("test_dict", {"status": "running", "progress": 0.45})
    print("✅ Saved 3 checkpoints\n")

    # Load checkpoints
    last_block = db.load_checkpoint("ethereum_last_block", default=0)
    start_date = db.load_checkpoint("ethereum_start_date", default="")
    test_dict = db.load_checkpoint("test_dict", default={})

    print(f"Loaded checkpoints:")
    print(f"  - ethereum_last_block: {last_block}")
    print(f"  - ethereum_start_date: {start_date}")
    print(f"  - test_dict: {test_dict}")
    print()

    # Get stats
    stats = db.get_stats()
    print("Database statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    print()

    # Test context manager
    print("Testing context manager:")
    with Database(db_path=test_db_path) as db_ctx:
        conn = db_ctx.connect()
        result = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()
        print(f"  - ethereum_blocks count: {result[0]}")
    print("✅ Context manager works\n")

    # Cleanup
    db.close()
    test_db_path.unlink()
    print(f"✅ Test complete, cleaned up: {test_db_path}")

    print("\n=== Production Usage ===\n")
    print("To use with production database:")
    print("  from gapless_network_data.db import Database")
    print("  ")
    print("  # Initialize (creates ~/.cache/gapless-network-data/data.duckdb)")
    print("  db = Database()")
    print("  db.initialize()")
    print("  ")
    print("  # Save checkpoint")
    print("  db.save_checkpoint('ethereum_last_block', 21000000)")
    print("  ")
    print("  # Load checkpoint")
    print("  last_block = db.load_checkpoint('ethereum_last_block', default=0)")
    print("  ")
    print("  # Get stats")
    print("  stats = db.get_stats()")
    print("  print(f'Total blocks: {stats[\"ethereum_blocks_count\"]}')")

if __name__ == "__main__":
    main()
