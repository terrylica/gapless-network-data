#!/bin/bash
# Test rate limiting by sending rapid requests
echo "Testing LlamaRPC rate limits..."
echo "Sending 60 requests in rapid succession (should exceed 50 RPS free tier limit)"
echo ""

success=0
failed=0
start_time=$(date +%s)

for i in {1..60}; do
    response=$(curl -X POST https://eth.llamarpc.com \
      -H "Content-Type: application/json" \
      --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":$i}" \
      -s -w "\n%{http_code}" 2>&1)
    
    http_code=$(echo "$response" | tail -1)
    
    if [ "$http_code" = "200" ]; then
        ((success++))
    else
        ((failed++))
        echo "Request $i failed with HTTP $http_code"
    fi
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo "Results:"
echo "Total requests: 60"
echo "Successful: $success"
echo "Failed: $failed"
echo "Duration: ${duration}s"
echo "Rate: $((60 / duration)) RPS"
