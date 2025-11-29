#!/bin/bash
# Lint links in documentation using lychee
#
# This script runs lychee with the correct options to handle
# repository-relative links (paths starting with /).
#
# Usage:
#   ./scripts/lint-links.sh              # Check all links
#   ./scripts/lint-links.sh --offline    # Check only local files
#   ./scripts/lint-links.sh docs/        # Check specific directory
#   ./scripts/lint-links.sh --offline .  # Check local files only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Collect lychee options and inputs separately
LYCHEE_OPTS=(
  --base-url "file://$PWD"
  --config ".lychee.toml"
  --no-progress
)

INPUTS=()
EXTRA_OPTS=()

for arg in "$@"; do
  if [[ "$arg" == --* ]]; then
    EXTRA_OPTS+=("$arg")
  else
    INPUTS+=("$arg")
  fi
done

# Default to current directory if no inputs specified
if [[ ${#INPUTS[@]} -eq 0 ]]; then
  INPUTS=(".")
fi

# Run lychee with options then inputs
lychee "${LYCHEE_OPTS[@]}" "${EXTRA_OPTS[@]}" "${INPUTS[@]}"
