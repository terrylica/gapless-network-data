---
version: "1.0.0"
last_updated: "2025-11-08"
---

# MotherDuck Credentials Management

## Overview

MotherDuck credentials are stored securely in Doppler and injected at runtime.

## Doppler Configuration

**Project**: `claude-config`
**Config**: `dev`
**Secret Name**: `MOTHERDUCK_TOKEN`

### Token Details

- **Token Name**: `terry_read_write_token_01`
- **Token Type**: `read_write` (full access)
- **Created**: 2025-11-08
- **Account Login**: terrylica GitHub account at motherduck.com

### Doppler Note

```
MotherDuck read/write token (terry_read_write_token_01).
Login: terrylica GitHub account at motherduck.com.
Created: 2025-11-08.
Token type: read_write.
Use with: export motherduck_token=$MOTHERDUCK_TOKEN
```

## Usage Patterns

### 1. Doppler CLI Injection (Recommended)

```bash
# Run any command with MotherDuck token injected
doppler run --project claude-config --config dev \
  --command='python your_script.py'
```

The script will automatically have `MOTHERDUCK_TOKEN` available as an environment variable.

### 2. Export to Shell Variable

```bash
# Export as motherduck_token (lowercase, DuckDB convention)
export motherduck_token=$(doppler secrets get MOTHERDUCK_TOKEN \
  --project claude-config --config dev --plain)

# Verify
echo "Token length: ${#motherduck_token}"
```

### 3. Python Script with Doppler

```python
import os
import duckdb

# Token automatically available when run via doppler
token = os.environ.get('MOTHERDUCK_TOKEN')

# DuckDB convention: use lowercase motherduck_token
os.environ['motherduck_token'] = token

# Connect to MotherDuck
conn = duckdb.connect('md:')
```

### 4. Direct Python Execution

For scripts that need the token directly:

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["duckdb"]
# ///

import os
import subprocess

# Get token from Doppler
token = subprocess.check_output([
    'doppler', 'secrets', 'get', 'MOTHERDUCK_TOKEN',
    '--project', 'claude-config',
    '--config', 'dev',
    '--plain'
], text=True).strip()

os.environ['motherduck_token'] = token

import duckdb
conn = duckdb.connect('md:')
```

## BigQuery Integration with MotherDuck

Complete workflow using Doppler-managed credentials:

```bash
# Set up Google Cloud authentication (one-time)
gcloud auth application-default login

# Run BigQuery → MotherDuck pipeline with Doppler
doppler run --project claude-config --config dev \
  --command='python scripts/bigquery_to_motherduck.py'
```

**Script example** (`scripts/bigquery_to_motherduck.py`):

```python
import os
from google.cloud import bigquery
import duckdb

# MotherDuck token injected by Doppler as MOTHERDUCK_TOKEN
os.environ['motherduck_token'] = os.environ['MOTHERDUCK_TOKEN']

# Query BigQuery
bq_client = bigquery.Client('my-gcp-project')
query = """
SELECT * FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
"""
pa_table = bq_client.query(query).to_arrow()

# Load to MotherDuck
conn = duckdb.connect('md:')
conn.sql("CREATE DATABASE IF NOT EXISTS gapless_network_data")
conn.sql("USE gapless_network_data")
conn.sql("CREATE OR REPLACE TABLE ethereum_blocks AS SELECT * FROM pa_table")
print(f"Loaded {len(pa_table)} rows to MotherDuck")
```

## Security Best Practices

1. ✅ **Never commit tokens** to git
2. ✅ **Use Doppler injection** instead of hardcoding
3. ✅ **Rotate tokens periodically** (recommended: 90 days)
4. ✅ **Use stdin for Doppler updates**: `echo -n 'token' | doppler secrets set`
5. ✅ **Document with notes**: Track token origin and purpose

## Token Rotation

When rotating the MotherDuck token:

```bash
# 1. Get new token from motherduck.com (terrylica GitHub account)

# 2. Update in Doppler using stdin
echo -n 'new_token_here' | doppler secrets set MOTHERDUCK_TOKEN \
  --project claude-config --config dev

# 3. Update note with new creation date
doppler secrets notes set MOTHERDUCK_TOKEN \
  --project claude-config \
  "MotherDuck read/write token (terry_read_write_token_02). Login: terrylica GitHub account at motherduck.com. Created: YYYY-MM-DD. Token type: read_write."

# 4. Test injection
doppler run --project claude-config --config dev \
  --command='echo "Token length: ${#MOTHERDUCK_TOKEN}"'
```

## Troubleshooting

### Token Not Found

```bash
# Verify secret exists
doppler secrets --project claude-config --config dev | grep MOTHERDUCK

# Check token value (truncated for security)
doppler secrets get MOTHERDUCK_TOKEN --project claude-config --config dev --plain | head -c 50
```

### DuckDB Connection Failed

```bash
# Test token manually
export motherduck_token=$(doppler secrets get MOTHERDUCK_TOKEN --project claude-config --config dev --plain)
python3 -c "import duckdb; conn = duckdb.connect('md:'); print('Connected!')"
```

### Doppler CLI Not Found

```bash
# Install Doppler CLI
brew install dopplerhq/cli/doppler

# Login
doppler login
```

## Reference

- **Doppler Project**: claude-config
- **Doppler Config**: dev
- **MotherDuck Account**: terrylica GitHub
- **Token Name**: terry_read_write_token_01
- **Created**: 2025-11-08
- **Stored**: 2025-11-08
