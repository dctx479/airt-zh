#!/bin/bash
# =============================================================================
# Lab 07 - 运行所有红队工具
# =============================================================================
#
# 此脚本依次运行所有三个自动化红队工具（garak、PyRIT、promptfoo）
# 对目标应用程序进行测试，并生成综合摘要报告。
#
# 用法（在 redteam-tools 容器内）：
#   bash /app/configs/run_all_tools.sh
#
# 或从主机运行：
#   docker-compose exec redteam-tools bash /app/configs/run_all_tools.sh
#
# 前置条件：
#   - 所有服务正在运行（docker-compose up -d）
#   - 模型已拉取完成（ollama-setup 已完成）
#   - 目标应用健康（curl http://target-app:5000/health）
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
RESULTS_DIR="/app/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_FILE="${RESULTS_DIR}/summary_${TIMESTAMP}.txt"
TARGET_URL="http://target-app:5000"
OLLAMA_URL="${OLLAMA_HOST:-http://ollama:11434}"

# 跟踪每个工具的通过/失败状态
GARAK_STATUS="NOT_RUN"
PYRIT_STATUS="NOT_RUN"
PROMPTFOO_STATUS="NOT_RUN"
GARAK_VULNS=0
PYRIT_VULNS=0
PROMPTFOO_FAILS=0

# ---------------------------------------------------------------------------
# 辅助函数
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
    log "检查目标应用健康状态..."
    if curl -sf "${TARGET_URL}/health" > /dev/null 2>&1; then
        log "目标应用健康。"
        return 0
    else
        log "错误：目标应用无法访问 ${TARGET_URL}"
        log "确保所有服务正在运行：docker-compose up -d"
        return 1
    fi
}

check_ollama() {
    log "检查 Ollama 健康状态..."
    if curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
        log "Ollama 健康。"
        return 0
    else
        log "错误：Ollama 无法访问 ${OLLAMA_URL}"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# 设置
# ---------------------------------------------------------------------------

separator "Lab 07 - 自动化 AI 红队评估"

log "时间戳：   ${TIMESTAMP}"
log "目标：      ${TARGET_URL}"
log "Ollama：      ${OLLAMA_URL}"
log "结果目录： ${RESULTS_DIR}"

mkdir -p "${RESULTS_DIR}"

# 验证服务是否可用
check_ollama || exit 1
check_target || exit 1

echo ""
log "所有服务健康。开始红队评估..."
echo ""

# ---------------------------------------------------------------------------
# 工具 1: Garak
# ---------------------------------------------------------------------------

separator "工具 1/3: Garak (LLM 漏洞扫描器)"

log "对目标运行 garak 扫描..."
log "这可能需要几分钟，具体取决于探针数量。"

GARAK_START=$(date +%s)

if garak \
    --model_type rest \
    --model_name "${TARGET_URL}/v1/chat/completions" \
    --probes encoding.InjectBase64,encoding.InjectROT13,dan.Dan_11_0,promptinject.HijackHateHumansMini \
    --generations 3 \
    --report_prefix "${RESULTS_DIR}/garak" \
    2>&1 | tee "${RESULTS_DIR}/garak_stdout.log"; then
    GARAK_STATUS="COMPLETED"
    log "Garak 扫描成功完成。"
else
    GARAK_STATUS="COMPLETED_WITH_ERRORS"
    log "Garak 扫描完成但有错误（这是正常的 - 意味着发现了漏洞）。"
fi

GARAK_END=$(date +%s)
GARAK_DURATION=$((GARAK_END - GARAK_START))
log "Garak 耗时：${GARAK_DURATION} 秒"

# 统计 garak 漏洞
if ls "${RESULTS_DIR}"/garak*.jsonl 1>/dev/null 2>&1; then
    GARAK_VULNS=$(grep -c '"status": "fail"' "${RESULTS_DIR}"/garak*.jsonl 2>/dev/null || echo "0")
fi
log "Garak 发现的漏洞：${GARAK_VULNS}"

# ---------------------------------------------------------------------------
# 工具 2: PyRIT
# ---------------------------------------------------------------------------

separator "工具 2/3: PyRIT (Python 风险识别工具包)"

log "运行 PyRIT 编排脚本..."

PYRIT_START=$(date +%s)

if python /app/configs/pyrit_config.py 2>&1 | tee "${RESULTS_DIR}/pyrit_stdout.log"; then
    PYRIT_STATUS="COMPLETED"
    log "PyRIT 评估成功完成。"
else
    PYRIT_STATUS="COMPLETED_WITH_ERRORS"
    log "PyRIT 评估完成但有错误。"
fi

PYRIT_END=$(date +%s)
PYRIT_DURATION=$((PYRIT_END - PYRIT_START))
log "PyRIT 耗时：${PYRIT_DURATION} 秒"

# 从报告中统计 PyRIT 漏洞
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
log "PyRIT 发现的漏洞：${PYRIT_VULNS}"

# ---------------------------------------------------------------------------
# 工具 3: Promptfoo
# ---------------------------------------------------------------------------

separator "工具 3/3: Promptfoo (LLM 红队评估)"

log "运行 promptfoo 红队评估..."

PROMPTFOO_START=$(date +%s)

if cd /app/configs && promptfoo eval \
    -c promptfoo_config.yaml \
    --output "${RESULTS_DIR}/promptfoo_results.json" \
    --no-progress-bar \
    2>&1 | tee "${RESULTS_DIR}/promptfoo_stdout.log"; then
    PROMPTFOO_STATUS="COMPLETED"
    log "Promptfoo 评估成功完成。"
else
    PROMPTFOO_STATUS="COMPLETED_WITH_ERRORS"
    log "Promptfoo 评估完成但有错误。"
fi

PROMPTFOO_END=$(date +%s)
PROMPTFOO_DURATION=$((PROMPTFOO_END - PROMPTFOO_START))
log "Promptfoo 耗时：${PROMPTFOO_DURATION} 秒"

# 统计 promptfoo 失败数
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
log "Promptfoo 失败的测试：${PROMPTFOO_FAILS}"

# ---------------------------------------------------------------------------
# 摘要报告
# ---------------------------------------------------------------------------

TOTAL_VULNS=$((GARAK_VULNS + PYRIT_VULNS + PROMPTFOO_FAILS))
TOTAL_DURATION=$((GARAK_DURATION + PYRIT_DURATION + PROMPTFOO_DURATION))

separator "评估摘要"

{
    echo "=================================================================="
    echo "  自动化 AI 红队评估报告"
    echo "  生成时间：$(date)"
    echo "=================================================================="
    echo ""
    echo "  目标：${TARGET_URL}"
    echo ""
    echo "  ┌────────────┬────────────────┬───────────────┬──────────┐"
    echo "  │ 工具       │ 状态           │ 漏洞/失败     │ 耗时     │"
    echo "  ├────────────┼────────────────┼───────────────┼──────────┤"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "Garak" "${GARAK_STATUS}" "${GARAK_VULNS}" "${GARAK_DURATION}"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "PyRIT" "${PYRIT_STATUS}" "${PYRIT_VULNS}" "${PYRIT_DURATION}"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "Promptfoo" "${PROMPTFOO_STATUS}" "${PROMPTFOO_FAILS}" "${PROMPTFOO_DURATION}"
    echo "  ├────────────┼────────────────┼───────────────┼──────────┤"
    printf "  │ %-10s │ %-14s │ %-13s │ %6ss  │\n" "总计" "" "${TOTAL_VULNS}" "${TOTAL_DURATION}"
    echo "  └────────────┴────────────────┴───────────────┴──────────┘"
    echo ""
    echo "  结果文件："
    echo "    - Garak:    ${RESULTS_DIR}/garak*.jsonl"
    echo "    - PyRIT:    ${RESULTS_DIR}/pyrit_report.json"
    echo "    - Promptfoo: ${RESULTS_DIR}/promptfoo_results.json"
    echo "    - 日志：     ${RESULTS_DIR}/*_stdout.log"
    echo ""
    echo "  摘要：    ${SUMMARY_FILE}"
    echo ""
    if [ "${TOTAL_VULNS}" -gt 0 ]; then
        echo "  结论：检测到漏洞（共 ${TOTAL_VULNS} 个）"
        echo "  查看详细报告以获取修复指导。"
    else
        echo "  结论：未检测到漏洞"
        echo "  目标通过了所有自动化红队测试。"
    fi
    echo ""
    echo "=================================================================="
} | tee "${SUMMARY_FILE}"

log "摘要报告已保存到：${SUMMARY_FILE}"
log "评估完成。"

# 如果发现漏洞则以非零状态退出（对 CI/CD 门控有用）
if [ "${TOTAL_VULNS}" -gt 0 ]; then
    exit 1
fi
