#!/usr/bin/env bash
# restart_collector.sh - Safe restart with pre-checks
#
# Usage: ./restart_collector.sh
#
# Safety checks:
# 1. Verify VM is running
# 2. Check current service status
# 3. Restart service
# 4. Verify service restarted successfully
# 5. Monitor logs for 30 seconds
#
# Exit codes:
# 0 - Service restarted successfully
# 1 - Pre-check failed or restart unsuccessful
# 2 - gcloud command failed

set -euo pipefail

# Configuration
VM_NAME="eth-realtime-collector"
ZONE="us-east1-b"
SERVICE_NAME="eth-collector"
MONITOR_DURATION=30  # seconds

echo "=== Safe Service Restart ==="
echo "VM: $VM_NAME"
echo "Zone: $ZONE"
echo "Service: $SERVICE_NAME"
echo

# Pre-check 1: Verify VM is running
echo "Pre-check 1: Verifying VM is running..."
if ! VM_STATUS=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)" 2>&1); then
    echo "❌ Failed to get VM status: $VM_STATUS"
    exit 2
fi

if [[ "$VM_STATUS" != "RUNNING" ]]; then
    echo "❌ VM is not running (status: $VM_STATUS)"
    echo "Start VM first: gcloud compute instances start $VM_NAME --zone=$ZONE"
    exit 1
fi

echo "✅ VM is running"
echo

# Pre-check 2: Check current service status
echo "Pre-check 2: Checking current service status..."
if ! CURRENT_STATUS=$(gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo systemctl is-active $SERVICE_NAME" 2>&1); then
    echo "⚠️  Service is not currently active: $CURRENT_STATUS"
    echo "This may be expected if service is already stopped."
else
    echo "Current service status: $CURRENT_STATUS"
fi

echo
echo "Proceeding with restart..."
echo

# Restart service
echo "Restarting $SERVICE_NAME..."
if ! gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo systemctl restart $SERVICE_NAME" 2>&1; then
    echo "❌ Failed to restart service"
    exit 2
fi

echo "✅ Restart command executed"
echo

# Wait 3 seconds for service to stabilize
echo "Waiting 3 seconds for service to stabilize..."
sleep 3

# Verify service restarted successfully
echo "Verifying service status..."
if ! NEW_STATUS=$(gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo systemctl is-active $SERVICE_NAME" 2>&1); then
    echo "❌ Service failed to start: $NEW_STATUS"

    echo
    echo "Detailed service status:"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
        --command="sudo systemctl status $SERVICE_NAME" || true

    exit 1
fi

if [[ "$NEW_STATUS" != "active" ]]; then
    echo "❌ Service is not active (status: $NEW_STATUS)"

    echo
    echo "Detailed service status:"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
        --command="sudo systemctl status $SERVICE_NAME" || true

    exit 1
fi

echo "✅ Service is active"
echo

# Monitor logs for 30 seconds
echo "Monitoring logs for $MONITOR_DURATION seconds..."
echo "Press Ctrl+C to stop monitoring"
echo

if ! timeout "$MONITOR_DURATION" gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo journalctl -u $SERVICE_NAME -f" 2>&1; then
    # timeout command exits with 124 when time expires, which is expected
    if [[ $? -eq 124 ]]; then
        echo
        echo "Monitoring complete (${MONITOR_DURATION}s elapsed)"
    else
        echo "❌ Failed to monitor logs"
        exit 2
    fi
fi

echo
echo "=== Restart Complete ==="
echo "✅ Service restarted successfully"
echo
echo "Next steps:"
echo "1. Verify data flow: uv run scripts/clickhouse/verify_blocks.py"
echo "2. Check ClickHouse for latest blocks within last 60 seconds"
exit 0
