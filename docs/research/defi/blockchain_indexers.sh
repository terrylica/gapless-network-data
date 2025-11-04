#!/bin/bash
# Test blockchain indexing services for DEX data

echo "=== Blockchain Indexing Services for DEX Data ==="
echo ""

echo "1. Alchemy Enhanced APIs:"
echo "   - NFT API, Token API, Webhook API"
echo "   - Free tier: 300M compute units/month"
echo "   - Does NOT provide pre-indexed DEX trade data"
echo "   - Would require parsing Swap events manually"
echo ""

echo "2. QuickNode:"
echo "   - Free tier: 10M requests/month (testnet only)"
echo "   - Mainnet requires paid plan"
echo "   - No pre-indexed DEX aggregation"
echo ""

echo "3. Moralis Web3 Data API:"
echo "   - Test token price endpoint"
curl -s "https://deep-index.moralis.io/api/v2.2/erc20/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2/price?chain=eth" \
  -H "Accept: application/json" | head -20
echo ""

echo "4. Ankr Advanced APIs:"
echo "   - Test token price endpoint"
curl -s -X POST "https://rpc.ankr.com/multichain" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "ankr_getTokenPrice",
    "params": {
      "blockchain": "eth",
      "contractAddress": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    },
    "id": 1
  }' | jq . 2>&1
echo ""

echo "5. Unmarshal API (Specialized DEX indexer):"
curl -s "https://api.unmarshal.com/v1/ethereum/address/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640/assets" | head -20
echo ""

echo "6. Covalent (requires API key but has free tier):"
echo "   - 100,000 credits/month free"
echo "   - DEX endpoints: /xy=k/uniswap_v2/tokens/address/"
echo "   - Historical liquidity and volume data"
echo "   - Requires API key signup"
