"""
CLI commands for schema management.

Commands:
    schema generate-types  - Generate Python types from YAML schema
    schema generate-ddl    - Generate ClickHouse DDL from YAML schema
    schema validate        - Validate live ClickHouse schema matches YAML
    schema apply           - Apply generated DDL to ClickHouse
    schema doc             - Generate Markdown documentation
"""

from __future__ import annotations

import sys
from pathlib import Path


def _print_usage() -> None:
    """Print schema command usage."""
    print("Usage: gapless-network-data schema <subcommand> [options]")
    print()
    print("Schema management commands:")
    print("  generate-types  Generate Python types from YAML schema")
    print("  generate-ddl    Generate ClickHouse DDL from YAML schema")
    print("  validate        Validate live ClickHouse schema matches YAML")
    print("  apply           Apply generated DDL to ClickHouse")
    print("  doc             Generate Markdown documentation")
    print()
    print("Options:")
    print("  --schema NAME   Schema name (default: ethereum_mainnet)")


def _cmd_generate_types(schema_name: str) -> int:
    """Generate Python types from YAML schema."""
    from gapless_network_data.cli.schema.generators.python_types import generate_types
    from gapless_network_data.schema.loader import load_schema

    try:
        schema = load_schema(schema_name)
        output_path = generate_types(schema)
        print(f"Generated Python types: {output_path}")
        return 0
    except Exception as e:
        print(f"Error generating types: {e}", file=sys.stderr)
        return 1


def _cmd_generate_ddl(schema_name: str) -> int:
    """Generate ClickHouse DDL from YAML schema."""
    from gapless_network_data.cli.schema.generators.clickhouse_ddl import generate_ddl
    from gapless_network_data.schema.loader import load_schema

    try:
        schema = load_schema(schema_name)
        output_path = generate_ddl(schema)
        print(f"Generated DDL: {output_path}")
        return 0
    except Exception as e:
        print(f"Error generating DDL: {e}", file=sys.stderr)
        return 1


def _cmd_validate(schema_name: str) -> int:
    """Validate live ClickHouse schema matches YAML."""
    from gapless_network_data.cli.schema.introspector import validate_schema
    from gapless_network_data.schema.loader import load_schema

    try:
        schema = load_schema(schema_name)
        is_valid, diff = validate_schema(schema)

        if is_valid:
            print(f"Schema {schema.full_table_name} is valid")
            return 0
        else:
            print(f"Schema {schema.full_table_name} has differences:")
            print(diff)
            return 1
    except Exception as e:
        print(f"Error validating schema: {e}", file=sys.stderr)
        return 1


def _cmd_apply(schema_name: str, execute: bool = False) -> int:
    """Apply generated DDL to ClickHouse."""
    from gapless_network_data.cli.schema.generators.clickhouse_ddl import generate_ddl
    from gapless_network_data.cli.schema.introspector import apply_ddl
    from gapless_network_data.schema.loader import load_schema

    try:
        schema = load_schema(schema_name)

        # Generate DDL first
        ddl_path = generate_ddl(schema)

        if execute:
            apply_ddl(ddl_path)
            print(f"Applied DDL to ClickHouse: {schema.full_table_name}")
        else:
            print("Dry run - DDL generated but not applied:")
            with open(ddl_path) as f:
                print(f.read())
            print()
            print("Use --execute to apply the DDL")

        return 0
    except Exception as e:
        print(f"Error applying DDL: {e}", file=sys.stderr)
        return 1


def _cmd_doc(schema_name: str) -> int:
    """Generate Markdown documentation."""
    from gapless_network_data.cli.schema.generators.markdown_doc import generate_doc
    from gapless_network_data.schema.loader import load_schema

    try:
        schema = load_schema(schema_name)
        output_path = generate_doc(schema)
        print(f"Generated documentation: {output_path}")
        return 0
    except Exception as e:
        print(f"Error generating documentation: {e}", file=sys.stderr)
        return 1


def schema_command(args: list[str]) -> int:
    """
    Handle schema subcommands.

    Args:
        args: Command-line arguments after 'schema'

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if not args:
        _print_usage()
        return 1

    subcommand = args[0]
    schema_name = "ethereum_mainnet"
    execute = False

    # Parse options
    i = 1
    while i < len(args):
        if args[i] == "--schema" and i + 1 < len(args):
            schema_name = args[i + 1]
            i += 2
        elif args[i] == "--execute":
            execute = True
            i += 1
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            return 1

    # Dispatch to subcommand
    if subcommand == "generate-types":
        return _cmd_generate_types(schema_name)
    elif subcommand == "generate-ddl":
        return _cmd_generate_ddl(schema_name)
    elif subcommand == "validate":
        return _cmd_validate(schema_name)
    elif subcommand == "apply":
        return _cmd_apply(schema_name, execute)
    elif subcommand == "doc":
        return _cmd_doc(schema_name)
    else:
        print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
        _print_usage()
        return 1
