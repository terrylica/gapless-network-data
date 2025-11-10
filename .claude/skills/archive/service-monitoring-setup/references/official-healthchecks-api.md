# Healthchecks.io Management API v3 Reference

**Fetched**: 2025-11-09
**Source**: https://healthchecks.io/docs/api/

## Check Creation Endpoint

**Endpoint:** `POST https://healthchecks.io/api/v3/checks/`

**Authentication:** Include `X-Api-Key: <your-api-key>` header or add `"api_key"` field to JSON body.

### Required/Optional Fields

**All parameters are optional with sensible defaults:**

- `name` (string): Check identifier
- `slug` (string): Custom URL-friendly identifier using `a-z`, `0-9`, hyphens, underscores
- `tags` (string): Space-delimited list
- `desc` (string): Description
- `timeout` (number): Expected period in seconds (60–31,536,000)
- `grace` (number): Grace period in seconds (60–31,536,000), default 3600
- `schedule` (string): Cron or systemd OnCalendar expression
- `tz` (string): Timezone (default: "UTC")
- `manual_resume` (boolean): Whether paused checks ignore pings
- `methods` (string): "" allows HEAD/GET/POST; "POST" restricts to POST only
- `channels` (string): Integration assignment ("*" for all, UUID list, or names)

**Example Request:**
```bash
curl https://healthchecks.io/api/v3/checks/ \
  --header "X-Api-Key: your-api-key" \
  --data '{"name": "Backups", "tags": "prod www", "timeout": 3600, "grace": 60}'
```

**Response Codes:**
- `201 Created`: New check successfully created
- `200 OK`: Existing check found and updated (with `unique` parameter)
- `400 Bad Request`: Invalid schema or field values
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Account check limit exceeded (20 for free tier)

## Ping Mechanics

Pings use check-specific URLs returned in responses (e.g., `https://hc-ping.com/[uuid]`).

**Ping Response Types** logged include:
- `type`: "success", "start", "fail"
- `duration`: Script execution time
- `date`: Timestamp
- `method`: HTTP method used
- `remote_addr`: Client IP

Pings can include request bodies and optional headers for filtering via keywords.

## Channel/Integration Management

**List Integrations:** `GET https://healthchecks.io/api/v3/channels/`

Response structure:
```json
{
  "channels": [
    {
      "id": "uuid-format",
      "name": "Integration Name",
      "kind": "email|sms|pushover|etc"
    }
  ]
}
```

**Assign to Checks:**
- Use integration UUID: `"channels": "4ec5a071-2d08-4baa-898a-eb4eb3cd6941"`
- Use integration name: `"channels": "My Work Email"`
- Assign all: `"channels": "*"`
- Remove all: `"channels": ""`

**Pushover Integration:**
- Kind: `"pushover"`
- Configuration: Must be set up through web UI at https://healthchecks.io/projects → Integrations
- Requires: Pushover application API token and subscription URL
- API cannot create Pushover integrations - only list and assign existing ones

## Error Response Handling

**HTTP Status Codes:**
- `2xx`: Success
- `4xx`: Client error (invalid key, malformed request, resource not found)
- `5xx`: Server error
- `409 Conflict`: Check not in expected state (e.g., attempting to resume non-paused check)

Example error scenarios:
- `401 Unauthorized`: API key missing or invalid
- `403 Forbidden`: Access denied; wrong key for resource
- `404 Not Found`: Check or resource does not exist
- `400 Bad Request`: Schema violation or invalid field values

## Authentication Methods

1. **Header-based:** `X-Api-Key: <your-api-key>`
2. **JSON body-based:** Include `"api_key": "your-api-key"` field in POST request body

**Key Types:**
- **Read-write:** Full access to all endpoints
- **Read-only:** Access to list, get, flips, and badges endpoints only; omits sensitive fields (`uuid`, `ping_url`, `update_url`, `pause_url`, `resume_url`, `channels`)

## Rate Limits

Not specified in official documentation (appears to have "reasonable use" policy for free tier).
