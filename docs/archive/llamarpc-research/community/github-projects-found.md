# GitHub Projects Using LlamaRPC

## Primary LlamaRPC Infrastructure

### 1. web3-proxy by llamanodes

- **URL**: https://github.com/llamanodes/web3-proxy
- **Description**: Fast loadbalancing and caching proxy for Ethereum or chains with similar JSON-RPC methods
- **Key Features**:
  - Sends signed transactions in parallel to configured private RPCs
  - Other requests sent to RPC server on latest block
  - Supports LlamaNodes and other providers
  - Built for production usage

### 2. ethereum-rpc-mpc by Phillip-Kemper

- **URL**: https://github.com/Phillip-Kemper/ethereum-rpc-mpc
- **Description**: TypeScript MCP server for Ethereum JSON-RPC calls
- **Key Features**:
  - Defaults to "https://eth.llamarpc.com" if no RPC URL provided
  - Enables AI models to interact with blockchain data
  - Leverages MCP SDK for all Ethereum JSON-RPC calls

## Projects Using LlamaRPC in Production

### 3. DefiLlama/chainlist

- **URL**: https://github.com/DefiLlama/chainlist
- **Usage**: Lists eth.llamarpc.com as RPC endpoint for Ethereum Mainnet
- **Significance**: Major DeFi aggregator trusts LlamaRPC

### 4. Uniswap/fillanthropist

- **URL**: https://github.com/Uniswap/fillanthropist/blob/main/.env.example
- **Usage**: Uses llamarpc.com for Ethereum, Optimism, and Base RPC URLs
- **Significance**: Major DEX using LlamaRPC in example configs

### 5. code-423n4/2023-04-eigenlayer

- **URL**: https://github.com/code-423n4/2023-04-eigenlayer/blob/main/.env.example
- **Usage**: Uses LlamaRPC in audit code examples
- **Significance**: Security auditors use it as reliable reference

### 6. ccbbccbb/viemcp

- **URL**: https://github.com/ccbbccbb/viemcp
- **Description**: Fast setup MCP server for Viem & Wagmi integration
- **Usage**: References LlamaRPC for onchain data parsing

### 7. EdenBlockVC/spook

- **URL**: https://github.com/EdenBlockVC/spook
- **Description**: Mixing service using Nym network to anonymize Ethereum RPC calls
- **Usage**: References LlamaRPC endpoints

## Other Ethereum RPC Projects (Learning Resources)

### 8. ethereumjs/ethrpc

- **URL**: https://github.com/ethereumjs/ethrpc
- **Description**: Maximal RPC wrapper for JavaScript
- **Relevance**: Pattern reference for RPC communication

### 9. VictorTaelin/ethereum-rpc

- **URL**: https://github.com/VictorTaelin/ethereum-rpc
- **Description**: Minimalist approach to Ethereum RPC
- **Relevance**: Simple implementation patterns

### 10. gabedonnan/pythereum

- **URL**: https://github.com/gabedonnan/pythereum
- **Description**: Lightweight Ethereum JSON RPC library for Python
- **Relevance**: Python implementation patterns for RPC

### 11. ethereum/execution-apis

- **URL**: https://github.com/ethereum/execution-apis
- **Description**: Official collection of APIs provided by Ethereum execution layer clients
- **Relevance**: Canonical API specifications

### 12. arddluma/awesome-list-rpc-nodes-providers

- **URL**: https://github.com/arddluma/awesome-list-rpc-nodes-providers
- **Description**: Curated list of Node providers and public RPC endpoints
- **Relevance**: Comprehensive list of alternatives to LlamaRPC

## Initial Observations

1. **Production Trust**: Major projects (Uniswap, DefiLlama) use LlamaRPC
2. **Default Choice**: Multiple projects default to LlamaRPC when RPC URL not specified
3. **Multi-chain Support**: LlamaRPC supports Ethereum, Optimism, Base, and more
4. **Infrastructure Focus**: LlamaNodes built web3-proxy specifically for production RPC load balancing
