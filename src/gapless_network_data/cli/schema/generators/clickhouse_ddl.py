"""
Generate ClickHouse DDL from YAML schema.

Usage:
    uv run gapless-network-data schema generate-ddl
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gapless_network_data.schema.loader import ColumnConfig, Schema


def _generate_column_def(col: ColumnConfig) -> str:
    """
    Generate a single column definition.

    ADR: 2025-12-10-clickhouse-codec-optimization - Added codec emission

    Args:
        col: Column configuration

    Returns:
        SQL column definition string
    """
    parts = [col.name, col.clickhouse_type]

    # Add NOT NULL for required columns (nullable columns don't need it)
    if col.clickhouse_not_null:
        parts.append("NOT NULL")

    # Add CODEC if specified (ADR: 2025-12-10-clickhouse-codec-optimization)
    if col.clickhouse_codec:
        parts.append(col.clickhouse_codec)

    # Add COMMENT with description
    if col.description:
        # Escape single quotes in description
        desc = col.description.replace("'", "''")
        parts.append(f"COMMENT '{desc}'")

    return " ".join(parts)


def _generate_header(schema_path: str) -> str:
    """Generate the file header."""
    return f"""-- AUTO-GENERATED from {schema_path}
-- DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-ddl
-- Generated at: {datetime.now().isoformat()}

"""


def generate_ddl(schema: Schema) -> Path:
    """
    Generate ClickHouse DDL from schema.

    Args:
        schema: Parsed schema object

    Returns:
        Path to generated file
    """
    ch = schema.clickhouse

    # Build column definitions
    column_defs = []
    for col in schema.columns:
        column_defs.append(f"    {_generate_column_def(col)}")

    columns_sql = ",\n".join(column_defs)

    # Build ORDER BY clause
    order_by = ", ".join(ch.order_by) if ch.order_by else "tuple()"

    # Build SETTINGS clause
    settings_parts = []
    for key, value in ch.settings.items():
        settings_parts.append(f"{key} = {value}")
    settings_sql = ", ".join(settings_parts) if settings_parts else ""

    # Build full DDL
    ddl = f"""CREATE TABLE IF NOT EXISTS {ch.database}.{ch.table} (
{columns_sql}
)
ENGINE = {ch.engine}
"""

    if ch.partition_by:
        ddl += f"PARTITION BY {ch.partition_by}\n"

    ddl += f"ORDER BY ({order_by})"

    if settings_sql:
        ddl += f"\nSETTINGS {settings_sql}"

    ddl += ";\n"

    # Generate projection ALTER statements (ADR: 2025-12-10-clickhouse-codec-optimization)
    for proj in ch.projections:
        order_by_proj = ", ".join(proj.order_by) if proj.order_by else "tuple()"
        ddl += f"""
-- Projection: {proj.name}
ALTER TABLE {ch.database}.{ch.table} ADD PROJECTION {proj.name} (
    SELECT {proj.select} ORDER BY ({order_by_proj})
);
ALTER TABLE {ch.database}.{ch.table} MATERIALIZE PROJECTION {proj.name};
"""

    # Determine output path
    output_dir = Path.cwd() / "schema" / "clickhouse" / "_generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use database name for output file
    output_file = output_dir / f"{ch.database}.sql"

    # Generate content
    schema_path = f"schema/clickhouse/{ch.database}.yaml"
    content = _generate_header(schema_path)
    content += ddl

    # Write file
    with open(output_file, "w") as f:
        f.write(content)

    return output_file
