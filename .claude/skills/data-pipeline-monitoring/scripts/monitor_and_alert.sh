#!/bin/bash
#
# Monitor pipeline health and send Pushover alerts on failures.
#
# Usage:
#     ./monitor_and_alert.sh
#
# Environment:
#     PUSHOVER_TOKEN: Pushover API token (from Doppler)
#     PUSHOVER_USER: Pushover user key (from Doppler)
#
# Exit codes:
#     0: All checks OK
#     1: Critical failure detected (alert sent)
#

set -euo pipefail

# Configuration
GCP_PROJECT="eonlabs-ethereum-bq"
CLOUD_RUN_JOB="eth-md-updater"
CLOUD_RUN_REGION="us-central1"
VM_NAME="eth-realtime-collector"
VM_ZONE="us-east1-b"
SYSTEMD_SERVICE="eth-collector"

# Load Pushover credentials from Doppler
export PUSHOVER_TOKEN=$(doppler secrets get PUSHOVER_TOKEN --project claude-config --config dev --plain)
export PUSHOVER_USER=$(doppler secrets get PUSHOVER_USER --project claude-config --config dev --plain)

# Temporary file for health check results
HEALTH_CHECK_RESULT=$(mktemp)

# Cleanup on exit
trap "rm -f $HEALTH_CHECK_RESULT" EXIT

echo "Running pipeline health check..."

# Run health check with JSON output
python3 check_pipeline_health.py \
  --gcp-project "$GCP_PROJECT" \
  --cloud-run-job "$CLOUD_RUN_JOB" \
  --region "$CLOUD_RUN_REGION" \
  --vm-name "$VM_NAME" \
  --vm-zone "$VM_ZONE" \
  --systemd-service "$SYSTEMD_SERVICE" \
  --json > "$HEALTH_CHECK_RESULT"

HEALTH_CHECK_EXIT_CODE=$?

# Send Pushover alert if there are issues
if [ $HEALTH_CHECK_EXIT_CODE -ne 0 ]; then
    echo "Health check failed, sending Pushover alert..."

    uv run send_pushover_alert.py \
      --health-check-json "$HEALTH_CHECK_RESULT"

    echo "Alert sent."
    exit 1
else
    echo "✅ All pipeline components operational"
    exit 0
fi
