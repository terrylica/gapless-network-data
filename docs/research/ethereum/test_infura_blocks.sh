#!/bin/bash
# Test Infura public endpoint for historical block data
# Block 14000000 is from early 2022 (Jan 2022)

echo "Testing Infura public endpoint for block 14000000 (Jan 2022):"
curl -s -X POST \
  https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0xD59F80", false],
    "id": 1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    gasUsed: .result.gasUsed,
    gasLimit: .result.gasLimit,
    baseFeePerGas: .result.baseFeePerGas
  }'

echo -e "\nTesting eth_feeHistory for last 10 blocks:"
curl -s -X POST \
  https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_feeHistory",
    "params": ["0xa", "latest", [25, 50, 75]],
    "id": 1
  }' | jq .
