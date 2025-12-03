"""
Command-line interface for gapless-network-data.
"""

import sys

# Minimum argv length: sys.argv[0] (program name) + sys.argv[1] (command)
MIN_ARGV_LENGTH = 2


def main() -> None:
    """
    Main CLI entry point.

    Commands:
        collect: Collect mempool data for a time range
        stream: Stream live mempool data
        schema: Schema management commands
        version: Show version information
    """
    if len(sys.argv) < MIN_ARGV_LENGTH:
        print("Usage: gapless-network-data <command> [options]")
        print()
        print("Commands:")
        print("  collect  Collect mempool data for a time range")
        print("  stream   Stream live mempool data")
        print("  schema   Schema management (generate-types, generate-ddl, validate, apply, doc)")
        print("  version  Show version information")
        sys.exit(1)

    command = sys.argv[1]

    if command == "version":
        from gapless_network_data import __version__

        print(f"gapless-network-data v{__version__}")
    elif command == "schema":
        from gapless_network_data.cli.schema import schema_command

        exit_code = schema_command(sys.argv[2:])
        sys.exit(exit_code)
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
