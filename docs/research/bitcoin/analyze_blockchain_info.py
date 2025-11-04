#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

import requests
from datetime import datetime

charts = [
    "market-price",
    "transactions-per-second", 
    "mempool-size",
    "avg-block-size",
    "n-transactions",
    "hash-rate",
    "difficulty",
    "miners-revenue",
    "transaction-fees",
    "cost-per-transaction",
    "n-unique-addresses",
    "n-transactions-total",
    "output-volume",
    "estimated-transaction-volume",
    "trade-volume"
]

print("=== Blockchain.info Charts API Analysis ===\n")

# Test with 3-year historical data
for chart in charts:
    try:
        url = f"https://api.blockchain.info/charts/{chart}?timespan=3years&sampled=false&format=json&cors=true"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            values = data.get('values', [])
            
            if len(values) > 0:
                first_ts = values[0]['x']
                last_ts = values[-1]['x']
                
                first_date = datetime.fromtimestamp(first_ts).strftime('%Y-%m-%d %H:%M:%S')
                last_date = datetime.fromtimestamp(last_ts).strftime('%Y-%m-%d %H:%M:%S')
                
                # Calculate frequency
                time_diff = last_ts - first_ts
                avg_interval = time_diff / len(values) if len(values) > 1 else 0
                
                print(f"Chart: {chart}")
                print(f"  Points: {len(values)}")
                print(f"  Date range: {first_date} to {last_date}")
                print(f"  Avg interval: {avg_interval:.1f}s ({avg_interval/60:.2f}m)")
                print(f"  Unit: {data.get('unit', 'N/A')}")
                print()
        else:
            print(f"Chart: {chart} - HTTP {resp.status_code}")
            print()
    except Exception as e:
        print(f"Chart: {chart} - Error: {str(e)[:80]}")
        print()

# Test timespan parameter
print("\n=== Testing different timespan parameters ===")
for timespan in ["1weeks", "1months", "1years", "3years", "all"]:
    try:
        url = f"https://api.blockchain.info/charts/mempool-size?timespan={timespan}&sampled=false&format=json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            values = data.get('values', [])
            if len(values) > 0:
                time_diff = values[-1]['x'] - values[0]['x']
                avg_interval = time_diff / len(values) if len(values) > 1 else 0
                print(f"{timespan:12s}: {len(values):6d} points, {avg_interval/60:6.2f}m avg interval")
    except Exception as e:
        print(f"{timespan:12s}: Error")
