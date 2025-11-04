#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

import requests
import json
from datetime import datetime

# Test different time periods
endpoints = {
    "1w": "https://mempool.space/api/v1/statistics/1w",
    "1m": "https://mempool.space/api/v1/statistics/1m",
    "3m": "https://mempool.space/api/v1/statistics/3m",
    "6m": "https://mempool.space/api/v1/statistics/6m",
    "1y": "https://mempool.space/api/v1/statistics/1y",
    "2y": "https://mempool.space/api/v1/statistics/2y",
    "3y": "https://mempool.space/api/v1/statistics/3y",
}

print("=== Mempool.space Statistics Endpoint Analysis ===\n")

for period, url in endpoints.items():
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            count = len(data)
            
            if count > 0:
                # Get first and last timestamps
                first_ts = data[0].get('added', data[0].get('timestamp', 0))
                last_ts = data[-1].get('added', data[-1].get('timestamp', 0))
                
                first_date = datetime.fromtimestamp(first_ts).strftime('%Y-%m-%d %H:%M:%S')
                last_date = datetime.fromtimestamp(last_ts).strftime('%Y-%m-%d %H:%M:%S')
                
                # Calculate frequency
                time_diff = last_ts - first_ts
                avg_interval = time_diff / count if count > 1 else 0
                
                print(f"Period: {period}")
                print(f"  Data points: {count}")
                print(f"  Date range: {first_date} to {last_date}")
                print(f"  Avg interval: {avg_interval:.1f} seconds ({avg_interval/60:.2f} minutes)")
                print(f"  Sample fields: {list(data[0].keys())}")
                print()
        else:
            print(f"Period: {period} - HTTP {resp.status_code}")
            print()
    except Exception as e:
        print(f"Period: {period} - Error: {e}")
        print()

print("\n=== Sample data point (1w) ===")
resp = requests.get(endpoints["1w"])
data = resp.json()
print(json.dumps(data[0], indent=2))
