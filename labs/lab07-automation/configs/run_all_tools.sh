#!/bin/bash
# =============================================================================
# Lab 07 - Run All Red Team Tools
# =============================================================================
#
# This script runs all three automated red teaming tools (garak, PyRIT,
# promptfoo) sequentially against the target application and produces
# a combined summary report.
#
# Usage (from inside the redteam-tools container):
#   bash /app/configs/run_all_tools.sh
#
# Or from the host:
#   docker-compose exec redteam-tools bash /app/configs/run_all_tools.sh
#
# Prerequisites:
#   - All services are running (docker-compose up -d)
#   - The model has been pulled (ollama-setup has completed)
#   - The target app is healthy (curl http://target-app:5000/health)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RESULTS_DIR="/app/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_FILE="${RESULTS_DIR}/summary_${TIMESTAMP}.txt"
TARGET_URL="http://target-app:5000"
OLLAMA_URL="${OLLAMA_HOST:-http://ollama:11434}"

# Track pass/fail for each tool
GARAK_STATUS="NOT_RUN"
PYRIT_STATUS="NOT_RUN"
PROMPTFOO_STATUS="NOT_RUN"
GARAK_VULNS=0
PYRIT_VULNS=0
PROMPTFOO_FAILS=0

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

separator() {
    echo ""
    echo "=================================================================="
    echo "  $*"
    echo "=================================================================="
    echo ""
}

check_target() {
    log "Checking target app health..."
    if curl -sf "${TARGET_URL}/health" > /dev/null 2>&1; then
        log "Target app is healthy."
        return 0
    else
        log "ERROR: Target app is not reachable at ${TARGET_URL}"
        log "Make sure all services are running: docker-compose up -d"
        return 1
    fi
}

check_ollama() {
    log "Checking Ollama health..."
    if curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
        log "Ollama is healthy."
        return 0
    else
        log "ERROR: Ollama is not reachable at ${OLLAMA_URL}"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

separator "Lab 07 - Automated AI Red Team Assessment"

log "Timestamp:   ${TIMESTAMP}"
log "Target:      ${TARGET_URL}"
log "Ollama:      ${OLLAMA_URL}"
log "Results dir: ${RESULTS_DIR}"

mkdir -p "${RESULTS_DIR}"

# Verify services are available
check_ollama || exit 1
check_target || exit 1

echo ""
log "All services are healthy. Starting red team assessment..."
echo ""

# ---------------------------------------------------------------------------
# Tool 1: Garak
# ---------------------------------------------------------------------------

separator "TOOL 1/3: Garak (LLM Vulnerability Scanner)"

log "Running garak scan against the target..."
log "This may take several minutes depending on the number of probes."

GARAK_START=$(date +%s)

if garak \
    --model_type rest \
    --model_name "${TARGET_URL}/v1/chat/completions" \
    --probes encoding.InjectBase64,encoding.InjectROT13,dan.Dan_11_0,promptinject.HijackHateHumansMini \
    --generations 3 \
    --report_prefix "${RESULTS_DIR}/garak" \
    2>&1 | tee "${RESULTS_DIR}/garak_stdout.log"; then
    GARAK_STATUS="COMPLETED"
    log "Garak scan completed successfully."
else
    GARAK_STATUS="COMPLETED_WITH_ERRORS"
    log "Garak scan completed with errors (this is normal - it means vulnerabilities were found)."
fi

GARAK_END=$(date +%s)
GARAK_DURATION=$((GARAK_END - GARAK_START))
log "Garak duration: ${GARAK_DURATION} seconds"

# Count garak vulnerabilities
if ls "${RESULTS_DIR}"/garak*.jsonl 1>/dev/null 2>&1; then
    GARAK_VULNS=$(grep -c '"status": "fail"' "${RESULTS_DIR}"/garak*.jsonl 2>/dev/null || echo "0")
fi
log "Garak vulnerabilities found: ${GARAK_VULNS}"

# ---------------------------------------------------------------------------
# Tool 2: PyRIT
# ---------------------------------------------------------------------------

separator "TOOL 2/3: PyRIT (Python Risk Identification Toolkit)"

log "Running PyRIT orchestration script..."

PYRIT_START=$(date +%s)

if python /app/configs/pyrit_config.py 2>&1 | tee "${RESULTS_DIR}/pyrit_stdout.log"; then
    PYRIT_STATUS="COMPLETED"
    log "PyRIT assessment completed successfully."
else
    PYRIT_STATUS="COMPLETED_WITH_ERRORS"
    log "PyRIT assessment completed with errors."
fi

PYRIT_END=$(date +%s)
PYRIT_DURATION=$((PYRIT_END - PYRIT_START))
log "PyRIT duration: ${PYRIT_DURATION} seconds"

# Count PyRIT vulnerabilities from the report
if [ -f "${RESULTS_DIR}/pyrit_report.json" ]; then
    PYRIT_VULNS=$(python3 -c "
import json
with open('${RESULTS_DIR}/pyrit_report.json') as f:
    data = json.load(f)
leaked = data.get('summary', {}).get('secrets_leaked', 0)
complied = data.get('summary', {}).get('model_complied_with_attack', 0)
print(leaked + complied)
" 2>/dev/null || echo "0")
fi
log "PyRIT vulnerabilities found: ${PYRIT_VULNS}"

# ---------------------------------------------------------------------------
# Tool 3: Promptfoo
# ---------------------------------------------------------------------------

separator "TOOL 3/3: Promptfoo (LLM Red Team Evaluation)"

log "Running promptfoo red team evaluation..."

PROMPTFOO_START=$(date +%s)

if cd /app/configs && promptfoo eval \
    -c promptfoo_config.yaml \
    --output "${RESULTS_DIR}/promptfoo_results.json" \
    --no-progress-bar \
    2>&1 | tee "${RESULTS_DIR}/promptfoo_stdout.log"; then
    PROMPTFOO_STATUS="COMPLETED"
    log "Promptfoo evaluation completed successfully."
else
    PROMPTFOO_STATUS="COMPLETED_WITH_ERRORS"
    log "Promptfoo evaluation completed with errors."
fi

PROMPTFOO_END=$(date +%s)
PROMPTFOO_DURATION=$((PROMPTFOO_END - PROMPTFOO_START))
log "Promptfoo duration: ${PROMPTFOO_DURATION} seconds"

# Count promptfoo failures
if [ -f "${RESULTS_DIR}/promptfoo_results.json" ]; then
    PROMPTFOO_FAILS=$(python3 -c "
import json
with open('${RESULTS_DIR}/promptfoo_results.json') as f:
    data = json.load(f)
results = data.get('results', [])
fails = sum(1 for r in results if not r.get('success', True))
print(fails)
" 2>/dev/null || echo "0")
fi
log "Promptfoo failed tests: ${PROMPTFOO_FAILS}"

# ---------------------------------------------------------------------------
# Summary Report
# ---------------------------------------------------------------------------

TOTAL_VULNS=$((GARAK_VULNS + PYRIT_VULNS + PROMPTFOO_FAILS))
TOTAL_DURATION=$((GARAK_DURATION + PYRIT_DURATION + PROMPTFOO_DURATION))

separator "ASSESSMENT SUMMARY"

{
    echo "=================================================================="
    echo "  AUTOMATED AI RED TEAM ASSESSMENT REPORT"
    echo "  Generated: $(date)"
    echo "=================================================================="
    echo ""
    echo "  Target: ${TARGET_URL}"
    echo ""
    echo "  ┌────────────┬────────────────┬───────────────┬──────────┐"
    echo "  │ Tool       │ Status         │ Vulns/Fails   │ Duration │"
    echo "  ├────────────┼────────────────┼───────────────┼──────────┤"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "Garak" "${GARAK_STATUS}" "${GARAK_VULNS}" "${GARAK_DURATION}"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "PyRIT" "${PYRIT_STATUS}" "${PYRIT_VULNS}" "${PYRIT_DURATION}"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "Promptfoo" "${PROMPTFOO_STATUS}" "${PROMPTFOO_FAILS}" "${PROMPTFOO_DURATION}"
    echo "  ├────────────┼────────────────┼───────────────┼──────────┤"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "TOTAL" "" "${TOTAL_VULNS}" "${TOTAL_DURATION}"
    echo "  └────────────┴────────────────┴───────────────┴──────────┘"
    echo ""
    echo "  Result files:"
    echo "    - Garak:    ${RESULTS_DIR}/garak*.jsonl"
    echo "    - PyRIT:    ${RESULTS_DIR}/pyrit_report.json"
    echo "    - Promptfoo: ${RESULTS_DIR}/promptfoo_results.json"
    echo "    - Logs:     ${RESULTS_DIR}/*_stdout.log"
    echo ""
    echo "  Summary:    ${SUMMARY_FILE}"
    echo ""
    if [ "${TOTAL_VULNS}" -gt 0 ]; then
        echo "  VERDICT: VULNERABILITIES DETECTED (${TOTAL_VULNS} total)"
        echo "  Review the detailed reports for remediation guidance."
    else
        echo "  VERDICT: NO VULNERABILITIES DETECTED"
        echo "  The target passed all automated red team tests."
    fi
    echo ""
    echo "=================================================================="
} | tee "${SUMMARY_FILE}"

log "Summary report saved to: ${SUMMARY_FILE}"
log "Assessment complete."

# Exit with non-zero if vulnerabilities were found (useful for CI/CD gates)
if [ "${TOTAL_VULNS}" -gt 0 ]; then
    exit 1
fi
