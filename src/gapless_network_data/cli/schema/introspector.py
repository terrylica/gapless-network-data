"""
ClickHouse schema introspector for validation and apply operations.

Queries live ClickHouse to:
- Validate schema matches YAML contract
- Apply DDL changes
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import clickhouse_connect

if TYPE_CHECKING:
    from gapless_network_data.schema.loader import Schema


@dataclass
class ColumnDiff:
    """Represents a difference between YAML and live schema."""

    column: str
    field: str
    yaml_value: str
    live_value: str


def _get_client() -> clickhouse_connect.driver.Client:
    """
    Get ClickHouse client using credentials from environment.

    Uses read-only credentials for validation, write credentials for apply.
    """
    # Try read-only credentials first (for validation)
    host = os.environ.get("CLICKHOUSE_HOST_READONLY") or os.environ.get("CLICKHOUSE_HOST")
    user = os.environ.get("CLICKHOUSE_USER_READONLY") or os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD_READONLY") or os.environ.get("CLICKHOUSE_PASSWORD")

    if not host:
        msg = "CLICKHOUSE_HOST or CLICKHOUSE_HOST_READONLY environment variable required"
        raise ValueError(msg)

    if not password:
        msg = "CLICKHOUSE_PASSWORD or CLICKHOUSE_PASSWORD_READONLY environment variable required"
        raise ValueError(msg)

    return clickhouse_connect.get_client(
        host=host,
        port=8443,
        username=user,
        password=password,
        secure=True,
    )


def _get_live_columns(client: clickhouse_connect.driver.Client, database: str, table: str) -> dict[str, dict]:
    """
    Query live ClickHouse schema from system.columns.

    Returns:
        Dict mapping column name to {type, comment, default_kind, default_expression}
    """
    query = f"""
    SELECT
        name,
        type,
        comment,
        default_kind,
        default_expression
    FROM system.columns
    WHERE database = '{database}' AND table = '{table}'
    ORDER BY position
    """

    result = client.query(query)

    columns = {}
    for row in result.result_rows:
        name, col_type, comment, default_kind, default_expr = row
        columns[name] = {
            "type": col_type,
            "comment": comment,
            "default_kind": default_kind,
            "default_expression": default_expr,
        }

    return columns


def validate_schema(schema: Schema) -> tuple[bool, str]:
    """
    Validate that live ClickHouse schema matches YAML contract.

    Args:
        schema: Parsed schema object

    Returns:
        Tuple of (is_valid, diff_message)
    """
    client = _get_client()

    try:
        live_columns = _get_live_columns(
            client,
            schema.clickhouse.database,
            schema.clickhouse.table,
        )
    except Exception as e:
        return False, f"Failed to query live schema: {e}"

    diffs: list[ColumnDiff] = []

    # Check each YAML column against live schema
    for col in schema.columns:
        if col.name not in live_columns:
            diffs.append(ColumnDiff(
                column=col.name,
                field="existence",
                yaml_value="defined",
                live_value="missing",
            ))
            continue

        live = live_columns[col.name]

        # Compare types
        if col.clickhouse_type != live["type"]:
            diffs.append(ColumnDiff(
                column=col.name,
                field="type",
                yaml_value=col.clickhouse_type,
                live_value=live["type"],
            ))

        # Compare comments (descriptions)
        if col.description and live["comment"] and col.description != live["comment"]:
            diffs.append(ColumnDiff(
                column=col.name,
                field="comment",
                yaml_value=col.description[:50] + "..." if len(col.description) > 50 else col.description,
                live_value=live["comment"][:50] + "..." if len(live["comment"]) > 50 else live["comment"],
            ))

    # Check for columns in live that aren't in YAML
    yaml_columns = {col.name for col in schema.columns}
    for live_col in live_columns:
        if live_col not in yaml_columns:
            diffs.append(ColumnDiff(
                column=live_col,
                field="existence",
                yaml_value="not defined",
                live_value="exists",
            ))

    if not diffs:
        return True, ""

    # Format diff message
    lines = []
    for diff in diffs:
        lines.append(f"  {diff.column}.{diff.field}: YAML={diff.yaml_value}, Live={diff.live_value}")

    return False, "\n".join(lines)


def apply_ddl(ddl_path: Path) -> None:
    """
    Apply DDL file to ClickHouse.

    Args:
        ddl_path: Path to generated DDL file

    Raises:
        Exception: If DDL execution fails
    """
    # For apply, we need write credentials
    host = os.environ.get("CLICKHOUSE_HOST")
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host:
        msg = "CLICKHOUSE_HOST environment variable required for apply"
        raise ValueError(msg)

    if not password:
        msg = "CLICKHOUSE_PASSWORD environment variable required for apply"
        raise ValueError(msg)

    client = clickhouse_connect.get_client(
        host=host,
        port=8443,
        username=user,
        password=password,
        secure=True,
    )

    with open(ddl_path) as f:
        ddl = f.read()

    # Skip header comments and execute DDL
    # Split on CREATE and rejoin to handle multi-statement files
    statements = []
    current = []
    for line in ddl.split("\n"):
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if line.strip().endswith(";"):
            statements.append("\n".join(current))
            current = []

    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            client.command(stmt)
