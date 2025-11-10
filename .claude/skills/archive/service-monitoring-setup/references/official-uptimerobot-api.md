# UptimeRobot API v2 Reference

**Fetched**: 2025-11-09
**Source**: https://uptimerobot.com/api/v2/

## Authentication

The API uses HTTP Basic Access Authentication with three API key types:

- **Account-specific**: All methods on all monitors
- **Monitor-specific**: Only `getMonitors` for single monitor
- **Read-only**: All `get*` endpoints only

API keys are sent in request body. Query parameter allowed only for `getMonitors`.

## Rate Limiting

**Limits by plan:**

- FREE: 10 req/min
- PRO: monitor limit \* 2 req/min (maximum 5000 req/min)

**Response headers:**

- `X-RateLimit-Limit`: Current rate limit
- `X-RateLimit-Remaining`: Calls left in current duration
- `X-RateLimit-Reset`: Epoch time when period ends
- `Retry-After`: Seconds before retry

HTTP status 429 returned when limits exceeded.

## Response Formats

Supported formats: XML, JSON, JSON-P

- Specify via `_format=xml` or `_format=json`
- JSON-P: use `callback=functionName` parameter

## Monitor Status Codes

- `1` = Up
- `2` = Down
- `9` = Paused

## Log Types

- `1` = Down
- `2` = Up
- `98` = Paused
- `99` = Resumed

## Key Endpoints

### POST getAccountDetails

Returns account limits and monitor counts.
**Required:** `api_key`

**Response includes:**

- `email`
- `monitor_limit`
- `monitor_interval`
- `up_monitors`, `down_monitors`, `paused_monitors`

### POST getMonitors

"Swiss-Army knife type of a method for getting any information on monitors."

**Key parameters:**

- `api_key` (required)
- `monitors` (optional, filter by IDs)
- `types` (optional, filter by type)
- `statuses` (optional, filter by status)
- `logs` (set to 1 for notification logs)
- `logs_start_date`, `logs_end_date` (Unix time, Pro Plan only)
- `log_types` (format: `1-2-98`)
- `response_times` (set to 1 for response data)
- `alert_contacts` (set to 1 to return alert contacts)
- `custom_uptime_ratios` (format: `7-30-45`)
- `offset`, `limit` (pagination; default limit 50)
- `search` (filter by URL or friendly_name)

### POST newMonitor

Creates new monitor.

**Required:** `api_key`, `friendly_name`, `url`, `type`

**Type-specific requirements:**

- Port monitoring: requires `sub_type`, `port`
- Keyword monitoring: requires `keyword_type`, `keyword_value`

**Optional parameters:**

- `interval` (seconds)
- `timeout` (1-60 seconds, HTTP/keyword/port only)
- `http_username`, `http_password`
- `http_auth_type` (1=Basic, 2=Digest)
- `http_method`
- `post_type`, `post_value`, `post_content_type`
- `alert_contacts` (format: `457_0_0-373_5_0` where ID_threshold_recurrence separated by underscore)
- `mwindows` (IDs: `345-2986-71`)
- `custom_http_headers` (JSON object)
- `custom_http_statuses` (format: `404:0_200:1`)
- `ignore_ssl_errors`
- `disable_domain_expire_notifications` (0=enable, 1=disable)

### POST editMonitor

**Note:** Monitor type cannot be changed; delete and recreate instead.

**Required:** `api_key`, `id`

**Optional:** Same as newMonitor except `type`, plus:

- `status` (0=pause, 1=resume)

### POST getAlertContacts

Retrieves alert contact configurations.

**Parameters:**

- `api_key` (required)
- Optional filters available

**Response includes alert contact type codes** (empirical validation required for complete list)

### POST newAlertContact

Creates alert contact for notifications.

**Required:** `api_key`, `type`, `value`

**Known Type Codes:**

- `1` = SMS
- `2` = Email
- `3` = Twitter DM
- `4` = Boxcar
- `5` = Web-Hook
- `6` = Pushbullet
- `7` = Zapier
- `9` = Slack
- `10` = Discord
- `11` = Telegram
- **Pushover**: Type code not confirmed (requires empirical validation)

**Pushover Integration:**

- Configuration: Must be set up through web UI at https://uptimerobot.com/dashboard → My Settings → Alert Contacts
- API can list existing Pushover contacts and assign them to monitors
- API cannot create Pushover integrations - web UI configuration required first

### POST deleteMonitor, deleteMWindow, deleteAlertContact

Standard delete endpoints requiring `api_key` and resource `id`.

## Response Structure Example

```json
{
  "stat": "ok",
  "monitor": {
    "id": 777810874,
    "status": 1
  }
}
```

## Error Handling

- `stat`: "ok" for success, "fail" for error
- Failed requests include `error` object with details
