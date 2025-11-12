# Quick Reference: Python Ethereum RPC Libraries

## TL;DR

**Use web3.py** - It's the industry standard and works perfectly with LlamaRPC.

```bash
uv add web3
```

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
latest_block = w3.eth.block_number
block = w3.eth.get_block(15000000)
```

---

## Comparison at a Glance

| Library         | Status              | Works with LlamaRPC HTTP? | Recommendation      |
| --------------- | ------------------- | ------------------------- | ------------------- |
| **web3.py**     | ✓ Active            | ✓ Yes                     | **USE THIS**        |
| **pythereum**   | ✓ Active            | ✗ No (WebSocket only)     | Skip                |
| **ethjsonrpc**  | ✗ Deprecated (2016) | N/A                       | Never use           |
| **httpx (raw)** | ✓ Active            | ✓ Yes                     | Advanced users only |

---

## Installation

### web3.py (Recommended)

```bash
# Using uv
uv add web3

# Using pip
pip install web3

# PEP 723 inline script
# /// script
# dependencies = ["web3>=7.0.0"]
# ///
```

### httpx (Minimal alternative)

```bash
# Using uv
uv add httpx

# Using pip
pip install httpx
```

---

## Common RPC Operations

### Get Latest Block Number

**web3.py**:

```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
latest = w3.eth.block_number
```

**httpx**:

```python
import httpx
response = httpx.post('https://eth.llamarpc.com', json={
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
})
latest_hex = response.json()["result"]
latest = int(latest_hex, 16)
```

### Get Block by Number

**web3.py**:

```python
block = w3.eth.get_block(15000000)
# Returns dict with proper types (int, bytes, etc.)
```

**httpx**:

```python
response = httpx.post('https://eth.llamarpc.com', json={
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": [hex(15000000), False],
    "id": 1
})
block = response.json()["result"]
# All values are hex strings - must convert manually
```

### Get Block with Full Transactions

**web3.py**:

```python
block = w3.eth.get_block(15000000, full_transactions=True)
for tx in block['transactions']:
    print(f"Hash: {tx['hash'].hex()}")
    print(f"Value: {Web3.from_wei(tx['value'], 'ether')} ETH")
```

**httpx**:

```python
response = httpx.post('https://eth.llamarpc.com', json={
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": [hex(15000000), True],
    "id": 1
})
block = response.json()["result"]
for tx in block['transactions']:
    print(f"Hash: {tx['hash']}")
    value_eth = int(tx['value'], 16) / 1e18
    print(f"Value: {value_eth} ETH")
```

### Get Chain ID

**web3.py**:

```python
chain_id = w3.eth.chain_id  # Returns 1 for mainnet
```

**httpx**:

```python
response = httpx.post('https://eth.llamarpc.com', json={
    "jsonrpc": "2.0",
    "method": "eth_chainId",
    "params": [],
    "id": 1
})
chain_id = int(response.json()["result"], 16)
```

---

## When to Use Each Library

### Use web3.py when:

- Building production applications
- Need contract interaction
- Want established patterns
- Prefer type safety
- Need ENS resolution
- Building DeFi/Web3 apps
- **Recommended for gapless-network-data**

### Use httpx when:

- Minimizing dependencies is critical
- Only need basic RPC calls
- Building custom abstraction layer
- Learning JSON-RPC protocol
- Deploying to resource-constrained environments

### Avoid pythereum when:

- RPC provider doesn't support WebSocket
- Need HTTP endpoint support
- **LlamaRPC works better with HTTP**

### Never use ethjsonrpc:

- Package is deprecated (2016)
- Not compatible with modern Python
- web3.py is the official replacement

---

## Common Patterns for Historical Data Collection

### Pattern 1: Fetch Block Range

```python
from web3 import Web3
from datetime import datetime

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

start_block = 15000000
end_block = 15000100

for block_num in range(start_block, end_block):
    block = w3.eth.get_block(block_num)
    timestamp = datetime.fromtimestamp(block['timestamp'])
    tx_count = len(block['transactions'])
    gas_utilization = (block['gasUsed'] / block['gasLimit']) * 100

    print(f"Block {block_num}: {timestamp} | {tx_count} txs | {gas_utilization:.1f}% gas")
```

### Pattern 2: Collect to DataFrame

```python
from web3 import Web3
import pandas as pd
from datetime import datetime

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

blocks_data = []
for block_num in range(15000000, 15000100):
    block = w3.eth.get_block(block_num)
    blocks_data.append({
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'tx_count': len(block['transactions']),
        'gas_used': block['gasUsed'],
        'gas_limit': block['gasLimit'],
        'base_fee_per_gas': block.get('baseFeePerGas', 0),
    })

df = pd.DataFrame(blocks_data)
df = df.set_index('timestamp')  # DatetimeIndex for time series
df.to_parquet('ethereum_blocks.parquet')
```

### Pattern 3: Rate Limit Handling

```python
from web3 import Web3
import time

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

for block_num in range(15000000, 15000100):
    try:
        block = w3.eth.get_block(block_num)
        # Process block...
    except Exception as e:
        if '429' in str(e):  # Rate limit
            print("Rate limited, waiting 5 seconds...")
            time.sleep(5)
            continue
        raise

    # Add small delay to avoid rate limits
    time.sleep(0.1)  # 100ms between requests
```

---

## LlamaRPC Specific Notes

### Endpoint

```python
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"
```

### Rate Limits

- Single requests: No issues
- Batch requests: Limit to 3-5 per batch
- Add 100-200ms delay between requests

### Supported Methods

All standard `eth_*` methods work:

- `eth_blockNumber`
- `eth_getBlockByNumber`
- `eth_getTransactionByHash`
- `eth_call`
- `eth_chainId`
- `web3_clientVersion`

### Unsupported Methods

- `debug_*` namespace
- `trace_*` namespace
- `admin_*` namespace

---

## Dependencies Comparison

### web3.py

```
Total: 39 packages
Core: web3, eth-abi, eth-account, eth-utils, requests, aiohttp
Size: ~15 MB
```

### httpx

```
Total: 7 packages
Core: httpx, certifi, idna
Size: ~2 MB
```

---

## Test Files

All test files available in: `/tmp/llamarpc-sdk-research/`

1. `test_web3py.py` - Comprehensive web3.py tests
2. `test_httpx_raw.py` - Raw JSON-RPC with httpx
3. `example_web3py_simple.py` - Simple historical data fetching
4. `RESEARCH_REPORT.md` - Full research findings

---

## Final Recommendation

**For 99% of use cases: Use web3.py**

```python
# pyproject.toml
[project]
dependencies = [
    "web3>=7.0.0",
]
```

Only use httpx if you have a specific reason (deployment size, learning, etc.).

---

## Resources

- web3.py docs: https://web3py.readthedocs.io/
- Ethereum JSON-RPC: https://ethereum.org/en/developers/docs/apis/json-rpc/
- LlamaRPC: https://llamarpc.com/
- Full report: `/tmp/llamarpc-sdk-research/RESEARCH_REPORT.md`
