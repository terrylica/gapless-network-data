#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "pandas"]
# ///

"""
Fetch historical OHLCV data for Alternative L1 blockchains from Binance API.

Usage:
    uv run fetch_binance_historical.py
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json


def fetch_binance_klines(symbol: str, interval: str, start_time_ms: int, limit: int = 1000) -> list:
    """
    Fetch OHLCV klines from Binance public API.

    Args:
        symbol: Trading pair (e.g., 'SOLUSDT')
        interval: Candle interval (e.g., '1m', '5m', '15m')
        start_time_ms: Start time in milliseconds since epoch
        limit: Number of candles to fetch (max 1000)

    Returns:
        List of OHLCV candles
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time_ms,
        "limit": limit
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def klines_to_dataframe(klines: list) -> pd.DataFrame:
    """Convert Binance klines to pandas DataFrame."""
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)

    # Convert price/volume to numeric
    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Set index
    df.set_index('timestamp', inplace=True)

    # Keep only essential columns
    df = df[['open', 'high', 'low', 'close', 'volume', 'trades']]

    return df


def fetch_historical_range(symbol: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical data for a date range with automatic pagination.

    Args:
        symbol: Trading pair (e.g., 'SOLUSDT')
        interval: Candle interval (e.g., '1m', '5m', '15m')
        start_date: Start date (ISO format: 'YYYY-MM-DD')
        end_date: End date (ISO format: 'YYYY-MM-DD')

    Returns:
        DataFrame with OHLCV data
    """
    # Parse dates
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    start_time_ms = int(start_dt.timestamp() * 1000)
    end_time_ms = int(end_dt.timestamp() * 1000)

    # Interval to milliseconds mapping
    interval_ms_map = {
        '1m': 60000,
        '3m': 180000,
        '5m': 300000,
        '15m': 900000,
        '30m': 1800000,
        '1h': 3600000,
        '2h': 7200000,
        '4h': 14400000,
        '6h': 21600000,
        '12h': 43200000,
        '1d': 86400000,
    }

    interval_ms = interval_ms_map.get(interval)
    if not interval_ms:
        raise ValueError(f"Unsupported interval: {interval}")

    all_klines = []
    current_time = start_time_ms

    print(f"Fetching {symbol} {interval} from {start_date} to {end_date}...")

    while current_time < end_time_ms:
        try:
            # Fetch batch
            klines = fetch_binance_klines(symbol, interval, current_time, limit=1000)

            if not klines:
                print("No more data available")
                break

            all_klines.extend(klines)

            # Update current time
            last_close_time = klines[-1][6]  # close_time is at index 6
            current_time = last_close_time + 1

            # Progress
            progress_pct = min(100, ((current_time - start_time_ms) / (end_time_ms - start_time_ms)) * 100)
            print(f"  Progress: {progress_pct:.1f}% ({len(all_klines)} candles)", end='\r')

            # Rate limiting: Conservative 1 request/second
            time.sleep(1)

            # Break if we got less than requested (end of available data)
            if len(klines) < 1000:
                break

        except requests.exceptions.RequestException as e:
            print(f"\nError fetching data: {e}")
            print("Waiting 5 seconds before retry...")
            time.sleep(5)
            continue

    print(f"\nFetched {len(all_klines)} total candles")

    # Convert to DataFrame
    if all_klines:
        df = klines_to_dataframe(all_klines)
        # Filter to exact date range
        df = df[(df.index >= start_dt) & (df.index < end_dt)]
        return df
    else:
        return pd.DataFrame()


def main():
    """Example usage: Fetch data for multiple alt-L1 tokens."""

    # Alternative L1 tokens on Binance
    alt_l1_symbols = [
        "SOLUSDT",   # Solana
        "AVAXUSDT",  # Avalanche
        "ADAUSDT",   # Cardano
        "DOTUSDT",   # Polkadot
        "ATOMUSDT",  # Cosmos
        "NEARUSDT",  # Near
        "ALGOUSDT",  # Algorand
        "XTZUSDT",   # Tezos
    ]

    # Fetch 1-minute data for first week of 2022
    start_date = "2022-01-01"
    end_date = "2022-01-08"
    interval = "1m"

    results = {}

    for symbol in alt_l1_symbols[:3]:  # Limit to 3 for demo
        print(f"\n{'='*60}")
        print(f"Processing {symbol}")
        print(f"{'='*60}")

        df = fetch_historical_range(symbol, interval, start_date, end_date)

        if not df.empty:
            results[symbol] = df

            # Summary
            print(f"\nSummary for {symbol}:")
            print(f"  Total rows: {len(df)}")
            print(f"  Date range: {df.index[0]} to {df.index[-1]}")
            print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
            print(f"  Total volume: {df['volume'].sum():,.0f}")

            # Save to CSV
            output_file = f"/tmp/altl1-research/{symbol}_{interval}_{start_date}_to_{end_date}.csv"
            df.to_csv(output_file)
            print(f"  Saved to: {output_file}")

        time.sleep(2)  # Pause between symbols

    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")
    print(f"Processed {len(results)} symbols")


if __name__ == "__main__":
    main()
