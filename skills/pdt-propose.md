# Skill: pdt-propose

需求分析 → 架构设计 → 测试用例 → 计划编排 → 人工评审。按 mode 裁剪步骤。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/{REQ-ID}/process.log`，格式：`[{timestamp}] [{角色}] {事件描述}`。timestamp 获取方式：优先使用 `date -u +%Y-%m-%dT%H:%M:%SZ`；如 date 命令不可用，使用递增序号 `#NNN`。

---

## 前置检查

1. 读取 `deliverables/.state.md` 获取当前 req_id
2. 验证 `deliverables/{REQ-ID}/.state.md` 中 phase=init 且 current_step=INIT-DONE
3. 读取 mode 字段确定流程裁剪方式
4. 验证 `deliverables/{REQ-ID}/proposal.md` 存在且非空
5. 不满足则阻塞，提示用户先执行 /pdt-init

---

## fast 模式

跳过 BA/SA/TE，PM 直接从 proposal 生成执行计划。

**Step 1: PM 直接编排计划**

1. `[PM] fast 模式，跳过需求分析/架构设计/测试用例，直接编排计划`
2. 读取 `deliverables/{REQ-ID}/proposal.md`
3. 生成简版 plan-action.md（任务列表 + 执行顺序，无需求对照表）
4. 写入 `deliverables/{REQ-ID}/plan-action.md`
5. 更新 `deliverables/{REQ-ID}/.state.md`: phase=propose, current_step=PROPOSE-DONE, sr_status.SR1=skipped
6. `[PM] 计划编排完成（fast模式，跳过SR1），可执行 /pdt-apply`

无 SR1 审批。

---

## standard 模式

跳过 BA，SA 出简版设计，TE 出测试用例，无 SR1。

**Step 1: 调度 SA 架构设计（REQ-2）**

1. `[PM] standard 模式，跳过BA需求分析，直接调度 SA 架构设计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-REQ2-R1.md`
   - to: SA
   - 白名单: `deliverables/{REQ-ID}/proposal.md`
   - 期望输出: `deliverables/{REQ-ID}/sa/design.md`
   - 约束: 简版设计（架构 + Tasks清单 + 需求映射简表，无需时序图）。因 standard 模式跳过 BA，SA 需在 design.md 中补充 Proposal 要点→Task→验证方式 的映射表
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-2
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/sa.md + 白名单文件
   - [Cline] 切换角色为 SA，指示读取 handoff
5. 接收回报，校验 `deliverables/{REQ-ID}/sa/design.md` 存在且非空
6. `[PM] REQ-2 完成，技术方案已生成`

**Step 2: 调度 TE 测试用例设计（REQ-3）**

1. `[PM] 调度 TE 执行测试用例设计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-REQ3-R1.md`
   - to: TE
   - 白名单: `deliverables/{REQ-ID}/proposal.md`, `deliverables/{REQ-ID}/sa/design.md`
   - 期望输出: `deliverables/{REQ-ID}/te/testcases.md`
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-3
4. 派发任务给 TE
5. 接收回报，校验 `deliverables/{REQ-ID}/te/testcases.md` 存在且非空
6. `[PM] REQ-3 完成，测试用例已生成`

**Step 3: PM 计划编排（REQ-4）**

1. `[PM] 启动计划编排`
2. 读取 design.md 中的 Tasks 清单 + testcases.md
3. 编排执行计划，写入 `deliverables/{REQ-ID}/plan-action.md`
4. 更新 `deliverables/{REQ-ID}/.state.md`: phase=propose, current_step=PROPOSE-DONE, sr_status.SR1=skipped
5. `[PM] 计划编排完成（standard模式，跳过SR1），可执行 /pdt-apply`

无 SR1 审批。

---

## full 模式

完整流程：BA → SA → TE → PM编排 → SR1。

**Step 1: 调度 BA 需求分析（REQ-1）**

1. `[PM] 启动 REQ-1 需求分析，派发任务给 BA`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-REQ1-R1.md`
   - to: BA
   - 白名单: reference/*, `deliverables/{REQ-ID}/proposal.md`
   - 期望输出: `deliverables/{REQ-ID}/ba/requirement-spec.md`
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-1, current_handoff={handoff文件名}
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/ba.md + 白名单文件
   - [Cline] 切换角色为 BA，指示读取 handoff
5. 接收回报，校验 `deliverables/{REQ-ID}/ba/requirement-spec.md` 存在且非空
6. `[PM] REQ-1 完成，需求规格已生成`

**Step 2: 调度 SA 架构设计（REQ-2）**

1. `[PM] 启动 REQ-2 架构设计，派发任务给 SA`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-REQ2-R1.md`
   - to: SA
   - 白名单: `deliverables/{REQ-ID}/ba/requirement-spec.md`
   - 期望输出: `deliverables/{REQ-ID}/sa/design.md`
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-2
4. 派发任务给 SA
5. 接收回报，校验 `deliverables/{REQ-ID}/sa/design.md` 存在且非空
6. `[PM] REQ-2 完成，技术方案已生成`

**Step 3: 调度 TE 测试用例设计（REQ-3）**

1. `[PM] 启动 REQ-3 测试用例设计，派发任务给 TE`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-REQ3-R1.md`
   - to: TE
   - 白名单: `deliverables/{REQ-ID}/ba/requirement-spec.md`, `deliverables/{REQ-ID}/sa/design.md`
   - 期望输出: `deliverables/{REQ-ID}/te/testcases.md`
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-3
4. 派发任务给 TE
5. 接收回报，校验 `deliverables/{REQ-ID}/te/testcases.md` 存在且非空
6. `[PM] REQ-3 完成，测试用例已生成`

**Step 4: PM 计划编排（REQ-4）**

1. `[PM] 启动 REQ-4 计划编排`
2. 读取 design.md Tasks 清单 + testcases.md 用例列表
3. 编排执行计划，写入 `deliverables/{REQ-ID}/plan-action.md`
4. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=REQ-4
5. `[PM] REQ-4 完成，执行计划已编排`

**Step 5: 需求评审（SR1）**

1. `[PM] 启动 SR1 需求评审`
2. 向用户呈现摘要：
   - 需求规格要点
   - 技术方案要点
   - 测试覆盖情况
   - 执行计划
3. 等待用户决策：
   - **通过**:
     - 创建 baselines: `deliverables/{REQ-ID}/baselines/requirement-spec.v1.md` 等
     - 写入 `deliverables/{REQ-ID}/SR1-record.md`
     - 更新 `deliverables/{REQ-ID}/.state.md`: phase=propose, current_step=PROPOSE-DONE, sr_status.SR1=approved
     - `[PM] SR1 通过，可执行 /pdt-apply`
   - **驳回**:
     - 记录驳回原因到 SR1-record.md
     - 回退到对应步骤重新执行

---

## 异常处理

- 任何步骤的 SubAgent 回报 status=failed: PM 检查失败原因，决定重试或上升人工
- 文件校验失败（不存在或为空）: 重新派发任务，轮次+1
- 轮次达到 5 次: 上升人工审核
