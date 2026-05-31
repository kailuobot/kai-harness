# 优化方案：消除残余冗余 + 补全运行时逻辑

## 改动清单

### 1. agents 禁止事项精简（§1）
所有 agent 的通用禁止事项（读白名单外文件、引用对话历史、下游不改上游）改为引用 CLAUDE.md，只保留角色特有禁止事项。

### 2. pm.md 增加白名单校验步骤（§3）
质量门禁节开头增加 "Step 0: 白名单校验"。

### 3. mh-apply.md 修复循环补充快照写入逻辑（§4）
修复派发前 PM 计算 output hash + 写入 repair_snapshots。

### 4. agents/de.md 修复轮次保留 code-report 副本（§4）
修复轮次指导中增加 code-report 版本化要求。

### 5. repair_history schema 增强（§6）
增加 root_cause_hypothesis + action_taken 字段。

### 6. source-of-truth.md 增加版本升级自检清单（§7）

### 7. design.md §10 阈值下调（§2）
Skill 拆分触发条件从 400 行改为 300 行。
