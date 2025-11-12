#!/usr/bin/env python3
"""
Example: Fetching historical Ethereum block data using web3.py with LlamaRPC.

This demonstrates collecting historical blockchain data for feature engineering,
similar to the gapless-network-data package architecture.
"""
# /// script
# dependencies = ["web3>=7.0.0", "pandas>=2.0.0"]
# ///

from datetime import datetime
from web3 import Web3
import pandas as pd

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def fetch_block_range(start_block: int, end_block: int) -> pd.DataFrame:
    """
    Fetch a range of blocks and return as DataFrame.

    Args:
        start_block: Starting block number
        end_block: Ending block number (inclusive)

    Returns:
        DataFrame with block data indexed by timestamp
    """
    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    if not w3.is_connected():
        raise ConnectionError("Failed to connect to Ethereum RPC")

    print(f"Fetching blocks {start_block} to {end_block}...")

    blocks_data = []
    for block_num in range(start_block, end_block + 1):
        block = w3.eth.get_block(block_num, full_transactions=False)

        blocks_data.append({
            'block_number': block['number'],
            'timestamp': datetime.fromtimestamp(block['timestamp']),
            'tx_count': len(block['transactions']),
            'gas_used': block['gasUsed'],
            'gas_limit': block['gasLimit'],
            'base_fee_per_gas': block.get('baseFeePerGas', 0),  # EIP-1559 (London fork)
            'difficulty': block.get('difficulty', 0),
            'size': block['size'],
            'hash': block['hash'].hex()
        })

        if (block_num - start_block + 1) % 10 == 0:
            print(f"  Fetched {block_num - start_block + 1} blocks...")

    # Create DataFrame with DatetimeIndex (gapless-crypto-data pattern)
    df = pd.DataFrame(blocks_data)
    df = df.set_index('timestamp')

    return df

def calculate_network_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate network congestion features from block data.

    Similar to cross-domain feature engineering in gapless-crypto-data.
    """
    # Gas utilization percentage
    df['gas_utilization'] = (df['gas_used'] / df['gas_limit']) * 100

    # Base fee change rate (proxy for congestion)
    df['base_fee_change'] = df['base_fee_per_gas'].pct_change()

    # Transaction density (tx per second, assuming ~12s block time)
    df['tx_per_second'] = df['tx_count'] / 12.0

    # Rolling averages (60 blocks ≈ 12 minutes)
    df['gas_utilization_60b_ma'] = df['gas_utilization'].rolling(60).mean()
    df['tx_count_60b_ma'] = df['tx_count'].rolling(60).mean()

    return df

def main():
    """Demonstrate historical data collection."""
    # Fetch recent blocks (small sample to avoid rate limits)
    # Block 15000000 was mined on June 21, 2022
    start_block = 15000000
    end_block = 15000050  # 50 blocks ≈ 10 minutes

    df = fetch_block_range(start_block, end_block)

    # Calculate features
    df = calculate_network_features(df)

    print(f"\n{'='*60}")
    print("Block Data Sample:")
    print(f"{'='*60}")
    print(df.head(10).to_string())

    print(f"\n{'='*60}")
    print("Network Features Summary:")
    print(f"{'='*60}")
    print(df[['gas_utilization', 'base_fee_per_gas', 'tx_per_second']].describe())

    print(f"\n{'='*60}")
    print("High Congestion Periods (gas utilization > 90%):")
    print(f"{'='*60}")
    high_congestion = df[df['gas_utilization'] > 90]
    if not high_congestion.empty:
        print(high_congestion[['block_number', 'gas_utilization', 'tx_count', 'base_fee_per_gas']])
    else:
        print("No high congestion periods in this sample")

    # Save to parquet (gapless-crypto-data output format)
    output_file = "/tmp/llamarpc-sdk-research/ethereum_blocks_sample.parquet"
    df.to_parquet(output_file, compression='snappy')
    print(f"\n✓ Data saved to {output_file}")

if __name__ == "__main__":
    main()
