#!/bin/bash
#
# verify-documentation-accuracy.sh
#
# Purpose: Verify documentation accuracy by querying primary sources (MotherDuck, git history)
# Usage: ./scripts/verify-documentation-accuracy.sh
# Output: Pass/fail status with specific discrepancies
# Related: MADR-0010 (Documentation Accuracy Standards)
#
# Exit codes:
#   0 - All verification passed
#   1 - Verification failures detected
#   2 - Script error (missing dependencies, connection failure)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verification results
FAILURES=0
WARNINGS=0

echo "=================================================="
echo "Documentation Accuracy Verification"
echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "=================================================="
echo ""

# ================================================
# 1. Verify Block Count
# ================================================
echo "1. Verifying Ethereum block count..."

# Query MotherDuck
BLOCK_COUNT=$(duckdb -c "SELECT COUNT(*) as total_blocks FROM ethereum_mainnet.blocks;" md: 2>/dev/null | grep -E "^[0-9]+$" | head -1 || echo "ERROR")

if [[ "$BLOCK_COUNT" == "ERROR" ]]; then
    echo -e "${RED}✗ FAIL: MotherDuck connection failed${NC}"
    ((FAILURES++))
    BLOCK_COUNT="N/A"
else
    echo -e "${GREEN}✓ PASS: MotherDuck block count: $BLOCK_COUNT${NC}"

    # Verify CLAUDE.md
    CLAUDE_CLAIM=$(grep -o "23\.8M blocks operational" CLAUDE.md || echo "NOT_FOUND")
    if [[ "$CLAUDE_CLAIM" == "NOT_FOUND" ]]; then
        echo -e "${RED}✗ FAIL: CLAUDE.md missing block count claim${NC}"
        ((FAILURES++))
    else
        # Check if 23.8M ≈ actual count (allowing 1% variance)
        EXPECTED_MIN=23600000
        EXPECTED_MAX=24000000
        if (( BLOCK_COUNT >= EXPECTED_MIN && BLOCK_COUNT <= EXPECTED_MAX )); then
            echo -e "${GREEN}✓ PASS: CLAUDE.md block count accurate (23.8M ≈ $BLOCK_COUNT)${NC}"
        else
            echo -e "${RED}✗ FAIL: CLAUDE.md block count inaccurate (23.8M vs $BLOCK_COUNT actual)${NC}"
            ((FAILURES++))
        fi
    fi

    # Verify master-roadmap.yaml
    ROADMAP_CLAIM=$(grep "data_loaded:" specifications/master-project-roadmap.yaml | grep -o "[0-9.]*M" | head -1 || echo "NOT_FOUND")
    if [[ "$ROADMAP_CLAIM" == "NOT_FOUND" ]]; then
        echo -e "${RED}✗ FAIL: master-roadmap.yaml missing block count${NC}"
        ((FAILURES++))
    elif [[ "$ROADMAP_CLAIM" != "23.84M" ]]; then
        echo -e "${RED}✗ FAIL: master-roadmap.yaml incorrect ($ROADMAP_CLAIM vs 23.84M expected)${NC}"
        ((FAILURES++))
    else
        echo -e "${GREEN}✓ PASS: master-roadmap.yaml block count correct (23.84M)${NC}"
    fi
fi

echo ""

# ================================================
# 2. Verify Phase 1 Completion Date
# ================================================
echo "2. Verifying Phase 1 completion date..."

# Get git authoritative commit
GIT_DATE=$(git log --all --format="%ai" --grep="align documentation with operational production state" | head -1 | cut -d' ' -f1 || echo "NOT_FOUND")

if [[ "$GIT_DATE" == "NOT_FOUND" ]]; then
    echo -e "${YELLOW}⚠ WARN: Git authoritative commit not found${NC}"
    ((WARNINGS++))
    GIT_DATE="UNKNOWN"
else
    echo -e "${GREEN}✓ PASS: Git authoritative date: $GIT_DATE${NC}"

    # Verify CLAUDE.md
    CLAUDE_DATE=$(grep "COMPLETED" CLAUDE.md | grep -o "2025-11-[0-9][0-9]" | head -1 || echo "NOT_FOUND")
    if [[ "$CLAUDE_DATE" == "NOT_FOUND" ]]; then
        echo -e "${RED}✗ FAIL: CLAUDE.md missing Phase 1 completion date${NC}"
        ((FAILURES++))
    elif [[ "$CLAUDE_DATE" != "$GIT_DATE" ]]; then
        echo -e "${RED}✗ FAIL: CLAUDE.md incorrect date ($CLAUDE_DATE vs $GIT_DATE actual)${NC}"
        ((FAILURES++))
    else
        echo -e "${GREEN}✓ PASS: CLAUDE.md Phase 1 date correct ($CLAUDE_DATE)${NC}"
    fi

    # Verify master-roadmap.yaml
    ROADMAP_DATE=$(grep "completion_date:" specifications/master-project-roadmap.yaml | grep -o "2025-11-[0-9][0-9]" | head -1 || echo "NOT_FOUND")
    if [[ "$ROADMAP_DATE" == "NOT_FOUND" ]]; then
        echo -e "${RED}✗ FAIL: master-roadmap.yaml missing completion date${NC}"
        ((FAILURES++))
    elif [[ "$ROADMAP_DATE" != "$GIT_DATE" ]]; then
        echo -e "${RED}✗ FAIL: master-roadmap.yaml incorrect date ($ROADMAP_DATE vs $GIT_DATE actual)${NC}"
        ((FAILURES++))
    else
        echo -e "${GREEN}✓ PASS: master-roadmap.yaml completion date correct ($ROADMAP_DATE)${NC}"
    fi
fi

echo ""

# ================================================
# 3. Verify Verification Comments Present
# ================================================
echo "3. Verifying verification comments..."

# Check CLAUDE.md
CLAUDE_COMMENTS=$(grep -c "Verified 2025-11-20 via" CLAUDE.md || echo "0")
if (( CLAUDE_COMMENTS >= 3 )); then
    echo -e "${GREEN}✓ PASS: CLAUDE.md has $CLAUDE_COMMENTS verification comments${NC}"
else
    echo -e "${YELLOW}⚠ WARN: CLAUDE.md has only $CLAUDE_COMMENTS verification comments (expected 3+)${NC}"
    ((WARNINGS++))
fi

# Check master-roadmap.yaml
ROADMAP_COMMENTS=$(grep -c "Verified 2025-11-20 via" specifications/master-project-roadmap.yaml || echo "0")
if (( ROADMAP_COMMENTS >= 2 )); then
    echo -e "${GREEN}✓ PASS: master-roadmap.yaml has $ROADMAP_COMMENTS verification comments${NC}"
else
    echo -e "${YELLOW}⚠ WARN: master-roadmap.yaml has only $ROADMAP_COMMENTS verification comments (expected 2+)${NC}"
    ((WARNINGS++))
fi

echo ""

# ================================================
# 4. Summary
# ================================================
echo "=================================================="
echo "Verification Summary"
echo "=================================================="

if (( FAILURES == 0 )); then
    echo -e "${GREEN}✓ All verification checks passed${NC}"
    if (( WARNINGS > 0 )); then
        echo -e "${YELLOW}⚠ $WARNINGS warnings detected${NC}"
        exit 0
    fi
    exit 0
else
    echo -e "${RED}✗ $FAILURES verification failures detected${NC}"
    if (( WARNINGS > 0 )); then
        echo -e "${YELLOW}⚠ $WARNINGS warnings detected${NC}"
    fi
    echo ""
    echo "Run Plan 0010 to resolve discrepancies:"
    echo "  See: docs/development/plan/0010-documentation-accuracy/plan.md"
    exit 1
fi
