#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

import requests
from datetime import datetime, timedelta

print("=== Blockchair API Analysis ===\n")

# Test stats endpoint
print("1. Current stats:")
resp = requests.get("https://api.blockchair.com/bitcoin/stats")
if resp.status_code == 200:
    data = resp.json()['data']
    print(f"  Blocks: {data.get('blocks')}")
    print(f"  Mempool txs: {data.get('mempool_transactions')}")
    print(f"  Mempool size: {data.get('mempool_size')} bytes")
    print(f"  Mempool TPS: {data.get('mempool_tps')}")
    print()

# Test blocks endpoint with dates
print("2. Testing historical blocks by date:")
dates = [
    "2025-11-03",
    "2024-01-01", 
    "2023-01-01",
    "2022-01-01"
]

for date in dates:
    try:
        url = f"https://api.blockchair.com/bitcoin/blocks?q=time({date})&limit=10"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data:
                blocks = data['data']
                print(f"  {date}: {len(blocks)} blocks found")
                if len(blocks) > 0:
                    first_block = blocks[0]
                    print(f"    Sample: height={first_block.get('id')}, time={first_block.get('time')}")
    except Exception as e:
        print(f"  {date}: Error - {str(e)[:50]}")
print()

# Test raw data endpoint
print("3. Testing raw data endpoints:")
endpoints = [
    "/bitcoin/raw/block/922000",
    "/bitcoin/mempool/transactions",
]

for endpoint in endpoints:
    url = f"https://api.blockchair.com{endpoint}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {endpoint}: Available")
            if 'data' in data:
                print(f"    Keys: {list(data['data'].keys())[:5]}")
        else:
            print(f"  {endpoint}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  {endpoint}: Error")
print()

# Check documentation for time-series
print("4. Checking context info:")
resp = requests.get("https://api.blockchair.com/bitcoin/stats")
if resp.status_code == 200:
    data = resp.json()
    if 'context' in data:
        context = data['context']
        print(f"  API version: {context.get('api_version')}")
        print(f"  Limit: {context.get('limit')}")
        print(f"  Request cost: {context.get('request_cost')}")

