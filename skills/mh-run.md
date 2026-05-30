# Skill: mh-run

全流程自动推进模式。PM 主导，一次性执行 clarify → propose → apply → archive 全部阶段，仅在人工审批节点暂停。

**日志规则：** 同各阶段 skill 定义，追加日志到 `deliverables/{REQ-ID}/process.log`

---

## 核心规则：自动推进

本 skill 与逐阶段执行的唯一区别：

1. 当某阶段到达 DONE 标记时，**禁止停下来等待用户输入下一个命令**
2. 替代行为：打印推进心跳后，立即读取下一阶段的 skill 文件并继续执行
3. 所有阶段内的人工审批节点（SR1/SR2/SR3/SR4、逐任务人工确认、Proposal确认、模式选择）照常暂停等待用户决策
4. 在 `deliverables/{REQ-ID}/.state.md` 中写入 `auto_advance: true`，用于断点恢复时识别模式

---

## 推进触发条件

| 当前阶段完成标记 | 推进动作 |
|---|---|
| current_step=INIT-DONE | `[PM] ✦ 自动推进 → propose 阶段` 然后读取并执行 skills/mh-propose.md |
| current_step=PROPOSE-DONE（fast/standard）或 SR1 通过（full） | `[PM] ✦ 自动推进 → apply 阶段` 然后读取并执行 skills/mh-apply.md |
| current_step=SR3-DONE | `[PM] ✦ 自动推进 → archive 阶段` 然后读取并执行 skills/mh-archive.md |
| phase=done | `[PM] ✦ 全流程完成` 打印最终摘要 |

---

## Fast 模式特殊行为：连续流

当 mode=fast 时，/mh-run 将 propose→apply→archive 合并为一个连续流，最大限度减少人工交互：

**整个 fast 连续流中，用户仅需在以下时刻做出决策：**
- Init 阶段的 Proposal 确认 + 模式选择
- Apply 阶段的人工确认（唯一审批点，合并了 SR2/SR3/SR4 的职能）

**被跳过的暂停点：**
- SR1（fast 模式无此节点）
- SR4（fast 模式直接结项）
- 阶段间等待（propose→apply→archive 全部自动衔接）

**推进触发条件覆盖（fast 模式）：**

| 当前阶段完成标记 | 推进动作 |
|---|---|
| current_step=INIT-DONE | 自动推进 → propose（无暂停） |
| current_step=PROPOSE-DONE | 自动推进 → apply（无暂停，跳过 SR1） |
| Apply 人工确认通过 | 自动推进 → archive（无暂停，跳过 SR4） |
| phase=done | 打印最终摘要 |

---

## 被覆盖的行为

执行各阶段 skill 时，以下结束语被替换为自动推进：

- `可执行 /mh-propose` → 自动推进
- `可执行 /mh-apply` → 自动推进
- `可执行 /mh-archive` → 自动推进
- 任何形式的"下一步请用户输入命令"提示 → 自动推进

---

## 断点恢复

PM 恢复时检测 `deliverables/{REQ-ID}/.state.md` 中 `auto_advance: true`：

1. 根据 phase + current_step 确定当前位置
2. 读取对应阶段的 skill 文件，从中断点继续执行
3. 该阶段完成后继续自动推进到下一阶段

---

## 执行序列

### Phase 1: Init

1. `[PM] ✦ /mh-run 启动，进入 clarify 阶段`
2. 在 .state.md 中写入 `auto_advance: true`
3. 读取 skills/mh-clarify.md，按其定义执行全部步骤
4. 到达 INIT-DONE 后：`[PM] ✦ clarify 完成，自动推进 → propose`

### Phase 2: Propose

1. 读取 skills/mh-propose.md，按其定义执行全部步骤（含 SR1 审批如适用）
2. 到达 PROPOSE-DONE（fast/standard）或 SR1 通过（full）后：`[PM] ✦ propose 完成，自动推进 → apply`

### Phase 3: Apply

1. 读取 skills/mh-apply.md，按其定义执行全部步骤
2. 所有人工审批节点（逐任务确认、SR2、SR3）照常暂停等待用户
3. 到达 SR3-DONE 后：`[PM] ✦ apply 完成，自动推进 → archive`

### Phase 4: Archive

1. 读取 skills/mh-archive.md，按其定义执行全部步骤（含 SR4 审批如适用）
2. 到达 phase=done 后：打印最终摘要

---

## 最终摘要格式

```
══════════════════════════════════════
[/mh-run 全流程完成]
需求编号: {REQ-ID}
模式: {fast|standard|full}
总耗时: {从 init 启动到 archive 完成的时间}
归档产物:
  - spec/requirement-spec.md（full模式）
  - spec/design.md（standard/full模式）
  - output/*
项目状态: DONE
══════════════════════════════════════
```

---

## 异常处理

- 任何阶段的异常处理逻辑不变，遵循各自 skill 文件定义
- 如果某阶段因异常暂停（如超过5轮修复上升人工），用户解决后流程继续自动推进
- 人工审批驳回后的回退逻辑不变，回退完成后继续自动推进
- 会话中断后重新执行 `/mh-run`，通过 auto_advance 标记自动恢复推进模式
