---
version: "1.1.0"
last_updated: "2025-11-03"
supersedes: ["1.0.0"]
---

# Ethereum RPC Quick Reference

## RPC Endpoints

### Get Latest Block

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest",false],"id":1}'
```

### Get Block by Number (with transactions)

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x16a00e1",true],"id":1}'
```

### Get Transaction by Hash

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":["0x764731..."],"id":1}'
```

### Get Fee History

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_feeHistory","params":["0x14","latest",[25,50,75]],"id":1}'
```

## Essential Field Reference

### Block Fields (Most Important)

| Field           | Type  | Conversion                      | Description              |
| --------------- | ----- | ------------------------------- | ------------------------ |
| `number`        | hex   | `int(v, 16)`                    | Block number             |
| `timestamp`     | hex   | `int(v, 16)`                    | Unix timestamp (seconds) |
| `gasLimit`      | hex   | `int(v, 16)`                    | Max gas allowed          |
| `gasUsed`       | hex   | `int(v, 16)`                    | Actual gas used          |
| `baseFeePerGas` | hex   | `int(v, 16) / 1e9`              | Base fee in gwei         |
| `blobGasUsed`   | hex   | `int(v, 16)`                    | Blob gas used (EIP-4844) |
| `transactions`  | array | `len(v)`                        | Tx hashes or objects     |
| `withdrawals`   | array | `len(v)`                        | Validator withdrawals    |
| `miner`         | hex   | -                               | Builder address          |
| `extraData`     | hex   | `bytes.fromhex(v[2:]).decode()` | Builder tag              |

### Transaction Fields (EIP-1559)

| Field                  | Type | Conversion          | Description            |
| ---------------------- | ---- | ------------------- | ---------------------- |
| `hash`                 | hex  | -                   | Tx hash                |
| `from`                 | hex  | -                   | Sender address         |
| `to`                   | hex  | -                   | Recipient address      |
| `value`                | hex  | `int(v, 16) / 1e18` | ETH value              |
| `gas`                  | hex  | `int(v, 16)`        | Gas limit              |
| `gasPrice`             | hex  | `int(v, 16) / 1e9`  | Effective price (gwei) |
| `maxFeePerGas`         | hex  | `int(v, 16) / 1e9`  | Max total fee (gwei)   |
| `maxPriorityFeePerGas` | hex  | `int(v, 16) / 1e9`  | Max tip (gwei)         |
| `type`                 | hex  | `int(v, 16)`        | 0=legacy, 2=EIP-1559   |

### Fee History Fields

| Field               | Type              | Length | Description              |
| ------------------- | ----------------- | ------ | ------------------------ |
| `baseFeePerGas`     | array[hex]        | N+1    | Base fees + next block   |
| `baseFeePerBlobGas` | array[hex]        | N+1    | Blob fees + next block   |
| `gasUsedRatio`      | array[float]      | N      | Gas utilization ratios   |
| `blobGasUsedRatio`  | array[float]      | N      | Blob utilization ratios  |
| `reward`            | array[array[hex]] | N      | Priority fee percentiles |

## Common Conversions

### Hex to Decimal

```python
# Block number
block_num = int("0x16a00e1", 16)  # 23,724,257

# Gas values
gas = int("0x13892e4", 16)  # 20,484,836
```

### Wei/Gwei/ETH

```python
# Wei to Gwei (for gas prices)
gwei = int("0x3b35c053", 16) / 1e9  # 0.995 gwei

# Wei to ETH (for transaction values)
eth = int("0x10fa186", 16) / 1e18  # 0.000017... ETH

# Gwei to ETH (for withdrawals - special case!)
withdrawal_eth = int("0x10fa186", 16) / 1e9  # 0.017... ETH
```

### Timestamp

```python
from datetime import datetime, timezone

timestamp = int("0x6909a133", 16)
dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
# 2025-11-04 06:50:35 UTC
```

### Builder Tag

```python
extra_hex = block["extraData"][2:]  # Remove 0x
tag = bytes.fromhex(extra_hex).decode('utf-8', errors='ignore')
# "Titan (titanbuilder.xyz)"
```

## Quick Metrics

### Gas Utilization

```python
utilization = int(block["gasUsed"], 16) / int(block["gasLimit"], 16)
# 0.4236 = 42.36%
```

### Blob Utilization

```python
blob_gas = int(block["blobGasUsed"], 16)
max_blob_gas = 9 * 131072  # 1,179,648 (EIP-7691 increased from 6 blobs)
utilization = blob_gas / max_blob_gas
# 1.0 = 100%
```

### Average Gas per Transaction

```python
gas_used = int(block["gasUsed"], 16)
tx_count = len(block["transactions"])
avg_gas = gas_used / tx_count
# 95,208 gas per tx
```

### Base Fee Trend

```python
fees = [int(f, 16) / 1e9 for f in fee_history["baseFeePerGas"]]
change_pct = (fees[-1] - fees[0]) / fees[0] * 100
# -7.81% = decreasing
```

### Congestion Level

```python
avg_ratio = sum(fee_history["gasUsedRatio"]) / len(fee_history["gasUsedRatio"])

if avg_ratio < 0.5:
    level = "LOW"
elif avg_ratio < 0.8:
    level = "MODERATE"
else:
    level = "HIGH"
```

### Recommended Gas Price

```python
base_fee = int(fee_history["baseFeePerGas"][-1], 16)  # Next block
priority = int(fee_history["reward"][-1][1], 16)      # 50th percentile
recommended = (base_fee + priority) / 1e9  # Gwei
# 0.996 gwei
```

## Gotchas

### 1. Withdrawal Amounts Are in Gwei (Not Wei!)

```python
# ❌ WRONG
eth = int(withdrawal["amount"], 16) / 1e18  # Off by 1e9!

# ✅ CORRECT
eth = int(withdrawal["amount"], 16) / 1e9
```

### 2. Fee History Array Lengths

```python
# baseFeePerGas has N+1 elements (includes next block prediction)
len(fee_history["baseFeePerGas"]) == block_count + 1  # True

# Other arrays have N elements
len(fee_history["gasUsedRatio"]) == block_count  # True
```

### 3. Timestamp in Seconds (Not Milliseconds)

```python
# ❌ WRONG
dt = datetime.fromtimestamp(timestamp / 1000)  # Treats as milliseconds

# ✅ CORRECT
dt = datetime.fromtimestamp(timestamp)  # Already in seconds
```

### 4. Transaction Type Determines Fields

```python
# Type 2 (EIP-1559) has:
tx["maxFeePerGas"]
tx["maxPriorityFeePerGas"]

# Type 0 (legacy) has:
tx["gasPrice"]  # No max fees
```

### 5. Post-Merge Fields Always Zero

```python
block["difficulty"] == "0x0"  # Always
block["nonce"] == "0x0000000000000000"  # Always
block["uncles"] == []  # Always empty
```

## Python One-Liners

```python
import json, urllib.request as req, datetime as dt

# Get latest block number
bn = lambda: int(json.loads(req.urlopen(req.Request("https://eth.llamarpc.com", json.dumps({"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}).encode(), {"Content-Type":"application/json"})).read())["result"], 16)

# Get block
blk = lambda n="latest": json.loads(req.urlopen(req.Request("https://eth.llamarpc.com", json.dumps({"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":[n,False],"id":1}).encode(), {"Content-Type":"application/json"})).read())["result"]

# Gas utilization
util = lambda b: int(b["gasUsed"],16)/int(b["gasLimit"],16)*100

# Example usage
block = blk()
print(f"Block {int(block['number'],16)}: {util(block):.2f}% full")
```

## Network Upgrade Timeline

| Upgrade   | Date     | Key Fields Added                                        |
| --------- | -------- | ------------------------------------------------------- |
| London    | Aug 2021 | `baseFeePerGas`                                         |
| The Merge | Sep 2022 | `difficulty`→0, `nonce`→0                               |
| Shanghai  | Apr 2023 | `withdrawals`, `withdrawalsRoot`                        |
| Cancun    | Mar 2024 | `blobGasUsed`, `excessBlobGas`, `parentBeaconBlockRoot` |
| Pectra    | May 2025 | Blob increase: target 3→6, max 6→9 (EIP-7691)           |

## Transaction Type Distribution (Observed)

From sample block #23,724,279:

- Type 2 (EIP-1559): ~90% of transactions
- Type 0 (Legacy): ~4% of transactions
- Type 3 (Blob): Rare, when present

## Blob Economics

- **Max blobs per block**: 9 (increased from 6 via EIP-7691, Pectra upgrade May 2025)
- **Target blobs per block**: 6 (increased from 3)
- **Gas per blob**: 131,072
- **Max blob gas**: 1,179,648 (9 × 131,072)
- **Typical blob size**: ~128 KB
- **Use case**: L2 rollup data
- **Observed utilization**: 0% to 100% (highly variable)

## Rate Limits

**LlamaRPC**: No explicit rate limit observed, but best practice:

- Use batch requests when possible
- Cache responses appropriately
- Implement exponential backoff on errors

## Error Codes

| Code   | Meaning             |
| ------ | ------------------- |
| 1015   | Rate limit exceeded |
| -32602 | Invalid params      |
| -32700 | Parse error         |

## Further Reading

- Complete schema: `/tmp/llamarpc-schema-research/ETHEREUM_BLOCK_SCHEMA.md `
- JSON schemas: `/tmp/llamarpc-schema-research/schemas.json `
- Working examples: `/tmp/llamarpc-schema-research/simple_metrics.py `
- Research summary: `/tmp/llamarpc-schema-research/RESEARCH_SUMMARY.md `
