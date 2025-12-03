"""
Generate Markdown documentation from YAML schema.

Usage:
    uv run gapless-network-data schema doc
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gapless_network_data.schema.loader import ColumnConfig, Schema


def _generate_header(schema: Schema, schema_path: str) -> str:
    """Generate the documentation header."""
    return f"""# {schema.full_table_name}

_Generated from: {schema_path}_

_Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_

{schema.description}

"""


def _generate_alpha_features_table(schema: Schema) -> str:
    """Generate the alpha features ranking table."""
    # Filter columns with alpha feature rankings
    alpha_cols = [col for col in schema.columns if col.alpha_rank is not None]

    if not alpha_cols:
        return ""

    # Sort by rank
    alpha_cols.sort(key=lambda c: c.alpha_rank or 999)

    lines = ["## Alpha Feature Rankings", "", "| Rank | Column | Importance | Description |"]
    lines.append("| --- | --- | --- | --- |")

    for col in alpha_cols:
        desc = col.description[:50] + "..." if len(col.description) > 50 else col.description
        lines.append(f"| {col.alpha_rank} | {col.name} | {col.alpha_importance} | {desc} |")

    lines.append("")
    return "\n".join(lines)


def _generate_schema_table(schema: Schema) -> str:
    """Generate the schema table."""
    lines = ["## Schema", "", "| Column | Type | Nullable | Description |"]
    lines.append("| --- | --- | --- | --- |")

    for col in schema.columns:
        nullable = "YES" if not col.clickhouse_not_null else "NO"
        # Handle Nullable() types
        if col.clickhouse_type.startswith("Nullable("):
            nullable = "YES"

        lines.append(f"| {col.name} | {col.clickhouse_type} | {nullable} | {col.description} |")

    lines.append("")
    return "\n".join(lines)


def _generate_deprecated_section(schema: Schema) -> str:
    """Generate the deprecated columns section."""
    deprecated_cols = [col for col in schema.columns if col.deprecated_since]

    if not deprecated_cols:
        return ""

    lines = ["## Deprecated Columns", ""]

    for col in deprecated_cols:
        lines.append(f"### {col.name}")
        lines.append("")
        lines.append(f"- **Deprecated since**: {col.deprecated_since}")
        lines.append(f"- **Reason**: {col.deprecated_reason}")
        lines.append("")

    return "\n".join(lines)


def _generate_availability_section(schema: Schema) -> str:
    """Generate the column availability section."""
    available_cols = [col for col in schema.columns if col.available_since_block]

    if not available_cols:
        return ""

    lines = ["## Column Availability", ""]
    lines.append("Some columns are only available after specific protocol upgrades:")
    lines.append("")

    for col in available_cols:
        lines.append(f"- **{col.name}**: Block {col.available_since_block:,} ({col.available_since_date})")

    lines.append("")
    return "\n".join(lines)


def _generate_engine_section(schema: Schema) -> str:
    """Generate the ClickHouse engine configuration section."""
    ch = schema.clickhouse

    lines = ["## ClickHouse Configuration", ""]
    lines.append(f"- **Engine**: `{ch.engine}`")
    lines.append(f"- **Partition By**: `{ch.partition_by}`")
    lines.append(f"- **Order By**: `({', '.join(ch.order_by)})`")

    if ch.settings:
        lines.append("- **Settings**:")
        for key, value in ch.settings.items():
            lines.append(f"  - `{key}`: {value}")

    lines.append("")
    return "\n".join(lines)


def generate_doc(schema: Schema) -> Path:
    """
    Generate Markdown documentation from schema.

    Args:
        schema: Parsed schema object

    Returns:
        Path to generated file
    """
    # Determine output path
    output_dir = Path.cwd() / "docs" / "schema"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{schema.clickhouse.database}.md"

    # Generate content
    schema_path = f"schema/clickhouse/{schema.clickhouse.database}.yaml"

    content = _generate_header(schema, schema_path)
    content += _generate_alpha_features_table(schema)
    content += _generate_schema_table(schema)
    content += _generate_deprecated_section(schema)
    content += _generate_availability_section(schema)
    content += _generate_engine_section(schema)

    # Write file
    with open(output_file, "w") as f:
        f.write(content)

    return output_file
