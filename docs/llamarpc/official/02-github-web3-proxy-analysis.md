# LlamaNodes web3-proxy GitHub Analysis

**Date**: 2025-11-03
**Source**: https://github.com/llamanodes/web3-proxy

## Repository Overview

web3-proxy is LlamaNodes' open-source "fast caching and load-balancing proxy designed for web3 (Ethereum or similar) JsonRPC servers."

## JSON-RPC Methods Supported

**Coverage**: "Most RPC methods are currently supported"
**Status**: Filters will be added soon (as of repository snapshot)

### Confirmed Methods (from examples):

- `web3_clientVersion` - Get client version
- `eth_blockNumber` - Get latest block number
- `eth_getBlockByNumber` - Get block by number
- `eth_getBalance` - Get account balance
- `eth_sendRawTransaction` - Send signed transactions (routed to private RPCs)
- `eth_subscribe` - WebSocket subscriptions (newHeads, newPendingTransactions)

### Implied Standard Support:

Since web3-proxy is Ethereum-compatible, it should support standard Ethereum JSON-RPC API methods including:

- Block operations (eth_getBlockByHash, eth_getBlockTransactionCountByNumber, etc.)
- Transaction operations (eth_getTransactionByHash, eth_getTransactionReceipt, etc.)
- State queries (eth_call, eth_estimateGas, eth_getCode, etc.)
- Filter operations (pending implementation)

## Rate Limiting Architecture

### Two-Level System:

**1. Server-Level Limits**:

- `soft_limit` - Performance degrades beyond this threshold
- `hard_limit` - Errors returned beyond this threshold
- Configurable per upstream RPC server

**2. User-Level Limits**:

- Different service tiers available
- "Unlimited" tier removes per-second request restrictions
- Configurable based on user authentication/API key

### Configuration:

Rate limits set via TOML config files (e.g., `./config/development.toml`)

## Archive Data Support

**Status**: Not explicitly documented in GitHub README
**Implication**: Archive node support depends on underlying RPC servers configured in web3-proxy
**Note**: Free tier mentions "50 Requests per Second" on llamarpc.com, premium offers "Archive data access"

## Usage Examples

### Basic RPC Call (curl):

```bash
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}' \
  http://127.0.0.1:8544
```

### WebSocket Connection:

```bash
websocat ws://127.0.0.1:8544
> {"jsonrpc":"2.0","id":1,"method":"eth_subscribe","params":["newHeads"]}
```

### Load Testing Tools Mentioned:

- `wrk` - HTTP benchmarking
- `ethspam` - Ethereum-specific load testing
- `versus` - Performance comparison tool

## Configuration Details

### Format: TOML

Example: `./config/development.toml`

### Key Configuration Areas:

**1. Server Settings**:

- Port specification
- Worker thread count

**2. RPC Endpoints**:

- Upstream server URLs
- Performance limits (soft_limit, hard_limit)
- Private RPC routing

**3. Database**:

- MySQL backend (requires `innodb_rollback_on_timeout=1`)

**4. Metrics**:

- InfluxDB integration
- Unique server IDs for multi-instance deployments

## Technical Architecture

**Design**: Load-balancing proxy with caching
**Purpose**: Distribute requests across multiple RPC providers
**Security Feature**: Option to use high-security JSON-RPC endpoints (private requests, MEV protection)
**Scalability**: Supports autoscaling and globally redundant infrastructure

## Key Insights

1. **Open Source**: Full implementation available on GitHub
2. **Ethereum-Compatible**: Works with any chain using Ethereum JSON-RPC standard
3. **Flexible Rate Limiting**: Both server-side and user-side controls
4. **Production-Grade**: MySQL backend, InfluxDB metrics, load testing tools
5. **Privacy-Conscious**: Private transaction routing to avoid sandwich attacks

## Next Steps for Research

- Test actual endpoint to confirm method support
- Verify archive data access on free vs premium tiers
- Determine historical data retention policy
- Find official examples/tutorials beyond GitHub README
