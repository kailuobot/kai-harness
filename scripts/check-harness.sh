#!/bin/bash
# check-harness.sh - 框架自检脚本
# 验证 mini-harness 框架文件完整性
# 退出码: 0=框架完整, 1=框架损坏

set -euo pipefail

ERRORS=0

echo "=== Mini-Harness 框架自检 ==="

# 1. 核心配置文件
echo ""
echo "--- 核心配置 ---"
core_files=(
    "CLAUDE.md"
    ".clinerules"
    ".mcp.json"
    "README.md"
)
for f in "${core_files[@]}"; do
    if [ -s "$f" ]; then
        echo "PASS: $f"
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

# 2. Agent 定义文件
echo ""
echo "--- Agent 定义 ---"
agents=(pm ba sa de te ux)
for agent in "${agents[@]}"; do
    f="agents/$agent.md"
    if [ -s "$f" ]; then
        echo "PASS: $f"
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

# 3. Skill 文件
echo ""
echo "--- Skill 文件 ---"
skills=(mh-clarify mh-propose mh-apply mh-archive mh-run mh-ppt dev-test post-verify)
for skill in "${skills[@]}"; do
    f="skills/$skill.md"
    if [ -s "$f" ]; then
        echo "PASS: $f"
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Command 引用文件
echo ""
echo "--- Command 引用 ---"
commands=(mh-clarify mh-propose mh-apply mh-archive mh-run mh-ppt)
for cmd in "${commands[@]}"; do
    f=".claude/commands/$cmd.md"
    if [ -s "$f" ]; then
        echo "PASS: $f"
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

# 5. 校验脚本自身
echo ""
echo "--- 校验脚本 ---"
scripts=(verify.sh baseline.sh check-harness.sh verify-ppt.sh)
for script in "${scripts[@]}"; do
    f="scripts/$script"
    if [ -s "$f" ]; then
        if [ -x "$f" ]; then
            echo "PASS: $f (可执行)"
        else
            echo "WARN: $f 存在但不可执行"
        fi
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

# 6. 目录结构
echo ""
echo "--- 目录结构 ---"
dirs=(
    "agents"
    "skills"
    "scripts"
    "templates"
    "reference"
    "deliverables"
    "spec"
    "output"
)
for d in "${dirs[@]}"; do
    if [ -d "$d" ]; then
        echo "PASS: $d/"
    else
        echo "FAIL: $d/ 不存在"
        ERRORS=$((ERRORS + 1))
    fi
done

# 7. Handoff 模板
echo ""
echo "--- 模板文件 ---"
if [ -s "templates/handoff-template.md" ]; then
    echo "PASS: handoff 模板"
else
    echo "FAIL: handoff 模板缺失"
    ERRORS=$((ERRORS + 1))
fi

# 8. PPT 子系统
echo ""
echo "--- PPT 子系统 ---"
ppt_files=(
    "agents/ux.md"
    "templates/ppt-base.css"
    "templates/ppt-base.html"
    "scripts/verify-ppt.sh"
)
for f in "${ppt_files[@]}"; do
    if [ -s "$f" ]; then
        echo "PASS: $f"
    else
        echo "FAIL: $f 缺失或为空"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ -d "templates/ppt-templates/layouts" ]; then
    local_count=$(find "templates/ppt-templates/layouts" -name "*.html" | wc -l | tr -d ' ')
    echo "PASS: templates/ppt-templates/layouts/ ($local_count 个模板)"
else
    echo "FAIL: templates/ppt-templates/layouts/ 不存在"
    ERRORS=$((ERRORS + 1))
fi

# 结果
echo ""
echo "========================"
if [ $ERRORS -eq 0 ]; then
    echo "框架自检通过 ✓"
    exit 0
else
    echo "框架自检失败: $ERRORS 项错误"
    exit 1
fi
