# Monitoring Setup

Autonomous monitoring configuration for dual-pipeline infrastructure using Healthchecks.io + UptimeRobot with Telegram alerts.

## Architecture

```
Cloud Run Job (hourly) --heartbeat--> Healthchecks.io --Telegram--> You
VM systemd (24/7) <--HTTP ping-- UptimeRobot --Telegram--> You
```

**Why two services?**

- **Healthchecks.io**: Heartbeat monitoring (job reports success)
- **UptimeRobot**: HTTP monitoring (service must respond to pings)

**Why separate infrastructure?**

- Both services run externally from GCP (no single point of failure)
- If GCP goes down → monitoring still alerts you

## Prerequisites

### 1. Create Accounts (Free Tier)

**Healthchecks.io**:

1. Sign up: https://healthchecks.io/accounts/signup/
2. Go to Settings → API Access
3. Copy your API key
4. Set up Telegram integration:
   - Go to Integrations → Add Integration → Telegram
   - Start chat with `@HealthchecksBot`
   - Send `/start` to the bot
   - Copy the confirmation code back to Healthchecks.io

**UptimeRobot**:

1. Sign up: https://uptimerobot.com/signUp
2. Go to My Settings → API Settings
3. Create Main API Key
4. Copy your API key
5. Set up Telegram integration:
   - Go to My Settings → Alert Contacts
   - Add New Alert Contact → Telegram
   - Follow the bot setup instructions

### 2. Store API Keys in Doppler

```bash
# Store API keys securely
doppler secrets set HEALTHCHECKS_API_KEY --project claude-config --config dev
doppler secrets set UPTIMEROBOT_API_KEY --project claude-config --config dev
```

Or use environment variables:

```bash
export HEALTHCHECKS_API_KEY="your-healthchecks-key"
export UPTIMEROBOT_API_KEY="your-uptimerobot-key"
```

## Installation

```bash
cd /Users/terryli/eon/gapless-network-data/deployment/monitoring

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Autonomous Setup (Recommended)

Run the automation script - it will:

1. Create Healthchecks.io check for Cloud Run Job
2. Create UptimeRobot monitor for VM HTTP endpoint
3. Configure Telegram alerts on both
4. Generate integration code snippets

```bash
python3 setup_monitoring.py
```

**Output**:

- `monitoring_setup_results.json` - Setup results with ping URLs and monitor IDs
- Integration code snippets for Cloud Run Job and VM collector

### Manual Setup (Alternative)

If you prefer manual configuration, see the API examples in `setup_monitoring.py`.

## Integration

### 1. Cloud Run Job (Heartbeat)

Add to `deployment/cloud-run/main.py` (end of `run_updater` function):

```python
import requests

def notify_healthcheck(ping_url: str, status: str = "success"):
    """Notify Healthchecks.io of job completion."""
    try:
        if status == "success":
            requests.get(ping_url, timeout=10)
        else:
            requests.get(f"{ping_url}/fail", timeout=10)
    except Exception as e:
        print(f"Failed to notify healthcheck: {e}")

# At end of successful execution
HEALTHCHECK_PING_URL = os.getenv("HEALTHCHECK_PING_URL")
if HEALTHCHECK_PING_URL:
    notify_healthcheck(HEALTHCHECK_PING_URL, "success")
```

Store ping URL in Secret Manager:

```bash
echo "https://hc-ping.com/YOUR-UUID" | \
  gcloud secrets create healthcheck-ping-url \
  --data-file=- \
  --project=eonlabs-ethereum-bq
```

### 2. VM HTTP Endpoint

Add to `deployment/vm/realtime_collector.py`:

```python
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint for UptimeRobot."""
    return jsonify({
        'status': 'ok',
        'service': 'eth-collector',
        'blocks_collected': global_block_count,
        'last_block_timestamp': global_last_timestamp
    }), 200

def start_health_server():
    """Start Flask health check server in background."""
    app.run(host='0.0.0.0', port=8000, debug=False)

if __name__ == '__main__':
    # Start health check server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # Start collector
    main()
```

Deploy updated collector:

```bash
bash deployment/vm/deploy.sh
```

Open firewall for health checks:

```bash
gcloud compute firewall-rules create allow-health-check \
  --allow tcp:8000 \
  --source-ranges 0.0.0.0/0 \
  --target-tags eth-collector \
  --project eonlabs-ethereum-bq
```

## Verification

### 1. Test Healthchecks.io

```bash
# Manual ping
curl https://hc-ping.com/YOUR-UUID

# Check status
curl -H "X-Api-Key: YOUR-API-KEY" \
  https://healthchecks.io/api/v3/checks/
```

### 2. Test UptimeRobot

```bash
# Test VM health endpoint
VM_IP=$(gcloud compute instances describe eth-realtime-collector \
  --zone us-east1-b \
  --project eonlabs-ethereum-bq \
  --format "value(networkInterfaces[0].accessConfigs[0].natIP)")

curl http://$VM_IP:8000/health
```

### 3. Test Telegram Alerts

- Healthchecks.io: Go to check → Click "Send Test Notification"
- UptimeRobot: Go to monitor → Click "Send Test Alert"

## Monitoring Patterns

### Pattern 1: Heartbeat (Cloud Run Job)

```
Job starts → Does work → Sends ping → Healthchecks.io: ✅
Job fails → No ping sent → Healthchecks.io: 🚨 Alert (after grace period)
```

**Timeout**: 2 hours (hourly job + buffer)
**Grace period**: 10 minutes (allows for delays)

### Pattern 2: HTTP Monitoring (VM Service)

```
Every 5 min: UptimeRobot --HTTP GET--> VM:8000/health
VM responds: 200 OK → UptimeRobot: ✅
VM down/no response → UptimeRobot: 🚨 Alert (after 2 failed checks)
```

**Interval**: 5 minutes
**Timeout**: 30 seconds

## Cost Analysis

| Service         | Free Tier        | Paid Plan          |
| --------------- | ---------------- | ------------------ |
| Healthchecks.io | 20 checks        | $4/mo (80 checks)  |
| UptimeRobot     | 50 HTTP monitors | $7/mo (+heartbeat) |

**Current setup**: $0/month (within free tier)

**Note**: UptimeRobot heartbeat monitoring requires Pro Plan ($7/mo). We use Healthchecks.io for heartbeats instead (free).

## Troubleshooting

### Healthchecks.io ping not received

```bash
# Check if ping URL is correct
curl -v https://hc-ping.com/YOUR-UUID

# Check Cloud Run Job logs
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=eth-md-updater" \
  --limit 50 --project eonlabs-ethereum-bq
```

### UptimeRobot cannot reach VM

```bash
# Test from external network
curl http://VM_IP:8000/health

# Check firewall rules
gcloud compute firewall-rules list --project eonlabs-ethereum-bq | grep 8000

# Check if Flask server is running
gcloud compute ssh eth-realtime-collector \
  --zone us-east1-b \
  --project eonlabs-ethereum-bq \
  --command="ps aux | grep flask"
```

### No Telegram alerts

1. Verify Telegram bot setup in service dashboard
2. Send test notification
3. Check bot chat history for error messages
4. Re-authorize bot if needed

## Files

- `setup_monitoring.py` - Autonomous setup script
- `requirements.txt` - Python dependencies
- `monitoring_setup_results.json` - Setup results (generated)
- `README.md` - This file

## References

- Healthchecks.io API: https://healthchecks.io/docs/api/
- UptimeRobot API: https://uptimerobot.com/api/
- Python SDK (Healthchecks): https://pypi.org/project/healthchecks-io/
- Python SDK (UptimeRobot): https://pypi.org/project/python-uptimerobot/
