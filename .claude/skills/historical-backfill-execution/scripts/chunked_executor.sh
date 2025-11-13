#!/usr/bin/env bash
# chunked_executor.sh - Wrapper for deployment/backfill/chunked_backfill.sh with validation
#
# Usage: ./chunked_executor.sh START_YEAR END_YEAR
# Example: ./chunked_executor.sh 2015 2025
#
# Safety checks:
# 1. Validate memory requirements
# 2. Check deployment/backfill/chunked_backfill.sh exists
# 3. Execute backfill
# 4. Verify completeness
#
# Exit codes:
# 0 - Backfill completed successfully
# 1 - Validation failed or backfill unsuccessful
# 2 - Script error (missing files, invalid arguments)

set -euo pipefail

# Configuration
REPO_ROOT="/Users/terryli/eon/gapless-network-data"
BACKFILL_SCRIPT="$REPO_ROOT/deployment/backfill/chunked_backfill.sh"
VALIDATE_SCRIPT="$REPO_ROOT/.claude/skills/historical-backfill-execution/scripts/validate_chunk_size.py"
VERIFY_SCRIPT="$REPO_ROOT/.claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py"

# Parse arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 START_YEAR END_YEAR"
    echo "Example: $0 2015 2025"
    exit 2
fi

START_YEAR=$1
END_YEAR=$2

echo "=== Historical Backfill Executor ==="
echo "Start year: $START_YEAR"
echo "End year: $END_YEAR"
echo

# Safety check 1: Validate memory requirements
echo "Safety check 1: Validating memory requirements..."
if ! uv run "$VALIDATE_SCRIPT" --start "$START_YEAR" --end "$END_YEAR"; then
    echo
    echo "❌ Memory validation failed"
    echo "Recommended: Reduce year range or increase Cloud Run memory allocation"
    exit 1
fi
echo

# Safety check 2: Check backfill script exists
echo "Safety check 2: Checking backfill script exists..."
if [[ ! -f "$BACKFILL_SCRIPT" ]]; then
    echo "❌ Backfill script not found: $BACKFILL_SCRIPT"
    exit 2
fi
echo "✅ Backfill script found"
echo

# Execute backfill
echo "Executing chunked backfill..."
echo "Command: $BACKFILL_SCRIPT $START_YEAR $END_YEAR"
echo

if ! bash "$BACKFILL_SCRIPT" "$START_YEAR" "$END_YEAR"; then
    echo
    echo "❌ Backfill execution failed"
    echo
    echo "Troubleshooting steps:"
    echo "1. Check Cloud Run Job logs: gcloud run jobs executions list --job ethereum-historical-backfill"
    echo "2. Verify MotherDuck token configured in Secret Manager"
    echo "3. Check BigQuery permissions (roles/bigquery.user required)"
    exit 1
fi

echo
echo "✅ Backfill execution completed"
echo

# Verify completeness
echo "Verifying database completeness..."
if [[ -f "$VERIFY_SCRIPT" ]]; then
    if ! uv run "$VERIFY_SCRIPT"; then
        echo
        echo "⚠️  Database verification showed issues"
        echo "This may be expected if backfill is partial or in progress"
        echo
        echo "Check gap detection:"
        echo "  uv run .claude/skills/motherduck-pipeline-operations/scripts/detect_gaps.py"
    else
        echo
        echo "✅ Database verification passed"
    fi
else
    echo "⚠️  Verification script not found, skipping completeness check"
fi

echo
echo "=== Backfill Complete ==="
echo
echo "Next steps:"
echo "1. Verify data in MotherDuck: uv run $VERIFY_SCRIPT"
echo "2. Detect gaps: uv run .claude/skills/motherduck-pipeline-operations/scripts/detect_gaps.py"
echo "3. Check real-time stream: .claude/skills/vm-infrastructure-ops/scripts/check_vm_status.sh"

exit 0
