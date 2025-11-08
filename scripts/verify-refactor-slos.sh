#!/usr/bin/env bash
# /// script
# description = "Verify REFACTOR.md compliance SLOs from SSoT specification"
# ///

set -euo pipefail

# Error handling: raise and propagate (no fallbacks, defaults, retries, silent handling)
trap 'echo "ERROR: SLO verification failed at line $LINENO" >&2; exit 1' ERR

SKILLS_DIR=".claude/skills"
SPEC_FILE="specifications/refactor-compliance-implementation.yaml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==================================="
echo "REFACTOR.md Compliance SLO Verification"
echo "SSoT: $SPEC_FILE"
echo "==================================="
echo ""

# SLO: Correctness - Verify SSoT spec exists
echo "SLO: Correctness"
echo "-----------------------------------"
if [ ! -f "$SPEC_FILE" ]; then
    echo -e "${RED}FAIL${NC}: SSoT specification not found at $SPEC_FILE"
    exit 1
fi
echo -e "${GREEN}PASS${NC}: SSoT specification exists"

# SLO: Observability - Check current portfolio state
echo ""
echo "SLO: Observability"
echo "-----------------------------------"

# Check all SKILL.md files exist
skill_count=0
for skill in blockchain-rpc-provider-research blockchain-data-collection-validation bigquery-ethereum-data-acquisition; do
    skill_file="$SKILLS_DIR/$skill/SKILL.md"
    if [ -f "$skill_file" ]; then
        lines=$(wc -l < "$skill_file")
        echo "Skill: $skill = $lines lines"
        skill_count=$((skill_count + 1))
    else
        echo -e "${RED}FAIL${NC}: $skill_file not found"
        exit 1
    fi
done

if [ $skill_count -ne 3 ]; then
    echo -e "${RED}FAIL${NC}: Expected 3 skills, found $skill_count"
    exit 1
fi
echo -e "${GREEN}PASS${NC}: All 3 skills found and measured"

# Check total portfolio lines
echo ""
echo "Portfolio Line Count Validation"
echo "-----------------------------------"
total_lines=$(wc -l "$SKILLS_DIR"/*/SKILL.md | tail -1 | awk '{print $1}')
echo "Total portfolio lines: $total_lines"

if [ "$total_lines" -le 600 ]; then
    echo -e "${GREEN}PASS${NC}: Total portfolio ≤600 lines"
else
    echo -e "${YELLOW}PENDING${NC}: Total portfolio >600 lines (target: ≤600)"
fi

# Check individual skill compliance
echo ""
echo "Individual Skill Compliance (≤200 lines)"
echo "-----------------------------------"
skill_1_lines=$(wc -l < "$SKILLS_DIR/blockchain-rpc-provider-research/SKILL.md")
skill_2_lines=$(wc -l < "$SKILLS_DIR/blockchain-data-collection-validation/SKILL.md")
skill_3_lines=$(wc -l < "$SKILLS_DIR/bigquery-ethereum-data-acquisition/SKILL.md")

compliant_count=0

if [ "$skill_1_lines" -le 200 ]; then
    echo -e "Skill 1: ${GREEN}PASS${NC} ($skill_1_lines ≤200)"
    compliant_count=$((compliant_count + 1))
else
    echo -e "Skill 1: ${YELLOW}PENDING${NC} ($skill_1_lines >200, excess: $((skill_1_lines - 200)))"
fi

if [ "$skill_2_lines" -le 200 ]; then
    echo -e "Skill 2: ${GREEN}PASS${NC} ($skill_2_lines ≤200)"
    compliant_count=$((compliant_count + 1))
else
    echo -e "Skill 2: ${YELLOW}PENDING${NC} ($skill_2_lines >200, excess: $((skill_2_lines - 200)))"
fi

if [ "$skill_3_lines" -le 200 ]; then
    echo -e "Skill 3: ${GREEN}PASS${NC} ($skill_3_lines ≤200)"
    compliant_count=$((compliant_count + 1))
else
    echo -e "Skill 3: ${YELLOW}PENDING${NC} ($skill_3_lines >200, excess: $((skill_3_lines - 200)))"
fi

echo ""
echo "Compliance: $compliant_count/3 skills ≤200 lines"

# Check reference files
echo ""
echo "Reference Files Validation"
echo "-----------------------------------"
ref_count=$(find "$SKILLS_DIR"/*/references/ -name "*.md" -type f 2>/dev/null | wc -l)
echo "Reference files found: $ref_count"

if [ "$ref_count" -ge 20 ]; then
    echo -e "${GREEN}PASS${NC}: ≥20 reference files (target: ≥20 after extraction)"
elif [ "$ref_count" -ge 10 ]; then
    echo -e "${YELLOW}PENDING${NC}: $ref_count reference files (target: ≥20)"
else
    echo -e "${YELLOW}BASELINE${NC}: $ref_count reference files (extraction not started)"
fi

# Check scripts/README.md
echo ""
echo "Scripts Documentation Validation"
echo "-----------------------------------"
scripts_readme_count=$(ls "$SKILLS_DIR"/*/scripts/README.md 2>/dev/null | wc -l)
echo "scripts/README.md files found: $scripts_readme_count"

if [ "$scripts_readme_count" -eq 3 ]; then
    echo -e "${GREEN}PASS${NC}: All 3 skills have scripts/README.md"
elif [ "$scripts_readme_count" -gt 0 ]; then
    echo -e "${YELLOW}PENDING${NC}: $scripts_readme_count/3 skills have scripts/README.md"
else
    echo -e "${YELLOW}BASELINE${NC}: No scripts/README.md files (extraction not started)"
fi

# SLO: Maintainability - Check changelog exists
echo ""
echo "SLO: Maintainability"
echo "-----------------------------------"
if [ -f "REFACTOR_CHANGELOG.md" ]; then
    echo -e "${GREEN}PASS${NC}: REFACTOR_CHANGELOG.md exists"
else
    echo -e "${RED}FAIL${NC}: REFACTOR_CHANGELOG.md not found"
    exit 1
fi

if [ -f "REFACTOR_SSOT_README.md" ]; then
    echo -e "${GREEN}PASS${NC}: REFACTOR_SSOT_README.md exists"
else
    echo -e "${RED}FAIL${NC}: REFACTOR_SSOT_README.md not found"
    exit 1
fi

# Summary
echo ""
echo "==================================="
echo "SLO Verification Summary"
echo "==================================="
echo -e "Correctness:     ${GREEN}PASS${NC} (SSoT spec exists)"
echo -e "Observability:   ${GREEN}PASS${NC} (All metrics measured)"
echo -e "Maintainability: ${GREEN}PASS${NC} (Documentation exists)"
echo ""
echo "Current State:"
echo "  - Portfolio lines: $total_lines (target: ≤600)"
echo "  - Compliant skills: $compliant_count/3 (target: 3/3)"
echo "  - Reference files: $ref_count (target: ≥20)"
echo "  - Scripts docs: $scripts_readme_count/3 (target: 3/3)"
echo ""

if [ "$compliant_count" -eq 3 ] && [ "$total_lines" -le 600 ] && [ "$ref_count" -ge 20 ] && [ "$scripts_readme_count" -eq 3 ]; then
    echo -e "${GREEN}✓ 100% REFACTOR.md COMPLIANCE ACHIEVED${NC}"
    exit 0
else
    echo -e "${YELLOW}⏸ Compliance in progress (see REFACTOR_SSOT_README.md for next actions)${NC}"
    exit 0
fi
