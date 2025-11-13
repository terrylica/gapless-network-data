#!/usr/bin/env bash
# check_vm_status.sh - Automated VM status check via gcloud
#
# Usage: ./check_vm_status.sh
#
# Checks:
# 1. VM instance status (running/stopped)
# 2. eth-collector systemd service status
# 3. Recent logs (last 10 lines)
#
# Exit codes:
# 0 - VM and service healthy
# 1 - VM or service unhealthy
# 2 - gcloud command failed

set -euo pipefail

# Configuration
VM_NAME="eth-realtime-collector"
ZONE="us-east1-b"
SERVICE_NAME="eth-collector"

echo "=== VM Infrastructure Status Check ==="
echo "VM: $VM_NAME"
echo "Zone: $ZONE"
echo "Service: $SERVICE_NAME"
echo

# Check VM instance status
echo "1. Checking VM instance status..."
if ! VM_STATUS=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format="value(status)" 2>&1); then
    echo "❌ Failed to get VM status: $VM_STATUS"
    exit 2
fi

echo "VM Status: $VM_STATUS"

if [[ "$VM_STATUS" != "RUNNING" ]]; then
    echo "❌ VM is not running"
    exit 1
fi

echo "✅ VM is running"
echo

# Check systemd service status
echo "2. Checking eth-collector systemd service..."
if ! SERVICE_STATUS=$(gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo systemctl is-active $SERVICE_NAME" 2>&1); then
    echo "❌ Failed to check service status: $SERVICE_STATUS"
    exit 2
fi

echo "Service Status: $SERVICE_STATUS"

if [[ "$SERVICE_STATUS" != "active" ]]; then
    echo "❌ Service is not active"

    # Get detailed status
    echo
    echo "Detailed service status:"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
        --command="sudo systemctl status $SERVICE_NAME" || true

    exit 1
fi

echo "✅ Service is active"
echo

# Check recent logs
echo "3. Recent logs (last 10 lines)..."
if ! gcloud compute ssh "$VM_NAME" --zone="$ZONE" \
    --command="sudo journalctl -u $SERVICE_NAME -n 10 --no-pager" 2>&1; then
    echo "❌ Failed to retrieve logs"
    exit 2
fi

echo
echo "=== Status Check Complete ==="
echo "✅ All checks passed"
exit 0
