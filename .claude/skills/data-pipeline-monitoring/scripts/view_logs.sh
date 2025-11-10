#!/bin/bash
# Universal log viewing script for GCP data pipelines
#
# Supports:
# - Cloud Run Jobs
# - VM systemd services
# - Cloud Logging queries
#
# Usage:
#   ./view_logs.sh --type cloud-run --project PROJECT --job JOB [--lines N] [--follow] [--filter PATTERN]
#   ./view_logs.sh --type systemd --project PROJECT --vm VM --zone ZONE --service SERVICE [--lines N] [--follow] [--filter PATTERN]

set -e

# Defaults
TYPE=""
PROJECT=""
VM_NAME=""
VM_ZONE=""
SERVICE_NAME=""
JOB_NAME=""
REGION="us-east1"
LINES=50
FOLLOW=false
FILTER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            TYPE="$2"
            shift 2
            ;;
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --vm)
            VM_NAME="$2"
            shift 2
            ;;
        --zone)
            VM_ZONE="$2"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --job)
            JOB_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --lines)
            LINES="$2"
            shift 2
            ;;
        --follow|-f)
            FOLLOW=true
            shift
            ;;
        --filter)
            FILTER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$TYPE" ]]; then
    echo "Error: --type required (cloud-run or systemd)"
    exit 1
fi

if [[ -z "$PROJECT" ]]; then
    echo "Error: --project required"
    exit 1
fi

# View Cloud Run Job logs
if [[ "$TYPE" == "cloud-run" ]]; then
    if [[ -z "$JOB_NAME" ]]; then
        echo "Error: --job required for cloud-run type"
        exit 1
    fi

    echo "Viewing Cloud Run Job logs: $JOB_NAME"
    echo "Project: $PROJECT, Region: $REGION"
    echo "Lines: $LINES, Follow: $FOLLOW, Filter: ${FILTER:-none}"
    echo ""

    if [[ "$FOLLOW" == true ]]; then
        # Follow mode requires polling
        echo "Note: Cloud Run logs don't support native --follow, polling every 5 seconds..."
        while true; do
            gcloud logging read \
                "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
                --limit "$LINES" \
                --project "$PROJECT" \
                --format "value(timestamp,severity,textPayload)" \
                | grep -E "${FILTER:-.}" || true
            echo "--- Refreshing in 5 seconds (Ctrl+C to stop) ---"
            sleep 5
        done
    else
        # One-time fetch
        gcloud logging read \
            "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
            --limit "$LINES" \
            --project "$PROJECT" \
            --format "value(timestamp,severity,textPayload)" \
            | grep -E "${FILTER:-.}"
    fi

# View VM systemd service logs
elif [[ "$TYPE" == "systemd" ]]; then
    if [[ -z "$VM_NAME" || -z "$VM_ZONE" || -z "$SERVICE_NAME" ]]; then
        echo "Error: --vm, --zone, and --service required for systemd type"
        exit 1
    fi

    echo "Viewing systemd service logs: $SERVICE_NAME"
    echo "VM: $VM_NAME, Zone: $VM_ZONE, Project: $PROJECT"
    echo "Lines: $LINES, Follow: $FOLLOW, Filter: ${FILTER:-none}"
    echo ""

    FOLLOW_FLAG=""
    if [[ "$FOLLOW" == true ]]; then
        FOLLOW_FLAG="-f"
    fi

    GREP_CMD=""
    if [[ -n "$FILTER" ]]; then
        GREP_CMD="| grep -E '$FILTER'"
    fi

    gcloud compute ssh "$VM_NAME" \
        --zone="$VM_ZONE" \
        --project="$PROJECT" \
        --command="sudo journalctl -u $SERVICE_NAME $FOLLOW_FLAG -n $LINES $GREP_CMD"

else
    echo "Error: Invalid type '$TYPE'. Must be 'cloud-run' or 'systemd'"
    exit 1
fi
