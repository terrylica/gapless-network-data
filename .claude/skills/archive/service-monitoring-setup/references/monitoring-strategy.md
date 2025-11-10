# Monitoring Strategy

## The Problem: Who Monitors the Monitor?

**Anti-Pattern**: Self-hosting monitoring on the same infrastructure being monitored creates a circular dependency.

```
❌ Bad: Uptime Kuma on GCP VM monitoring GCP VM
   - VM down → Uptime Kuma down → No alerts
   - Network issue → Monitor can't send alerts
   - Single point of failure

✅ Good: External SaaS monitoring separate infrastructure
   - VM down → External service detects, sends Telegram alert
   - Multiple independent services for redundancy
   - No shared failure modes
```

**Principle**: Always monitor from external infrastructure with different failure modes.

## Dual-Service Architecture

**Rationale**: No single service provides all monitoring needs in free tier.

| Service | Provides | Cost |
|---------|----------|------|
| **Healthchecks.io** | Heartbeat monitoring (Dead Man's Switch) | $0 |
| **UptimeRobot** | HTTP endpoint polling | $0 |
| **BOTH** | Complete monitoring coverage | **$0/month** |

### Why Not Just One Service?

**UptimeRobot Free Tier**:
- ✅ HTTP endpoint monitoring
- ❌ Heartbeat monitoring (requires Pro $7/mo)

**Healthchecks.io Free Tier**:
- ✅ Heartbeat monitoring
- ❌ HTTP endpoint monitoring (not offered)

**Conclusion**: Dual-service architecture provides complete coverage at zero cost.

## Architecture Decision Matrix

### Use Healthchecks.io (Dead Man's Switch) When:

- ✅ Workload is ephemeral (Cloud Run Jobs, cron jobs, Lambda functions)
- ✅ Job runs and exits (no persistent endpoint)
- ✅ Need to catch: job crashes, hangs, scheduling failures
- ✅ Job duration is variable or unpredictable
- ✅ Running on serverless infrastructure

**Example Use Cases**:
- Daily data backfill jobs
- Scheduled ETL pipelines
- Backup scripts
- Database maintenance jobs
- Report generation tasks

**How It Works**:
```
1. Job starts
2. Job executes work
3. Job pings Healthchecks.io on success
4. If no ping within timeout → Alert

Catches:
- Job didn't start (scheduler failure)
- Job crashed mid-execution
- Job hung/froze
- Job completed but failed
```

### Use UptimeRobot (HTTP Polling) When:

- ✅ Workload has persistent HTTP endpoint (APIs, web services)
- ✅ Running on VMs or always-on infrastructure
- ✅ Need to catch: service down, endpoint unresponsive, network issues
- ✅ Service availability is critical metric
- ✅ Want external validation of reachability

**Example Use Cases**:
- VM-hosted APIs
- Web applications
- Database endpoints (with HTTP health check)
- Microservices with health endpoints
- WebSocket servers with HTTP fallback

**How It Works**:
```
1. UptimeRobot pings endpoint every 5 minutes
2. Expects 200 OK response
3. If no response or error code → Alert

Catches:
- Service crashed
- Network connectivity lost
- Port blocked by firewall
- DNS resolution failure
- Certificate expiration
```

## Complete Monitoring Setup

### Phase 1: Doppler Secret Storage

```bash
# Store API keys in Doppler
doppler secrets set UPTIMEROBOT_API_KEY --project claude-config --config dev
doppler secrets set HEALTHCHECKS_API_KEY --project claude-config --config dev

# Verify
doppler secrets get UPTIMEROBOT_API_KEY --project claude-config --config dev --plain
doppler secrets get HEALTHCHECKS_API_KEY --project claude-config --config dev --plain
```

### Phase 2: Telegram Integration (Manual)

**CRITICAL**: Both services require manual Telegram setup before production use.

**UptimeRobot**:
1. Visit https://uptimerobot.com/dashboard
2. My Settings → Alert Contacts → Add Telegram
3. Message UptimeRobot bot, complete verification

**Healthchecks.io**:
1. Visit https://healthchecks.io/projects
2. Integrations → Add Telegram
3. Message @HealthchecksBot, send `/start`
4. Copy code, complete verification

**Validation**:
```python
# Verify Telegram configured
assert client.get_telegram_contact_id() is not None
```

### Phase 3: Production Deployment

```python
# /// script
# dependencies = ["requests"]
# ///

import os
from scripts.healthchecks_client import HealthchecksClient
from scripts.uptimerobot_client import UptimeRobotClient

# Get API keys from Doppler
healthchecks_key = os.popen(
    "doppler secrets get HEALTHCHECKS_API_KEY --plain"
).read().strip()

uptimerobot_key = os.popen(
    "doppler secrets get UPTIMEROBOT_API_KEY --plain"
).read().strip()

# Initialize clients
hc = HealthchecksClient(healthchecks_key)
ur = UptimeRobotClient(uptimerobot_key)

# Setup Cloud Run Job monitoring (heartbeat)
job_check = hc.create_check(
    name="Ethereum Collector Job",
    timeout=7200,  # 2 hours
    grace=600,     # 10 minutes
    channels=hc.get_telegram_channel_id()
)

print(f"Cloud Run Job: {job_check['ping_url']}")

# Setup VM HTTP monitoring (polling)
vm_monitor = ur.create_monitor(
    friendly_name="VM API Endpoint",
    url="https://your-vm-ip:8000/health",
    type=1,
    interval=300,
    alert_contacts=ur.get_telegram_contact_id()
)

print(f"VM Monitor: {vm_monitor['monitor']['id']}")
```

## Production Example: gapless-network-data

### Infrastructure Components

**Cloud Run Job** (ephemeral):
- Name: `eth-collector`
- Schedule: Every 2 hours
- Duration: 30-90 minutes
- Monitoring: **Healthchecks.io** (Dead Man's Switch)

**VM Service** (persistent):
- Name: `eth-realtime-collector`
- HTTP Health: `http://VM_IP:8000/health`
- Uptime: 24/7
- Monitoring: **UptimeRobot** (HTTP polling)

### Complete Setup

```python
# /// script
# dependencies = ["requests"]
# ///

import os
from scripts.healthchecks_client import HealthchecksClient
from scripts.uptimerobot_client import UptimeRobotClient

# Get API keys
hc_key = os.popen("doppler secrets get HEALTHCHECKS_API_KEY --plain").read().strip()
ur_key = os.popen("doppler secrets get UPTIMEROBOT_API_KEY --plain").read().strip()

hc = HealthchecksClient(hc_key)
ur = UptimeRobotClient(ur_key)

# Verify Telegram
hc_telegram = hc.get_telegram_channel_id()
ur_telegram = ur.get_telegram_contact_id()

if not hc_telegram or not ur_telegram:
    raise Exception("Telegram not configured - see manual setup steps")

# 1. Cloud Run Job monitoring
job_check = hc.create_check(
    name="Ethereum Collector (Cloud Run Job)",
    timeout=7200,  # 2 hours
    grace=600,     # 10 minutes
    tags="production ethereum cloud-run",
    channels=hc_telegram
)

print("=" * 60)
print("Cloud Run Job Monitoring")
print("=" * 60)
print(f"Ping URL: {job_check['ping_url']}")
print("\nAdd to Cloud Run Job:")
print(f"  gcloud run jobs update eth-collector \\")
print(f"    --set-env-vars HEALTHCHECK_PING_URL={job_check['ping_url']}")
print()

# 2. VM HTTP endpoint monitoring
vm_monitor = ur.create_monitor(
    friendly_name="Ethereum Collector VM API",
    url="http://34.123.45.67:8000/health",  # Replace with real IP
    type=1,
    interval=300,
    alert_contacts=ur_telegram
)

print("=" * 60)
print("VM HTTP Monitoring")
print("=" * 60)
print(f"Monitor ID: {vm_monitor['monitor']['id']}")
print(f"Checks endpoint every 5 minutes")
print()

print("✅ Dual-service monitoring active")
print("📱 Telegram alerts configured for both")
```

### Job Integration

```python
# In Cloud Run Job script (historical_backfill.py):

import os
import sys
import requests

def main():
    """Main job execution."""
    ping_url = os.getenv("HEALTHCHECK_PING_URL")

    try:
        # Do work
        backfill_data()

        # Success ping
        if ping_url:
            requests.get(ping_url)
            print("✅ Healthcheck pinged (success)")

        return 0

    except Exception as e:
        print(f"❌ Job failed: {e}")

        # Failure ping
        if ping_url:
            requests.get(f"{ping_url}/fail")
            print("⚠️ Healthcheck pinged (failure)")

        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Alert Flow

### Scenario 1: Cloud Run Job Fails

```
Timeline:
14:00 - Job scheduled to run
14:01 - Job starts, no start ping sent
16:00 - Job should complete (2h timeout)
16:10 - Grace period expires (10 min)
16:10 - 📱 Telegram alert: "Ethereum Collector (Cloud Run Job) is DOWN"

Root Cause Investigation:
- Check Cloud Run logs
- Was job scheduled? (scheduler issue)
- Did job start? (permission issue)
- Did job crash? (code error)
- Did job hang? (network timeout)
```

### Scenario 2: VM Service Down

```
Timeline:
10:00 - VM running normally
10:05 - UptimeRobot checks endpoint (200 OK)
10:10 - UptimeRobot checks endpoint (timeout)
10:15 - UptimeRobot checks endpoint (timeout)
10:15 - 📱 Telegram alert: "Ethereum Collector VM API is DOWN"

Root Cause Investigation:
- SSH to VM (if accessible)
- Check systemd service status
- Check VM metrics (CPU, memory, disk)
- Check network connectivity
- Check health endpoint logs
```

## Cost Comparison

### Self-Hosted (Uptime Kuma)

**Infrastructure**:
- VM for Uptime Kuma: $10-20/month
- Domain/SSL: $12/year
- Maintenance time: 2-4 hours/month

**Total**: $120-240/year + maintenance burden

**Risks**:
- Single point of failure
- Same infrastructure being monitored
- Maintenance overhead
- No external validation

### External SaaS (Dual Service)

**Free Tiers**:
- Healthchecks.io: $0/month (20 checks)
- UptimeRobot: $0/month (50 monitors)

**Total**: **$0/year**

**Benefits**:
- ✅ External infrastructure (different failure modes)
- ✅ Zero maintenance
- ✅ Professional SLA
- ✅ Telegram integration included
- ✅ No infrastructure to manage

**Upgrade Paths** (if needed in future):
- Healthchecks.io Pro: $20/month (100 checks, SMS alerts)
- UptimeRobot Pro: $7/month (heartbeat monitoring, 1-min intervals)

## Monitoring Best Practices

### 1. Timeout Configuration

**Healthchecks.io Timeouts**:
- Set timeout = 1.5× typical job duration
- Add 10-30 minute grace period
- Example: 1-hour job → 90-minute timeout + 15-minute grace

**Why**: Allows for normal variability without false alerts.

### 2. Alert Fatigue Prevention

**Configure Properly**:
- Use appropriate grace periods
- Don't monitor too frequently (5-minute minimum)
- Test alert flow before production

**Example**: 5-minute check interval + 10-minute grace = alert after 15 minutes down.

### 3. False Positive Handling

**Common Causes**:
- Network blips (transient)
- Planned maintenance (pause monitoring)
- Job duration variability (increase timeout)

**Mitigation**:
- Grace periods (buffer before alert)
- Manual pause before maintenance
- Monitor metrics to adjust timeouts

### 4. Alert Routing

**Production Strategy**:
- Critical services: Telegram + Email
- Development: Email only
- Test environments: No alerts (pause monitoring)

### 5. Documentation

**Required for Each Monitor**:
- What is being monitored
- Why this timeout/interval
- Who to contact on failure
- Runbook link for troubleshooting

## Troubleshooting

### No Telegram Alerts

**Symptom**: Monitors configured but no Telegram messages received.

**Check**:
1. Verify Telegram integration: `client.get_telegram_contact_id()` not None
2. Check UptimeRobot contact status (must be `status=2`)
3. Test alert manually in dashboard
4. Verify Telegram bot not blocked

**Fix**: Complete Telegram setup steps in dashboard.

### Healthcheck Never Pings

**Symptom**: Check always shows "new" status, never receives pings.

**Check**:
1. Verify `HEALTHCHECK_PING_URL` environment variable set
2. Check job logs for ping attempts
3. Test ping URL manually: `curl <ping_url>`
4. Check network connectivity from job

**Fix**: Add environment variable, verify network access.

### UptimeRobot False Positives

**Symptom**: VM is up but UptimeRobot reports down.

**Check**:
1. Test health endpoint manually: `curl http://VM_IP:8000/health`
2. Check firewall rules (allow HTTP from UptimeRobot IPs)
3. Verify health endpoint returns 200 OK
4. Check VM network connectivity

**Fix**: Adjust firewall, fix health endpoint, increase grace period.

## Future Enhancements

### Phase 1: Basic Monitoring (Current)
- ✅ API key storage in Doppler
- ✅ Telegram integration (manual)
- ✅ Monitor creation scripts
- ⏳ Production deployment

### Phase 2: Automation
- Auto-detect Cloud Run Jobs and create checks
- Auto-detect VMs with health endpoints
- Bulk monitor creation from config file
- Terraform/IaC integration

### Phase 3: Advanced Alerting
- Alert aggregation (multiple failures → single alert)
- Custom alert messages with context
- Incident tracking integration (PagerDuty, Opsgenie)
- Status page generation

### Phase 4: Analytics
- Uptime percentage tracking
- Response time monitoring
- Failure pattern analysis
- SLA reporting

## Validation Evidence

All patterns validated through empirical API probing:

**UptimeRobot**:
- 5 probe scripts (`/tmp/probe/uptimerobot/`)
- Complete API lifecycle validated
- Rate limiting discovered and documented
- Probe report: `/tmp/probe/uptimerobot/PROBE_REPORT.md`

**Healthchecks.io**:
- 5 probe scripts (`/tmp/probe/healthchecks-io/`)
- Core operations validated
- API format differences documented
- Probe report: `/tmp/probe/healthchecks-io/PROBE_REPORT.md`

**Total Validation**: 10 probe scripts, 2 comprehensive reports, all patterns tested against live APIs.
