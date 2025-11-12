# Ethereum Block Schema Documentation

## Data Source

- **RPC Endpoint**: https://eth.llamarpc.com
- **Method**: `eth_getBlockByNumber`
- **Parameters**: `[blockNumber, includeTransactions]`
  - `blockNumber`: hex string (e.g., "0x16a00e1") or "latest"
  - `includeTransactions`: boolean (false = tx hashes only, true = full tx objects)

## Block Schema

### Core Block Fields

| Field                   | Type       | Description                                          | Example Value                  |
| ----------------------- | ---------- | ---------------------------------------------------- | ------------------------------ |
| `baseFeePerGas`         | hex string | Base fee per gas unit (EIP-1559, post-London)        | "0x3b35c053" (995,074,643 wei) |
| `blobGasUsed`           | hex string | Total blob gas used in block (EIP-4844, post-Cancun) | "0xe0000" (917,504)            |
| `difficulty`            | hex string | Mining difficulty (0 after The Merge)                | "0x0"                          |
| `excessBlobGas`         | hex string | Excess blob gas from previous blocks (EIP-4844)      | "0x4c0000" (4,980,736)         |
| `extraData`             | hex string | Arbitrary data included by miner/builder             | "0x4275696c646572..."          |
| `gasLimit`              | hex string | Maximum gas allowed in this block                    | "0x2aea540" (45,000,000)       |
| `gasUsed`               | hex string | Actual gas consumed by all transactions              | "0x13892e4" (20,456,676)       |
| `hash`                  | hex string | Block hash (32 bytes)                                | "0x803ad3ed..."                |
| `logsBloom`             | hex string | Bloom filter for logs (256 bytes)                    | "0x0163a1ec..."                |
| `miner`                 | hex string | Address that produced this block (builder)           | "0x6adb3bab..."                |
| `mixHash`               | hex string | PoS mix hash (post-Merge)                            | "0x9009692b..."                |
| `nonce`                 | hex string | Block nonce (always 0x0 post-Merge)                  | "0x0000000000000000"           |
| `number`                | hex string | Block number (height)                                | "0x16a00e1" (23,593,185)       |
| `parentBeaconBlockRoot` | hex string | Root of parent beacon chain block (EIP-4788)         | "0x01357a66..."                |
| `parentHash`            | hex string | Hash of previous block                               | "0xca262737..."                |
| `receiptsRoot`          | hex string | Root hash of receipts trie                           | "0x10fedd23..."                |
| `requestsHash`          | hex string | Hash of withdrawal requests (EIP-7685)               | "0xe3b0c442..."                |
| `sha3Uncles`            | hex string | Hash of uncles list (always empty post-Merge)        | "0x1dcc4de8..."                |
| `size`                  | hex string | Block size in bytes                                  | "0x36a4e" (223,822 bytes)      |
| `stateRoot`             | hex string | Root hash of state trie                              | "0xec5d06eb..."                |
| `timestamp`             | hex string | Unix timestamp (seconds)                             | "0x6909a133" (1762017587)      |
| `transactions`          | array      | Transaction hashes or full tx objects                | ["0x764731...", ...]           |
| `transactionsRoot`      | hex string | Root hash of transactions trie                       | "0x9030996c..."                |
| `uncles`                | array      | Uncle block hashes (empty post-Merge)                | []                             |
| `withdrawals`           | array      | Validator withdrawal objects (post-Shanghai)         | [{...}, {...}]                 |
| `withdrawalsRoot`       | hex string | Root hash of withdrawals trie                        | "0xccc5b542..."                |

### Withdrawal Object Schema

Each withdrawal in the `withdrawals` array contains:

| Field            | Type       | Description                     | Example                                         |
| ---------------- | ---------- | ------------------------------- | ----------------------------------------------- |
| `address`        | hex string | Recipient address               | "0xb9d79348..."                                 |
| `amount`         | hex string | Withdrawal amount (Gwei)        | "0x10fa186" (17,891,718 Gwei = 0.017891718 ETH) |
| `index`          | hex string | Global withdrawal index         | "0x66120fb"                                     |
| `validatorIndex` | hex string | Validator index on beacon chain | "0x9ece8" (650,472)                             |

## Transaction Schema

### Full Transaction Object Fields

When `eth_getBlockByNumber` is called with `includeTransactions=true`, or when using `eth_getTransactionByHash`:

| Field                  | Type       | Description                                                     | Example Value                  |
| ---------------------- | ---------- | --------------------------------------------------------------- | ------------------------------ |
| `accessList`           | array      | EIP-2930 access list (addresses and storage keys)               | []                             |
| `blockHash`            | hex string | Block hash containing this tx                                   | "0x803ad3ed..."                |
| `blockNumber`          | hex string | Block number containing this tx                                 | "0x16a00e1"                    |
| `chainId`              | hex string | Chain ID (1 = mainnet)                                          | "0x1"                          |
| `from`                 | hex string | Sender address                                                  | "0xbeee82b7..."                |
| `gas`                  | hex string | Gas limit for this transaction                                  | "0x4d3a1" (316,321)            |
| `gasPrice`             | hex string | Effective gas price paid (wei)                                  | "0x3b35c053" (995,074,643 wei) |
| `hash`                 | hex string | Transaction hash (32 bytes)                                     | "0x76473129..."                |
| `input`                | hex string | Transaction calldata                                            | "0x0965d04b..."                |
| `maxFeePerGas`         | hex string | Max total fee willing to pay (EIP-1559)                         | "0x3b35c053"                   |
| `maxPriorityFeePerGas` | hex string | Max priority fee (tip to miner)                                 | "0x0"                          |
| `nonce`                | hex string | Sender's transaction count                                      | "0x3d8" (984)                  |
| `r`                    | hex string | ECDSA signature r value                                         | "0x9af2b532..."                |
| `s`                    | hex string | ECDSA signature s value                                         | "0x454b9d91..."                |
| `to`                   | hex string | Recipient address (null for contract creation)                  | "0xbeef0296..."                |
| `transactionIndex`     | hex string | Position in block (0-indexed)                                   | "0x0"                          |
| `type`                 | hex string | Transaction type (0=legacy, 1=EIP-2930, 2=EIP-1559, 3=EIP-4844) | "0x2"                          |
| `v`                    | hex string | ECDSA recovery ID                                               | "0x0"                          |
| `value`                | hex string | ETH value transferred (wei)                                     | "0x0"                          |
| `yParity`              | hex string | Y-parity of signature (EIP-2718)                                | "0x0"                          |

### Transaction Types

- **Type 0**: Legacy transactions (pre-EIP-2718)
- **Type 1**: EIP-2930 transactions (with access lists)
- **Type 2**: EIP-1559 transactions (with dynamic fees)
- **Type 3**: EIP-4844 blob transactions (with blob gas)

## Fee History Schema

### Method: `eth_feeHistory`

**Parameters**: `[blockCount, newestBlock, rewardPercentiles]`

- `blockCount`: hex string or number of blocks to query
- `newestBlock`: hex string block number or "latest"
- `rewardPercentiles`: array of percentile values [0-100]

**Example**:

```json
{
  "jsonrpc": "2.0",
  "method": "eth_feeHistory",
  "params": ["0x5", "latest", [25, 50, 75]],
  "id": 1
}
```

### Fee History Response Fields

| Field               | Type            | Description                                       | Example                  |
| ------------------- | --------------- | ------------------------------------------------- | ------------------------ |
| `baseFeePerBlobGas` | array of hex    | Base fee per blob gas for each block + next block | ["0x3", "0x2", ...]      |
| `baseFeePerGas`     | array of hex    | Base fee per gas for each block + next block      | ["0x3b561e55", ...]      |
| `blobGasUsedRatio`  | array of float  | Ratio of blob gas used to max (0.0-1.0)           | [0, 0.7777, 0.5555, ...] |
| `gasUsedRatio`      | array of float  | Ratio of gas used to gas limit (0.0-1.0)          | [0.4914, 0.4552, ...]    |
| `oldestBlock`       | hex string      | Oldest block number in range                      | "0x16a00e0"              |
| `reward`            | array of arrays | Priority fee percentiles for each block           | [[p25, p50, p75], ...]   |

**Important Notes**:

- `baseFeePerGas` and `baseFeePerBlobGas` arrays have length `blockCount + 1` (includes next block prediction)
- Other arrays have length `blockCount`
- `reward[i][j]` is the j-th percentile priority fee for block i (in wei)

## Hex Value Conversion

All numeric values in Ethereum RPC are returned as hexadecimal strings prefixed with "0x".

### Conversion Examples

```python
# Block number
block_num = int("0x16a00e1", 16)  # 23,593,185

# Gas used
gas_used = int("0x13892e4", 16)  # 20,456,676

# Base fee per gas (wei)
base_fee_wei = int("0x3b35c053", 16)  # 995,074,643 wei

# Convert wei to gwei (1 gwei = 10^9 wei)
base_fee_gwei = base_fee_wei / 1e9  # 0.995074643 gwei

# Convert wei to ETH (1 ETH = 10^18 wei)
value_eth = int("0x10fa186", 16) / 1e9  # 0.017891718 ETH (from gwei)

# Timestamp to datetime
import datetime
timestamp = int("0x6909a133", 16)
dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
# 2025-11-01 15:39:47 UTC
```

### Gas Price Calculation (EIP-1559)

```python
# For type 2 transactions
base_fee = int("0x3b35c053", 16)  # from block
max_priority_fee = int("0x0", 16)  # from transaction
max_fee_per_gas = int("0x3b35c053", 16)  # from transaction

# Effective gas price = min(max_fee_per_gas, base_fee + max_priority_fee)
effective_gas_price = min(max_fee_per_gas, base_fee + max_priority_fee)

# Total cost = gas_used * effective_gas_price
# (Note: gas_used comes from transaction receipt, not available in this example)
```

## Derivable Network Metrics

### Block-Level Metrics

1. **Gas Utilization Rate**

   ```python
   gas_limit = int(block["gasLimit"], 16)
   gas_used = int(block["gasUsed"], 16)
   utilization = gas_used / gas_limit  # 0.4549... (45.49%)
   ```

2. **Base Fee (Gwei)**

   ```python
   base_fee_gwei = int(block["baseFeePerGas"], 16) / 1e9  # 0.995 gwei
   ```

3. **Transaction Count**

   ```python
   tx_count = len(block["transactions"])  # 188 transactions
   ```

4. **Block Time** (requires previous block)

   ```python
   current_timestamp = int(block["timestamp"], 16)
   previous_timestamp = int(previous_block["timestamp"], 16)
   block_time = current_timestamp - previous_timestamp  # ~12 seconds
   ```

5. **Blob Gas Utilization** (EIP-4844)

   ```python
   blob_gas_used = int(block["blobGasUsed"], 16)
   max_blob_gas = 6 * 131072  # 6 blobs per block * 128KB each
   blob_utilization = blob_gas_used / max_blob_gas
   ```

6. **Average Gas per Transaction**

   ```python
   avg_gas = int(block["gasUsed"], 16) / len(block["transactions"])
   # 108,813 gas per tx
   ```

7. **Block Size (MB)**

   ```python
   block_size_mb = int(block["size"], 16) / 1_048_576  # 0.213 MB
   ```

8. **Withdrawal Count & Volume**
   ```python
   withdrawal_count = len(block["withdrawals"])  # 16
   total_withdrawn_gwei = sum(int(w["amount"], 16) for w in block["withdrawals"])
   total_withdrawn_eth = total_withdrawn_gwei / 1e9  # 0.282 ETH
   ```

### Fee Market Metrics (from `eth_feeHistory`)

1. **Base Fee Trend**

   ```python
   base_fees = [int(fee, 16) / 1e9 for fee in fee_history["baseFeePerGas"]]
   # [0.996, 0.995, 0.985, 1.002, 0.971, 0.911] gwei
   base_fee_change = (base_fees[-1] - base_fees[0]) / base_fees[0]
   # -8.5% decrease over 5 blocks
   ```

2. **Priority Fee Percentiles**

   ```python
   # rewards[i][0] = 25th percentile, [i][1] = 50th, [i][2] = 75th
   median_priority_fees = [int(r[1], 16) / 1e9 for r in fee_history["reward"]]
   # [0.100, 0.100, 0.170, 0.171, 0.237] gwei
   ```

3. **Network Congestion Score**

   ```python
   avg_gas_ratio = sum(fee_history["gasUsedRatio"]) / len(fee_history["gasUsedRatio"])
   # 0.44 (44% average utilization)
   congestion_level = "low" if avg_gas_ratio < 0.5 else "moderate" if avg_gas_ratio < 0.8 else "high"
   ```

4. **Blob Market Activity**

   ```python
   avg_blob_ratio = sum(fee_history["blobGasUsedRatio"]) / len(fee_history["blobGasUsedRatio"])
   # 0.42 (42% blob space usage)
   ```

5. **Recommended Gas Prices**

   ```python
   # For fast inclusion (75th percentile)
   fast_priority_fee = int(fee_history["reward"][-1][2], 16)  # latest block, 75th percentile
   fast_max_fee = int(fee_history["baseFeePerGas"][-1], 16) + fast_priority_fee

   # For standard inclusion (50th percentile)
   standard_priority_fee = int(fee_history["reward"][-1][1], 16)
   standard_max_fee = int(fee_history["baseFeePerGas"][-1], 16) + standard_priority_fee
   ```

### Transaction-Level Metrics

1. **Effective Gas Price**

   ```python
   # For EIP-1559 transactions (type 2)
   block_base_fee = int(block["baseFeePerGas"], 16)
   tx_max_priority = int(tx["maxPriorityFeePerGas"], 16)
   tx_max_fee = int(tx["maxFeePerGas"], 16)

   effective_priority = min(tx_max_priority, tx_max_fee - block_base_fee)
   effective_gas_price = block_base_fee + effective_priority
   ```

2. **Transaction Value (ETH)**

   ```python
   value_eth = int(tx["value"], 16) / 1e18  # 0 ETH (this tx only calls contract)
   ```

3. **Transaction Type Distribution**
   ```python
   from collections import Counter
   types = Counter(int(tx["type"], 16) for tx in block["transactions"])
   # {2: 180, 0: 8} - 180 EIP-1559, 8 legacy
   ```

## Common Use Cases

### 1. Real-Time Gas Price Monitor

```python
import requests

def get_gas_prices():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_feeHistory",
        "params": ["0x1", "latest", [25, 50, 75]],
        "id": 1
    }
    response = requests.post("https://eth.llamarpc.com", json=payload)
    data = response.json()["result"]

    base_fee = int(data["baseFeePerGas"][-1], 16) / 1e9  # next block base fee
    priority_fees = [int(r, 16) / 1e9 for r in data["reward"][0]]

    return {
        "slow": base_fee + priority_fees[0],    # 25th percentile
        "standard": base_fee + priority_fees[1], # 50th percentile
        "fast": base_fee + priority_fees[2]      # 75th percentile
    }
```

### 2. Network Congestion Dashboard

```python
def get_network_metrics():
    # Get latest block
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["latest", False],
        "id": 1
    }
    response = requests.post("https://eth.llamarpc.com", json=payload)
    block = response.json()["result"]

    gas_limit = int(block["gasLimit"], 16)
    gas_used = int(block["gasUsed"], 16)

    return {
        "block_number": int(block["number"], 16),
        "gas_utilization": gas_used / gas_limit,
        "base_fee_gwei": int(block["baseFeePerGas"], 16) / 1e9,
        "tx_count": len(block["transactions"]),
        "timestamp": int(block["timestamp"], 16)
    }
```

### 3. MEV Analysis (Builder Identification)

```python
def analyze_builder(block):
    miner = block["miner"]
    extra_data = bytes.fromhex(block["extraData"][2:]).decode('utf-8', errors='ignore')

    # Example: "0x4275696c646572..." decodes to "Builder+ www.btcs.com/builder"
    return {
        "builder_address": miner,
        "builder_tag": extra_data,
        "tx_count": len(block["transactions"]),
        "gas_used": int(block["gasUsed"], 16)
    }
```

## Advanced Metrics

### Block Production Efficiency

```python
def calculate_efficiency_metrics(block):
    gas_limit = int(block["gasLimit"], 16)
    gas_used = int(block["gasUsed"], 16)
    block_size = int(block["size"], 16)

    return {
        "gas_efficiency": gas_used / gas_limit,  # how full is the block
        "bytes_per_gas": block_size / gas_used,  # data density
        "tx_density": len(block["transactions"]) / gas_used * 1000  # txs per 1000 gas
    }
```

### Validator Withdrawal Rate

```python
def analyze_withdrawals(block):
    withdrawals = block["withdrawals"]
    total_gwei = sum(int(w["amount"], 16) for w in withdrawals)

    return {
        "withdrawal_count": len(withdrawals),
        "total_eth_withdrawn": total_gwei / 1e9,
        "avg_withdrawal_eth": total_gwei / 1e9 / len(withdrawals) if withdrawals else 0,
        "unique_recipients": len(set(w["address"] for w in withdrawals))
    }
```

### EIP-4844 Blob Metrics

```python
def analyze_blob_market(block):
    blob_gas_used = int(block["blobGasUsed"], 16) if block.get("blobGasUsed") else 0
    max_blob_gas = 6 * 131072  # 786,432 gas per block

    return {
        "blob_gas_used": blob_gas_used,
        "blob_utilization": blob_gas_used / max_blob_gas,
        "estimated_blob_count": blob_gas_used // 131072  # approximate
    }
```

## Field Availability by Network Upgrade

| Field                   | Pre-London | London (EIP-1559) | Shanghai | Cancun (EIP-4844)  |
| ----------------------- | ---------- | ----------------- | -------- | ------------------ |
| `baseFeePerGas`         | ❌         | ✅                | ✅       | ✅                 |
| `withdrawals`           | ❌         | ❌                | ✅       | ✅                 |
| `withdrawalsRoot`       | ❌         | ❌                | ✅       | ✅                 |
| `blobGasUsed`           | ❌         | ❌                | ❌       | ✅                 |
| `excessBlobGas`         | ❌         | ❌                | ❌       | ✅                 |
| `baseFeePerBlobGas`     | ❌         | ❌                | ❌       | ✅ (in feeHistory) |
| `parentBeaconBlockRoot` | ❌         | ❌                | ❌       | ✅                 |

## Important Notes

1. **Timestamp Precision**: Block timestamps are in seconds (not milliseconds)
2. **Gas Units**: All gas values are in gas units (not gwei or wei)
3. **Fee Units**: All fee values (baseFeePerGas, maxFeePerGas, etc.) are in wei
4. **Array Lengths**: `baseFeePerGas` in `eth_feeHistory` has length N+1 (includes prediction for next block)
5. **Post-Merge**: `difficulty`, `nonce`, and `uncles` are always zero/empty
6. **EIP-1559**: Legacy transactions (type 0) still work but use `gasPrice` instead of `maxFeePerGas`
7. **Block Size Limit**: Soft limit around 220KB, depends on gas limit and transaction types
8. **Withdrawal Amounts**: Measured in Gwei (1 Gwei = 10^9 wei = 0.000000001 ETH)

## Undocumented/Interesting Fields

1. **`extraData`**: Can contain builder signatures, MEV-boost info, vanity text
2. **`requestsHash`**: Future-proofing for EIP-7685 (execution layer requests)
3. **`parentBeaconBlockRoot`**: Links to consensus layer (useful for PoS analysis)
4. **`blobGasUsedRatio`**: Easier than calculating from raw blob gas values
5. **`logsBloom`**: Can be used for fast event filtering before fetching receipts
