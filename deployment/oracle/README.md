---
version: "1.0.0"
last_updated: "2025-11-11"
status: "implementation complete, infrastructure provisioning pending"
---

# Oracle Cloud MotherDuck Monitoring

Oracle Cloud-based automated monitoring for MotherDuck Ethereum database gap detection.

## Overview

**Architecture**: OCI Compute VM + cron + OCI Vault

**Monitoring Scope**:

- **Gap Detection**: Detect >15s gaps in Ethereum block timestamps (1 year → 3 min ago)
- **Staleness Detection**: Alert if latest block >5 minutes old
- **Notifications**: Pushover emergency alerts + Healthchecks.io Dead Man's Switch

**Cost**: ~$0/month (OCI Always Free Tier)

## Files

| File                    | Purpose                                 | Status      |
| ----------------------- | --------------------------------------- | ----------- |
| `migrate_secrets.py`    | Automated Doppler → OCI Vault migration | ✅ Complete |
| `motherduck_monitor.py` | Gap detection + monitoring script       | ✅ Complete |
| `deploy.sh`             | SCP deployment automation               | ✅ Complete |
| `README.md`             | This file                               | ✅ Complete |

## Quick Start

### Prerequisites

1. **OCI CLI configured**: `~/.oci/config` with valid credentials
2. **Doppler secrets**: MOTHERDUCK_TOKEN, HEALTHCHECKS_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER
3. **SSH key**: `~/.ssh/motherduck-monitor` for VM access

Verify:

```bash
oci iam region list  # Should list 41 regions
doppler secrets --project claude-config --config dev  # Should show secrets
```

### Step 1: Infrastructure Provisioning

**Note**: This step requires interactive Oracle Cloud setup and is NOT automated.

#### 1.1. Create OCI VM

```bash
# Via OCI Console (web UI):
# 1. Go to Compute > Instances > Create Instance
# 2. Name: motherduck-monitor
# 3. Shape: VM.Standard.A1.Flex (1 OCPU, 6 GB RAM, ARM)
# 4. Image: Ubuntu 22.04 LTS
# 5. Network: Default VCN with public subnet
# 6. SSH key: Upload ~/.ssh/motherduck-monitor.pub
# 7. Click "Create"
```

**Alternative (OCI CLI)**:

```bash
# Get compartment OCID
COMPARTMENT_OCID=$(oci iam compartment list --query 'data[0].id' --raw-output)

# Create VM
oci compute instance launch \
  --compartment-id "$COMPARTMENT_OCID" \
  --display-name motherduck-monitor \
  --availability-domain "$(oci iam availability-domain list --query 'data[0].name' --raw-output)" \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus":1,"memoryInGBs":6}' \
  --image-id "$(oci compute image list --compartment-id $COMPARTMENT_OCID --operating-system 'Canonical Ubuntu' --operating-system-version '22.04' --limit 1 --query 'data[0].id' --raw-output)" \
  --subnet-id "$(oci network subnet list --compartment-id $COMPARTMENT_OCID --query 'data[0].id' --raw-output)" \
  --ssh-authorized-keys-file ~/.ssh/motherduck-monitor.pub \
  --wait-for-state RUNNING
```

#### 1.2. Idle Reclamation Prevention (Keep-Alive Mechanism)

**Oracle Cloud Policy**: VMs with <20% CPU/network/memory for 7 consecutive days are reclaimed on Free Tier accounts.

**Solution**: This deployment includes an automated keep-alive mechanism that maintains >20% CPU usage without requiring PAYG upgrade.

**Keep-Alive Strategy**:

- Runs every hour via cron (0 \* \* \* \*)
- Uses ~25% CPU for 30 seconds
- Prevents reclamation while staying 100% in free tier
- Cost: $0/month (CPU usage within limits)

**Alternative**: Upgrade to PAYG (no charges for Always Free resources, but requires credit card and account verification).

### Step 2: Secret Migration

Migrate secrets from Doppler to OCI Vault:

```bash
cd deployment/oracle
uv run migrate_secrets.py
```

**What it does**:

1. Fetches 4 secrets from Doppler (claude-config/dev)
2. Creates OCI Vault: `motherduck-monitoring-secrets`
3. Creates master encryption key
4. Creates secrets in OCI Vault
5. Validates all secrets

**Output**:

```
Vault OCID: ocid1.vault.oc1.iad.xxx
Key OCID: ocid1.key.oc1.iad.xxx

Secrets migrated:
  MOTHERDUCK_TOKEN: ocid1.vaultsecret.oc1.iad.xxx
  HEALTHCHECKS_API_KEY: ocid1.vaultsecret.oc1.iad.xxx
  PUSHOVER_TOKEN: ocid1.vaultsecret.oc1.iad.xxx
  PUSHOVER_USER: ocid1.vaultsecret.oc1.iad.xxx
```

**Save the secret OCIDs** - you'll need them in Step 3.

### Step 3: Deploy to VM

Deploy monitoring script to VM:

```bash
cd deployment/oracle
./deploy.sh deploy
```

**What it does**:

1. Gets VM public IP via OCI CLI
2. SCPs `motherduck_monitor.py` to VM
3. Installs `uv` on VM
4. Creates `~/.env-motherduck` environment file

### Step 4: Configure Secrets

SSH to VM and edit environment file:

```bash
ssh -i ~/.ssh/motherduck-monitor opc@<VM_PUBLIC_IP>
vi ~/.env-motherduck
```

Add secret OCIDs from Step 2:

```bash
# OCI Secret OCIDs (from migrate_secrets.py output)
SECRET_MOTHERDUCK_TOKEN_OCID=ocid1.vaultsecret.oc1.iad.xxx
SECRET_HEALTHCHECKS_API_KEY_OCID=ocid1.vaultsecret.oc1.iad.xxx
SECRET_PUSHOVER_TOKEN_OCID=ocid1.vaultsecret.oc1.iad.xxx
SECRET_PUSHOVER_USER_OCID=ocid1.vaultsecret.oc1.iad.xxx

# Healthchecks.io ping URL
HEALTHCHECKS_PING_URL=https://hc-ping.com/YOUR-UUID-HERE
```

### Step 5: Test Manual Execution

Test monitoring script:

```bash
./deploy.sh test
```

Expected output:

```
================================================================================
MotherDuck Gap Detection Monitor (Oracle Cloud)
================================================================================
[SECRETS] Loading secrets from OCI Vault...
  ✅ motherduck_token (32 characters)
  ✅ healthchecks_api_key (22 characters)
  ✅ pushover_token (30 characters)
  ✅ pushover_user (30 characters)

[MOTHERDUCK] Connecting to ethereum_mainnet...
  ✅ Connected

[STALENESS] Checking latest block...
  Latest block: 23,765,432
  Age: 45.1s
  Fresh: True

[GAP DETECTION] Analyzing blocks...
  Blocks checked: 2,630,000
  Gaps found: 0

[NOTIFICATIONS]
[PUSHOVER] Sending notification...
  ✅ Notification sent
[HEALTHCHECKS] Pinging...
  ✅ Pinged Healthchecks.io

✅ HEALTH CHECK PASSED
```

**Verify**:

1. Pushover notification received on your device
2. Healthchecks.io dashboard shows 'up' status

### Step 6: Configure Cron

Setup automatic execution every 3 hours:

```bash
./deploy.sh cron
```

**Cron schedule**: `0 */3 * * *` (runs at 00:00, 03:00, 06:00, etc.)

**Verify**:

```bash
ssh -i ~/.ssh/motherduck-monitor opc@<VM_PUBLIC_IP> 'crontab -l'
```

### Step 7: Configure Keep-Alive

Configure keep-alive mechanism to prevent idle reclamation:

```bash
./deploy.sh keep-alive
```

**What it does**:

1. Installs `stress-ng` for precise CPU control
2. Deploys `keep_alive.sh` script
3. Configures hourly cron job (0 \* \* \* \*)
4. Creates `~/keep_alive.log` for monitoring

**Verify**:

```bash
# Check crontab includes keep-alive
ssh -i ~/.ssh/motherduck-monitor opc@<VM_PUBLIC_IP> 'crontab -l | grep keep_alive'

# Monitor keep-alive logs
ssh -i ~/.ssh/motherduck-monitor opc@<VM_PUBLIC_IP> 'tail -f ~/keep_alive.log'
```

**Expected behavior**: Script runs every hour, uses 25% CPU for 30 seconds, prevents Oracle idle reclamation (no PAYG upgrade needed).

## Architecture

### Gap Detection Algorithm

Uses DuckDB LAG() window function (20x faster than Python iteration):

```sql
WITH gaps AS (
    SELECT
        number AS block_number,
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
    FROM blocks
    WHERE timestamp BETWEEN (CURRENT_TIMESTAMP - INTERVAL '1 year')
                        AND (CURRENT_TIMESTAMP - INTERVAL '3 minutes')
)
SELECT * FROM gaps WHERE gap_seconds > 15
```

**Why 3-minute exclusion?** Prevents false positives from real-time data collection still in progress.

### Exit Codes

| Code | Meaning                            | Action                       |
| ---- | ---------------------------------- | ---------------------------- |
| 0    | Healthy (no gaps, data fresh)      | None                         |
| 1    | Unhealthy (gaps detected or stale) | Alert sent                   |
| 2    | Fatal error (query failed)         | Alert + manual investigation |

### Notification Examples

**Success**:

```
✅ MOTHERDUCK HEALTHY

Blocks: 2,630,000
Latest: 23,765,432
Age: 45s ago
Gaps: 0

Time window: 365d → 3m ago
```

**Failure (Gap Detected)**:

```
❌ MOTHERDUCK UNHEALTHY

Issues: GAPS: 3 found, largest 127s

Latest block: 23,765,432
Age: 45s
Gaps: 3

Time window: 365d → 3m ago
```

**Failure (Stale Data)**:

```
❌ MOTHERDUCK UNHEALTHY

Issues: STALE: 420s (7.0 min)

Latest block: 23,765,100
Age: 420s
Gaps: 0

Time window: 365d → 3m ago
```

## Troubleshooting

### Issue: "Secret OCID not configured"

**Symptom**:

```
ValueError: Secret OCID not configured: motherduck_token
Set environment variable: SECRET_MOTHERDUCK_TOKEN_OCID
```

**Solution**: Edit `~/.env-motherduck` on VM and add secret OCIDs from `migrate_secrets.py` output.

### Issue: "OCI Vault authentication failed"

**Symptom**:

```
Exception: ServiceError 401 Unauthorized
```

**Solution**: Grant IAM permissions to VM:

```bash
COMPARTMENT_OCID=$(oci iam compartment list --query 'data[0].id' --raw-output)

oci iam policy create \
  --name motherduck-monitor-secrets \
  --compartment-id "$COMPARTMENT_OCID" \
  --statements '["Allow any-user to read secret-bundles in compartment id '"$COMPARTMENT_OCID"' where request.principal.type=\"instance\""]'
```

### Issue: "MotherDuck connection timeout"

**Symptom**:

```
Exception: CatalogException: md: connection failed
```

**Solutions**:

1. Verify egress rules in security list allow HTTPS (443)
2. Check MotherDuck token is valid: `doppler secrets get MOTHERDUCK_TOKEN`
3. Rotate token in OCI Vault if expired

### Issue: Cron not executing

**Symptom**: No log entries in `~/monitor.log`

**Solutions**:

1. Verify cron entry: `crontab -l | grep motherduck`
2. Check cron logs: `grep CRON /var/log/syslog | grep motherduck`
3. Ensure environment file sourced in cron: `source ~/.env-motherduck` in cron entry
4. Test manual execution: `cd ~ && source ~/.env-motherduck && uv run motherduck_monitor.py`

### Issue: False positive gaps in recent data

**Symptom**: Gaps detected but manual query shows continuous data

**Explanation**: Real-time collector still ingesting recent blocks. The 3-minute exclusion window already accounts for this.

**Verification**:

```bash
# SSH to VM
duckdb md:ethereum_mainnet -c "
SELECT MAX(number), MAX(timestamp),
       EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(timestamp))) AS age_seconds
FROM blocks
"
```

If age_seconds < 180 (3 minutes), this is expected behavior.

## Monitoring Validation

### Manual Verification Commands

**Check VM status**:

```bash
oci compute instance list \
  --compartment-id "$(oci iam compartment list --query 'data[0].id' --raw-output)" \
  --display-name motherduck-monitor \
  --query 'data[0]."lifecycle-state"'
```

**Check secrets exist**:

```bash
oci vault secret list \
  --compartment-id "$(oci iam compartment list --query 'data[0].id' --raw-output)" \
  --query 'data[*]."secret-name"'
```

**Check cron logs**:

```bash
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP> 'tail -50 ~/monitor.log'
```

**Check Healthchecks.io status**:

```bash
curl -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  https://healthchecks.io/api/v3/checks/ | jq '.checks[] | select(.name | contains("MotherDuck"))'
```

## Cost Analysis

| Resource        | Usage                          | Free Tier                  | Cost         |
| --------------- | ------------------------------ | -------------------------- | ------------ |
| OCI Compute     | 1 VM (1 OCPU, 6 GB ARM)        | 4 OCPU, 24 GB total        | $0           |
| OCI Vault       | 4 secrets, ~240 accesses/month | 20 secrets, 10K operations | $0           |
| OCI Network     | ~10 MB/month egress            | 10 TB/month                | $0           |
| Healthchecks.io | 1 check                        | 20 checks                  | $0           |
| Pushover        | Unlimited notifications        | One-time $5 purchase       | $0/month     |
| MotherDuck      | ~240 queries/month (~24 KB)    | 10 GB queries/month        | $0           |
| **Total**       |                                |                            | **$0/month** |

## Operational Commands

### Update monitoring script

```bash
# Edit locally
vi deployment/oracle/motherduck_monitor.py

# Deploy update
cd deployment/oracle
./deploy.sh deploy

# Restart (if running as service)
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP> 'sudo systemctl restart motherduck-monitor'
```

### Rotate secrets

```bash
# Update secret in Doppler
doppler secrets set MOTHERDUCK_TOKEN --value <new-token>

# Re-run migration (updates existing secrets)
uv run migrate_secrets.py

# No VM restart needed (secrets fetched at runtime)
```

### View logs

```bash
# Last 50 lines
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP> 'tail -50 ~/monitor.log'

# Follow live
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP> 'tail -f ~/monitor.log'

# Cron execution history
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP> 'grep "motherduck_monitor" ~/monitor.log | tail -20'
```

### Test notifications manually

```bash
# SSH to VM
ssh -i ~/.ssh/motherduck-monitor opc@<VM_IP>

# Load environment
source ~/.env-motherduck

# Run monitoring script
uv run ~/motherduck_monitor.py
```

## References

- **Specification**: `specifications/oracle-motherduck-monitoring.yaml`
- **Master Roadmap**: `specifications/master-project-roadmap.yaml` (x-sub-specifications)
- **GCP Alternative**: `deployment/cloud-run/data_quality_checker.py` (reference implementation)
- **DuckDB LAG() Pattern**: gapless-network-data/specifications/duckdb-integration-strategy.yaml
- **Healthchecks.io API**: https://healthchecks.io/docs/api/
- **Pushover API**: https://pushover.net/api
- **OCI Vault SDK**: https://docs.oracle.com/en-us/iaas/tools/python/latest/api/secrets.html

## Version History

| Version | Date       | Changes                                                   |
| ------- | ---------- | --------------------------------------------------------- |
| 1.0.0   | 2025-11-11 | Initial implementation (specification + scripts complete) |
