# 优化计划：金标准示例 + 编排质量 + 文档同步 + output_type 参考

## 约束
- 不增加 CLAUDE.md 大小
- 不破坏角色隔离
- 不改变流程顺序
- 示例文件保持精简（每个 <80 行），避免仓库膨胀

---

## Step 1: 金标准示例（方向 A）

创建 `templates/examples/` 目录，每个角色一个示例文件：

- `templates/examples/requirement-spec-example.md` — BA 金标准
  - 展示：正确的 SHALL + GWT 格式、异常路径覆盖、无模糊词、粒度一致
  - 场景：一个简单的"用户注册"功能（3-4 条需求）

- `templates/examples/design-example.md` — SA 金标准
  - 展示：技术决策有理由、对照表完整、Task 拆分合理、依赖标注正确
  - 场景：对应上面的"用户注册"功能

- `templates/examples/code-report-example.md` — DE 金标准
  - 展示：实现摘要清晰、文件清单完整、测试结果详细、自检全 PASS

- `templates/examples/test-report-example.md` — TE 金标准
  - 展示：需求覆盖分析、结论明确、失败项有完整复现信息

在各 agent 定义中添加一行引用：`> 金标准示例见 templates/examples/{file}`

## Step 2: PM 编排质量标准（方向 B）

在 skills/mh-propose.md 的 "plan-action.md 格式要求" 章节后，新增编排质量标准：

- 粒度检查：Task 数量与需求复杂度匹配（不是 1 个 Task 包揽全部）
- 依赖检查：依赖图无环、Batch-1 占比合理（不是全部 deps=none）
- 完整性检查：每条需求/对照表行至少映射到 1 个 Task
- 可验证性：每个 Task 有明确的验证方式（来自 SA 的 design.md）

## Step 3: CHANGELOG 更新（方向 D）

新增 v0.3.2、v0.4.0、v0.4.1 的变更记录。

## Step 4: docs/design.md 同步（方向 C）

更新 design.md 中与当前实现脱节的章节：
- §3.3 角色职责边界：补充质量门禁职责
- 新增章节：质量保障机制（思考框架 + 反模式 + 交付自检 + PM 质量门禁）
- 新增章节：修复收敛机制（根因分析 + repair_history + 提前升级）
- 新增章节：审批决策上下文

注意：不重复 skills/agents 的完整内容，只描述设计理念和机制概述。

## Step 5: output_type 结构参考（方向 E）

创建 `templates/output-guides/` 目录，为高频 output_type 提供结构参考（不是代码模板，是"好的产出长什么样"的指南）：

- `templates/output-guides/web-app.md` — Web 应用产出结构参考
- `templates/output-guides/backend-api.md` — 后端 API 产出结构参考
- `templates/output-guides/cli-tool.md` — CLI 工具产出结构参考

每个文件包含：推荐目录结构、关键文件说明、质量检查点。
不绑定具体框架（不是 React 模板，是通用 Web 应用结构）。

## Step 6: check-harness.sh 更新

添加新目录和文件到框架自检：
- templates/examples/ 目录存在
- templates/output-guides/ 目录存在

---

## 不改动的
- CLAUDE.md
- 流程顺序和审批节点
- handoff 协议
- scripts/verify.sh（上一轮刚更新）
