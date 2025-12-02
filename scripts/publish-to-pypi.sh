#!/bin/bash
# publish-to-pypi.sh - Local-only PyPI publishing with Doppler credentials
#
# WORKSPACE-WIDE POLICY: This script must ONLY run on local machines, NEVER in CI/CD.
# See: ADR-0027, docs/development/PUBLISHING.md

set -euo pipefail

# Source shell profile to get mise/uv in PATH
if [[ -f ~/.zshrc ]]; then
    source ~/.zshrc 2>/dev/null || true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Publishing to PyPI (Local Workflow)${NC}"
echo "======================================"
echo ""

# ==============================================================================
# CI Detection Guards - CRITICAL SECURITY CHECK
# ==============================================================================

CI_DETECTED=false
CI_VARS=""

if [[ -n "${CI:-}" ]]; then
    CI_DETECTED=true
    CI_VARS="$CI_VARS\n   - CI: $CI"
fi

if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    CI_DETECTED=true
    CI_VARS="$CI_VARS\n   - GITHUB_ACTIONS: $GITHUB_ACTIONS"
fi

if [[ -n "${GITLAB_CI:-}" ]]; then
    CI_DETECTED=true
    CI_VARS="$CI_VARS\n   - GITLAB_CI: $GITLAB_CI"
fi

if [[ -n "${JENKINS_URL:-}" ]]; then
    CI_DETECTED=true
    CI_VARS="$CI_VARS\n   - JENKINS_URL: $JENKINS_URL"
fi

if [[ -n "${CIRCLECI:-}" ]]; then
    CI_DETECTED=true
    CI_VARS="$CI_VARS\n   - CIRCLECI: $CIRCLECI"
fi

if [[ "$CI_DETECTED" == "true" ]]; then
    echo -e "${RED}❌ ERROR: This script must ONLY be run on your LOCAL machine${NC}"
    echo ""
    echo -e "   Detected CI environment variables:$CI_VARS"
    echo ""
    echo "   This project enforces LOCAL-ONLY PyPI publishing for:"
    echo "   - Security: No long-lived PyPI tokens in GitHub secrets"
    echo "   - Speed: 30 seconds locally vs 3-5 minutes in CI"
    echo "   - Control: Manual approval step before production release"
    echo ""
    echo "   See: docs/development/PUBLISHING.md (ADR-0027)"
    exit 1
fi

# ==============================================================================
# Repository Verification - Prevent fork abuse
# ==============================================================================

EXPECTED_REPO="terrylica/gapless-network-data"
CURRENT_REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]\(.*\)\.git/\1/' || echo "unknown")

if [[ "$CURRENT_REPO" != "$EXPECTED_REPO" ]]; then
    echo -e "${RED}❌ ERROR: Repository mismatch${NC}"
    echo "   Expected: $EXPECTED_REPO"
    echo "   Got: $CURRENT_REPO"
    echo ""
    echo "   This script can only publish from the official repository."
    exit 1
fi

# ==============================================================================
# Step 0: Verify Doppler credentials
# ==============================================================================

echo -e "${YELLOW}🔐 Step 0: Verifying Doppler credentials...${NC}"

if ! command -v doppler &> /dev/null; then
    echo -e "${RED}❌ Doppler CLI not installed${NC}"
    echo "   Install with: brew install dopplerhq/cli/doppler"
    exit 1
fi

PYPI_TOKEN=$(doppler secrets get PYPI_TOKEN --project claude-config --config prd --plain 2>/dev/null || echo "")

if [[ -z "$PYPI_TOKEN" ]]; then
    echo -e "${RED}❌ PYPI_TOKEN not found in Doppler${NC}"
    echo "   Run: doppler secrets set PYPI_TOKEN='your-token' --project claude-config --config prd"
    exit 1
fi

echo -e "   ${GREEN}✅ Doppler token verified${NC}"
echo ""

# ==============================================================================
# Step 1: Pull latest release commit
# ==============================================================================

echo -e "${YELLOW}📥 Step 1: Pulling latest release commit...${NC}"
git pull origin main --quiet

VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "   Current version: ${GREEN}v${VERSION}${NC}"
echo ""

# ==============================================================================
# Step 2: Clean old builds
# ==============================================================================

echo -e "${YELLOW}🧹 Step 2: Cleaning old builds...${NC}"
rm -rf dist/ build/ *.egg-info/
echo -e "   ${GREEN}✅ Cleaned${NC}"
echo ""

# ==============================================================================
# Step 3: Build package
# ==============================================================================

echo -e "${YELLOW}📦 Step 3: Building package...${NC}"
uv build --quiet

WHEEL=$(ls dist/*.whl 2>/dev/null | head -1)
if [[ -z "$WHEEL" ]]; then
    echo -e "${RED}❌ Build failed - no wheel found${NC}"
    exit 1
fi

echo -e "   ${GREEN}✅ Built: ${WHEEL}${NC}"
echo ""

# ==============================================================================
# Step 4: Publish to PyPI
# ==============================================================================

echo -e "${YELLOW}📤 Step 4: Publishing to PyPI...${NC}"
echo "   Using PYPI_TOKEN from Doppler"

UV_PUBLISH_TOKEN="${PYPI_TOKEN}" uv publish --quiet

echo -e "   ${GREEN}✅ Published to PyPI${NC}"
echo ""

# ==============================================================================
# Step 5: Verify on PyPI
# ==============================================================================

echo -e "${YELLOW}🔍 Step 5: Verifying on PyPI...${NC}"
PACKAGE_NAME=$(grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PYPI_URL="https://pypi.org/project/${PACKAGE_NAME}/${VERSION}/"

# Wait a moment for PyPI to index
sleep 3

if curl -s -o /dev/null -w "%{http_code}" "$PYPI_URL" | grep -q "200"; then
    echo -e "   ${GREEN}✅ Verified: ${PYPI_URL}${NC}"
else
    echo -e "   ${YELLOW}⚠️  Package published but may take a few minutes to appear${NC}"
    echo "   Check: ${PYPI_URL}"
fi

echo ""
echo -e "${GREEN}✅ Complete! Published v${VERSION} to PyPI${NC}"
