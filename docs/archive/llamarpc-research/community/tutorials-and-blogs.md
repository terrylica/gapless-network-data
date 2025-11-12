# Ethereum Data Collection Tutorials and Blog Posts

## Mempool Data Collection Tutorials

### 1. Magnus Hansson - Parse Ethereum Mempool Data (2024)

- **URL**: https://magnushansson.xyz/blog_posts/crypto_defi/2024-01-15-parse_mempool_data
- **Key Tools**: py_evm, eth-utils
- **Data Source**: Mempool Dumpster by Flashbots
- **Coverage**: August 2023 onwards, 1-2 million transactions/day
- **Approach**: Parse historical mempool dumps from multiple node operators

### 2. QuickNode - How to Access Ethereum Mempool

- **URL**: https://www.quicknode.com/guides/ethereum-development/transactions/how-to-access-ethereum-mempool
- **Key Tools**: Ethers.js, Viem (recommended), Web3.js (deprecated)
- **Approach**: Subscribe to mempool using WebSocket
- **Note**: Viem and Ethers.js recommended for new development

### 3. Amberdata - Historical and Real-Time Eth Mempool Data

- **URL**: https://blog.amberdata.io/how-to-access-historical-and-real-time-eth-mempool-data
- **API Endpoints**:
  - Real-time: WebSocket Secure (WSS)
  - Historical: REST endpoint
- **Data Fields**: Transaction hash, time in mempool, size, fee
- **Note**: Commercial service with API access

### 4. Bitquery - Ethereum Mempool API (2023)

- **URL**: https://bitquery.io/blog/mempool-data-providers
- **Features**: Real-time stream of newly broadcasted transactions
- **Query Support**: Token transfers, DEX trades (Uniswap, Sushiswap)
- **Latency**: Low latency access
- **Note**: Commercial API service

### 5. Blocknative - Mempool Explorer & Data Archive

- **URL**: https://www.blocknative.com/explorer
- **Features**: Mempool Data Archive, Blob Archive API (post-EIP-4844)
- **Focus**: Data availability landscape insights
- **Note**: Commercial service

### 6. Pawel Urbanek - Hunting Rare NFTs in Ethereum Mempool

- **URL**: https://pawelurbanek.com/ethereum-mempool-monitoring
- **Focus**: Real-time mempool monitoring for NFT sniping
- **Approach**: Dark forest monitoring techniques
- **Relevance**: Advanced mempool monitoring patterns

## Free Ethereum RPC Best Practices

### Provider Comparisons

#### Alchemy vs. Quicknode

- **Source**: https://www.alchemy.com/overviews/free-ethereum-rpc
- **Alchemy Free Tier**: 10x more computing resources for overlapping JSON-RPC calls
- **Recommendation**: Alchemy for higher performance in free tier

#### Chainstack

- **Source**: https://chainstack.com/build-better-with-ethereum/
- **Free Tier**: 3 million requests/month
- **Description**: "Rock-solid endpoint"
- **Setup**: Zero maintenance, quick setup

#### Ankr

- **Source**: https://www.ankr.com/rpc/eth/
- **Features**: Free WEB3 API endpoints for blockchain interaction
- **Focus**: Dedicated RPC for Ethereum

### Best Practices Summary

From multiple sources (101 Blockchains, Medium, NOWNodes):

#### 1. Use Alternative RPC Endpoints

- Avoid downtime with backup endpoints
- Maintain smooth user experience in dApps
- Critical for production reliability

#### 2. Private vs Public RPC Nodes

- **Public**: Free/low-cost, testing, small-scale projects
- **Private**: Managed nodes, production dApps
- **Self-hosted**: Maximum control, high maintenance

#### 3. Security Practices

- Secure endpoints with authentication
- Implement whitelisting
- Never expose API keys in public repos
- Use untrusted endpoints cautiously

#### 4. Rate Limiting Awareness

- Most public endpoints limit requests/second
- Higher latency on shared infrastructure
- Plan for rate limit errors

#### 5. Technical Implementation

- **Web3 Libraries**: ethers.js (JavaScript), web3.py (Python)
- **Protocols**: HTTP or WebSocket
- **Format**: JSON-RPC

### Official Resources

#### Ethereum.org JSON-RPC API Documentation

- **URL**: https://ethereum.org/developers/docs/apis/json-rpc/
- **Authority**: Official Ethereum Foundation documentation
- **Coverage**: Complete JSON-RPC specification

#### Stack Exchange Discussion

- **URL**: https://ethereum.stackexchange.com/questions/102967/free-and-public-ethereum-json-rpc-api-nodes
- **Community**: Active developer discussions
- **Value**: Real-world experiences with different providers

## mempool.space API Resources

### Official Documentation

- **REST API**: https://mempool.space/docs/api/rest
- **WebSocket API**: https://mempool.space/docs/api/websocket
- **Focus**: Bitcoin blockchain (not Ethereum)
- **Authentication**: Not required for public data

### JavaScript Library (mempool.js)

- **Repository**: https://github.com/mempool/mempool.js
- **Features**:
  - Get last 10 transactions entering mempool
  - Transaction fields: txid, fee, vsize, value
  - Address details: chain_stats, mempool_stats
  - WebSocket subscriptions for real-time data

### Python Library

- **Repository**: https://github.com/kenedii/Mempool.space-API
- **Description**: Python library for Mempool.space free API
- **Focus**: Bitcoin blockchain information retrieval

### Self-Hosting Option

- **Repository**: https://github.com/mempool/mempool
- **Features**: Full Bitcoin ecosystem explorer
- **Platforms**: Umbrel, Raspiblitz, Start9
- **Approach**: One-click installation on Raspberry Pi fullnode distros

## Key Insights

### Ethereum Mempool Data

1. **No simple free public API**: Unlike Bitcoin's mempool.space, Ethereum mempool data requires:
   - Commercial services (Amberdata, Bitquery, Blocknative)
   - Historical dumps (Flashbots Mempool Dumpster)
   - Direct node access (QuickNode WebSocket subscriptions)

2. **Real-time vs Historical**:
   - Real-time requires WebSocket connections to nodes
   - Historical data available via Flashbots dumps (1-2M tx/day)

3. **Library Recommendations**:
   - ✅ Ethers.js - Modern, actively maintained
   - ✅ Viem - Modern, TypeScript-first
   - ❌ Web3.js - No longer actively maintained

### Free RPC Best Practices

1. **Always have backup endpoints**: Downtime is common on free tiers
2. **Monitor rate limits**: Plan for 429 errors
3. **Use libraries, not raw HTTP**: ethers.js/web3.py handle edge cases
4. **Never commit API keys**: Even for free tiers

### Bitcoin vs Ethereum Mempool

- **Bitcoin**: mempool.space provides excellent free API
- **Ethereum**: Fragmented landscape, mostly commercial services
- **Note**: Our project targets Bitcoin mempool data (mempool.space), not Ethereum
