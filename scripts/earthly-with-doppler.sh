#!/bin/bash
# Wrapper script to run Earthly with Doppler secrets
# Usage: ./scripts/earthly-with-doppler.sh +test-schema-e2e
set -euo pipefail

DOPPLER_PROJECT="gapless-network-data"
DOPPLER_CONFIG="prd"

SECRETS_FILE=$(mktemp)
trap "rm -f $SECRETS_FILE" EXIT

echo "Fetching ClickHouse secrets from Doppler..."
# Earthly --secret-file expects KEY=value format without quotes
doppler secrets download \
    --project "$DOPPLER_PROJECT" \
    --config "$DOPPLER_CONFIG" \
    --format env \
    --no-file | grep -E '^CLICKHOUSE_' | sed 's/"//g' > "$SECRETS_FILE"

echo "Running: earthly $*"
earthly --secret-file-path="$SECRETS_FILE" "$@"
