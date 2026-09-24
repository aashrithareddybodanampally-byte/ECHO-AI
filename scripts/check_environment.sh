#!/usr/bin/env bash
# ============================================================
# ECHO-AI — Environment Validation Script (Bash)
# ============================================================
# Usage: bash scripts/check_environment.sh
# ============================================================

set -euo pipefail

PASS=0
WARN=0
FAIL=0

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  ECHO-AI — Environment Validation${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

check_tool() {
    local name="$1"
    local command="$2"
    local required="${3:-true}"

    if version_output=$(eval "$command" 2>&1); then
        version=$(echo "$version_output" | head -n1)
        echo -e "  ${GREEN}[OK]${NC}   $name — $version"
        PASS=$((PASS + 1))
    else
        if [ "$required" = "true" ]; then
            echo -e "  ${RED}[FAIL]${NC} $name — Not found (REQUIRED)"
            FAIL=$((FAIL + 1))
        else
            echo -e "  ${YELLOW}[WARN]${NC} $name — Not found (optional for Phase 1)"
            WARN=$((WARN + 1))
        fi
    fi
}

echo "  Checking development tools..."
echo ""

# Required tools
check_tool "Git" "git --version" true
check_tool "Python" "python3 --version || python --version" true
check_tool "Node.js" "node --version" true
check_tool "npm" "npm --version" true

# Optional tools
check_tool "Docker" "docker --version" false
check_tool "Docker Compose" "docker compose version" false
check_tool "GitHub CLI" "gh --version" false

echo ""
echo -e "${GRAY}------------------------------------------------------------${NC}"
echo ""
echo "  Checking project structure..."
echo ""

# Required files
for file in .gitignore .env.example AGENTS.md PROJECT-CONTEXT.md README.md LICENSE; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}[OK]${NC}   $file"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} $file — Missing"
        FAIL=$((FAIL + 1))
    fi
done

# Required directories
for dir in frontend backend ml rag safety database tests docs scripts infrastructure data models logs; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}[OK]${NC}   $dir/"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} $dir/ — Missing"
        FAIL=$((FAIL + 1))
    fi
done

# Security check
echo ""
echo "  Checking security..."
echo ""

if [ -f ".env" ]; then
    tracked=$(git ls-files .env 2>/dev/null || true)
    if [ -n "$tracked" ]; then
        echo -e "  ${RED}[FAIL]${NC} .env is tracked by Git — REMOVE IT"
        FAIL=$((FAIL + 1))
    else
        echo -e "  ${GREEN}[OK]${NC}   .env exists but is git-ignored"
        PASS=$((PASS + 1))
    fi
else
    echo -e "  ${GREEN}[OK]${NC}   No .env file (use .env.example as template)"
    PASS=$((PASS + 1))
fi

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Results:  $PASS passed  |  $WARN warnings  |  $FAIL failed${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}❌ Environment validation FAILED. Fix the issues above.${NC}"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  Environment OK with warnings. Phase 1 can proceed.${NC}"
    exit 0
else
    echo -e "  ${GREEN}✅ Environment validation PASSED. Ready for development.${NC}"
    exit 0
fi
