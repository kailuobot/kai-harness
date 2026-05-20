#!/bin/bash
# verify.sh - 产出物校验脚本
# 退出码: 0=全部通过, 1=存在失败项
# 用法: ./scripts/verify.sh [A|B|C|all] [REQ-ID]

set -euo pipefail

DELIVERABLES_DIR="deliverables"
SPEC_DIR="spec"
OUTPUT_DIR="output/final"
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

# B类检查: 阶段产出物完整性（mode 感知）
check_b() {
    echo "=== B类检查: 阶段产出物完整性 ==="

    if [ -z "$req_id" ]; then
        echo "SKIP: 无 REQ-ID，无法执行 B 类检查"
        return
    fi

    local phase
    phase=$(grep "^phase:" "$REQ_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")
    local mode
    mode=$(get_mode)

    echo "INFO: phase=$phase, mode=$mode"

    # propose 阶段产物检查（propose/apply/archive 都需要）
    if [ "$phase" = "propose" ] || [ "$phase" = "apply" ] || [ "$phase" = "archive" ]; then
        if [ "$mode" != "fast" ]; then
            if [ ! -s "$REQ_DIR/sa/design.md" ]; then
                echo "FAIL: $REQ_DIR/sa/design.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $REQ_DIR/sa/design.md"
            fi
        fi

        if [ "$mode" = "full" ]; then
            if [ ! -s "$REQ_DIR/ba/requirement-spec.md" ]; then
                echo "FAIL: $REQ_DIR/ba/requirement-spec.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $REQ_DIR/ba/requirement-spec.md"
            fi
        fi

        if [ "$mode" != "fast" ]; then
            if [ ! -s "$REQ_DIR/te/testcases.md" ]; then
                echo "FAIL: $REQ_DIR/te/testcases.md 缺失或为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $REQ_DIR/te/testcases.md"
            fi
        fi

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

    local handoff_dir="$REQ_DIR/handoffs"
    if [ -d "$handoff_dir" ]; then
        local handoff_count
        handoff_count=$(find "$handoff_dir" -name "*.md" -not -name ".*" | wc -l)
        echo "INFO: 共 $handoff_count 个 handoff 文件"
    fi

    echo "PASS: 流程一致性基础检查"
}

# 执行检查
case "$check_type" in
    A|a) check_a ;;
    B|b) check_b ;;
    C|c) check_c ;;
    all)
        check_a
        echo ""
        check_b
        echo ""
        check_c
        ;;
    *)
        echo "用法: $0 [A|B|C|all] [REQ-ID]"
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
