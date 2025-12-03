"""
Schema module for gapless-network-data.

This module provides:
- Schema loading from YAML files
- Generated Python types (Pydantic models, TypedDict)
- DataFrame validation helpers

Usage:
    from gapless_network_data.schema import load_schema, EthereumBlock

    # Load the schema definition
    schema = load_schema()

    # Access generated types (after running: uv run gapless-network-data schema generate-types)
    from gapless_network_data.schema import EthereumBlock, EthereumBlockRow
"""

from gapless_network_data.schema.loader import load_schema

__all__ = ["load_schema"]

# Generated types are imported dynamically after generation
# from gapless_network_data.schema._generated.ethereum_mainnet import (
#     EthereumBlock,
#     EthereumBlockRow,
# )
