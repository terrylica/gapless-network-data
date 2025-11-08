# LittleBlack Hardware Assessment for Ethereum Archive Node

**Assessment Date**: 2025-11-06
**Machine**: littleblack (172.25.236.1 via ZeroTier)
**User**: kab
**Purpose**: Can this machine run Erigon v3 archive node?

---

## Hardware Specifications

### CPU ✅ EXCELLENT
```
Model: Intel Core i9-9900K @ 3.60GHz
Cores: 8 physical (16 logical with hyperthreading)
Requirement: 8-12 cores
Status: ✅ PASS (meets requirement)
```

### RAM ⚠️ BORDERLINE
```
Total: 62GB
Available: 56GB
Requirement: 64GB minimum (128GB recommended)
Status: ⚠️ MARGINAL (2GB below minimum, but might work)
```

### Storage ❌ INSUFFICIENT
```
NVMe (nvme0n1): 953.9GB total, 549GB available
SATA SSD (sda): 915GB total, 173GB available
Combined Available: 722GB

Requirement: 2TB for full archive node
Status: ❌ INSUFFICIENT (1.3TB short of requirement)
```

**Critical Issue**: Erigon requires NVMe for main datadir, but your NVMe only has 549GB free. The SATA SSD is too slow for Erigon's intensive I/O operations.

### GPU (Informational)
```
Model: NVIDIA GeForce RTX 2080 Ti
Status: ℹ️ Not used (Ethereum sync is CPU+disk intensive)
```

---

## What CAN You Do on LittleBlack?

### Option 1: Run Ethereum ETL with RPC ✅ RECOMMENDED

**What it does**: Fetch historical blocks via RPC and store locally

**Why it works**:
- Minimal storage (13M blocks = ~100GB compressed)
- Works with your current 549GB NVMe
- Can use 1RPC (77 RPS) or dRPC (100 RPS)
- No need for full 2TB archive

**Timeline**:
```bash
# Using Cryo + 1RPC
cryo blocks --blocks 11560000:24000000 \
            --rpc https://1rpc.io/eth \
            --output-dir /path/to/nvme

# Storage needed: ~100GB
# Timeline: 1.9 days (77 RPS sustained)
# Available: 549GB (plenty of space)
```

### Option 2: Pruned Archive Node ⚠️ EXPERIMENTAL

**What it does**: Run Erigon with pruning enabled

**Storage requirement**: ~1TB (vs 2TB full)

**Limitations**:
- May not have all historical state
- Some queries might fail
- Not officially recommended

**Command**:
```bash
erigon --datadir=/path/to/nvme \
       --prune=htc \
       --prune.h.older=90000
```

### Option 3: Upgrade Storage ✅ BEST LONG-TERM

**What to buy**: 2TB+ NVMe SSD

**Cost**: ~$150-250 for 2TB NVMe

**Benefit**: Run full Erigon archive node
- 18-hour sync (one-time)
- Unlimited queries (no rate limits)
- Complete control

---

## What You CANNOT Do on LittleBlack (Without Upgrades)

❌ **Full Erigon Archive Node** - Needs 2TB NVMe (you have 549GB)
❌ **Reth Archive Node** - Same storage requirement (2-3TB)
❌ **Geth Archive Node** - Needs ~2TB minimum

---

## Recommended Approach for Your Use Case

**Goal**: Get 13M Ethereum blocks as fast as possible

**BEST Strategy**: Hybrid approach

### Phase 1: Immediate (Today) - Use Your Mac + Cloud RPC
```bash
# On your MacBook M3 Max
mkdir ~/ethereum_data
cd ~/ethereum_data

# Install Cryo
pip install cryo

# Start downloading via 1RPC (fastest public endpoint)
cryo blocks --blocks 11560000:24000000 \
            --rpc https://1rpc.io/eth \
            --output-dir ./blocks

# Timeline: 1.9 days
# Storage: ~100GB (your Mac has plenty)
# No rate limits to manage (Cryo handles it)
```

### Phase 2: Transfer to LittleBlack (After Download)
```bash
# Copy data from Mac to LittleBlack
rsync -avz --progress ~/ethereum_data/ \
      littleblack:/path/to/nvme/ethereum_data/

# Load into DuckDB on LittleBlack for fast queries
```

### Phase 3: Long-term (Optional) - Upgrade LittleBlack
```
Buy: 2TB NVMe SSD (~$200)
Install: Replace or add to littleblack
Benefit: Run full Erigon node for unlimited future queries
```

---

## Alternative: Google BigQuery (Fastest)

**If you have Google Cloud access**:

```python
from google.cloud import bigquery

client = bigquery.Client()

query = """
SELECT
    number AS block_number,
    timestamp,
    base_fee_per_gas AS baseFeePerGas,
    gas_used AS gasUsed,
    gas_limit AS gasLimit,
    transaction_count
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
"""

df = client.query(query).to_dataframe()
df.to_parquet('ethereum_blocks.parquet')
```

**Timeline**: <1 hour (vs 1.9 days with RPC)
**Cost**: FREE (within BigQuery free tier)
**Storage**: Download to your Mac, then transfer to LittleBlack

---

## Summary

### Your LittleBlack Machine:
- ✅ **CPU**: Excellent (i9-9900K, 16 threads)
- ⚠️ **RAM**: Borderline (62GB vs 64GB required)
- ❌ **Storage**: Insufficient (722GB vs 2TB required)

### What You Should Do:
1. **TODAY**: Use Cryo + 1RPC on your Mac to download blocks (1.9 days)
2. **OR**: Use Google BigQuery for <1 hour download
3. **TRANSFER**: Move data to LittleBlack for processing
4. **LATER**: Consider 2TB NVMe upgrade (~$200) for full node capability

### Do NOT Try:
- Running full Erigon archive node (need 2TB NVMe)
- Syncing directly on LittleBlack (will run out of space)

---

## Open Source Tools Available

These tools will work on BOTH your Mac and LittleBlack:

### 1. Cryo (Recommended - Fastest)
```bash
# Rust-based, parallel fetching
https://github.com/paradigmxyz/cryo
pip install cryo

cryo blocks --blocks 11560000:24000000 \
            --rpc https://1rpc.io/eth \
            --output-dir ./data
```

### 2. Ethereum ETL (Most Mature)
```bash
# Python-based, battle-tested
https://github.com/blockchain-etl/ethereum-etl
pip install ethereum-etl

ethereumetl export_blocks_and_transactions \
  --start-block 11560000 \
  --end-block 24000000 \
  --provider-uri https://1rpc.io/eth \
  --blocks-output blocks.csv
```

### 3. TrueBlocks (Decentralized)
```bash
# Local indexing + caching
https://github.com/TrueBlocks/trueblocks-core
chifra blocks 11560000-24000000
```

---

## Cost Analysis

| Approach | Timeline | Cost | Pros | Cons |
|----------|----------|------|------|------|
| **Cryo + 1RPC (Mac)** | 1.9 days | FREE | Start now, no hardware | 1.9 days wait |
| **Google BigQuery** | <1 hour | FREE | Fastest | Needs GCP access |
| **Upgrade LittleBlack** | 18h sync | $200 | Unlimited future use | Upfront cost |
| **Alchemy Free Tier** | 26 days | FREE | Zero setup | Slowest |

---

## Next Steps

**Recommended**: Start with Cryo + 1RPC on your Mac TODAY while you decide on long-term strategy.

```bash
# On your MacBook M3 Max (right now):
pip install cryo
mkdir ~/ethereum_historical_data
cd ~/ethereum_historical_data

# Start the download (will take 1.9 days)
cryo blocks --blocks 11560000:24000000 \
            --rpc https://1rpc.io/eth \
            --output-dir ./blocks \
            --hex
```

Then in 2 days:
```bash
# Transfer to LittleBlack
rsync -avz --progress ~/ethereum_historical_data/ \
      littleblack:/home/kab/ethereum_data/
```

**Total Timeline**: 1.9 days + transfer time (~1-2 hours)
**Total Cost**: $0
**Storage Needed on Mac**: ~100GB (you have plenty)
**Storage Needed on LittleBlack**: ~100GB (you have 549GB available)
