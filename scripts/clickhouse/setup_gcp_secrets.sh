#!/bin/bash
# Setup ClickHouse secrets in GCP Secret Manager for dual-write migration
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - doppler CLI configured
#
# Usage:
#   ./setup_gcp_secrets.sh

set -e

PROJECT="eonlabs-ethereum-bq"

echo "============================================================"
echo "ClickHouse → GCP Secret Manager Setup"
echo "============================================================"
echo ""

# Get credentials from Doppler
echo "[1/3] Fetching credentials from Doppler..."
CH_HOST=$(doppler secrets get CLICKHOUSE_HOST --project aws-credentials --config prd --plain)
CH_PASS=$(doppler secrets get CLICKHOUSE_PASSWORD --project aws-credentials --config prd --plain)
echo "✅ Credentials fetched (host: $CH_HOST)"
echo ""

# Create secrets in GCP
echo "[2/3] Creating secrets in GCP Secret Manager..."

for secret in clickhouse-host clickhouse-password; do
  if gcloud secrets describe "$secret" --project "$PROJECT" &>/dev/null; then
    echo "   $secret: exists (skipping create)"
  else
    echo "   $secret: creating..."
    gcloud secrets create "$secret" --project "$PROJECT" --replication-policy=automatic
  fi
done

# Add versions
echo ""
echo "[3/3] Adding secret versions..."
echo -n "$CH_HOST" | gcloud secrets versions add clickhouse-host --data-file=- --project "$PROJECT"
echo "   ✅ clickhouse-host version added"

echo -n "$CH_PASS" | gcloud secrets versions add clickhouse-password --data-file=- --project "$PROJECT"
echo "   ✅ clickhouse-password version added"

echo ""
echo "============================================================"
echo "✅ GCP SECRETS SETUP COMPLETE"
echo "============================================================"
echo ""
echo "Secrets created:"
echo "  - clickhouse-host"
echo "  - clickhouse-password"
echo ""
echo "Next steps:"
echo "  1. Deploy VM collector: cd deployment/vm && ./deploy.sh"
echo "  2. Deploy Cloud Run: gcloud run jobs update..."
echo "  3. Deploy Cloud Function: gcloud functions deploy..."
echo ""
