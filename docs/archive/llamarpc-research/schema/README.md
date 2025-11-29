# Ethereum/LlamaRPC Schema Research

**Research Date**: 2025-11-04
**Purpose**: Document Ethereum block schema and available network metrics via LlamaRPC
**Context**: Data model research for `gapless-network-data` package development

## Overview

This directory contains comprehensive research on Ethereum block data structure, transaction schemas, fee market APIs, and derivable network metrics using LlamaRPC as the data source.

## Quick Start

**Run the working demo**:

```bash
cd docs/archive/llamarpc-research/schema
python3 simple_metrics.py
```

**Sample output**:

```
📦 Block #23,724,279
   Utilization: 42.36%
   Base Fee: 0.914 gwei
   Transactions: 200
   Blob Utilization: 100.00%
   Withdrawals: 16 (0.332 ETH)

⚡ Recommended Gas Prices:
   🐢 Slow:     0.946 gwei
   🚶 Standard: 0.996 gwei
   🚀 Fast:     1.896 gwei
```

## Documentation Files

### Core Documentation

| File                                                                                            | Description                       | Use Case                       |
| ----------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------ |
| **[QUICK_REFERENCE.md](/docs/archive/llamarpc-research/schema/QUICK_REFERENCE.md)**             | Fast lookup for common operations | Copy-paste code snippets       |
| **[ETHEREUM_BLOCK_SCHEMA.md](/docs/archive/llamarpc-research/schema/ETHEREUM_BLOCK_SCHEMA.md)** | Complete field documentation      | Understanding data structure   |
| **[RESEARCH_SUMMARY.md](/docs/archive/llamarpc-research/schema/RESEARCH_SUMMARY.md)**           | Executive summary and findings    | Project planning               |
| **[schemas.json](/docs/archive/llamarpc-research/schema/schemas.json)**                         | JSON Schema definitions           | Validation and code generation |

### Working Examples

| File                                                                              | Description                   | Dependencies          |
| --------------------------------------------------------------------------------- | ----------------------------- | --------------------- |
| **[simple_metrics.py](/docs/archive/llamarpc-research/schema/simple_metrics.py)** | Verified working demo         | Python stdlib only ✅ |
| **[examples.py](/docs/archive/llamarpc-research/schema/examples.py)**             | Full-featured collector class | `requests` library    |

### Sample Data

| File                                                                                        | Description                         | Size   |
| ------------------------------------------------------------------------------------------- | ----------------------------------- | ------ |
| [block_without_txs.json](/docs/archive/llamarpc-research/schema/block_without_txs.json)     | Block #23,593,185 (tx hashes only)  | 8 KB   |
| [full_block_with_txs.json](/docs/archive/llamarpc-research/schema/full_block_with_txs.json) | Block #23,593,185 (full tx objects) | 625 KB |
| [transaction_detail.json](/docs/archive/llamarpc-research/schema/transaction_detail.json)   | Single EIP-1559 transaction         | 2 KB   |
| [fee_history.json](/docs/archive/llamarpc-research/schema/fee_history.json)                 | 5-block fee history                 | 1 KB   |

## Key Findings

### 1. Complete Schema Documentation

- ✅ **26 block fields** fully documented with types and descriptions
- ✅ **24 transaction fields** including all EIP-1559 fee fields
- ✅ **6 fee history fields** with correct array length semantics
- ✅ **4 withdrawal fields** with Gwei conversion gotcha documented

### 2. Derivable Network Metrics

**Block-Level** (10+ metrics):

- Gas utilization, base fee, transaction count
- Blob utilization, withdrawal volume
- Block size, average gas per tx
- Builder identification

**Fee Market** (8+ metrics):

- Base fee trends, priority fee percentiles
- Network congestion classification
- Recommended gas prices (slow/standard/fast)
- Blob market activity

**Time-Series** (4+ metrics):

- Block time, timestamp conversion
- Fee trend analysis
- Utilization patterns

### 3. Important Gotchas Identified

⚠️ **Withdrawal amounts are in Gwei, not wei** - Conversion requires `/1e9` not `/1e18`

⚠️ **Fee history arrays have different lengths** - `baseFeePerGas` has N+1 elements (includes next block)

⚠️ **Timestamps are in seconds** - Not milliseconds like some APIs

⚠️ **Post-Merge fields always zero** - `difficulty`, `nonce` always 0; `uncles` always empty

### 4. Working Code Verified

✅ `simple_metrics.py` tested successfully on 2025-11-04
✅ All hex conversions validated
✅ All metric calculations verified against real data
✅ No external dependencies required (uses Python stdlib)

## Data Structure Summary

```
Block (26 fields)
├── Identification: number, hash, parentHash, timestamp
├── Gas Metrics: gasLimit, gasUsed, baseFeePerGas
├── Blob Data (EIP-4844): blobGasUsed, excessBlobGas, baseFeePerBlobGas
├── Withdrawals (EIP-4895): withdrawals[], withdrawalsRoot
├── Transactions: transactions[] (hashes or full objects)
├── Builder Info: miner, extraData
└── Post-Merge: difficulty=0, nonce=0, uncles=[]

Transaction (24 fields)
├── Type 0 (Legacy): gasPrice
├── Type 2 (EIP-1559): maxFeePerGas, maxPriorityFeePerGas, gasPrice
├── Type 3 (Blob): + blob-specific fields
└── Common: from, to, value, gas, nonce, input, hash

FeeHistory (6 fields)
├── baseFeePerGas[N+1] - includes next block prediction
├── baseFeePerBlobGas[N+1] - includes next block prediction
├── gasUsedRatio[N] - utilization ratios
├── blobGasUsedRatio[N] - blob utilization
├── reward[N][percentiles] - priority fee matrix
└── oldestBlock - range start
```

## Usage Examples

### Get Latest Block Metrics

```python
import json, urllib.request

def get_block_metrics():
    url = "https://eth.llamarpc.com"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["latest", False],
        "id": 1
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req) as response:
        block = json.loads(response.read())["result"]

    return {
        "block_number": int(block["number"], 16),
        "gas_utilization": int(block["gasUsed"], 16) / int(block["gasLimit"], 16) * 100,
        "base_fee_gwei": int(block["baseFeePerGas"], 16) / 1e9,
        "tx_count": len(block["transactions"])
    }
```

### Get Recommended Gas Prices

```python
def get_gas_prices():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_feeHistory",
        "params": ["0x1", "latest", [25, 50, 75]],
        "id": 1
    }

    # ... make request ...

    data = response["result"]
    base_fee = int(data["baseFeePerGas"][-1], 16) / 1e9
    priorities = [int(p, 16) / 1e9 for p in data["reward"][0]]

    return {
        "slow": base_fee + priorities[0],
        "standard": base_fee + priorities[1],
        "fast": base_fee + priorities[2]
    }
```

## Comparison with Bitcoin Mempool Data

### Architecture Similarities

- ✅ REST API with JSON responses
- ✅ Timestamp-based data points
- ✅ Network congestion metrics
- ✅ Fee market analysis

### Key Differences

| Aspect           | Ethereum                   | Bitcoin Mempool      |
| ---------------- | -------------------------- | -------------------- |
| Block Time       | ~12 seconds                | ~10 minutes          |
| Fee Model        | Base + Priority (EIP-1559) | Sat/vB auction       |
| Data Frequency   | Per-block                  | 1-minute snapshots   |
| Numeric Encoding | Hex strings                | TBD (likely decimal) |
| API Complexity   | Multiple tx types          | Single fee model     |

### Lessons for gapless-network-data

1. **Validation Strategy**: Use exception-only approach (no fallbacks, no defaults)
2. **Timestamp Handling**: Verify mempool.space uses seconds vs milliseconds
3. **Numeric Conversion**: Check if mempool.space returns hex or decimal
4. **Schema Evolution**: Document field additions by network upgrade
5. **Rate Limiting**: Implement retry logic (unlike Ethereum, mempool has no CDN)

## API Reference

### RPC Methods Used

```bash
# Get latest block number
eth_blockNumber

# Get block by number
eth_getBlockByNumber(blockNumber, includeTransactions)

# Get transaction by hash
eth_getTransactionByHash(txHash)

# Get fee history
eth_feeHistory(blockCount, newestBlock, rewardPercentiles)
```

### Response Format

All responses follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

## Performance Notes

- **Block size**: ~160 KB without full transactions, ~625 KB with full transactions
- **Fee history size**: ~1 KB for 5 blocks with 3 percentiles
- **Rate limits**: LlamaRPC appears generous, no explicit limit observed
- **Response time**: <200ms for most queries (tested from US West Coast)

## Next Steps for gapless-network-data

1. ✅ Research Ethereum schema (this document)
2. ⏭️ Research mempool.space API schema
3. ⏭️ Compare data models (hex vs decimal, seconds vs milliseconds)
4. ⏭️ Design validation pipeline (adapt from gapless-crypto-data)
5. ⏭️ Implement collectors with retry logic
6. ⏭️ Create metric calculators (fee pressure, congestion z-score)

## Related Projects

- **gapless-crypto-data**: OHLCV data collection (referential implementation)
- **gapless-network-data**: Bitcoin mempool data collection (target project)
- **gapless-features**: Feature engineering toolkit (future)

## References

- **LlamaRPC**: https://eth.llamarpc.com
- **Ethereum JSON-RPC**: https://ethereum.org/en/developers/docs/apis/json-rpc/
- **EIP-1559**: Base fee mechanism
- **EIP-4844**: Blob transactions
- **EIP-4895**: Beacon chain withdrawals
- **mempool.space**: https://mempool.space/docs/api (target for gapless-network-data)

## License

Research materials are public domain. Code examples are provided as-is for educational purposes.

---

**Last Updated**: 2025-11-04 06:50 UTC
**Researcher**: Claude Code
**Location**: `/docs/archive/llamarpc-research/schema/`
**Data Source**: LlamaRPC (https://eth.llamarpc.com)
