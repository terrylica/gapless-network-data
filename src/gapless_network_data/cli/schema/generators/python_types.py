"""
Generate Python types (Pydantic models, TypedDict) from YAML schema.

Usage:
    uv run gapless-network-data schema generate-types
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gapless_network_data.schema.loader import ColumnConfig, Schema


def _json_type_to_python(json_type: str | list[str], pandas_dtype: str) -> str:
    """
    Convert JSON Schema type to Python type annotation.

    Args:
        json_type: JSON Schema type (string or list for nullable)
        pandas_dtype: pandas dtype hint for better type inference

    Returns:
        Python type annotation string
    """
    # Handle nullable types (e.g., ["integer", "null"])
    is_nullable = isinstance(json_type, list) and "null" in json_type
    base_type = json_type[0] if isinstance(json_type, list) else json_type

    # Map JSON Schema types to Python types
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict[str, Any]",
        "array": "list[Any]",
    }

    # Special case for datetime
    if pandas_dtype.startswith("datetime64"):
        python_type = "datetime"
    elif pandas_dtype == "object":
        # Usually means arbitrary precision integer (UInt256)
        python_type = "int"
    else:
        python_type = type_map.get(base_type, "Any")

    if is_nullable:
        return f"{python_type} | None"
    return python_type


def _generate_header(schema_path: str) -> str:
    """Generate the file header with imports."""
    return f'''# AUTO-GENERATED from {schema_path}
# DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-types
# Generated at: {datetime.now().isoformat()}

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, Field

'''


def _generate_typeddict(schema: Schema) -> str:
    """Generate TypedDict class for DataFrame rows."""
    lines = []
    class_name = _table_to_class_name(schema.clickhouse.table) + "Row"

    lines.append(f'class {class_name}(TypedDict):')
    lines.append(f'    """{schema.title} - typed dict for DataFrame rows."""')
    lines.append('')

    for col in schema.columns:
        python_type = _json_type_to_python(col.json_type, col.pandas_dtype)
        lines.append(f'    {col.name}: {python_type}')

    lines.append('')
    return '\n'.join(lines)


def _generate_pydantic_model(schema: Schema) -> str:
    """Generate Pydantic model for validation."""
    lines = []
    class_name = _table_to_class_name(schema.clickhouse.table)

    lines.append(f'class {class_name}(BaseModel):')
    lines.append(f'    """')
    lines.append(f'    {schema.title} - Pydantic model for validation.')
    lines.append('')
    if schema.description:
        for line in schema.description.strip().split('\n'):
            lines.append(f'    {line}')
    lines.append(f'    """')
    lines.append('')

    for col in schema.columns:
        python_type = _json_type_to_python(col.json_type, col.pandas_dtype)

        # Build Field() arguments
        field_args = []

        # Add ge=0 for minimum: 0
        if col.minimum is not None and col.minimum == 0:
            field_args.append('ge=0')

        # Add description
        if col.description:
            # Escape quotes in description
            desc = col.description.replace('"', '\\"')
            field_args.append(f'description="{desc}"')

        if field_args:
            field_str = f'Field({", ".join(field_args)})'
            lines.append(f'    {col.name}: {python_type} = {field_str}')
        else:
            lines.append(f'    {col.name}: {python_type}')

    lines.append('')
    return '\n'.join(lines)


def _table_to_class_name(table_name: str) -> str:
    """Convert table name to PascalCase class name."""
    # blocks -> Block, ethereum_blocks -> EthereumBlocks
    parts = table_name.split('_')
    # Make singular (remove trailing 's' if present)
    if parts[-1].endswith('s') and len(parts[-1]) > 1:
        parts[-1] = parts[-1][:-1]
    return ''.join(word.capitalize() for word in parts)


def generate_types(schema: Schema) -> Path:
    """
    Generate Python types from schema.

    Args:
        schema: Parsed schema object

    Returns:
        Path to generated file
    """
    # Determine output path
    output_dir = Path(__file__).parent.parent.parent.parent / "schema" / "_generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{schema.clickhouse.table}.py"

    # Generate content
    schema_path = f"schema/clickhouse/{schema.clickhouse.table.replace('blocks', 'ethereum_mainnet')}.yaml"
    content = _generate_header(schema_path)
    content += _generate_typeddict(schema)
    content += '\n'
    content += _generate_pydantic_model(schema)

    # Write file
    with open(output_file, 'w') as f:
        f.write(content)

    return output_file
