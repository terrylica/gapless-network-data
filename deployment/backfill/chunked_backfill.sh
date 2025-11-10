#!/bin/bash

# chunked_backfill.sh
# Canonical pattern for executing multi-year historical backfills in 1-year chunks
#
# RATIONALE: 1-year chunking prevents OOM failures in Cloud Run Jobs (4GB memory limit)
#            and establishes a safe, reproducible pattern for future 6-8+ year backfills.
#
# USAGE: ./chunked_backfill.sh <START_YEAR> <END_YEAR>
# EXAMPLE: ./chunked_backfill.sh 2020 2025  # Executes 5 chunks: 2020, 2021, 2022, 2023, 2024-2025
#
# PERFORMANCE: Each 1-year chunk (~2.6M blocks) completes in ~1m40s-2m on Cloud Run (4GB, 1 CPU)
#
# REQUIREMENTS:
#   - gcloud CLI authenticated and configured
#   - Cloud Run Job "ethereum-historical-backfill" already created
#   - Service account with BigQuery User + Secret Manager Accessor roles
#   - MOTHERDUCK_TOKEN stored in Google Secret Manager

set -euo pipefail

# Configuration
readonly PROJECT="eonlabs-ethereum-bq"
readonly REGION="us-central1"
readonly JOB_NAME="ethereum-historical-backfill"
readonly CHUNK_SIZE_YEARS=1

# Parse arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <START_YEAR> <END_YEAR>"
    echo "Example: $0 2020 2025"
    exit 1
fi

START_YEAR=$1
END_YEAR=$2

# Validate years
if [ "$START_YEAR" -ge "$END_YEAR" ]; then
    echo "Error: START_YEAR ($START_YEAR) must be less than END_YEAR ($END_YEAR)"
    exit 1
fi

echo "🚀 Starting chunked historical backfill: $START_YEAR-$END_YEAR"
echo "   Project: $PROJECT"
echo "   Region: $REGION"
echo "   Job: $JOB_NAME"
echo "   Chunk size: $CHUNK_SIZE_YEARS year(s)"
echo ""

# Execute chunks sequentially
current_year=$START_YEAR
chunk_num=1
total_chunks=$(( (END_YEAR - START_YEAR + CHUNK_SIZE_YEARS - 1) / CHUNK_SIZE_YEARS ))

while [ "$current_year" -lt "$END_YEAR" ]; do
    next_year=$(( current_year + CHUNK_SIZE_YEARS ))

    # Cap next_year at END_YEAR for final chunk
    if [ "$next_year" -gt "$END_YEAR" ]; then
        next_year=$END_YEAR
    fi

    echo "📦 Chunk $chunk_num/$total_chunks: $current_year-$next_year"
    echo "   Updating Cloud Run Job environment variables..."

    gcloud run jobs update "$JOB_NAME" \
        --update-env-vars "START_YEAR=$current_year,END_YEAR=$next_year" \
        --region "$REGION" \
        --project "$PROJECT" \
        --quiet

    echo "   Executing backfill..."
    gcloud run jobs execute "$JOB_NAME" \
        --region "$REGION" \
        --project "$PROJECT" \
        --wait

    # Check execution status
    execution_status=$(gcloud run jobs executions list \
        --job "$JOB_NAME" \
        --region "$REGION" \
        --project "$PROJECT" \
        --limit 1 \
        --format="value(status.conditions[0].type)")

    if [ "$execution_status" != "Completed" ]; then
        echo "❌ Chunk $chunk_num failed! Status: $execution_status"
        echo "   Investigate logs: gcloud run jobs executions describe <EXECUTION_ID> --region $REGION --project $PROJECT"
        exit 1
    fi

    echo "✅ Chunk $chunk_num complete!"
    echo ""

    current_year=$next_year
    chunk_num=$(( chunk_num + 1 ))
done

echo "🎉 All chunks complete!"
echo "   Total chunks executed: $(( chunk_num - 1 ))"
echo ""
echo "🔍 Verify MotherDuck database:"
echo "   python3 -c \""
echo "   import duckdb"
echo "   conn = duckdb.connect('md:?motherduck_token=<TOKEN>')"
echo "   print(conn.execute('SELECT COUNT(*) FROM ethereum_mainnet.blocks').fetchone())"
echo "   \""
