#!/bin/bash
# verify.sh - 产出物校验脚本
# 退出码: 0=全部通过, 1=存在失败项
# 用法: ./scripts/verify.sh [A|B|C|D|all] [REQ-ID]

set -euo pipefail

DELIVERABLES_DIR="deliverables"
SPEC_DIR="spec"
OUTPUT_DIR="output"
ERRORS=0

check_type="${1:-all}"
req_id="${2:-}"

# 自动从 .state.md 读取 REQ-ID
if [ -z "$req_id" ]; then
    req_id=$(grep "^req_id:" "$DELIVERABLES_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
fi

if [ -z "$req_id" ]; then
    echo "WARN: 未指定 REQ-ID 且无法从 .state.md 读取，部分检查将跳过"
fi

REQ_DIR="$DELIVERABLES_DIR/$req_id"

# 读取 mode 字段
get_mode() {
    if [ -n "$req_id" ] && [ -f "$REQ_DIR/.state.md" ]; then
        grep "^mode:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo ""
    else
        echo ""
    fi
}

# A类检查: 基础文件存在性
check_a() {
    echo "=== A类检查: 文件存在性 ==="

    # 全局状态文件
    local f="$DELIVERABLES_DIR/.state.md"
    if [ ! -f "$f" ]; then
        echo "FAIL: $f 不存在"
        ERRORS=$((ERRORS + 1))
    elif [ ! -s "$f" ]; then
        echo "FAIL: $f 为空"
        ERRORS=$((ERRORS + 1))
    else
        echo "PASS: $f"
    fi

    # REQ-ID 级别文件
    if [ -n "$req_id" ]; then
        local req_files=(
            "$REQ_DIR/.state.md"
            "$REQ_DIR/proposal.md"
        )
        for f in "${req_files[@]}"; do
            if [ ! -f "$f" ]; then
                echo "FAIL: $f 不存在"
                ERRORS=$((ERRORS + 1))
            elif [ ! -s "$f" ]; then
                echo "FAIL: $f 为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $f"
            fi
        done
    fi
}

# B类检查: 阶段产出物完整性（mode + output_type 感知）
check_b() {
    echo "=== B类检查: 阶段产出物完整性 ==="

    if [ -z "$req_id" ]; then
        echo "SKIP: 无 REQ-ID，无法执行 B 类检查"
        return
    fi

    local phase mode output_type test_strategy
    phase=$(grep "^phase:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
    mode=$(get_mode)
    output_type=$(grep "^output_type:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
    test_strategy=$(grep "^test_strategy:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")

    echo "INFO: phase=$phase, mode=$mode, output_type=$output_type, test_strategy=$test_strategy"

    # propose 阶段产物检查（propose/apply/archive 都需要）
    if [ "$phase" = "propose" ] || [ "$phase" = "apply" ] || [ "$phase" = "archive" ]; then
        # SA design.md - required for standard/full
        if [ "$mode" != "fast" ]; then
            if [ ! -s "$REQ_DIR/sa/design.md" ]; then
                echo "FAIL: $REQ_DIR/sa/design.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $REQ_DIR/sa/design.md"
            fi
        fi

        # BA requirement-spec.md - only full mode
        if [ "$mode" = "full" ]; then
            if [ ! -s "$REQ_DIR/ba/requirement-spec.md" ]; then
                echo "FAIL: $REQ_DIR/ba/requirement-spec.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $REQ_DIR/ba/requirement-spec.md"
            fi
        fi

        # TE testcases.md - standard/full, skip for manual/none test_strategy
        if [ "$mode" != "fast" ]; then
            if [ "$test_strategy" != "manual" ] && [ "$test_strategy" != "none" ]; then
                if [ ! -s "$REQ_DIR/te/testcases.md" ]; then
                    echo "FAIL: $REQ_DIR/te/testcases.md 缺失或为空"
                    ERRORS=$((ERRORS + 1))
                else
                    echo "PASS: $REQ_DIR/te/testcases.md"
                fi
            else
                echo "INFO: test_strategy=$test_strategy, testcases.md 非必需"
            fi
        fi

        # plan-action.md - always required
        if [ ! -s "$REQ_DIR/plan-action.md" ]; then
            echo "FAIL: $REQ_DIR/plan-action.md 缺失或为空"
            ERRORS=$((ERRORS + 1))
        else
            echo "PASS: $REQ_DIR/plan-action.md"
        fi
    fi

    # apply 阶段产物检查（apply/archive 都需要）
    if [ "$phase" = "apply" ] || [ "$phase" = "archive" ]; then
        if [ ! -d "$REQ_DIR/output" ] || [ -z "$(ls -A "$REQ_DIR/output" 2>/dev/null)" ]; then
            echo "FAIL: $REQ_DIR/output/ 为空"
            ERRORS=$((ERRORS + 1))
        else
            echo "PASS: $REQ_DIR/output/ 非空"
        fi

        # output_type-specific checks
        case "$output_type" in
            ppt)
                if [ ! -s "$REQ_DIR/ux/slide-spec.md" ]; then
                    echo "FAIL: slide-spec.md 缺失（output_type=ppt）"
                    ERRORS=$((ERRORS + 1))
                else
                    echo "PASS: slide-spec.md 存在（output_type=ppt）"
                fi
                ;;
            web-app)
                if ! find "$REQ_DIR/output" -type f \( -name "*.html" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.vue" -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.rs" -o -name "*.js" -o -name "*.ts" -o -name "*.rb" \) 2>/dev/null | grep -q .; then
                    echo "WARN: output_type=web-app 但未检测到源代码文件"
                fi
                ;;
            backend-api|cli-tool|library)
                if ! find "$REQ_DIR/output" -type f \( -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.rs" -o -name "*.js" -o -name "*.ts" -o -name "*.rb" -o -name "*.c" -o -name "*.cpp" \) 2>/dev/null | grep -q .; then
                    echo "WARN: output_type=$output_type 但未检测到源代码文件"
                fi
                ;;
            *)
                echo "INFO: output_type=$output_type, 使用通用产出物检查"
                ;;
        esac
    fi

    # archive 阶段产物检查
    if [ "$phase" = "archive" ]; then
        if [ "$mode" != "fast" ]; then
            if [ ! -s "$SPEC_DIR/design.md" ]; then
                echo "FAIL: $SPEC_DIR/design.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $SPEC_DIR/design.md"
            fi
        fi
        if [ "$mode" = "full" ]; then
            if [ ! -s "$SPEC_DIR/requirement-spec.md" ]; then
                echo "FAIL: $SPEC_DIR/requirement-spec.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $SPEC_DIR/requirement-spec.md"
            fi
        fi
    fi

    if [ "$phase" != "propose" ] && [ "$phase" != "apply" ] && [ "$phase" != "archive" ]; then
        echo "INFO: phase=$phase，跳过B类检查"
    fi
}

# C类检查: 流程一致性
check_c() {
    echo "=== C类检查: 流程一致性 ==="

    if [ -z "$req_id" ]; then
        echo "SKIP: 无 REQ-ID，无法执行 C 类检查"
        return
    fi

    if [ ! -f "$REQ_DIR/.state.md" ]; then
        echo "FAIL: $REQ_DIR/.state.md 不存在，无法校验流程"
        ERRORS=$((ERRORS + 1))
        return
    fi

    # .state.md 必填字段校验
    local required_fields="req_id mode phase current_step current_role last_updated"
    for field in $required_fields; do
        if ! grep -q "^${field}:" "$REQ_DIR/.state.md" 2>/dev/null; then
            echo "FAIL: .state.md 缺少必填字段: $field"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # phase 与产物一致性校验
    local phase
    phase=$(grep "^phase:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
    local mode
    mode=$(get_mode)

    if [ "$phase" = "apply" ] || [ "$phase" = "archive" ] || [ "$phase" = "done" ]; then
        if [ ! -s "$REQ_DIR/plan-action.md" ]; then
            echo "FAIL: phase=$phase 但 plan-action.md 缺失（propose 阶段产物不完整）"
            ERRORS=$((ERRORS + 1))
        fi
    fi

    if [ "$phase" = "done" ]; then
        if [ ! -d "$OUTPUT_DIR" ] || [ -z "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]; then
            echo "FAIL: phase=done 但 $OUTPUT_DIR/ 为空（归档未完成）"
            ERRORS=$((ERRORS + 1))
        fi
    fi

    # Handoff 文件统计
    local handoff_dir="$REQ_DIR/handoffs"
    if [ -d "$handoff_dir" ]; then
        local handoff_count
        handoff_count=$(find "$handoff_dir" -name "*.md" -not -name ".*" | wc -l)
        echo "INFO: 共 $handoff_count 个 handoff 文件"

        # fast 模式至少 2 个 handoff（DEV + TEST），standard/full 至少有 propose 阶段的 handoff
        if [ "$mode" = "fast" ] && [ "$phase" = "done" ] && [ "$handoff_count" -lt 2 ]; then
            echo "WARN: fast 模式 phase=done 但 handoff 数量不足（期望 ≥2，实际 $handoff_count）"
        fi
    fi

    echo "PASS: 流程一致性检查完成"
}

# D类检查: 流程健康度
check_d() {
    echo "=== D类检查: 流程健康度 ==="

    if [ -z "$req_id" ]; then
        echo "SKIP: 无 REQ-ID，无法执行 D 类检查"
        return
    fi

    if [ ! -f "$REQ_DIR/.state.md" ]; then
        echo "SKIP: $REQ_DIR/.state.md 不存在"
        return
    fi

    # 修复循环耗尽检测
    local repair_round
    repair_round=$(grep "^repair_round:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "0")
    if [ "$repair_round" -ge 5 ] 2>/dev/null; then
        echo "FAIL: repair_round=$repair_round（修复循环耗尽，需人工介入）"
        ERRORS=$((ERRORS + 1))
    elif [ "$repair_round" -ge 3 ] 2>/dev/null; then
        echo "WARN: repair_round=$repair_round（修复循环进入高轮次）"
    else
        echo "PASS: repair_round=$repair_round"
    fi

    # Handoff 超时检测（pending 且 >30 分钟）
    local handoff_dir="$REQ_DIR/handoffs"
    if [ -d "$handoff_dir" ]; then
        local now
        now=$(date +%s)
        local stale_count=0
        for handoff in "$handoff_dir"/*.md; do
            [ -f "$handoff" ] || continue
            if grep -q "^status: pending" "$handoff" 2>/dev/null; then
                local file_age
                file_age=$(( now - $(stat -f%m "$handoff" 2>/dev/null || stat -c%Y "$handoff" 2>/dev/null || echo "$now") ))
                if [ "$file_age" -gt 1800 ]; then
                    echo "WARN: $(basename "$handoff") 处于 pending 状态超过 30 分钟"
                    stale_count=$((stale_count + 1))
                fi
            fi
        done
        if [ "$stale_count" -eq 0 ]; then
            echo "PASS: 无超时 handoff"
        fi
    fi

    # 状态一致性检测
    local current_step current_handoff
    current_step=$(grep "^current_step:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
    current_handoff=$(grep "^current_handoff:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")

    if [ -n "$current_handoff" ] && [ "$current_handoff" != '""' ] && [ "$current_handoff" != "''" ]; then
        if [ ! -f "$handoff_dir/$current_handoff" ]; then
            echo "FAIL: current_handoff=$current_handoff 但文件不存在"
            ERRORS=$((ERRORS + 1))
        else
            echo "PASS: current_handoff 文件存在"
        fi
    fi

    # TODO/占位符残留检测（扫描 output/ 中的代码文件）
    if [ -d "$REQ_DIR/output" ]; then
        local todo_count=0
        todo_count=$(grep -rl "TODO\|FIXME\|PLACEHOLDER\|{待填充}\|Lorem ipsum" "$REQ_DIR/output" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$todo_count" -gt 0 ]; then
            echo "WARN: output/ 中 $todo_count 个文件含 TODO/FIXME/占位符"
            grep -rl "TODO\|FIXME\|PLACEHOLDER\|{待填充}\|Lorem ipsum" "$REQ_DIR/output" 2>/dev/null | head -3 | while read -r f; do
                echo "  - $f"
            done
        else
            echo "PASS: output/ 无 TODO/占位符残留"
        fi
    fi
}

# 执行检查
case "$check_type" in
    A|a) check_a ;;
    B|b) check_b ;;
    C|c) check_c ;;
    D|d) check_d ;;
    all)
        check_a
        echo ""
        check_b
        echo ""
        check_c
        echo ""
        check_d
        ;;
    *)
        echo "用法: $0 [A|B|C|D|all] [REQ-ID]"
        exit 2
        ;;
esac

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "=== 校验通过 ==="
    exit 0
else
    echo "=== 校验失败: $ERRORS 项错误 ==="
    exit 1
fi
