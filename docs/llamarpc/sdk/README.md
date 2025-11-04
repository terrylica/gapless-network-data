# LlamaRPC SDK Research - Python Ethereum Libraries

**Research Date**: 2025-11-03
**Working Directory**: `/tmp/llamarpc-sdk-research/`

## Quick Start

**TL;DR**: Use **web3.py** - it's the industry standard and works perfectly with LlamaRPC.

```bash
uv add web3
```

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
latest_block = w3.eth.block_number
print(f"Latest block: {latest_block}")
```

---

## Files in This Directory

### Documentation

| File                   | Description                                  |
| ---------------------- | -------------------------------------------- |
| **QUICK_REFERENCE.md** | Quick reference guide with code examples     |
| **RESEARCH_REPORT.md** | Comprehensive research findings and analysis |
| **README.md**          | This file - overview and navigation          |

### Test Files

| File                        | Library         | Status            |
| --------------------------- | --------------- | ----------------- |
| **test_web3py.py**          | web3.py 7.14.0  | ✓ Working         |
| **test_httpx_raw.py**       | httpx 0.27.0    | ✓ Working         |
| **test_pythereum_async.py** | pythereum 1.2.1 | ⚠️ WebSocket only |
| **test_pythereum.py**       | pythereum 1.2.1 | ✗ Import error    |
| **test_ethjsonrpc.py**      | ethjsonrpc      | ✗ Deprecated      |

### Examples

| File                             | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| **example_web3py_simple.py**     | Simple historical block fetching                |
| **example_web3py_historical.py** | Advanced historical data collection with pandas |

---

## Research Summary

### Libraries Tested

1. **web3.py** (✓ RECOMMENDED)
   - Industry standard
   - Works with LlamaRPC HTTP endpoint
   - 39 dependencies
   - Full feature set

2. **pythereum** (⚠️ Not suitable)
   - WebSocket only
   - Doesn't support HTTP endpoints
   - LlamaRPC primarily uses HTTP

3. **ethjsonrpc** (✗ Deprecated)
   - Last updated 2016
   - Not available on PyPI
   - Do not use

4. **httpx (raw JSON-RPC)** (✓ Alternative)
   - Minimal dependencies (7 packages)
   - Full control over RPC calls
   - For advanced users only

### Key Findings

| Aspect                 | web3.py     | httpx      |
| ---------------------- | ----------- | ---------- |
| LlamaRPC Compatibility | ✓ Excellent | ✓ Good     |
| Dependencies           | 39 packages | 7 packages |
| Ease of Use            | ✓ Easy      | Manual     |
| Type Safety            | ✓ Yes       | Manual     |
| Documentation          | ✓ Excellent | N/A        |
| Community Support      | ✓ Large     | N/A        |

---

## Running the Tests

### Test web3.py

```bash
cd /tmp/llamarpc-sdk-research
uv run test_web3py.py
```

Expected output:

```
✓ Connection successful!
✓ Latest block: 23724259
✓ Chain ID: 1
✓ All tests passed
```

### Test httpx (raw JSON-RPC)

```bash
uv run test_httpx_raw.py
```

Expected output:

```
✓ Latest block: 23724272
✓ Chain ID: 1
✓ Historical block fetching works
⚠️ Batch requests hit rate limit
```

### Run Examples

```bash
# Simple example
uv run example_web3py_simple.py

# Historical data collection
uv run example_web3py_historical.py
```

---

## Recommendation

**For gapless-network-data package: Use web3.py**

### pyproject.toml

```toml
[project]
dependencies = [
    "web3>=7.0.0",
]
```

### Rationale

1. Industry standard for Ethereum development
2. Excellent documentation and community support
3. Works seamlessly with LlamaRPC HTTP endpoint
4. Built-in retry logic and error handling
5. Type hints for better IDE support
6. Actively maintained by Ethereum Foundation
7. Aligns with gapless-crypto-data philosophy (use established libraries)

---

## Common Use Cases

### 1. Get Latest Block

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
latest_block = w3.eth.block_number
```

### 2. Fetch Historical Block

```python
block = w3.eth.get_block(15000000)
print(f"Timestamp: {block['timestamp']}")
print(f"Transactions: {len(block['transactions'])}")
```

### 3. Fetch Block Range for Analysis

```python
from datetime import datetime
import pandas as pd

blocks_data = []
for block_num in range(15000000, 15000100):
    block = w3.eth.get_block(block_num)
    blocks_data.append({
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'tx_count': len(block['transactions']),
        'gas_used': block['gasUsed'],
    })

df = pd.DataFrame(blocks_data)
df = df.set_index('timestamp')
```

---

## LlamaRPC Details

### Endpoint

```
HTTP: https://eth.llamarpc.com
WebSocket: wss://eth.llamarpc.com (limited support)
```

### Rate Limits

- Single requests: No issues
- Batch requests: Limit to 3-5 concurrent
- Recommended delay: 100-200ms between requests

### Supported RPC Methods

All standard `eth_*` methods:

- `eth_blockNumber`
- `eth_getBlockByNumber`
- `eth_getTransactionByHash`
- `eth_call`
- `eth_chainId`
- `web3_clientVersion`

---

## Next Steps

1. **Read QUICK_REFERENCE.md** for code examples
2. **Read RESEARCH_REPORT.md** for detailed analysis
3. **Run test files** to verify LlamaRPC connectivity
4. **Adapt examples** for your specific use case

---

## Resources

- web3.py Documentation: https://web3py.readthedocs.io/
- Ethereum JSON-RPC Spec: https://ethereum.org/en/developers/docs/apis/json-rpc/
- LlamaRPC: https://llamarpc.com/
- gapless-crypto-data: /Users/terryli/eon/gapless-crypto-data/

---

## Contact

Research conducted by: Claude Code CLI
Date: 2025-11-03
Python Environment: uv 0.7.13, Python 3.13.6
