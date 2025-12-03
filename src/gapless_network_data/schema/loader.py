"""
Schema loader for gapless-network-data.

Loads and parses YAML schema files that serve as the single source of truth
for all generated types, DDL, and documentation.

Usage:
    from gapless_network_data.schema.loader import load_schema

    schema = load_schema()  # Load ethereum_mainnet by default
    print(schema.title)
    print(schema.properties)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _find_schema_dir() -> Path:
    """
    Find the schema directory relative to package or project root.

    Searches in order:
    1. Relative to this file (when installed as package)
    2. Project root (when running from source)
    """
    # Option 1: Installed package - schema is at package_root/../../../schema
    package_dir = Path(__file__).parent.parent.parent.parent
    schema_dir = package_dir / "schema" / "clickhouse"
    if schema_dir.exists():
        return schema_dir

    # Option 2: Project root from CWD
    cwd = Path.cwd()
    schema_dir = cwd / "schema" / "clickhouse"
    if schema_dir.exists():
        return schema_dir

    # Option 3: Environment variable override
    env_path = os.environ.get("GAPLESS_SCHEMA_DIR")
    if env_path:
        schema_dir = Path(env_path)
        if schema_dir.exists():
            return schema_dir

    msg = (
        "Could not find schema directory. "
        "Ensure schema/clickhouse/ exists in project root or set GAPLESS_SCHEMA_DIR."
    )
    raise FileNotFoundError(msg)


@dataclass
class ClickHouseConfig:
    """ClickHouse-specific configuration from x-clickhouse extension."""

    database: str
    table: str
    engine: str
    order_by: list[str]
    partition_by: str
    settings: dict[str, Any]


@dataclass
class ColumnConfig:
    """Configuration for a single column."""

    name: str
    json_type: str | list[str]
    description: str
    clickhouse_type: str
    clickhouse_not_null: bool
    pandas_dtype: str
    alpha_rank: int | None
    alpha_importance: str | None
    deprecated_since: str | None
    deprecated_reason: str | None
    available_since_block: int | None
    available_since_date: str | None
    minimum: int | None


@dataclass
class Schema:
    """
    Parsed schema representing a ClickHouse table.

    Attributes:
        title: Human-readable title
        description: Detailed description for documentation
        clickhouse: ClickHouse-specific configuration
        columns: List of column configurations
        required_columns: List of required column names
        raw: Original parsed YAML dict for custom access
    """

    title: str
    description: str
    clickhouse: ClickHouseConfig
    columns: list[ColumnConfig]
    required_columns: list[str]
    raw: dict[str, Any]

    @property
    def database(self) -> str:
        """Get the database name."""
        return self.clickhouse.database

    @property
    def table(self) -> str:
        """Get the table name."""
        return self.clickhouse.table

    @property
    def full_table_name(self) -> str:
        """Get fully qualified table name (database.table)."""
        return f"{self.database}.{self.table}"


def _parse_column(name: str, props: dict[str, Any]) -> ColumnConfig:
    """Parse a single column definition from YAML."""
    x_ch = props.get("x-clickhouse", {})
    x_pandas = props.get("x-pandas", {})
    x_alpha = props.get("x-alpha-feature", {})
    x_deprecated = props.get("x-deprecated", {})
    x_available = props.get("x-available-since", {})

    return ColumnConfig(
        name=name,
        json_type=props.get("type", "string"),
        description=props.get("description", ""),
        clickhouse_type=x_ch.get("type", "String"),
        clickhouse_not_null=x_ch.get("not_null", False),
        pandas_dtype=x_pandas.get("dtype", "object"),
        alpha_rank=x_alpha.get("rank"),
        alpha_importance=x_alpha.get("importance"),
        deprecated_since=x_deprecated.get("since"),
        deprecated_reason=x_deprecated.get("reason"),
        available_since_block=x_available.get("block"),
        available_since_date=x_available.get("date"),
        minimum=props.get("minimum"),
    )


def _parse_clickhouse_config(x_clickhouse: dict[str, Any]) -> ClickHouseConfig:
    """Parse ClickHouse configuration from x-clickhouse extension."""
    return ClickHouseConfig(
        database=x_clickhouse.get("database", "default"),
        table=x_clickhouse.get("table", "unknown"),
        engine=x_clickhouse.get("engine", "MergeTree()"),
        order_by=x_clickhouse.get("order_by", []),
        partition_by=x_clickhouse.get("partition_by", ""),
        settings=x_clickhouse.get("settings", {}),
    )


def load_schema(name: str = "ethereum_mainnet") -> Schema:
    """
    Load a schema from YAML file.

    Args:
        name: Schema name (without .yaml extension). Default: ethereum_mainnet

    Returns:
        Parsed Schema object with typed access to all fields

    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema file is invalid
    """
    schema_dir = _find_schema_dir()
    schema_path = schema_dir / f"{name}.yaml"

    if not schema_path.exists():
        msg = f"Schema file not found: {schema_path}"
        raise FileNotFoundError(msg)

    with open(schema_path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        msg = f"Empty schema file: {schema_path}"
        raise ValueError(msg)

    # Parse columns from properties
    properties = raw.get("properties", {})
    columns = [_parse_column(name, props) for name, props in properties.items()]

    # Sort columns by order in YAML (preserve definition order)
    # Note: Python 3.7+ dicts maintain insertion order

    return Schema(
        title=raw.get("title", ""),
        description=raw.get("description", ""),
        clickhouse=_parse_clickhouse_config(raw.get("x-clickhouse", {})),
        columns=columns,
        required_columns=raw.get("required", []),
        raw=raw,
    )


def get_schema_path(name: str = "ethereum_mainnet") -> Path:
    """
    Get the path to a schema file.

    Args:
        name: Schema name (without .yaml extension)

    Returns:
        Path to the schema file
    """
    schema_dir = _find_schema_dir()
    return schema_dir / f"{name}.yaml"
