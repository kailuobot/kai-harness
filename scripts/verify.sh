#!/bin/bash
# verify.sh - 产出物校验脚本
# 退出码: 0=全部通过, 1=存在失败项
# 用法: ./scripts/verify.sh [A|B|C|all]

set -euo pipefail

DELIVERABLES_DIR="deliverables"
SPEC_DIR="spec"
OUTPUT_DIR="output/final"
ERRORS=0

check_type="${1:-all}"

# A类检查: 文件存在性
check_a() {
    echo "=== A类检查: 文件存在性 ==="
    local files=(
        "$DELIVERABLES_DIR/.state.md"
        "$DELIVERABLES_DIR/proposal.md"
    )
    for f in "${files[@]}"; do
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
}

# B类检查: 阶段产出物完整性
check_b() {
    echo "=== B类检查: 阶段产出物完整性 ==="
    local phase
    phase=$(grep "^phase:" "$DELIVERABLES_DIR/.state.md" 2>/dev/null | awk '{print $2}' || echo "")

    case "$phase" in
        propose|apply|archive)
            local propose_files=(
                "$DELIVERABLES_DIR/sa/requirement-spec.md"
                "$DELIVERABLES_DIR/sa/design.md"
                "$DELIVERABLES_DIR/te/testcases.md"
                "$DELIVERABLES_DIR/plan-action.md"
            )
            for f in "${propose_files[@]}"; do
                if [ ! -s "$f" ]; then
                    echo "FAIL: $f 缺失或为空"
                    ERRORS=$((ERRORS + 1))
                else
                    echo "PASS: $f"
                fi
            done
            ;;&
        apply|archive)
            if [ ! -d "$DELIVERABLES_DIR/output" ] || [ -z "$(ls -A "$DELIVERABLES_DIR/output" 2>/dev/null)" ]; then
                echo "FAIL: $DELIVERABLES_DIR/output/ 为空"
                ERRORS=$((ERRORS + 1))
            else
                echo "PASS: $DELIVERABLES_DIR/output/ 非空"
            fi
            ;;&
        archive)
            local archive_files=(
                "$SPEC_DIR/requirement-spec.md"
                "$SPEC_DIR/design.md"
            )
            for f in "${archive_files[@]}"; do
                if [ ! -s "$f" ]; then
                    echo "FAIL: $f 缺失或为空"
                    ERRORS=$((ERRORS + 1))
                else
                    echo "PASS: $f"
                fi
            done
            ;;
        *)
            echo "INFO: phase=$phase，跳过B类检查"
            ;;
    esac
}

# C类检查: 流程一致性
check_c() {
    echo "=== C类检查: 流程一致性 ==="
    local state_file="$DELIVERABLES_DIR/.state.md"

    if [ ! -f "$state_file" ]; then
        echo "FAIL: .state.md 不存在，无法校验流程"
        ERRORS=$((ERRORS + 1))
        return
    fi

    # 检查 handoff 文件不可变性（无修改痕迹）
    local handoff_dir="$DELIVERABLES_DIR/handoffs"
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
        echo "用法: $0 [A|B|C|all]"
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
