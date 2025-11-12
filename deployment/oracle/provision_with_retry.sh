#!/usr/bin/env bash
#
# Oracle Cloud VM Provisioning with Automatic Retry
#
# Retries VM provisioning every 5 minutes until ARM capacity becomes available.
# This script is necessary because Oracle Free Tier ARM instances are in high demand.
#
# Usage:
#   ./provision_with_retry.sh [max_attempts]
#
# Example:
#   ./provision_with_retry.sh 100  # Try up to 100 times (8+ hours)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROVISION_SCRIPT="$SCRIPT_DIR/provision.sh"

# Configuration
MAX_ATTEMPTS="${1:-288}"  # Default: 288 attempts = 24 hours (5 min intervals)
RETRY_INTERVAL=300        # 5 minutes in seconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

main() {
    log "========================================"
    log "Oracle Cloud VM Provisioning with Retry"
    log "========================================"
    log "Max attempts: $MAX_ATTEMPTS"
    log "Retry interval: ${RETRY_INTERVAL}s ($(($RETRY_INTERVAL / 60)) minutes)"
    log "Max duration: ~$(($MAX_ATTEMPTS * $RETRY_INTERVAL / 3600)) hours"
    log ""

    for ((attempt=1; attempt<=MAX_ATTEMPTS; attempt++)); do
        log "Attempt $attempt of $MAX_ATTEMPTS"
        log "========================================"

        # Try to provision VM
        if "$PROVISION_SCRIPT" vm 2>&1 | tee "/tmp/provision_attempt_$attempt.log"; then
            log ""
            log "✅ VM provisioned successfully on attempt $attempt!"
            log ""
            log "Next steps:"
            log "  1. Run: ./deploy.sh deploy    # Deploy monitoring scripts"
            log "  2. Run: ./deploy.sh test      # Test monitoring"
            log "  3. Run: ./deploy.sh cron      # Configure cron"
            exit 0
        fi

        # Check if this was the last attempt
        if ((attempt == MAX_ATTEMPTS)); then
            error "Failed to provision VM after $MAX_ATTEMPTS attempts"
            error "ARM capacity may be exhausted. Consider:"
            error "  1. Try a different region (edit ~/.oci/config)"
            error "  2. Increase max_attempts and retry"
            error "  3. Wait for off-peak hours (weekends, late night)"
            exit 1
        fi

        # Wait before next attempt
        warn "Failed to provision VM (likely out of ARM capacity)"
        warn "Waiting ${RETRY_INTERVAL}s before attempt $(($attempt + 1))..."
        warn "Press Ctrl+C to cancel"
        sleep "$RETRY_INTERVAL"
        log ""
    done
}

# Handle Ctrl+C gracefully
trap 'echo ""; warn "Provisioning cancelled by user"; exit 130' INT TERM

main "$@"
