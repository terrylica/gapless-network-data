#!/bin/bash
# Test DEX aggregator APIs

echo "=== DEX Aggregator APIs ==="
echo ""

echo "1. 1inch API v5.2 (Free tier: 1 RPS):"
# Get quote for WETH -> USDC swap
curl -s "https://api.1inch.dev/swap/v5.2/1/quote?src=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2&dst=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48&amount=1000000000000000000" | head -20
echo ""

echo "2. 0x API (Free, no auth required for quotes):"
curl -s "https://api.0x.org/swap/v1/quote?sellToken=WETH&buyToken=USDC&sellAmount=1000000000000000000" | jq '{
  price: .price,
  guaranteedPrice: .guaranteedPrice,
  estimatedGas: .estimatedGas,
  sources: .sources[0:3]
}' 2>&1
echo ""

echo "3. ParaSwap API:"
curl -s "https://apiv5.paraswap.io/prices/?srcToken=0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee&destToken=0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48&amount=1000000000000000000&srcDecimals=18&destDecimals=6&side=SELL&network=1" | jq '{
  priceRoute: .priceRoute.destAmount,
  bestRoute: .priceRoute.bestRoute[0]
}' 2>&1
echo ""

echo "4. KyberSwap API:"
curl -s "https://aggregator-api.kyberswap.com/ethereum/api/v1/routes?tokenIn=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2&tokenOut=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48&amountIn=1000000000000000000" | jq '. | keys' 2>&1
echo ""

echo "5. CowSwap API (MEV-protected):"
curl -s "https://api.cow.fi/mainnet/api/v1/markets/WETH-USDC" | jq . 2>&1 | head -20
echo ""

echo "6. SushiSwap API:"
curl -s "https://api.sushi.com/price/v1/1/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" | jq . 2>&1
echo ""

echo "=== Note ==="
echo "These aggregator APIs provide:"
echo "- Real-time pricing"
echo "- Routing information"
echo "- NOT historical OHLCV data"
echo "- NOT suitable for feature engineering with M15+ frequency"
