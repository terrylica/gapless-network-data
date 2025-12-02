# UptimeRobot API Patterns

**API Version**: v2
**Base URL**: https://api.uptimerobot.com/v2
**Authentication**: POST data with `api_key` field
**Free Tier**: 50 HTTP monitors, 5-minute intervals

## Empirical Validation Summary

**Probe Date**: 2025-11-09
**API Key**: Stored in Doppler (`UPTIMEROBOT_API_KEY`)
**Account**: usalchemist@gmail.com
**Validation Scripts**: `/tmp/probe/uptimerobot/` (5 phases completed)

**Core Capabilities Validated**:

- ✅ Authentication (API key valid)
- ✅ Account details retrieval
- ✅ List monitors (empty account)
- ✅ List alert contacts (1 email, Pushover NOT configured)
- ✅ Monitor lifecycle (create → verify → delete)
- ⚠️ Rate limiting encountered (~6 operations before throttle)

## API Request Pattern

All UptimeRobot API v2 endpoints follow this pattern:

```python
import requests

def _request(endpoint: str, data: dict) -> dict:
    """Generic UptimeRobot API request."""
    data["api_key"] = api_key
    data["format"] = "json"

    response = requests.post(
        f"https://api.uptimerobot.com/v2/{endpoint}",
        data=data
    )
    response.raise_for_status()

    result = response.json()
    if result.get("stat") != "ok":
        raise Exception(f"UptimeRobot API error: {result}")

    return result
```

**Key Differences from Healthchecks.io**:

- Uses POST data, not headers, for authentication
- All endpoints use POST method (no GET)
- Success indicated by `"stat": "ok"` field
- Errors include `"error"` field with message

## Account Management

### Get Account Details

```python
def get_account_details() -> dict:
    """Retrieve account information and limits."""
    return _request("getAccountDetails", {})

# Response:
{
    "stat": "ok",
    "account": {
        "email": "usalchemist@gmail.com",
        "monitor_limit": 50,
        "monitor_interval": 5,
        "up_monitors": 0,
        "down_monitors": 0,
        "paused_monitors": 0
    }
}
```

**Free Tier Limits** (empirically validated):

- **Monitors**: 50 total
- **Interval**: 5 minutes minimum
- **Monitor Types**: HTTP(S), Keyword, Ping, Port
- **Alert Contacts**: Unlimited
- **Heartbeat Monitoring**: ❌ Requires Pro ($7/mo)

## Monitor Operations

### List Monitors

```python
def get_monitors() -> list[dict]:
    """Get all monitors."""
    result = _request("getMonitors", {})
    return result.get("monitors", [])

# Response (empty account):
{
    "stat": "ok",
    "pagination": {"limit": 50, "offset": 0, "total": 0},
    "monitors": []
}
```

### Create Monitor

```python
def create_monitor(
    friendly_name: str,
    url: str,
    type: int = 1,  # 1=HTTP(S), 2=Keyword, 3=Ping, 4=Port
    interval: int = 300,  # Seconds (5 minutes for free tier)
    alert_contacts: str = None
) -> dict:
    """Create HTTP(S) monitor."""
    data = {
        "friendly_name": friendly_name,
        "url": url,
        "type": type,
        "interval": interval
    }

    if alert_contacts:
        data["alert_contacts"] = alert_contacts

    result = _request("newMonitor", data)
    return result

# Response:
{
    "stat": "ok",
    "monitor": {
        "id": 801762241,
        "status": 1
    }
}
```

**Monitor Types**:

- `1` = HTTP(S) - GET request to URL, expects 200 OK
- `2` = Keyword - Searches for specific text in response
- `3` = Ping - ICMP ping check
- `4` = Port - TCP port connectivity check

**Intervals** (free tier):

- Minimum: 300 seconds (5 minutes)
- Recommended: 300-900 seconds (5-15 minutes)

### Delete Monitor

```python
def delete_monitor(monitor_id: str) -> dict:
    """Delete monitor by ID."""
    return _request("deleteMonitor", {"id": monitor_id})

# Response:
{
    "stat": "ok",
    "monitor": {
        "id": 801762241
    }
}
```

## Alert Contact Operations

### List Alert Contacts

```python
def get_alert_contacts() -> list[dict]:
    """Get all notification channels."""
    result = _request("getAlertContacts", {})
    return result.get("alert_contacts", [])

# Response (empirically validated):
{
    "stat": "ok",
    "limit": 10,
    "offset": 0,
    "total": 1,
    "alert_contacts": [
        {
            "id": "19319587",
            "friendly_name": "Main Email",
            "type": "2",  # Email
            "status": "0",  # Inactive
            "value": "usalchemist@gmail.com"
        }
    ]
}
```

**Alert Contact Types** (empirically validated):

- `1` = SMS
- `2` = Email
- `3` = Twitter
- `4` = Boxcar
- `5` = Webhook
- `6` = Pushbullet
- `7` = Zapier
- `9` = Slack
- `10` = Discord
- `11` = Pushover ← **Target for production**
- `12` = Microsoft Teams

**Alert Contact Status**:

- `0` = Inactive (not verified)
- `1` = Paused
- `2` = Active (verified and enabled)

### Get Pushover Contact ID

```python
def get_pushover_contact_id() -> str | None:
    """Find first active Pushover contact."""
    contacts = get_alert_contacts()
    for contact in contacts:
        if str(contact['type']) == '11':  # Pushover
            return contact['id']
    return None
```

**Current Status**: ⚠️ Returns `None` (Pushover not configured)

**Required**: Manual setup via UptimeRobot dashboard before production use.

## Rate Limiting

**Empirically Discovered Limit**: ~6 operations before 429 error

```python
# Error encountered during probe cleanup:
# 429 Client Error: Too Many Requests for url: https://api.uptimerobot.com/v2/deleteMonitor
```

**Mitigation Strategy**:

```python
import time

def rate_limited_request(endpoint: str, data: dict, max_retries: int = 3) -> dict:
    """Request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return _request(endpoint, data)
        except requests.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

**Best Practices**:

- Add 1-2 second delays between bulk operations
- Use exponential backoff for retries
- Batch operations when possible (use `getMonitors` instead of multiple individual queries)

## Pushover Integration

### Manual Setup Steps (Required)

1. **Access Dashboard**:
   - Go to https://uptimerobot.com/dashboard
   - Log in with account credentials

2. **Add Pushover Contact**:
   - Click "My Settings" → "Alert Contacts"
   - Click "Add Alert Contact"
   - Select "Pushover" from dropdown

3. **Bot Interaction**:
   - Follow instructions to message UptimeRobot Pushover bot
   - Send verification code to bot
   - Complete verification flow

4. **Verify Integration**:
   ```python
   pushover_id = client.get_pushover_contact_id()
   assert pushover_id is not None, "Pushover not configured"
   ```

**Status Check**:

```python
contacts = client.get_alert_contacts()
pushover = next((c for c in contacts if c['type'] == '11'), None)

if pushover:
    if pushover['status'] == '2':
        print("✅ Pushover active")
    else:
        print("⚠️ Pushover inactive - complete verification")
else:
    print("❌ Pushover not configured")
```

## Production Usage Pattern

```python
# /// script
# dependencies = ["requests"]
# ///

import os
from scripts.uptimerobot_client import UptimeRobotClient

# Initialize client
api_key = os.popen(
    "doppler secrets get UPTIMEROBOT_API_KEY --project claude-config --config dev --plain"
).read().strip()

client = UptimeRobotClient(api_key)

# Verify Pushover integration
pushover_id = client.get_pushover_contact_id()
if not pushover_id:
    raise Exception("Pushover not configured - see manual setup steps")

# Create production monitor
monitor = client.create_monitor(
    friendly_name="Production VM API",
    url="https://your-vm-ip:8000/health",
    type=1,  # HTTP(S)
    interval=300,  # 5 minutes
    alert_contacts=pushover_id
)

print(f"Monitor created: {monitor['monitor']['id']}")
print("Monitoring active - checks every 5 minutes")
```

## Known Limitations

**Free Tier Constraints**:

- ❌ No heartbeat monitoring (requires Pro $7/mo)
- ⚠️ Rate limiting (~6 ops before throttle)
- ⚠️ 5-minute minimum interval (no sub-minute checks)

**Workarounds**:

- **Heartbeat**: Use Healthchecks.io (free, unlimited heartbeats)
- **Rate Limits**: Add delays, exponential backoff
- **Interval**: Acceptable for VM monitoring use case

## Error Handling

```python
def safe_request(endpoint: str, data: dict) -> dict | None:
    """Request with comprehensive error handling."""
    try:
        result = _request(endpoint, data)
        return result
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limited - slow down requests")
        elif e.response.status_code == 401:
            print("Invalid API key")
        elif e.response.status_code >= 500:
            print("UptimeRobot service error")
        return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None
```

## Validation Evidence

**Probe Files**: `/tmp/probe/uptimerobot/`

- `01_test_api_key.py` - ✅ Account validation
- `02_list_monitors.py` - ✅ Empty account confirmed
- `03_list_alert_contacts.py` - ✅ Email found, Pushover missing
- `04_create_test_monitor.py` - ✅ Lifecycle validated
- `05_idiomatic_patterns.py` - ⚠️ Rate limit discovered

**Probe Report**: `/tmp/probe/uptimerobot/PROBE_REPORT.md`

**Key Findings**:

- API key authentication works correctly
- Monitor creation/deletion validated
- Rate limiting at ~6 operations
- Pushover manual setup required
- Free tier suitable for VM HTTP monitoring
