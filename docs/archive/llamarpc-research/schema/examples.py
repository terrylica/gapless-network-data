#!/usr/bin/env python3
"""
Ethereum Network Metrics Calculator
Examples of deriving meaningful metrics from LlamaRPC/Ethereum block data
"""

import requests
from typing import Dict, List, Any
from datetime import datetime, timezone


class EthereumMetricsCollector:
    """Collect and calculate Ethereum network metrics using LlamaRPC"""

    def __init__(self, rpc_url: str = "https://eth.llamarpc.com"):
        self.rpc_url = rpc_url
        self.session = requests.Session()

    def _rpc_call(self, method: str, params: List[Any]) -> Dict:
        """Make JSON-RPC call to Ethereum node"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        response = self.session.post(self.rpc_url, json=payload)
        response.raise_for_status()
        return response.json()["result"]

    def get_latest_block(self, include_transactions: bool = False) -> Dict:
        """Fetch the latest block"""
        return self._rpc_call("eth_getBlockByNumber", ["latest", include_transactions])

    def get_block_by_number(self, block_number: int, include_transactions: bool = False) -> Dict:
        """Fetch a specific block by number"""
        return self._rpc_call("eth_getBlockByNumber", [hex(block_number), include_transactions])

    def get_fee_history(
        self,
        block_count: int = 5,
        newest_block: str = "latest",
        percentiles: List[int] = None
    ) -> Dict:
        """Fetch fee history for multiple blocks"""
        if percentiles is None:
            percentiles = [25, 50, 75]
        return self._rpc_call("eth_feeHistory", [hex(block_count), newest_block, percentiles])

    # ==================== BLOCK-LEVEL METRICS ====================

    def calculate_gas_metrics(self, block: Dict) -> Dict:
        """Calculate gas utilization metrics"""
        gas_limit = int(block["gasLimit"], 16)
        gas_used = int(block["gasUsed"], 16)

        return {
            "block_number": int(block["number"], 16),
            "gas_limit": gas_limit,
            "gas_used": gas_used,
            "gas_utilization_pct": (gas_used / gas_limit) * 100,
            "gas_available": gas_limit - gas_used,
            "base_fee_gwei": int(block["baseFeePerGas"], 16) / 1e9,
        }

    def calculate_transaction_metrics(self, block: Dict) -> Dict:
        """Calculate transaction-related metrics"""
        gas_used = int(block["gasUsed"], 16)
        tx_count = len(block["transactions"])

        return {
            "transaction_count": tx_count,
            "avg_gas_per_tx": gas_used / tx_count if tx_count > 0 else 0,
            "block_size_kb": int(block["size"], 16) / 1024,
            "block_size_mb": int(block["size"], 16) / 1_048_576,
        }

    def calculate_blob_metrics(self, block: Dict) -> Dict:
        """Calculate EIP-4844 blob metrics"""
        blob_gas_used = int(block.get("blobGasUsed", "0x0"), 16)
        excess_blob_gas = int(block.get("excessBlobGas", "0x0"), 16)
        max_blob_gas_per_block = 6 * 131072  # 6 blobs * 128KB each

        return {
            "blob_gas_used": blob_gas_used,
            "blob_gas_utilization_pct": (blob_gas_used / max_blob_gas_per_block) * 100,
            "excess_blob_gas": excess_blob_gas,
            "estimated_blob_count": blob_gas_used // 131072,
        }

    def calculate_withdrawal_metrics(self, block: Dict) -> Dict:
        """Calculate validator withdrawal metrics"""
        withdrawals = block.get("withdrawals", [])
        withdrawal_count = len(withdrawals)

        if withdrawal_count == 0:
            return {
                "withdrawal_count": 0,
                "total_eth_withdrawn": 0.0,
                "avg_withdrawal_eth": 0.0,
                "unique_recipients": 0,
            }

        # Amounts are in Gwei
        total_gwei = sum(int(w["amount"], 16) for w in withdrawals)
        total_eth = total_gwei / 1e9

        return {
            "withdrawal_count": withdrawal_count,
            "total_eth_withdrawn": total_eth,
            "avg_withdrawal_eth": total_eth / withdrawal_count,
            "unique_recipients": len(set(w["address"] for w in withdrawals)),
        }

    def calculate_timestamp_metrics(self, block: Dict, previous_block: Dict = None) -> Dict:
        """Calculate time-based metrics"""
        timestamp = int(block["timestamp"], 16)
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        metrics = {
            "timestamp_unix": timestamp,
            "timestamp_iso": dt.isoformat(),
            "block_datetime_utc": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        if previous_block:
            prev_timestamp = int(previous_block["timestamp"], 16)
            metrics["block_time_seconds"] = timestamp - prev_timestamp

        return metrics

    def get_builder_info(self, block: Dict) -> Dict:
        """Extract block builder/miner information"""
        extra_data_hex = block["extraData"][2:]  # Remove 0x prefix
        try:
            extra_data_text = bytes.fromhex(extra_data_hex).decode('utf-8', errors='ignore')
        except:
            extra_data_text = ""

        return {
            "builder_address": block["miner"],
            "builder_tag": extra_data_text.strip(),
            "extra_data_hex": block["extraData"],
        }

    # ==================== FEE MARKET METRICS ====================

    def calculate_fee_trends(self, fee_history: Dict) -> Dict:
        """Calculate fee market trends"""
        base_fees_gwei = [int(fee, 16) / 1e9 for fee in fee_history["baseFeePerGas"]]

        # The last element is the prediction for the next block
        current_base_fee = base_fees_gwei[-1]
        oldest_base_fee = base_fees_gwei[0]

        base_fee_change_pct = ((current_base_fee - oldest_base_fee) / oldest_base_fee) * 100

        return {
            "current_base_fee_gwei": current_base_fee,
            "min_base_fee_gwei": min(base_fees_gwei),
            "max_base_fee_gwei": max(base_fees_gwei),
            "avg_base_fee_gwei": sum(base_fees_gwei) / len(base_fees_gwei),
            "base_fee_change_pct": base_fee_change_pct,
            "base_fee_trend": "increasing" if base_fee_change_pct > 5 else "decreasing" if base_fee_change_pct < -5 else "stable",
        }

    def calculate_priority_fee_metrics(self, fee_history: Dict) -> Dict:
        """Calculate priority fee percentile metrics"""
        # rewards[i][0] = 25th percentile, [i][1] = 50th, [i][2] = 75th
        latest_block_rewards = fee_history["reward"][-1]  # Most recent block

        priority_25th = int(latest_block_rewards[0], 16) / 1e9
        priority_50th = int(latest_block_rewards[1], 16) / 1e9
        priority_75th = int(latest_block_rewards[2], 16) / 1e9

        return {
            "priority_fee_25th_gwei": priority_25th,
            "priority_fee_50th_gwei": priority_50th,
            "priority_fee_75th_gwei": priority_75th,
        }

    def calculate_congestion_metrics(self, fee_history: Dict) -> Dict:
        """Calculate network congestion indicators"""
        gas_ratios = fee_history["gasUsedRatio"]
        blob_ratios = fee_history["blobGasUsedRatio"]

        avg_gas_utilization = sum(gas_ratios) / len(gas_ratios)
        avg_blob_utilization = sum(blob_ratios) / len(blob_ratios) if blob_ratios else 0

        # Congestion level classification
        if avg_gas_utilization < 0.5:
            congestion = "low"
        elif avg_gas_utilization < 0.8:
            congestion = "moderate"
        else:
            congestion = "high"

        return {
            "avg_gas_utilization_pct": avg_gas_utilization * 100,
            "avg_blob_utilization_pct": avg_blob_utilization * 100,
            "congestion_level": congestion,
            "recent_gas_trend": "increasing" if gas_ratios[-1] > gas_ratios[0] else "decreasing",
        }

    def get_recommended_gas_prices(self, fee_history: Dict) -> Dict:
        """Get recommended gas prices for different urgency levels"""
        current_base_fee = int(fee_history["baseFeePerGas"][-1], 16)  # Next block prediction
        latest_priorities = fee_history["reward"][-1]

        # Priority fees in wei
        slow_priority = int(latest_priorities[0], 16)      # 25th percentile
        standard_priority = int(latest_priorities[1], 16)  # 50th percentile
        fast_priority = int(latest_priorities[2], 16)      # 75th percentile

        return {
            "slow_max_fee_gwei": (current_base_fee + slow_priority) / 1e9,
            "slow_priority_fee_gwei": slow_priority / 1e9,
            "standard_max_fee_gwei": (current_base_fee + standard_priority) / 1e9,
            "standard_priority_fee_gwei": standard_priority / 1e9,
            "fast_max_fee_gwei": (current_base_fee + fast_priority) / 1e9,
            "fast_priority_fee_gwei": fast_priority / 1e9,
        }

    # ==================== TRANSACTION-LEVEL METRICS ====================

    def calculate_tx_gas_metrics(self, tx: Dict, block: Dict) -> Dict:
        """Calculate gas metrics for a specific transaction"""
        block_base_fee = int(block["baseFeePerGas"], 16)
        tx_type = int(tx["type"], 16)

        if tx_type == 2:  # EIP-1559
            max_fee = int(tx["maxFeePerGas"], 16)
            max_priority = int(tx["maxPriorityFeePerGas"], 16)

            # Effective priority fee is the minimum of:
            # 1. max_priority_fee_per_gas
            # 2. max_fee_per_gas - base_fee
            effective_priority = min(max_priority, max_fee - block_base_fee)
            effective_gas_price = block_base_fee + effective_priority

            return {
                "tx_type": "EIP-1559",
                "max_fee_per_gas_gwei": max_fee / 1e9,
                "max_priority_fee_gwei": max_priority / 1e9,
                "effective_gas_price_gwei": effective_gas_price / 1e9,
                "effective_priority_fee_gwei": effective_priority / 1e9,
            }
        else:  # Legacy (type 0) or EIP-2930 (type 1)
            gas_price = int(tx["gasPrice"], 16)
            return {
                "tx_type": "Legacy" if tx_type == 0 else "EIP-2930",
                "gas_price_gwei": gas_price / 1e9,
            }

    def calculate_tx_value_metrics(self, tx: Dict) -> Dict:
        """Calculate value transfer metrics"""
        value_wei = int(tx["value"], 16)
        value_eth = value_wei / 1e18

        return {
            "value_wei": value_wei,
            "value_eth": value_eth,
            "is_contract_call": tx["to"] is not None and value_eth == 0,
            "is_eth_transfer": value_eth > 0,
        }

    # ==================== COMPREHENSIVE REPORTS ====================

    def generate_block_report(self, block_number: int = None) -> Dict:
        """Generate comprehensive metrics report for a block"""
        if block_number is None:
            block = self.get_latest_block(include_transactions=False)
            block_number = int(block["number"], 16)
        else:
            block = self.get_block_by_number(block_number, include_transactions=False)

        # Get previous block for block time calculation
        previous_block = self.get_block_by_number(block_number - 1, include_transactions=False)

        return {
            "block_number": block_number,
            "gas_metrics": self.calculate_gas_metrics(block),
            "transaction_metrics": self.calculate_transaction_metrics(block),
            "blob_metrics": self.calculate_blob_metrics(block),
            "withdrawal_metrics": self.calculate_withdrawal_metrics(block),
            "timestamp_metrics": self.calculate_timestamp_metrics(block, previous_block),
            "builder_info": self.get_builder_info(block),
        }

    def generate_fee_market_report(self, block_count: int = 10) -> Dict:
        """Generate comprehensive fee market report"""
        fee_history = self.get_fee_history(block_count=block_count)

        return {
            "blocks_analyzed": block_count,
            "oldest_block": int(fee_history["oldestBlock"], 16),
            "fee_trends": self.calculate_fee_trends(fee_history),
            "priority_fees": self.calculate_priority_fee_metrics(fee_history),
            "congestion": self.calculate_congestion_metrics(fee_history),
            "recommended_gas_prices": self.get_recommended_gas_prices(fee_history),
        }


def demo_basic_metrics():
    """Demonstrate basic metric collection"""
    print("=== Ethereum Network Metrics Demo ===\n")

    collector = EthereumMetricsCollector()

    # Get latest block metrics
    print("Fetching latest block metrics...")
    block_report = collector.generate_block_report()

    print(f"\n📦 Block #{block_report['block_number']}")
    print(f"   Timestamp: {block_report['timestamp_metrics']['block_datetime_utc']}")
    print(f"   Block Time: {block_report['timestamp_metrics'].get('block_time_seconds', 'N/A')} seconds")

    gas = block_report['gas_metrics']
    print(f"\n⛽ Gas Metrics:")
    print(f"   Utilization: {gas['gas_utilization_pct']:.2f}%")
    print(f"   Base Fee: {gas['base_fee_gwei']:.3f} gwei")
    print(f"   Gas Used: {gas['gas_used']:,} / {gas['gas_limit']:,}")

    tx = block_report['transaction_metrics']
    print(f"\n📝 Transactions:")
    print(f"   Count: {tx['transaction_count']}")
    print(f"   Avg Gas/Tx: {tx['avg_gas_per_tx']:,.0f}")
    print(f"   Block Size: {tx['block_size_kb']:.2f} KB")

    blob = block_report['blob_metrics']
    print(f"\n🫧 Blob Data (EIP-4844):")
    print(f"   Blob Utilization: {blob['blob_gas_utilization_pct']:.2f}%")
    print(f"   Estimated Blobs: {blob['estimated_blob_count']}")

    withdrawal = block_report['withdrawal_metrics']
    print(f"\n💰 Withdrawals:")
    print(f"   Count: {withdrawal['withdrawal_count']}")
    print(f"   Total ETH: {withdrawal['total_eth_withdrawn']:.6f}")

    builder = block_report['builder_info']
    print(f"\n🏗️  Builder:")
    print(f"   Address: {builder['builder_address']}")
    print(f"   Tag: {builder['builder_tag']}")

    # Get fee market metrics
    print("\n\nFetching fee market analysis...")
    fee_report = collector.generate_fee_market_report(block_count=20)

    trends = fee_report['fee_trends']
    print(f"\n📈 Fee Trends ({fee_report['blocks_analyzed']} blocks):")
    print(f"   Current Base Fee: {trends['current_base_fee_gwei']:.3f} gwei")
    print(f"   Trend: {trends['base_fee_trend']} ({trends['base_fee_change_pct']:+.2f}%)")
    print(f"   Range: {trends['min_base_fee_gwei']:.3f} - {trends['max_base_fee_gwei']:.3f} gwei")

    priority = fee_report['priority_fees']
    print(f"\n💎 Priority Fees (Latest Block):")
    print(f"   25th percentile: {priority['priority_fee_25th_gwei']:.3f} gwei")
    print(f"   50th percentile: {priority['priority_fee_50th_gwei']:.3f} gwei")
    print(f"   75th percentile: {priority['priority_fee_75th_gwei']:.3f} gwei")

    congestion = fee_report['congestion']
    print(f"\n🚦 Network Congestion:")
    print(f"   Level: {congestion['congestion_level'].upper()}")
    print(f"   Avg Gas Utilization: {congestion['avg_gas_utilization_pct']:.2f}%")
    print(f"   Recent Trend: {congestion['recent_gas_trend']}")

    gas_prices = fee_report['recommended_gas_prices']
    print(f"\n⚡ Recommended Gas Prices:")
    print(f"   🐢 Slow:     {gas_prices['slow_max_fee_gwei']:.3f} gwei (base + {gas_prices['slow_priority_fee_gwei']:.3f})")
    print(f"   🚶 Standard: {gas_prices['standard_max_fee_gwei']:.3f} gwei (base + {gas_prices['standard_priority_fee_gwei']:.3f})")
    print(f"   🚀 Fast:     {gas_prices['fast_max_fee_gwei']:.3f} gwei (base + {gas_prices['fast_priority_fee_gwei']:.3f})")


if __name__ == "__main__":
    demo_basic_metrics()
