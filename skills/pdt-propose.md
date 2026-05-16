# Skill: pdt-propose

需求分析 → 架构设计 → 测试用例 → 计划编排 → 人工评审。PM 调度，BA/SA/TE 分步执行。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/process.log`，格式：`[{时间}] [{角色}] {事件描述}`

---

## 前置检查

1. 验证 .state.md 中 phase=init 且 current_step=INIT-DONE
2. 验证 deliverables/proposal.md 存在且非空
3. 不满足则阻塞，提示用户先执行 /pdt-init

## Step REQ-1: 需求分析

**调度角色:** PM → BA

1. `[PM] 启动 REQ-1 需求分析，派发任务给 BA`
2. 写入 handoff: `deliverables/handoffs/{REQ-ID}-REQ1-R1.md`
   - to: BA
   - 白名单: reference/*, deliverables/proposal.md
   - 期望输出: deliverables/sa/requirement-spec.md
3. 更新 .state.md: current_step=REQ-1, current_handoff={handoff文件名}
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/ba.md + 白名单文件
   - [Cline] 切换角色为 BA，指示读取 handoff
5. 接收回报，校验 deliverables/sa/requirement-spec.md 存在且非空
6. `[PM] REQ-1 完成，需求规格已生成`

## Step REQ-2: 架构设计

**调度角色:** PM → SA

1. `[PM] 启动 REQ-2 架构设计，派发任务给 SA`
2. 写入 handoff: `deliverables/handoffs/{REQ-ID}-REQ2-R1.md`
   - to: SA
   - 白名单: deliverables/sa/requirement-spec.md
   - 期望输出: deliverables/sa/design.md
3. 更新 .state.md: current_step=REQ-2
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/sa.md + 白名单文件
   - [Cline] 切换角色为 SA，指示读取 handoff
5. 接收回报，校验 deliverables/sa/design.md 存在且非空
6. `[PM] REQ-2 完成，技术方案已生成`

## Step REQ-3: 测试用例设计

**调度角色:** PM → TE

1. `[PM] 启动 REQ-3 测试用例设计，派发任务给 TE`
2. 写入 handoff: `deliverables/handoffs/{REQ-ID}-REQ3-R1.md`
   - to: TE
   - 白名单: deliverables/sa/requirement-spec.md, deliverables/sa/design.md
   - 期望输出: deliverables/te/testcases.md
3. 更新 .state.md: current_step=REQ-3
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/te.md + 白名单文件
   - [Cline] 切换角色为 TE，指示读取 handoff
5. 接收回报，校验 deliverables/te/testcases.md 存在且非空
6. `[PM] REQ-3 完成，测试用例已生成`

## Step REQ-4: 计划编排

**执行角色:** PM

1. `[PM] 启动 REQ-4 计划编排`
2. 读取 deliverables/sa/design.md 中的 Tasks 清单
3. 读取 deliverables/te/testcases.md 中的用例列表
4. 编排执行计划，写入 deliverables/plan-action.md
5. 更新 .state.md: current_step=REQ-4
6. `[PM] REQ-4 完成，执行计划已编排`

### plan-action.md 格式

```markdown
# 执行计划

## 任务列表
| 序号 | Task ID | 描述 | 依赖 | 对应测试用例 |
|------|---------|------|------|-------------|

## 执行顺序
{按依赖关系排列的执行序列}

## 预估工作量
{整体评估}
```

## Step SR1: 需求评审（人工审批）

**执行角色:** PM（人机交互）

1. `[PM] 启动 SR1 需求评审`
2. 向用户呈现摘要：
   - 需求规格要点（来自 requirement-spec.md）
   - 技术方案要点（来自 design.md）
   - 测试覆盖情况（来自 testcases.md）
   - 执行计划（来自 plan-action.md）
3. 等待用户决策：
   - **通过**: 
     - 创建 baselines: deliverables/baselines/requirement-spec.v1.md 等
     - 写入 deliverables/SR1-record.md
     - 更新 .state.md: current_step=SR1-DONE, sr_status.SR1=approved
     - `[PM] SR1 通过，可执行 /pdt-apply`
   - **驳回**:
     - 记录驳回原因到 SR1-record.md
     - 根据驳回范围回退到对应步骤重新执行
     - 更新 .state.md: sr_status.SR1=rejected

## 异常处理

- 任何步骤的 SubAgent 回报 status=failed: PM 检查失败原因，决定重试或上升人工
- 文件校验失败（不存在或为空）: 重新派发任务，轮次+1
- 轮次达到 5 次: 上升人工审核
