# Plan: Alpha Features API Design for gapless-network-data

**Created**: 2025-11-28
**ADR**: [/docs/architecture/decisions/2025-11-28-alpha-features-api.md](/docs/architecture/decisions/2025-11-28-alpha-features-api.md)
**Scope**: Design highly opinionated PyPI API for Ethereum alpha features, optimized for AI coding agent consumption

---

## (a) Context

### Problem Statement

The `gapless-network-data` package exposes Ethereum block data but lacks:

1. Opinionated guidance on which features are valuable for ML/forecasting
2. AI-agent-discoverable feature rankings
3. Secure credential distribution for internal team access

### Key Decisions (from ADR)

| Decision            | Choice                        | Rationale                                                     |
| ------------------- | ----------------------------- | ------------------------------------------------------------- |
| Deprecated Features | Exclude by default            | Guides users away from useless data (difficulty=0 post-Merge) |
| Column Ordering     | Traditional (timestamp first) | Rankings via separate `probe.get_alpha_features()` API        |
| Signaling Mechanism | Separate rankings API         | Clean separation, AI agents call probe first                  |
| Data Access         | Double-layer security         | ClickHouse read-only user + Doppler service token             |

---

## (b) Task List

- [x] Create ADR 2025-11-28-alpha-features-api.md
- [x] Create plan directory and sync plan.md
- [x] Phase A1: Create ClickHouse read-only user (`team_reader`)
- [x] Phase A2: Store credentials in Doppler (`gapless-network-data/prd`)
- [x] Phase A3: Create Doppler service token
- [x] Phase A4: Store in 1Password (Engineering vault → "gapless-network-data Doppler Service Token")
- [x] Phase B1: Update api.py with include_deprecated param, add fetch_blocks(), credential resolution
- [x] Phase B2: Create probe.py with alpha features, protocol eras, setup workflow
- [x] Phase B3: Create llms.txt at project root
- [x] Phase B4: Update CLAUDE.md with Alpha Features API section

**Status**: COMPLETED (2025-11-28)

---

## (c) Plan

## Summary

Design and implement an AI-agent-friendly API that exposes ranked Ethereum block features for financial time series forecasting, following patterns from `gapless-crypto-clickhouse`.

## User Requirements

1. **Raw features only** - users compute derived features
2. **All features available** - with crystal-clear, AI-agent-discoverable recommendations
3. **Native format** - pandas DataFrame (per gapless-crypto-clickhouse pattern)
4. **AI-agent optimized** - probe module + llms.txt for Claude Code CLI consumption

---

## Alpha Feature Ranking (Opinionated)

### Tier 1: Core Predictive Features (MUST EXPOSE)

| Rank   | Feature                  | Justification                                                                                                                                     |
| ------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **#1** | `base_fee_per_gas`       | THE most valuable. EIP-1559 algorithmic adjustment creates predictable patterns. Directly actionable for MEV, arbitrage timing, gas optimization. |
| **#2** | `gas_used` / `gas_limit` | Block utilization is a leading indicator for fee movements. >50% util = fee increases.                                                            |
| **#3** | `transaction_count`      | Network activity correlates with market volatility. Spikes precede liquidations, DEX activity.                                                    |

### Tier 2: Supporting Features (SHOULD EXPOSE)

| Rank   | Feature     | Justification                                                              |
| ------ | ----------- | -------------------------------------------------------------------------- |
| **#4** | `timestamp` | Block timestamp for temporal alignment. Enables ASOF JOIN with OHLCV data. |
| **#5** | `number`    | Block number as unique identifier and ordering key.                        |
| **#6** | `size`      | Block size in bytes. Larger = more complex transactions.                   |

### Tier 3: L2/Rollup Features (CONDITIONAL)

| Rank   | Feature           | Availability                  | Justification            |
| ------ | ----------------- | ----------------------------- | ------------------------ |
| **#7** | `blob_gas_used`   | Post-EIP4844 only (Mar 2024+) | L2 rollup activity proxy |
| **#8** | `excess_blob_gas` | Post-EIP4844 only             | Blob fee market pressure |

### DEPRECATED (Opinionated: DO NOT EXPOSE BY DEFAULT)

| Feature            | Reason                                                              | Recommendation           |
| ------------------ | ------------------------------------------------------------------- | ------------------------ |
| `difficulty`       | Always 0 post-Merge (Sep 2022). Zero predictive value for 2+ years. | Exclude from default API |
| `total_difficulty` | Frozen post-Merge. Historical artifact only.                        | Exclude from default API |

---

## API Design (Following gapless-crypto-clickhouse Patterns)

### Primary API: Function-Based

```python
# gapless_network_data/api.py

def fetch_blocks(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
    include_deprecated: bool = False,  # Opinionated default
) -> pd.DataFrame:
    """
    Fetch Ethereum block data optimized for alpha feature engineering.

    Alpha Feature Rankings (for AI agents):
        #1 base_fee_per_gas - Fee prediction (most valuable)
        #2 gas_used/gas_limit - Congestion leading indicator
        #3 transaction_count - Network activity proxy
        #4-6 timestamp, number, size - Temporal alignment
        #7-8 blob_gas_used, excess_blob_gas - L2 metrics (post-Mar 2024)

    Deprecated (excluded by default):
        - difficulty: Always 0 post-Merge (Sep 2022)
        - total_difficulty: Frozen post-Merge

    Args:
        start: Start date (ISO 8601 or 'YYYY-MM-DD')
        end: End date (ISO 8601 or 'YYYY-MM-DD')
        limit: Max blocks to return (default: None = all)
        include_deprecated: Include difficulty/total_difficulty (default: False)

    Returns:
        pd.DataFrame with standard time-series column order:
        - timestamp (datetime64[ns, UTC])
        - number (uint64)
        - gas_limit (uint64)
        - gas_used (uint64)
        - base_fee_per_gas (uint64)
        - transaction_count (uint64)
        - size (uint64)
        - blob_gas_used (uint64, nullable) - Post-EIP4844
        - excess_blob_gas (uint64, nullable) - Post-EIP4844
        - [difficulty, total_difficulty if include_deprecated=True]

    Note:
        For alpha feature rankings, call probe.get_alpha_features() first.

    Examples:
        # Fetch last 1000 blocks (recommended for live trading)
        df = fetch_blocks(limit=1000)

        # Compute block utilization (#2 alpha feature)
        df['utilization'] = df['gas_used'] / df['gas_limit']

        # Date range query
        df = fetch_blocks(start='2024-01-01', end='2024-01-31')
    """
```

### AI Discoverability: probe.py

```python
# gapless_network_data/probe.py

def get_alpha_features() -> dict:
    """
    Get ranked alpha features for financial time series forecasting.

    Returns dict with:
        - ranked_features: List ordered by predictive importance
        - deprecated_features: Features excluded from default API
        - protocol_eras: Era boundaries and feature availability
        - recommendations: Opinionated usage guidance
    """
    return {
        "ranked_features": [
            {
                "rank": 1,
                "name": "base_fee_per_gas",
                "type": "uint64",
                "availability": "Post-EIP1559 (Aug 2021, block 12,965,000+)",
                "predictive_value": "highest",
                "use_case": "Gas price prediction, MEV timing, arbitrage optimization",
                "justification": "EIP-1559 algorithmic adjustment creates predictable patterns"
            },
            {
                "rank": 2,
                "name": "block_utilization",
                "derived_from": ["gas_used", "gas_limit"],
                "formula": "gas_used / gas_limit",
                "python_code": "df['utilization'] = df['gas_used'] / df['gas_limit']",
                "type": "float64",
                "availability": "All blocks (since genesis)",
                "predictive_value": "high",
                "use_case": "Fee prediction leading indicator",
                "justification": "Utilization >50% triggers base_fee increase, <50% decrease"
            },
            {
                "rank": 3,
                "name": "transaction_count",
                "type": "uint64",
                "availability": "All blocks (since genesis)",
                "predictive_value": "medium",
                "use_case": "Network activity proxy, volatility indicator"
            },
            {
                "rank": 4,
                "name": "block_interval",
                "derived_from": ["timestamp"],
                "formula": "timestamp[n] - timestamp[n-1]",
                "python_code": "df['block_interval'] = df['timestamp'].diff().dt.total_seconds()",
                "type": "float64",
                "availability": "All blocks",
                "predictive_value": "medium",
                "use_case": "Network health indicator (should be ~12s post-Merge)"
            },
            {
                "rank": 5,
                "name": "avg_tx_size",
                "derived_from": ["size", "transaction_count"],
                "formula": "size / transaction_count",
                "python_code": "df['avg_tx_size'] = df['size'] / df['transaction_count'].replace(0, 1)",
                "type": "float64",
                "availability": "All blocks",
                "predictive_value": "low",
                "use_case": "Transaction complexity indicator"
            },
            {
                "rank": 6,
                "name": "base_fee_velocity",
                "derived_from": ["base_fee_per_gas"],
                "formula": "(base_fee[n] - base_fee[n-1]) / base_fee[n-1]",
                "python_code": "df['base_fee_velocity'] = df['base_fee_per_gas'].pct_change()",
                "type": "float64",
                "availability": "Post-EIP1559 (block 12,965,000+)",
                "predictive_value": "medium",
                "use_case": "Fee momentum indicator"
            },
            {
                "rank": 7,
                "name": "blob_utilization",
                "derived_from": ["blob_gas_used"],
                "formula": "blob_gas_used / 786432",  # max blob gas per block
                "python_code": "df['blob_utilization'] = df['blob_gas_used'] / 786432",
                "type": "float64",
                "availability": "Post-EIP4844 (block 19,426,587+)",
                "predictive_value": "medium",
                "use_case": "L2 rollup activity proxy"
            }
        ],
        "deprecated_features": [
            {
                "name": "difficulty",
                "reason": "Always 0 post-Merge (Sep 2022, block 15,537,394+)",
                "recommendation": "DO NOT USE for post-2022 analysis"
            },
            {
                "name": "total_difficulty",
                "reason": "Frozen post-Merge",
                "recommendation": "Only useful for historical PoW analysis (pre-Sep 2022)"
            }
        ],
        "protocol_eras": {
            "pre_eip1559": {"blocks": "0 - 12,964,999", "base_fee": False},
            "post_eip1559_pow": {"blocks": "12,965,000 - 15,537,393", "base_fee": True, "difficulty": True},
            "post_merge": {"blocks": "15,537,394 - 19,426,586", "base_fee": True, "difficulty": False},
            "post_eip4844": {"blocks": "19,426,587+", "base_fee": True, "blob_gas": True}
        },
        "recommendations": {
            "for_forecasting": "Focus on base_fee_per_gas and block_utilization",
            "for_l2_analysis": "Use blob_gas_used post-EIP4844 (Mar 2024+)",
            "avoid": "difficulty, total_difficulty (no predictive value post-2022)"
        }
    }

def get_setup_workflow() -> dict:
    """
    Get credential setup workflow for new team members.

    This is safe to expose - it's just workflow documentation, not secrets.
    """
    return {
        "description": "Setup workflow for accessing gapless-network-data ClickHouse",
        "prerequisites": [
            "Doppler CLI installed: brew install doppler",
            "1Password CLI installed: brew install 1password-cli",
            "Team lead has shared Doppler service token via 1Password"
        ],
        "steps": [
            {
                "step": 1,
                "action": "Get Doppler service token from 1Password",
                "command": "op item get 'gapless-network-data Doppler Service Token' --vault Shared --field token",
                "notes": "Or manually copy from 1Password app"
            },
            {
                "step": 2,
                "action": "Configure Doppler with service token",
                "command": "doppler configure set token <token_from_step_1>",
                "notes": "One-time setup"
            },
            {
                "step": 3,
                "action": "Link to gapless-network-data project",
                "command": "doppler setup --project gapless-network-data --config team",
                "notes": "Links current directory to team config"
            },
            {
                "step": 4,
                "action": "Verify access",
                "command": "doppler run -- python -c \"from gapless_network_data import fetch_blocks; print(fetch_blocks(limit=5))\"",
                "notes": "Should print 5 Ethereum blocks"
            }
        ],
        "troubleshooting": {
            "credential_error": "Ensure Doppler token is valid and project exists",
            "connection_error": "Check network connectivity to ClickHouse Cloud",
            "permission_denied": "Contact team lead - your token may be revoked"
        },
        "1password_location": {
            "vault": "Shared",
            "item_name": "gapless-network-data Doppler Service Token",
            "fields": ["token", "usage", "project", "config"]
        }
    }
```

### llms.txt (Root Level)

````
# gapless-network-data v3.0.0

Ethereum block data with opinionated alpha feature rankings for AI-driven trading.

## Quick Start

```python
from gapless_network_data import fetch_blocks

# Fetch optimized for alpha feature engineering
df = fetch_blocks(limit=1000)

# Top alpha feature: base_fee_per_gas (#1)
print(df['base_fee_per_gas'].describe())

# Compute utilization (#2 alpha feature)
df['utilization'] = df['gas_used'] / df['gas_limit']
````

## Alpha Feature Rankings (Opinionated)

| Rank | Feature                          | Predictive Value         |
| ---- | -------------------------------- | ------------------------ |
| #1   | base_fee_per_gas                 | Highest - Fee prediction |
| #2   | gas_used/gas_limit (utilization) | High - Leading indicator |
| #3   | transaction_count                | Medium - Activity proxy  |

## DEPRECATED (Excluded by Default)

- difficulty: Always 0 post-Merge (Sep 2022)
- total_difficulty: Frozen post-Merge

Use `include_deprecated=True` only for historical PoW analysis.

## AI Agent Introspection

```python
from gapless_network_data import probe

# Get ranked alpha features with justifications
features = probe.get_alpha_features()

# Get package capabilities
caps = probe.get_capabilities()
```

```

---

## Implementation Steps (Claude Code Autonomous Execution)

### Phase A: Credential Infrastructure (Autonomous)

**Step A1: Create ClickHouse read-only user**
- Connect via clickhouse-connect with admin credentials (from Doppler aws-credentials/prd)
- Execute SQL: CREATE ROLE, GRANT SELECT, CREATE USER, GRANT ROLE
- Generate secure random password

**Step A2: Store credentials in Doppler**
- Create `team` config under gapless-network-data project
- Set CLICKHOUSE_HOST_READONLY, CLICKHOUSE_PASSWORD_READONLY, CLICKHOUSE_USER_READONLY

**Step A3: Create Doppler service token**
- Create token for team config (no expiration, revocable)
- Capture token value

**Step A4: Store in 1Password**
- Use `op item create` to store service token in Shared vault
- Include usage instructions in item fields

### Phase B: API Implementation

**Step B1: Update api.py**
- Add `include_deprecated=False` parameter to `fetch_blocks()`
- Implement `_get_clickhouse_credentials()` with Doppler-preferred resolution
- Keep traditional column order (timestamp first)
- Add rich docstrings with alpha rankings

**Step B2: Create probe.py**
- Implement `get_alpha_features()` with ranked features + python_code
- Implement `get_setup_workflow()` with 1Password location
- Implement `get_capabilities()` following gapless-crypto-clickhouse pattern

**Step B3: Create llms.txt**
- Root-level quick start with alpha focus
- Feature ranking table
- Setup workflow reference
- Deprecation warnings

**Step B4: Update CLAUDE.md**
- Add Alpha Features section with rankings
- Document probe module usage (including get_setup_workflow)
- Add examples for AI coding agents

---

## Critical Files to Modify

1. `src/gapless_network_data/api.py` - Add include_deprecated param, reorder columns
2. `src/gapless_network_data/probe.py` - New file for AI introspection
3. `llms.txt` - New file at project root
4. `CLAUDE.md` - Add Alpha Features documentation

---

## Design Decisions (FINALIZED)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Deprecated Features** | Exclude by default | Opinionated: guides users away from useless data. Use `include_deprecated=True` for historical PoW analysis. |
| **Column Ordering** | Traditional (timestamp first) | Standard time-series convention. Rankings communicated via separate `probe.get_alpha_features()` API. |
| **Signaling Mechanism** | Separate rankings API | Clean separation. AI agents call `probe.get_alpha_features()` first to understand priorities. |
| **Derived Formulas** | Include in probe output | AI agents can auto-compute derived features like `utilization = gas_used / gas_limit`. |
| **Return Format** | pandas DataFrame | Per gapless-crypto-clickhouse pattern. Maximum compatibility. |

---

## Data Access Architecture (Double-Layer Security)

### Overview

Package is on public PyPI but requires private credentials. Credentials are NOT in package.

```

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PyPI Package │────▶│ Doppler Token │────▶│ ClickHouse │
│ (public) │ │ (Layer 2) │ │ Read-Only User │
│ NO CREDENTIALS │ │ Revocable │ │ (Layer 1) │
└─────────────────┘ └─────────────────┘ └─────────────────┘

````

### Layer 1: ClickHouse Read-Only User

```sql
-- Run as admin in ClickHouse Cloud console:

-- Create read-only role
CREATE ROLE readonly_team;

-- Grant SELECT only on ethereum_mainnet database
GRANT SELECT ON ethereum_mainnet.* TO readonly_team;

-- Create user for team access
CREATE USER team_reader IDENTIFIED BY '<secure_password>';

-- Assign role to user
GRANT readonly_team TO team_reader;
````

**Security**: Even if credentials leaked, attacker can only READ, not write/delete.

### Layer 2: Doppler Service Token

1. Store read-only credentials in Doppler (e.g., `gapless-network-data/team` config)
2. Create service token with read-only access to that project
3. Share service token with coworkers via secure channel (1Password, Slack DM)
4. Coworker runs:

   ```bash
   # One-time setup
   doppler configure set token <service_token>
   doppler setup --project gapless-network-data --config team

   # Or use env var directly
   export DOPPLER_TOKEN=<service_token>
   doppler run -- python script.py
   ```

**Security**: Token can be revoked if compromised. Coworker doesn't need full Doppler account.

### Package Credential Resolution

```python
# In api.py - Credential resolution order:

def _get_clickhouse_credentials():
    """
    Resolve credentials with Doppler-preferred strategy.

    Resolution order:
    1. Doppler (if DOPPLER_TOKEN or doppler CLI configured)
    2. Environment variables (CLICKHOUSE_HOST, CLICKHOUSE_PASSWORD)
    3. Raise clear error with setup instructions
    """
    # Try Doppler first
    try:
        import subprocess
        result = subprocess.run(
            ['doppler', 'secrets', 'get', 'CLICKHOUSE_HOST', 'CLICKHOUSE_PASSWORD', '--json'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            secrets = json.loads(result.stdout)
            return secrets['CLICKHOUSE_HOST'], secrets['CLICKHOUSE_PASSWORD']
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Fall back to env vars
    host = os.environ.get('CLICKHOUSE_HOST')
    password = os.environ.get('CLICKHOUSE_PASSWORD')

    if host and password:
        return host, password

    # Clear error with setup instructions
    raise CredentialError(
        "ClickHouse credentials not found.\n\n"
        "Option 1 (Recommended): Use Doppler service token\n"
        "  doppler configure set token <your_service_token>\n"
        "  doppler setup --project gapless-network-data --config team\n\n"
        "Option 2: Set environment variables\n"
        "  export CLICKHOUSE_HOST=<host>\n"
        "  export CLICKHOUSE_PASSWORD=<password>\n\n"
        "Contact your team lead for credentials."
    )
```

### Credential Distribution Workflow (Claude Code Autonomous Execution)

**Claude Code will execute steps 1-4 autonomously:**

1. **Create ClickHouse read-only user** via clickhouse-connect:

   ```python
   # Connect as admin, run SQL
   client.command("CREATE ROLE readonly_team")
   client.command("GRANT SELECT ON ethereum_mainnet.* TO readonly_team")
   client.command("CREATE USER team_reader IDENTIFIED BY '<generated_password>'")
   client.command("GRANT readonly_team TO team_reader")
   ```

2. **Store credentials in Doppler**:

   ```bash
   # Create new config for team access
   doppler configs create team --project gapless-network-data

   # Set read-only credentials
   doppler secrets set CLICKHOUSE_HOST_READONLY=<host> --config team
   doppler secrets set CLICKHOUSE_PASSWORD_READONLY=<password> --config team
   doppler secrets set CLICKHOUSE_USER_READONLY=team_reader --config team
   ```

3. **Create Doppler service token**:

   ```bash
   doppler configs tokens create team-access \
     --project gapless-network-data \
     --config team \
     --max-age 0 \  # Never expires (revoke manually if compromised)
     --plain
   ```

4. **Store service token in 1Password**:

   ```bash
   # Create item in 1Password vault
   op item create \
     --category login \
     --title "gapless-network-data Doppler Service Token" \
     --vault "Shared" \
     --field "token=<service_token>" \
     --field "usage=doppler configure set token <token>" \
     --field "project=gapless-network-data" \
     --field "config=team"
   ```

5. **User locates token**: 1Password → "Shared" vault → "gapless-network-data Doppler Service Token"

6. **Coworker setup**:

   ```bash
   # Copy token from 1Password, then:
   doppler configure set token <token>
   doppler setup --project gapless-network-data --config team

   # Use package
   python -c "from gapless_network_data import fetch_blocks; print(fetch_blocks(limit=10))"
   ```

### Security Properties

| Layer                     | Protection                                          | Revocation                        |
| ------------------------- | --------------------------------------------------- | --------------------------------- |
| ClickHouse read-only user | DB-level: Can only SELECT, not INSERT/UPDATE/DELETE | `DROP USER team_reader;`          |
| Doppler service token     | Access-level: Controls who can retrieve credentials | Revoke token in Doppler dashboard |

**Sources**:

- [ClickHouse Access Control and Account Management](https://clickhouse.com/docs/operations/access-rights)
- [ClickHouse RBAC Best Practices](https://chistadata.com/best-practices-for-clickhouses-role-based-access-control/)
