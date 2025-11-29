---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Data Collection Guide

**Status**: 🚧 Pending Phase 1 implementation

This document will provide comprehensive guidance for collecting blockchain network data using the CLI.

## Planned Content

### CLI Usage

#### Collect Command

```bash
# Ethereum block data collection (PRIMARY - 12s intervals)
gapless-network-data collect \
    --chain ethereum \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --output-dir ./data

# Bitcoin mempool data collection (SECONDARY - 5min intervals)
gapless-network-data collect \
    --chain bitcoin \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --output-dir ./data
```

#### Stream Command

```bash
# Live Ethereum block streaming
gapless-network-data stream \
    --chain ethereum \
    --output-dir ./data

# Live Bitcoin mempool streaming
gapless-network-data stream \
    --chain bitcoin \
    --output-dir ./data
```

#### Validate Command

```bash
# Validate collected data
gapless-network-data validate \
    --input-dir ./data \
    --chain ethereum \
    --report-file validation_report.parquet
```

### Collection Modes

- **Historical Collection**: Backfill past data with gap detection
- **Live Streaming**: Real-time collection with automatic reconnection
- **Hybrid Mode**: Live + backfill gaps on-the-fly

### Configuration

- Environment variables (LLAMARPC_URL, MEMPOOL_SPACE_URL)
- Config file format (.gapless-network-data.yaml)
- Rate limiting configuration

### Best Practices

- Recommended collection intervals per chain
- Output directory organization
- Handling API rate limits
- Monitoring collection health

### Troubleshooting

- Common errors and solutions
- Gap detection and recovery
- API endpoint failures

---

## Current Quick Start

Until this document is completed, refer to:

- [README.md](/README.md) - CLI quick start section (lines 66-87)
- [CLAUDE.md](/CLAUDE.md) - Data collection patterns

**Example from README.md**:

```bash
# Collect Ethereum block data
gapless-network-data collect \
    --chain ethereum \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --output-dir ./data

# Stream live Ethereum blocks
gapless-network-data stream \
    --chain ethereum \
    --output-dir ./data
```

---

**Related Documentation**:

- [Python API Reference](/docs/guides/python-api.md) - Programmatic collection
- [Data Format Specification](/docs/architecture/DATA_FORMAT.md) - Output schemas

**This document will be completed during Phase 1 implementation.**
