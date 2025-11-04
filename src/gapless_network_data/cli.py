"""
Command-line interface for gapless-network-data.
"""

import sys
from datetime import datetime


def main() -> None:
    """
    Main CLI entry point.

    Commands:
        collect: Collect mempool data for a time range
        stream: Stream live mempool data
        version: Show version information
    """
    if len(sys.argv) < 2:
        print("Usage: gapless-network-data <command> [options]")
        print()
        print("Commands:")
        print("  collect  Collect mempool data for a time range")
        print("  stream   Stream live mempool data")
        print("  version  Show version information")
        sys.exit(1)

    command = sys.argv[1]

    if command == "version":
        from gapless_network_data import __version__

        print(f"gapless-network-data v{__version__}")
    elif command == "collect":
        print("collect command: Implementation pending")
        print("Use Python API for now:")
        print()
        print("  import gapless_network_data as gmd")
        print('  df = gmd.fetch_snapshots(start="...", end="...")')
    elif command == "stream":
        print("stream command: Implementation pending")
        print("Use Python API for now:")
        print()
        print("  import gapless_network_data as gmd")
        print("  snapshot = gmd.get_latest_snapshot()")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
