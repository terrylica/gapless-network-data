# Free High-Frequency Ethereum On-Chain Data Sources Research

**Research Date**: 2025-11-03
**Perspective**: Ethereum ecosystem data sources
**Target Frequency**: M1, M5, M15+ (going back to 2022 or earlier)

---

## Executive Summary

This research identified **6 viable free data sources** for Ethereum on-chain data with varying levels of frequency granularity. The most promising sources for high-frequency historical data are:

1. **JSON-RPC Archive Nodes** (LlamaRPC, Alchemy, Infura) - Block-level data (~12s intervals)
2. **Dune Analytics** - SQL-based queries with block-level granularity
3. **Bitquery GraphQL API** - Real-time and historical blockchain data
4. **Flipside Crypto** - SQL-based blockchain datasets
5. **The Graph Protocol** - Subgraph queries for DeFi protocols
6. **Etherscan API V2** - Daily aggregates only

**Key Finding**: Ethereum's ~12-second block time means native blockchain data provides sub-minute granularity. To achieve M1, M5, M15 frequency, you need to aggregate block-level data.

---

## 1. JSON-RPC Archive Nodes (Block-Level Data)

### Overview

Free public JSON-RPC endpoints provide access to historical Ethereum blocks going back to genesis (2015). Each block contains timestamp, gas data, and transactions.

### Data Sources

#### LlamaRPC ✅ TESTED

- **Endpoint**: `https://eth.llamarpc.com`
- **Frequency**: Block-level (~12 seconds average)
- **Historical Depth**: Full archive (2015-present)
- **Rate Limits**: Not publicly documented, generous free tier
- **Cost**: FREE
- **Authentication**: None required

**Key Methods**:

- `eth_getBlockByNumber` - Retrieve block data by number
- `eth_feeHistory` - Get historical gas fee data
- `eth_blockNumber` - Get latest block number

**Schema** (block data):

```json
{
  "number": "0xd59f80", // Block number (14000000)
  "timestamp": "0x61e0aeeb", // Unix timestamp (2022-01-13 14:59:55)
  "gasUsed": "0x7be612", // Gas used in block
  "gasLimit": "0x1c9c380", // Gas limit
  "baseFeePerGas": "0x207d533808" // Base fee (139.54 Gwei for this block)
}
```

**Example - Fetch Block Data**:

```bash
curl -s -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_getBlockByNumber",
    "params":["0xD59F80", false],
    "id":1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    gasUsed: .result.gasUsed,
    baseFeePerGas: .result.baseFeePerGas
  }'
```

**Example - Get Fee History**:

```bash
curl -s -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_feeHistory",
    "params":["0xa", "latest", [25,50,75]],
    "id":1
  }' | jq .
```

**Output**:

```json
{
  "oldestBlock": "0x169fe78",
  "baseFeePerGas": [
    "0xf84132f",
    "0xf41c55d",
    "0x10413653",
    "0xf9b7706",
    "0x1067007b",
    "0xfc48873"
  ],
  "gasUsedRatio": [0.43, 0.76, 0.34, 0.7, 0.35]
}
```

#### Alchemy

- **Endpoint**: `https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY`
- **Frequency**: Block-level (~12 seconds)
- **Historical Depth**: Full archive
- **Rate Limits**:
  - Free tier: 300M compute units/month
  - ~5 requests/second sustained
- **Cost**: FREE (with signup)
- **Authentication**: API key required

**Same methods as LlamaRPC** plus enhanced APIs:

- `alchemy_getAssetTransfers` - Token transfers
- `alchemy_getTokenBalances` - ERC-20 balances

#### Infura

- **Endpoint**: `https://mainnet.infura.io/v3/YOUR_API_KEY`
- **Frequency**: Block-level (~12 seconds)
- **Historical Depth**: Full archive
- **Rate Limits**: 100K requests/day (free tier)
- **Cost**: FREE (with signup)
- **Authentication**: API key required

**Note**: Archive node access included in free tier.

### Data Fields Available

| Field           | Description                   | Use Case             |
| --------------- | ----------------------------- | -------------------- |
| `number`        | Block number                  | Time-series ordering |
| `timestamp`     | Unix timestamp                | Convert to datetime  |
| `baseFeePerGas` | EIP-1559 base fee (Wei)       | Gas price tracking   |
| `gasUsed`       | Total gas consumed            | Network congestion   |
| `gasLimit`      | Maximum gas allowed           | Network capacity     |
| `transactions`  | Transaction hashes            | Detailed tx analysis |
| `size`          | Block size (bytes)            | Data throughput      |
| `difficulty`    | Mining difficulty (pre-merge) | PoW metrics          |

### Converting to M1/M5/M15

Since block time averages ~12 seconds, you need to aggregate:

- **M1 (1-minute)**: Average ~5 blocks
- **M5 (5-minute)**: Average ~25 blocks
- **M15 (15-minute)**: Average ~75 blocks

**Strategy**: Fetch block data sequentially and aggregate by time intervals.

---

## 2. Dune Analytics (SQL-Based Queries)

### Overview

Dune provides free SQL query access to indexed Ethereum blockchain data with block-level granularity.

- **Endpoint**: REST API + Web UI
- **Frequency**: Block-level (can aggregate to any interval)
- **Historical Depth**: Full history (2015-present)
- **Rate Limits**: 2,500 credits/month (free tier)
- **Cost**: FREE (with signup), $5/100 credits after
- **Authentication**: API key required

### Key Tables

#### `ethereum.blocks`

```sql
SELECT
  time,              -- Timestamp (datetime)
  number,            -- Block number
  gas_used,          -- Gas consumed
  gas_limit,         -- Gas limit
  base_fee_per_gas,  -- EIP-1559 base fee
  size               -- Block size
FROM ethereum.blocks
WHERE time >= '2022-01-01'
ORDER BY time DESC
```

#### `ethereum.transactions`

```sql
SELECT
  block_time,        -- Transaction timestamp
  hash,              -- Transaction hash
  gas_price,         -- Gas price (Wei)
  gas_used,          -- Gas consumed
  value,             -- ETH transferred (Wei)
  from,              -- Sender address
  to                 -- Recipient address
FROM ethereum.transactions
WHERE block_time >= '2022-01-01'
  AND block_time < '2022-02-01'
ORDER BY gas_price DESC
LIMIT 100
```

### Python SDK Example

```bash
pip install dune-client
export DUNE_API_KEY="your_api_key"
```

```python
from dune_client.client import DuneClient
from dune_client.types import QueryParameter

dune = DuneClient.from_env()

sql = """
SELECT
  DATE_TRUNC('minute', time) as minute,
  AVG(CAST(base_fee_per_gas AS DOUBLE) / 1e9) as avg_base_fee_gwei,
  AVG(CAST(gas_used AS DOUBLE) / CAST(gas_limit AS DOUBLE)) as avg_utilization
FROM ethereum.blocks
WHERE time >= TIMESTAMP '2022-01-01'
  AND time < TIMESTAMP '2022-01-02'
GROUP BY DATE_TRUNC('minute', time)
ORDER BY minute
"""

query = dune.create_query(
    name="ETH Minutely Gas Metrics - Jan 1 2022",
    query_sql=sql,
    is_private=False
)

results = dune.get_result(query.query_id)
```

### Features

- ✅ M1/M5/M15 aggregation via SQL `DATE_TRUNC`
- ✅ Full historical data back to 2022
- ✅ Free tier includes API access
- ✅ Can query transaction-level data
- ❌ Credit consumption limits queries
- ❌ Not real-time (data lag ~few minutes)

---

## 3. Bitquery GraphQL API

### Overview

Bitquery provides GraphQL API for 40+ blockchains including Ethereum, with both historical and real-time data.

- **Endpoint**: `https://graphql.bitquery.io/`
- **Frequency**: Block-level, can aggregate to minutes
- **Historical Depth**: Full history (2015-present)
- **Rate Limits**:
  - Free tier: 1,000 API calls/day
  - Trial: 100K points for 1 month (no credit card)
- **Cost**: FREE (with signup)
- **Authentication**: API key required

### Example Query - Minutely Gas Prices

```graphql
{
  ethereum(network: ethereum) {
    blocks(
      date: { since: "2022-01-01", till: "2022-01-02" }
      options: { desc: "timestamp.time", limit: 1000 }
    ) {
      timestamp {
        time(format: "%Y-%m-%d %H:%M:%S")
      }
      height
      gasUsed
      gasLimit
      baseFeePerGas
    }
  }
}
```

### cURL Example

```bash
curl -X POST https://graphql.bitquery.io/ \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: YOUR_API_KEY" \
  -d '{
    "query": "{ ethereum(network: ethereum) { blocks(date: {since: \"2022-01-01\", till: \"2022-01-02\"}) { timestamp { time } gasUsed baseFeePerGas } } }"
  }'
```

### Features

- ✅ GraphQL flexibility for custom queries
- ✅ Multi-chain support (40+ blockchains)
- ✅ Real-time and historical data
- ✅ DEX trades, token transfers, smart contract events
- ❌ Free tier limited to 1K calls/day
- ❌ Points-based pricing can be complex

---

## 4. Flipside Crypto (SQL API)

### Overview

Flipside provides curated blockchain datasets accessible via SQL API and Python/JavaScript SDKs.

- **Endpoint**: `https://api-v2.flipsidecrypto.xyz/`
- **Frequency**: Block-level, table-dependent
- **Historical Depth**: Varies by table, generally 2+ years
- **Rate Limits**: 500 query seconds/month (free tier)
- **Cost**: FREE (with signup)
- **Authentication**: API key required

### Python SDK Example

```bash
pip install flipside
```

```python
from flipside import Flipside

flipside = Flipside("YOUR_API_KEY", "https://api-v2.flipsidecrypto.xyz")

sql = """
SELECT
  DATE_TRUNC('minute', block_timestamp) as minute,
  AVG(gas_price / 1e9) as avg_gas_price_gwei,
  COUNT(*) as tx_count
FROM ethereum.core.fact_transactions
WHERE block_timestamp >= '2022-01-01'
  AND block_timestamp < '2022-01-02'
GROUP BY DATE_TRUNC('minute', block_timestamp)
ORDER BY minute
"""

query_result_set = flipside.query(sql)
```

### Key Tables

#### `ethereum.core.fact_transactions`

- `block_timestamp` - Transaction timestamp
- `block_number` - Block number
- `gas_price` - Gas price (Wei)
- `gas_used` - Gas consumed
- `tx_hash` - Transaction hash
- `from_address` - Sender
- `to_address` - Recipient
- `value` - ETH transferred

#### `ethereum.core.fact_blocks`

- `block_timestamp` - Block timestamp
- `block_number` - Block number
- `gas_used` - Total gas used
- `gas_limit` - Gas limit

### Features

- ✅ SQL-based queries (familiar interface)
- ✅ Python/JS/R SDKs
- ✅ Curated, clean datasets
- ✅ Community-contributed tables
- ❌ 500 query seconds/month limit (tight for large queries)
- ❌ Data granularity depends on table design

---

## 5. The Graph Protocol (Subgraph Queries)

### Overview

The Graph indexes smart contract events and exposes data via GraphQL. Ideal for DeFi protocol-specific data.

- **Endpoint**: `https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/SUBGRAPH_ID`
- **Frequency**: Event-based (varies by protocol)
- **Historical Depth**: Depends on subgraph deployment
- **Rate Limits**: 100K queries/month (free tier)
- **Cost**: FREE (with signup), $2/100K queries after
- **Authentication**: API key required

### Available Subgraphs

#### Uniswap V3

- **Subgraph ID**: `5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`
- **Data**: Swaps, pools, liquidity, volume
- **Granularity**: Block-level events

#### Aave V3

- **Data**: Deposits, borrows, liquidations, interest rates
- **Granularity**: Event-based (per transaction)

### Example Query - Uniswap Swaps

```graphql
{
  swaps(
    first: 1000
    orderBy: timestamp
    orderDirection: desc
    where: {
      timestamp_gte: 1640995200 # 2022-01-01 00:00:00 UTC
      timestamp_lte: 1641081599 # 2022-01-01 23:59:59 UTC
    }
  ) {
    timestamp
    amountUSD
    amount0
    amount1
    token0 {
      symbol
    }
    token1 {
      symbol
    }
    pool {
      id
    }
  }
}
```

### cURL Example

```bash
curl -X POST \
  https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ swaps(first: 10, orderBy: timestamp) { timestamp amountUSD } }"
  }'
```

### Features

- ✅ Protocol-specific data (Uniswap, Aave, Compound, etc.)
- ✅ Event-level granularity
- ✅ 100K free queries/month
- ✅ GraphQL flexibility
- ❌ Requires API key (no free anonymous access)
- ❌ Subgraph-specific schemas (not standardized)
- ❌ Not all protocols have subgraphs back to 2022

---

## 6. Etherscan API V2 (Daily Aggregates Only)

### Overview

Etherscan provides stats APIs with DAILY granularity only. Not suitable for M1/M5/M15 frequency.

- **Endpoint**: `https://api.etherscan.io/v2/api`
- **Frequency**: **DAILY** (not suitable for high-frequency)
- **Historical Depth**: 2015-present
- **Rate Limits**: 1 request per 5 seconds (free tier)
- **Cost**: FREE (with API key signup)
- **Authentication**: API key required

### Available Daily Endpoints

#### Daily Average Gas Price

```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=stats&action=dailyavggasprice&startdate=2022-01-01&enddate=2022-01-31&sort=asc&apikey=YOUR_API_KEY"
```

#### Daily Gas Used

```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=stats&action=dailygasused&startdate=2022-01-01&enddate=2022-01-31&sort=asc&apikey=YOUR_API_KEY"
```

#### Daily Transaction Count

```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=stats&action=dailytx&startdate=2022-01-01&enddate=2022-01-31&sort=asc&apikey=YOUR_API_KEY"
```

### Features

- ✅ Simple REST API
- ✅ Historical data back to 2015
- ✅ Multi-chain support (V2 API)
- ❌ **DAILY granularity only** (no M1/M5/M15)
- ❌ Very restrictive rate limit (1 req/5s)

### Real-Time Gas Oracle (Current Only)

```bash
curl "https://api.etherscan.io/v2/api?chainid=1&module=gastracker&action=gasoracle"
```

Response:

```json
{
  "status": "1",
  "message": "OK",
  "result": {
    "LastBlock": "23723637",
    "SafeGasPrice": "0.244885969",
    "ProposeGasPrice": "0.244893027",
    "FastGasPrice": "0.249530031",
    "suggestBaseFee": "0.244885969",
    "gasUsedRatio": "0.78,0.29,0.63,0.59,0.64"
  }
}
```

**Note**: This is real-time only, not historical.

---

## Summary Comparison Table

| Source              | Frequency         | Historical Depth           | Free Tier Limits                  | Auth Required | Best For                      |
| ------------------- | ----------------- | -------------------------- | --------------------------------- | ------------- | ----------------------------- |
| **LlamaRPC**        | Block (~12s)      | Full archive (2015+)       | Generous (undocumented)           | ❌ No         | Quick prototyping, no signup  |
| **Alchemy**         | Block (~12s)      | Full archive (2015+)       | 300M compute units/month          | ✅ API key    | Production RPC access         |
| **Infura**          | Block (~12s)      | Full archive (2015+)       | 100K requests/day                 | ✅ API key    | Archive node queries          |
| **Dune Analytics**  | Block → M1/M5/M15 | Full history (2015+)       | 2,500 credits/month               | ✅ API key    | SQL-based analysis            |
| **Bitquery**        | Block → Minutes   | Full history (2015+)       | 1K calls/day (trial: 100K points) | ✅ API key    | GraphQL multi-chain           |
| **Flipside Crypto** | Block → M1/M5/M15 | 2+ years (table-dependent) | 500 query seconds/month           | ✅ API key    | Curated datasets              |
| **The Graph**       | Event-based       | Subgraph-dependent         | 100K queries/month                | ✅ API key    | DeFi protocols                |
| **Etherscan V2**    | **Daily only**    | Full history (2015+)       | 1 req/5s                          | ✅ API key    | ❌ Not suitable for M1/M5/M15 |

---

## Recommended Data Collection Strategy

### For M1/M5/M15 OHLCV-Style Data

**Best Approach**: Combine JSON-RPC archive nodes with aggregation logic

1. **Data Source**: LlamaRPC (free, no auth) or Alchemy (more reliable, requires signup)
2. **Method**: `eth_getBlockByNumber` for sequential block data
3. **Aggregation**:
   - Fetch blocks in batches (e.g., 500 blocks = ~1.67 hours)
   - Group by time intervals (M1/M5/M15)
   - Calculate OHLCV-style metrics:
     - **Open**: First block's baseFeePerGas in interval
     - **High**: Max baseFeePerGas in interval
     - **Low**: Min baseFeePerGas in interval
     - **Close**: Last block's baseFeePerGas in interval
     - **Volume**: Sum of gasUsed in interval

### For DeFi Protocol Data

**Best Approach**: The Graph protocol subgraphs

1. Query Uniswap/Aave/Compound subgraphs
2. Event-level data (swaps, deposits, borrows)
3. Aggregate to desired frequency

### For Ad-Hoc Analysis

**Best Approach**: Dune Analytics

1. Write SQL queries with `DATE_TRUNC` for time aggregation
2. Export results via API
3. Suitable for research, backtesting

---

## Sample Implementation: Fetch M1 Gas Price Data

### Python Script Using LlamaRPC

```python
#!/usr/bin/env python3
"""
Fetch Ethereum M1 gas price data from LlamaRPC
"""
import requests
from datetime import datetime, timedelta
import pandas as pd

RPC_URL = "https://eth.llamarpc.com"

def get_block_by_number(block_num: int) -> dict:
    """Fetch block data by number"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_num), False],
        "id": 1
    }
    response = requests.post(RPC_URL, json=payload)
    return response.json()["result"]

def get_latest_block() -> int:
    """Get latest block number"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    response = requests.post(RPC_URL, json=payload)
    return int(response.json()["result"], 16)

def fetch_m1_data(start_block: int, end_block: int) -> pd.DataFrame:
    """
    Fetch block data and aggregate to M1 intervals

    Args:
        start_block: Starting block number
        end_block: Ending block number (exclusive)

    Returns:
        DataFrame with M1 OHLCV-style gas data
    """
    blocks = []

    # Fetch blocks
    for block_num in range(start_block, end_block):
        block = get_block_by_number(block_num)

        blocks.append({
            'number': int(block['number'], 16),
            'timestamp': int(block['timestamp'], 16),
            'baseFeePerGas': int(block['baseFeePerGas'], 16) / 1e9,  # Convert to Gwei
            'gasUsed': int(block['gasUsed'], 16),
            'gasLimit': int(block['gasLimit'], 16)
        })

        if block_num % 100 == 0:
            print(f"Fetched {block_num - start_block + 1}/{end_block - start_block} blocks")

    df = pd.DataFrame(blocks)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

    # Aggregate to M1
    df.set_index('datetime', inplace=True)

    m1_data = df.resample('1min').agg({
        'baseFeePerGas': ['first', 'max', 'min', 'last'],  # OHLC
        'gasUsed': 'sum',
        'gasLimit': 'mean'
    })

    m1_data.columns = ['open', 'high', 'low', 'close', 'gasUsed', 'gasLimit']
    m1_data['utilization'] = m1_data['gasUsed'] / m1_data['gasLimit']

    return m1_data

# Example usage
if __name__ == "__main__":
    # Block 14000000 = Jan 13, 2022
    start_block = 14000000
    end_block = 14000300  # ~1 hour of blocks

    print(f"Fetching blocks {start_block} to {end_block}")
    m1_data = fetch_m1_data(start_block, end_block)

    print("\nFirst 5 rows:")
    print(m1_data.head())

    # Save to parquet
    m1_data.to_parquet('/tmp/ethereum-research/eth_m1_gas_20220113.parquet')
    print("\nData saved to /tmp/ethereum-research/eth_m1_gas_20220113.parquet")
```

---

## Rate Limit Considerations

### Sustainable Free-Tier Collection Strategies

| Source   | Daily Limit             | Blocks/Day          | Coverage                   |
| -------- | ----------------------- | ------------------- | -------------------------- |
| LlamaRPC | ~Unlimited              | ~200K+              | ~27 days of history/day    |
| Alchemy  | 300M CU/month           | ~1M blocks/month    | ~12 days/month             |
| Infura   | 100K req/day            | 100K blocks/day     | ~14 days/day               |
| Dune     | 2,500 credits/month     | Unlimited (via SQL) | Full history (query-based) |
| Bitquery | 1K calls/day            | ~1K blocks/day      | ~0.14 days/day             |
| Flipside | 500 query seconds/month | Depends on query    | Variable                   |

**Recommendation**:

- Use **Dune Analytics** for bulk historical queries (2,500 credits can fetch years of M1 data in one query)
- Use **LlamaRPC** for real-time or incremental updates
- Use **Alchemy** for production pipelines with predictable usage

---

## Additional Resources

### Block Explorers

- [Etherscan](https://etherscan.io/) - Web UI for blockchain data
- [Beaconcha.in](https://beaconcha.in/) - Ethereum consensus layer explorer

### Data Providers (Honorable Mentions)

- **Covalent** - Multi-chain API (freemium, limited free tier)
- **Moralis** - Web3 API (free tier available)
- **QuickNode** - RPC provider (free tier: 100K credits/month)
- **Ankr** - Public RPC endpoints (free, no auth)

### Documentation Links

- [Ethereum JSON-RPC Spec](https://ethereum.org/en/developers/docs/apis/json-rpc/)
- [Dune Docs](https://docs.dune.com/)
- [The Graph Docs](https://thegraph.com/docs/)
- [Bitquery Docs](https://docs.bitquery.io/)
- [Flipside Docs](https://docs.flipsidecrypto.xyz/)

---

## Conclusion

For collecting **M1/M5/M15 Ethereum on-chain data going back to 2022**, the optimal free strategy is:

1. **Historical Bulk Collection**: Dune Analytics (SQL queries for large time ranges)
2. **Real-Time Updates**: LlamaRPC or Alchemy (block-by-block fetching)
3. **DeFi Metrics**: The Graph Protocol (protocol-specific subgraphs)

All sources provide block-level data (~12s intervals) which can be aggregated to M1/M5/M15 using standard time-series techniques (pandas resample, SQL DATE_TRUNC, etc.).

**Key Insight**: Ethereum's native block time IS high-frequency data. You just need to aggregate it properly.
