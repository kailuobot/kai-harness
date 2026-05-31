# 优化计划：效率提升 + 修复收敛 + 决策质量

## 约束
- 不增加 CLAUDE.md 大小
- 不破坏角色隔离
- 不改变流程顺序

---

## Step 1: 精简 Handoff 模板

当前 69 行 → 目标 ~40 行。

改动：
- 删除"完成回报"中的解释性文字（agents 已知格式）
- 将两个示例块（成功+失败）移到独立文件 `templates/handoff-examples.md`
- 模板中只保留结构骨架

涉及文件：
- templates/handoff-template.md（精简）
- templates/handoff-examples.md（新建，存放示例）

## Step 2: 增强人工审批上下文

改动 skills/mh-apply.md 中所有人工审批呈现格式，增加决策上下文：
- fast 模式人工确认：增加文件数、测试结果摘要、修复历史
- standard 模式 Batch 确认：增加变更摘要、测试覆盖率
- SR2/SR3 审批：增加风险评估、PM 建议

涉及文件：
- skills/mh-apply.md（修改审批呈现格式）

## Step 3: 结构化修复上下文

当前修复循环只传递"上轮失败原因"一句话。改为结构化的修复上下文。

改动：
- 在修复循环章节中，要求 PM 在 handoff 中附加结构化修复上下文
- 增加根因分析步骤（PM 基于 TE 报告分析失败特征）
- 增加收敛追踪（连续发散时提前升级人工）

涉及文件：
- skills/mh-apply.md（修复循环章节重写）

## Step 4: 补充 verify.sh 检查项

新增 D 类检查（流程健康度）：
- 修复循环耗尽检测（repair_round=5）
- Handoff 超时检测（pending 且 >30 分钟）
- 状态一致性检测（current_step 与 handoff 文件匹配）
- TODO/占位符残留检测（扫描 output/ 中的代码文件）

涉及文件：
- scripts/verify.sh（新增 D 类检查）

## Step 5: Fast 模式轻量化

改动 skills/dev-test.md，增加 fast 模式快速路径：
- mode=fast 且 repair_round=0 时：跳过 lint、简化构建检查
- 保留测试执行（核心价值）

改动 skills/mh-apply.md fast 模式 TE 审计：
- 明确 fast 模式 TE 做轻量验证（工程检查 + 关键路径抽查），不做全量覆盖分析

涉及文件：
- skills/dev-test.md（增加 fast 模式快速路径）
- skills/mh-apply.md（fast 模式 TE 约束调整）

## Step 6: 状态文件增加修复历史

在 state-template.md 中增加 repair_history 字段，用于追踪修复收敛：

```yaml
repair_history: []  # 修复历史（每轮追加）
# 格式: [{round: 1, error_type: "test_failure", failed_count: 3, summary: "..."}]
```

涉及文件：
- templates/state-template.md（增加 repair_history 字段定义）

---

## 不改动的
- CLAUDE.md
- agents/*.md（上一轮刚升级完）
- 流程顺序和审批节点数量
- handoff 协议的核心机制（文件隔离、白名单）
- scripts/check-harness.sh（无新文件需要检查，只是 verify.sh 内部新增检查类型）
