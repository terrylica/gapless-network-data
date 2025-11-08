#!/usr/bin/env python3
"""
Timeline Calculator for Blockchain Data Collection

Calculate collection timeline given rate limits (RPS or compute units).

Usage:
    # RPS-based calculation
    python calculate_timeline.py --blocks 13000000 --rps 5.79

    # Compute unit calculation
    python calculate_timeline.py --blocks 13000000 --cu-per-month 300000000 --cu-per-request 20
"""

import argparse


def calculate_from_rps(total_blocks: int, rps: float) -> dict:
    """Calculate timeline from requests per second."""
    seconds = total_blocks / rps
    minutes = seconds / 60
    hours = seconds / 3600
    days = seconds / 86400

    return {
        "total_blocks": total_blocks,
        "rps": rps,
        "seconds": seconds,
        "minutes": minutes,
        "hours": hours,
        "days": days,
    }


def calculate_from_compute_units(
    total_blocks: int,
    cu_per_month: int,
    cu_per_request: int
) -> dict:
    """Calculate timeline from compute units."""
    monthly_requests = cu_per_month / cu_per_request
    daily_requests = monthly_requests / 30
    sustainable_rps = daily_requests / 86400

    # Use RPS calculation
    timeline = calculate_from_rps(total_blocks, sustainable_rps)
    timeline["cu_per_month"] = cu_per_month
    timeline["cu_per_request"] = cu_per_request
    timeline["monthly_requests"] = monthly_requests
    timeline["daily_requests"] = daily_requests

    return timeline


def format_timeline(result: dict) -> str:
    """Format timeline results for display."""
    output = []
    output.append("=" * 70)
    output.append("Blockchain Data Collection Timeline")
    output.append("=" * 70)

    output.append(f"\nInput:")
    output.append(f"  Total blocks: {result['total_blocks']:,}")

    if "cu_per_month" in result:
        output.append(f"  Compute units/month: {result['cu_per_month']:,}")
        output.append(f"  CU per request: {result['cu_per_request']}")
        output.append(f"\nCalculated:")
        output.append(f"  Monthly requests: {result['monthly_requests']:,.0f}")
        output.append(f"  Daily requests: {result['daily_requests']:,.0f}")
        output.append(f"  Sustainable RPS: {result['rps']:.2f}")
    else:
        output.append(f"  Requests per second: {result['rps']:.2f}")

    output.append(f"\nTimeline:")
    output.append(f"  {result['seconds']:,.0f} seconds")
    output.append(f"  {result['minutes']:,.0f} minutes")
    output.append(f"  {result['hours']:,.1f} hours")
    output.append(f"  {result['days']:.1f} days")

    output.append("\n" + "=" * 70)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate blockchain data collection timeline"
    )
    parser.add_argument(
        "--blocks",
        type=int,
        required=True,
        help="Total number of blocks to collect"
    )

    # RPS-based calculation
    parser.add_argument(
        "--rps",
        type=float,
        help="Requests per second (sustainable rate)"
    )

    # Compute unit calculation
    parser.add_argument(
        "--cu-per-month",
        type=int,
        help="Compute units available per month (e.g., 300000000 for Alchemy)"
    )
    parser.add_argument(
        "--cu-per-request",
        type=int,
        help="Compute units per request (e.g., 20 for eth_getBlockByNumber)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.rps and (args.cu_per_month or args.cu_per_request):
        parser.error("Cannot specify both --rps and compute unit parameters")

    if not args.rps and not (args.cu_per_month and args.cu_per_request):
        parser.error("Must specify either --rps or both --cu-per-month and --cu-per-request")

    # Calculate timeline
    if args.rps:
        result = calculate_from_rps(args.blocks, args.rps)
    else:
        result = calculate_from_compute_units(
            args.blocks,
            args.cu_per_month,
            args.cu_per_request
        )

    # Display results
    print(format_timeline(result))


if __name__ == "__main__":
    main()
