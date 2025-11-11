#!/usr/bin/env bash
#
# Keep-Alive Script for Oracle Cloud Always Free Tier
#
# Purpose: Prevent Oracle Cloud idle reclamation by maintaining >20% CPU usage
# Schedule: Runs every hour via cron (0 * * * *)
# Strategy: CPU-intensive operation for 30 seconds to exceed 20% threshold
#
# Oracle Cloud Idle Reclamation Policy:
#   VMs with <20% CPU/network/memory for 7 consecutive days are reclaimed
#   This script ensures CPU usage spikes above 20% hourly to prevent reclamation
#
# Cost: $0 (CPU usage within Always Free Tier limits)

set -euo pipefail

# ================================================================================
# Configuration
# ================================================================================

# Duration to run CPU-intensive task (seconds)
DURATION=30

# Target CPU usage (percentage)
# Note: 25% target ensures we exceed 20% threshold with margin
TARGET_CPU=25

# Log file
LOG_FILE="$HOME/keep_alive.log"

# ================================================================================
# Keep-Alive Logic
# ================================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

keep_alive() {
    log "Keep-alive started (target: ${TARGET_CPU}% CPU for ${DURATION}s)"

    # CPU-intensive task: Calculate prime numbers using stress-ng
    # If stress-ng not available, fallback to dd + sha256sum
    if command -v stress-ng &> /dev/null; then
        # stress-ng: More precise CPU control
        log "  Using stress-ng (1 CPU worker, ${TARGET_CPU}% load)"
        timeout "${DURATION}s" stress-ng --cpu 1 --cpu-load "${TARGET_CPU}" --quiet 2>/dev/null || true
    else
        # Fallback: dd + sha256sum loop
        log "  Using dd + sha256sum fallback"
        local end_time=$(($(date +%s) + DURATION))

        while [ $(date +%s) -lt $end_time ]; do
            dd if=/dev/zero bs=1M count=100 2>/dev/null | sha256sum > /dev/null
        done
    fi

    log "Keep-alive completed"
}

# ================================================================================
# Main
# ================================================================================

main() {
    # Create log file if it doesn't exist
    touch "$LOG_FILE"

    # Run keep-alive
    keep_alive

    # Rotate log file if > 10MB
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt 10485760 ]; then
        log "Rotating log file (size > 10MB)"
        mv "$LOG_FILE" "${LOG_FILE}.old"
        touch "$LOG_FILE"
    fi
}

main "$@"
