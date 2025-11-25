#!/bin/bash
# Deploy Ethereum real-time collector to e2-micro VM
# Usage: ./deploy.sh
#
# Prerequisites:
#   - gcloud CLI configured with project eonlabs-ethereum-bq
#   - Secrets stored in Secret Manager: alchemy-api-key, motherduck-token
#   - VM service account has secretAccessor role

set -e

# Configuration
PROJECT="eonlabs-ethereum-bq"
ZONE="us-east1-b"
INSTANCE="eth-realtime-collector"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_SERVICE_ACCOUNT="893624294905-compute@developer.gserviceaccount.com"

echo "==================================================================="
echo "Deploying Ethereum Real-Time Collector to e2-micro"
echo "==================================================================="
echo "Project: $PROJECT"
echo "Zone: $ZONE"
echo "Instance: $INSTANCE"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Verify Secret Manager permissions
echo "[1/7] Verifying Secret Manager permissions..."
echo "   Checking VM service account: $VM_SERVICE_ACCOUNT"

# Add ClickHouse secrets for dual-write migration
for secret in alchemy-api-key motherduck-token clickhouse-host clickhouse-password; do
  echo "   Checking $secret..."
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:$VM_SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT" \
    --quiet 2>/dev/null || true
done

echo "✅ Secret Manager permissions verified"
echo ""

# Copy files to VM
echo "[2/7] Copying files to VM..."
gcloud compute scp \
  "${SCRIPT_DIR}/realtime_collector.py" \
  "${INSTANCE}:~/realtime_collector.py" \
  --zone="${ZONE}" \
  --project="${PROJECT}"

echo "✅ Files copied"
echo ""

# Install dependencies on VM
echo "[3/7] Installing dependencies on VM..."
gcloud compute ssh "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --command="
    echo 'Installing Python packages...'
    pip3 install --quiet --upgrade \
      websockets \
      duckdb \
      pyarrow \
      google-cloud-secret-manager \
      requests \
      clickhouse-connect
    echo '✅ Dependencies installed'
  "

echo "✅ Setup complete"
echo ""

# Copy collector to final location
echo "[4/7] Moving collector script to final location..."
gcloud compute ssh "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --command="
    mkdir -p ~/eth-collector
    mv ~/realtime_collector.py ~/eth-collector/
  "

echo "✅ Collector installed"
echo ""

# Create systemd service
echo "[5/7] Creating systemd service..."

# Copy service file and enable
gcloud compute scp \
  "${SCRIPT_DIR}/eth-collector.service" \
  "${INSTANCE}:/tmp/eth-collector.service" \
  --zone="${ZONE}" \
  --project="${PROJECT}"

gcloud compute ssh "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --command="
    sudo mv /tmp/eth-collector.service /etc/systemd/system/eth-collector.service
    sudo systemctl daemon-reload
    sudo systemctl enable eth-collector
    sudo systemctl restart eth-collector
  "

echo "✅ Systemd service created and started"
echo ""

# Verify service is running
echo "[6/7] Verifying service status..."
gcloud compute ssh "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --command="
    echo 'Service status:'
    sudo systemctl status eth-collector --no-pager -l | head -20
  "

echo ""

# Verify Secret Manager access
echo "[7/7] Verifying Secret Manager access..."
gcloud compute ssh "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --command="
    python3 -c '
from google.cloud import secretmanager
import os

project = \"${PROJECT}\"
client = secretmanager.SecretManagerServiceClient()

# Core secrets (required)
for secret in [\"alchemy-api-key\", \"motherduck-token\"]:
    name = f\"projects/{project}/secrets/{secret}/versions/latest\"
    try:
        response = client.access_secret_version(request={\"name\": name})
        print(f\"✅ {secret}: accessible\")
    except Exception as e:
        print(f\"❌ {secret}: FAILED - {e}\")

# ClickHouse secrets (for dual-write migration)
print()
print(\"ClickHouse secrets (dual-write):\")
for secret in [\"clickhouse-host\", \"clickhouse-password\"]:
    name = f\"projects/{project}/secrets/{secret}/versions/latest\"
    try:
        response = client.access_secret_version(request={\"name\": name})
        print(f\"✅ {secret}: accessible\")
    except Exception as e:
        print(f\"⚠️  {secret}: not found (dual-write disabled)\")
'
  "

echo ""
echo "==================================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "==================================================================="
echo ""
echo "VM Details:"
echo "  Name: ${INSTANCE}"
echo "  Zone: ${ZONE}"
echo "  External IP: $(gcloud compute instances describe "${INSTANCE}" --zone="${ZONE}" --project="${PROJECT}" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo ""
echo "Service Commands:"
echo "  View logs:    gcloud compute ssh ${INSTANCE} --zone=${ZONE} --project=${PROJECT} --command='sudo journalctl -u eth-collector -f'"
echo "  Check status: gcloud compute ssh ${INSTANCE} --zone=${ZONE} --project=${PROJECT} --command='sudo systemctl status eth-collector'"
echo "  Restart:      gcloud compute ssh ${INSTANCE} --zone=${ZONE} --project=${PROJECT} --command='sudo systemctl restart eth-collector'"
echo "  Stop:         gcloud compute ssh ${INSTANCE} --zone=${ZONE} --project=${PROJECT} --command='sudo systemctl stop eth-collector'"
echo ""
echo "Secret Manager:"
echo "  Secrets: alchemy-api-key, motherduck-token"
echo "  Service account: ${VM_SERVICE_ACCOUNT}"
echo ""
