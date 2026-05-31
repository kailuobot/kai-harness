# 架构优化方案

## 诊断认同

建议中的 9 个问题全部成立。核心矛盾是：v0.5.0 为了"操作化"而在 skills 中展开了 pm.md 的内容，导致同一信息出现 3-4 次。这违反了我们自己定义的"单一真相源"原则。

---

## 立即执行（本轮）

### A1: 消除质量门禁冗余（§1 方案 A）

**原则：引用而非复制。AI Agent 能读文件。**

将 skills 中展开的质量门禁内容回退为简洁引用：
```
接收回报，执行质量门禁（agents/pm.md "{角色}产出验收"清单）:
  - 全部通过 → 继续
  - 不通过 → 驳回（新 handoff 附未通过项 + 位置 + 修正方向）
```

不再在 skills 中逐条列出检查项。pm.md 是唯一权威源。

涉及文件：skills/mh-apply.md, skills/mh-propose.md

### A2: design.md 瘦身为架构地图（§2）

砍到 ~200 行。只保留：
- §1 设计目标（四层防线图，10行）
- §2 架构总览（模块表 + 目录结构，50行）
- §3 角色总览（一张表，10行）
- §4 流程总览（状态机图 + SR标准表 + 铁律表，40行）
- §5 上下文管控（隔离表 + prompt构成，15行）
- §6-11 每个主题一句话 + "详见 {权威源}"
- §12 文档一致性（保留，10行）

所有详细描述删除，替换为指向权威源的链接。

涉及文件：docs/design.md

### A3: 合并 pm-dispatch-protocol.md 到 agents/pm.md（§3）

PM 调度协议就是 PM 角色定义的一部分。合并后：
- agents/pm.md ~180 行（可接受）
- 删除 templates/pm-dispatch-protocol.md
- PM 运行时少读一个文件

同时在 agents/pm.md 头部标注：
```
> PM 运行时读取本文件 + 当前 skill + .state.md + handoff。
> 不需要读取 design.md、source-of-truth.md（人工维护参考）。
```

涉及文件：agents/pm.md, templates/pm-dispatch-protocol.md（删除）

### A4: Handoff 白名单运行时验证（§4）

在 handoff 完成回报中新增 `read_files` 字段：
```
- read_files: ["file1.md", "file2.md"]  # 实际读取的文件列表
```

PM 验收时对比白名单，不匹配则驳回。

涉及文件：templates/handoff-template.md, templates/handoff-examples.md

### A5: 修复循环状态快照（§5）

在 state-template.md 中新增：
```yaml
repair_snapshots: []
# 格式: [{round: 1, output_hash: "md5", code_report: "de/code-report-r1.md"}]
```

DE 每轮修复保留独立的 code-report（追加轮次后缀）。

涉及文件：templates/state-template.md

### A6: 任务超时机制（§6）

在 state-template.md 中新增：
```yaml
task_started_at: ""  # 当前任务开始时间（PM 派发时写入）
```

在 verify.sh D 类检查中新增超时检测：
- >15 分钟 → WARN
- >30 分钟 → FAIL

涉及文件：templates/state-template.md, scripts/verify.sh

### A7: Handoff 契约一致性检查（§8）

在 verify.sh 中新增 E 类检查：
- 检查 handoff "期望输出"与下游 handoff "白名单"是否对齐
- 检查 completed_steps 与实际文件存在性一致

涉及文件：scripts/verify.sh

---

## 记录为未来方向（写入 design.md）

### B1: Skill 按需加载（§7）
- 当前 skill 文件 200-300 行，尚可接受
- 当单个 skill 超过 400 行时，拆分为 main.md + 子文件
- 记录在 design.md 演进方向中

### B2: 轻量级状态机引擎（§9）
- 当前 PM 直接写 .state.md，依赖 prompt 理解
- 未来可用 scripts/state-engine.sh 封装状态转移
- 记录在 design.md 演进方向中

---

## 不改动的
- CLAUDE.md
- agents/ba|sa|de|te|ux.md（上轮刚改完，本轮不动）
- scripts/check-harness.sh（需要适配删除 pm-dispatch-protocol.md）
- 流程顺序和审批节点

## 预期效果
- design.md: 513行 → ~200行
- PM 运行时文件数: 减少 1 个（合并 dispatch protocol）
- skills 中质量门禁: 从逐条展开回退为引用（每处省 3-5 行）
- 新增机制: 白名单验证 + 修复快照 + 任务超时 + 契约一致性检查
