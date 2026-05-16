# PSDT Workflow

PM 调度手册。PM 必须严格按此手册执行，不得跳步或自行决策技术问题。

---

## 流程总览

```
/pdt-init          /pdt-propose                    /pdt-apply                         /pdt-archive
─────────────      ─────────────────────────       ──────────────────────────────     ─────────────────
                                                                                     
[人机协作]         [自动化 + 人工审批]              [自动化 + 多轮修复 + 人工审批]     [归档 + 结项]
                                                                                     
 PM                PM→BA→PM→SA→PM→TE→PM            PM→DE→PM→TE→PM (循环)             PM
 │                 │                                │                                 │
 ▼                 ▼                                ▼                                 ▼
 场景检测           REQ-1 需求分析                   DEV-1.N 编码实现                   ARC-1 需求归档
 │                 │                                │                                 │
 ▼                 ▼                                ▼                                 ▼
 需求澄清          REQ-2 架构设计                   TEST-1.N 审计验证                  ARC-2 设计归档
 │                 │                                │                                 │
 ▼                 ▼                                ├─FAIL→ 修复循环(≤5轮)            ▼
 Proposal定稿      REQ-3 测试用例                   │                                 ARC-3 代码归档
                   │                                ▼                                 │
                   ▼                                人工逐任务确认                     ▼
                   REQ-4 计划编排                    │                                ★SR4 结项确认
                   │                                ▼                                 
                   ▼                               ★SR2 功能评审                      
                  ★SR1 需求评审                     │                                 
                                                    ▼                                 
                                                    TEST-2 最终审计                   
                                                    │                                 
                                                    ▼                                 
                                                   ★SR3 最终评审                     
```

★ = 人工审批节点

---

## 详细时序

```
┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐
│ User │     │  PM  │     │  BA  │     │  SA  │     │  DE  │     │  TE  │
└──┬───┘     └──┬───┘     └──┬───┘     └──┬───┘     └──┬───┘     └──┬───┘
   │            │            │            │            │            │
   │ /pdt-init  │            │            │            │            │
   │───────────>│            │            │            │            │
   │            │            │            │            │            │
   │<──提问──── │            │            │            │            │
   │───回答────>│            │            │            │            │
   │            │            │            │            │            │
   │<─Proposal─ │            │            │            │            │
   │──确认─────>│            │            │            │            │
   │            │            │            │            │            │
   │ /pdt-propose            │            │            │            │
   │───────────>│            │            │            │            │
   │            │──handoff──>│            │            │            │
   │            │<──回报─────│            │            │            │
   │            │──handoff───────────────>│            │            │
   │            │<──回报─────────────────-│            │            │
   │            │──handoff──────────────────────────────────────── >│
   │            │<──回报────────────────────────────────────────── │
   │            │            │            │            │            │
   │            │──编排计划──>│            │            │            │
   │<──SR1审批──│            │            │            │            │
   │──通过─────>│            │            │            │            │
   │            │            │            │            │            │
   │ /pdt-apply │            │            │            │            │
   │───────────>│            │            │            │            │
   │            │──handoff───────────────────────────>│            │
   │            │<──回报─────────────────────────────-│            │
   │            │──handoff──────────────────────────────────────── >│
   │            │<──回报────────────────────────────────────────── │
   │            │            │            │            │            │
   │            │ (失败则循环 DE→TE，最多5轮)         │            │
   │            │            │            │            │            │
   │<──SR2审批──│            │            │            │            │
   │──通过─────>│            │            │            │            │
   │            │──handoff(最终审计)────────────────────────────── >│
   │            │<──回报────────────────────────────────────────── │
   │<──SR3审批──│            │            │            │            │
   │──通过─────>│            │            │            │            │
   │            │            │            │            │            │
   │ /pdt-archive            │            │            │            │
   │───────────>│            │            │            │            │
   │            │──归档──────>            │            │            │
   │<──SR4确认──│            │            │            │            │
   │──确认─────>│            │            │            │            │
   │            │            │            │            │            │
   │<──完成────-│            │            │            │            │
```

---

## Handoff 流转

```
PM 写入 handoff          角色执行              角色回报
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ status: pending │────>│ 读取白名单    │────>│ status: done    │
│ to: {role}      │     │ 执行任务      │     │ output_files: []│
│ input_files: [] │     │ 写入产出物    │     │ summary: ""     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                                                      ▼
                                              PM 校验产出物
                                              更新 .state.md
                                              启动下一步
```

---

## 修复循环

```
        ┌─────────────────────────────────────┐
        │                                     │
        ▼                                     │
  DE 编码(R{N}) ──> TE 审计 ──> PASS ──> 下一步
                        │
                        ▼
                      FAIL
                        │
                        ▼
                   N < 5 ? ──YES──> PM 写新 handoff(R{N+1}) ─┘
                        │
                        NO
                        │
                        ▼
                   上升人工审核
```

---

## 状态机

```
init ──────> propose ──────> apply ──────> archive ──────> DONE
  │              │              │              │
  │ (RESUME)     │ (SR1驳回)    │ (SR2/3驳回)  │ (SR4驳回)
  └──> init      └──> propose   └──> apply     └──> apply
```

---

## 通用规则

### 角色切换指令格式

PM 向其他角色发送任务时，使用以下标准格式：

```
[调度指令]
目标角色: {BA/SA/DE/TE}
任务类型: {任务名称}
Handoff 文件: deliverables/handoffs/{handoff-id}.md
输入物: {文件路径列表}
输出物: {期望产出路径}
参考: skills/{skill-file}.md Step {N}
```

### Handoff 协议（角色切换前必须执行）

PM 在每次调度非 PM 角色前，MUST 按以下顺序执行：

0. 打印心跳: `[PM] 调度 {角色} 执行 {任务类型}`
1. 写入 Handoff 文件 → `deliverables/handoffs/{REQ-ID}-{STEP-ID}-R{N}.md`
   - 使用 deliverables/handoffs/.handoff-template.md 格式
   - 白名单必须精确列出目标角色可读取的每一个文件路径（禁止通配符）
2. 更新 `.state.md` → current_role, current_step, current_handoff
3. 发出 [调度指令]（含 Handoff 文件路径字段）
4. 追加日志到 `deliverables/process.log`

目标角色完成后，PM：
5. 验证产出物（文件存在 + 非空 + 格式合规）
6. 更新 `.state.md`（追加已完成步骤、恢复 current_role 为 PM）
7. 追加日志到 `deliverables/process.log`

### 心跳打印规则

PM 在以下时机必须打印心跳信息（格式: `[PM] {描述}`）：

- 流程开始时: `[PM] /pdt-{command} 流程启动，REQ-ID: {REQ-ID}`
- 调度角色前: `[PM] 调度 {role} 执行 {任务类型}`
- 角色完成后: `[PM] {role} {任务类型}完成，产物已验证`
- 人工审批前: `[PM] 进入 {SR-N} 人工审批`
- 审批结果后: `[PM] {SR-N} 审批通过` 或 `[PM] {SR-N} 审批驳回，回退到 Step {X}`
- 异常处理时: `[PM] TE 审计失败（轮次 {N}/5），转发 DE 修复`
- 流程结束时: `[PM] /pdt-{command} 流程完成`

### 过程日志规则

所有角色的执行过程必须记录到 `deliverables/process.log`，格式：

```
[{时间}] [{角色}] {事件描述}
```

示例：
```
[2026-05-16T10:00:00Z] [PM] /pdt-propose 流程启动
[2026-05-16T10:00:01Z] [PM] 调度 BA 执行需求分析
[2026-05-16T10:01:30Z] [BA] 需求分析完成，输出: deliverables/sa/requirement-spec.md
[2026-05-16T10:01:31Z] [PM] BA 需求分析完成，产物已验证
[2026-05-16T10:01:32Z] [PM] 调度 SA 执行架构设计
```

日志写入规则：
- PM 每次调度前、验证后各追加一条
- BA/SA/DE/TE 完成任务后追加一条（含产物路径）
- 人工审批结果追加一条
- 异常/失败追加一条（含原因摘要）

### 断点恢复协议

PM 恢复执行时（新会话或上下文重置后）：
1. 读取 `deliverables/.state.md`
2. 根据 phase + current_role + current_step 确定恢复点
3. 检查 current_handoff 对应文件的 status：
   - status=done → 推进下一步
   - status=pending → 重新派发（创建新 handoff，轮次+1）
   - status=failed → 进入修复循环
4. 禁止依赖对话历史推断进度

### 异常处理

- 任何步骤产出物自检失败 → 回退到该步骤重新执行
- TE 审计失败 → 将失败报告转发 DE 修复，最多 5 轮
- 超过 5 轮 → 暂停流程，上升到人工审核
- 人工审批驳回 → 记录驳回原因，回退到对应步骤

### 人工审批呈现格式

```
[人工审批节点]
评审节点: {SR1/SR2/SR3/SR4}
审批内容摘要:
  - {要点1}
  - {要点2}
相关产物: {文件路径列表}
请确认: 通过 / 驳回（请说明原因）
```

### Token 节流规则（贯穿 apply 流程）

- 每完成一个任务的开发+审计后，清洗上下文中该任务的代码内容
- 只保留文件路径引用（如"已完成: deliverables/output/xxx"）
- 下一任务开发时重新读取 design.md 对应段落，不依赖上下文中的历史代码

---
<!-- WORKFLOW_DETAIL_PLACEHOLDER -->

## /pdt-init 详细执行序列

### 触发条件
用户输入 `/pdt-init`

### 执行序列

**Step 1: 场景检测**

根据当前状态判断场景：

- 检查 deliverables/.state.md：
  - 为空/不存在 → MODE=NEW
  - phase 非空且未归档 → MODE=RESUME
  - spec/ 下有已归档文件 → MODE=CHANGE

**MODE = RESUME（断点续作）：**
- 向用户确认："检测到未完成的 {REQ-ID}，是否继续？"
  - 用户确认继续：根据 phase 提示用户输入对应命令
  - 用户要求放弃：清理 .state.md，重新进入 NEW 模式
- 流程结束（不创建新 REQ）

**MODE = NEW（全新项目）：**
- 生成新 REQ-ID（递增）
- 初始化 .state.md
- 继续 Step 2

**MODE = CHANGE（变更迭代）：**
- 生成新 REQ-ID
- 自动备份当前 spec/ 到 spec/baselines/
- 继续 Step 2（变更模式）

---

**Step 2: 检查 reference/**
- 检查 reference/ 下是否有输入文件
- 如果为空：提示用户放入参考资料，等待用户操作后继续
- 如果有图片：调用 zai-mcp-server 识别内容
- 如果有文件：进入 Step 3

**Step 3: 启动需求澄清**
- 读取 reference/ 下所有文件
- **变更模式额外操作：**
  - 读取 spec/requirement-spec.md 和 spec/design.md 作为现有基线
  - 澄清聚焦变更点：新增了什么、修改了什么、删除了什么
  - 不重复讨论未变更的内容

**Step 4: 缺失项检测**
- 对照 Proposal 格式的必填项
- 列出所有缺失信息
- **变更模式：** 仅检测变更相关的必填项，未变更部分标注"沿用基线"

**Step 5: 交互澄清（循环）**
- 每轮向用户提出最多 3 个问题
- 收集回答后更新 proposal 草稿
- 循环直到所有必填项补齐
- **变更模式：** 问题仅围绕变更点

**Step 6: 定稿确认**
- 向用户展示完整 proposal 草稿
- **变更模式：** 明确标注哪些是变更项、哪些沿用基线
- 用户确认后：
  - 写入 deliverables/proposal.md
  - 更新 .state.md: phase=init, current_step=INIT-DONE
  - 自检：文件存在 + 非空
- 用户要求修改：回到 Step 5

**完成输出**
```
[/pdt-init 完成]
需求编号: {REQ-ID}
模式: {NEW/CHANGE}
产物: deliverables/proposal.md (READY)
基线备份: {spec/baselines/*.vN.md 或 N/A}
下一步: 用户输入 /pdt-propose
```

---
<!-- WORKFLOW_PROPOSE_PLACEHOLDER -->

## /pdt-propose 详细执行序列

### 触发条件
用户输入 `/pdt-propose`

### 执行序列

**Step 1: 前置检查**
- 验证 .state.md 中 phase=init 且 current_step=INIT-DONE
- 验证 deliverables/proposal.md 存在且非空
- 不满足则阻塞，提示用户先执行 /pdt-init

**Step 2: 调度 BA 需求分析（REQ-1）**

`[PM] 调度 BA 执行需求分析`

2a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-REQ1-R1.md
- 白名单: agents/ba.md, deliverables/proposal.md, reference/ 下具体文件列表
- 输出: deliverables/sa/requirement-spec.md

2b. 更新 .state.md: current_role=BA, current_step=REQ-1, current_handoff={文件名}

2c. 发出调度指令:
```
[调度指令]
目标角色: BA
任务类型: 需求分析
Handoff 文件: deliverables/handoffs/{REQ-ID}-REQ1-R1.md
输入物: deliverables/proposal.md, reference/*
输出物: deliverables/sa/requirement-spec.md
参考: skills/pdt-propose.md Step REQ-1
```

2d. BA 完成后，PM 自检产出物：文件存在 + 非空 + 包含 SHALL 格式需求
2e. 更新 .state.md: 追加 REQ-1 到 completed_steps，current_role=PM
2f. 追加日志到 process.log

**Step 3: 调度 SA 架构设计（REQ-2）**

`[PM] 调度 SA 执行架构设计`

3a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-REQ2-R1.md
- 白名单: agents/sa.md, deliverables/sa/requirement-spec.md
- 输出: deliverables/sa/design.md

3b. 更新 .state.md: current_role=SA, current_step=REQ-2

3c. 发出调度指令:
```
[调度指令]
目标角色: SA
任务类型: 架构设计
Handoff 文件: deliverables/handoffs/{REQ-ID}-REQ2-R1.md
输入物: deliverables/sa/requirement-spec.md
输出物: deliverables/sa/design.md
参考: skills/pdt-propose.md Step REQ-2
```

3d. SA 完成后，PM 自检产出物：文件存在 + 非空 + 包含 Tasks 清单
3e. 更新 .state.md: 追加 REQ-2 到 completed_steps，current_role=PM

**Step 4: 调度 TE 测试用例设计（REQ-3）**

`[PM] 调度 TE 执行测试用例设计`

4a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-REQ3-R1.md
- 白名单: agents/te.md, deliverables/sa/requirement-spec.md, deliverables/sa/design.md
- 输出: deliverables/te/testcases.md

4b. 更新 .state.md: current_role=TE, current_step=REQ-3

4c. 发出调度指令:
```
[调度指令]
目标角色: TE
任务类型: 测试用例设计
Handoff 文件: deliverables/handoffs/{REQ-ID}-REQ3-R1.md
输入物: deliverables/sa/requirement-spec.md, deliverables/sa/design.md
输出物: deliverables/te/testcases.md
参考: skills/pdt-propose.md Step REQ-3
```

4d. TE 完成后，PM 自检产出物：文件存在 + 非空 + 包含 E2E/回归/工程三类用例
4e. 更新 .state.md: 追加 REQ-3 到 completed_steps，current_role=PM

**Step 5: PM 计划编排（REQ-4）**

`[PM] 执行计划编排`

- 读取 design.md 中的 Tasks 清单
- 读取 testcases.md 中的用例列表
- 编排执行计划，写入 deliverables/plan-action.md
- 更新 .state.md: 追加 REQ-4 到 completed_steps

**Step 6: 需求评审（SR1）**

`[PM] 进入 SR1 人工审批`

6a. 执行 `./scripts/verify.sh B` 汇总检查结果
6b. 创建基线快照：
  - cp requirement-spec.md → deliverables/baselines/requirement-spec.v1.md
  - cp design.md → deliverables/baselines/design.v1.md
  - cp testcases.md → deliverables/baselines/testcases.v1.md
6c. 向用户呈现：
```
[人工审批节点]
评审节点: SR1
审批内容摘要:
  - 结构化需求文档（SHALL + GWT 格式）
  - 技术设计方案（架构 + Tasks 清单）
  - 测试用例（E2E/回归/工程三类）
  - verify.sh B 级检查结果
相关产物: deliverables/sa/requirement-spec.md, deliverables/sa/design.md, deliverables/te/testcases.md
请确认: 通过 / 驳回（请说明原因）
```

6d. 用户通过：
  - 写入 deliverables/SR1-record.md 标记 PASS
  - 更新 .state.md: sr_status.SR1=approved, phase=propose, current_step=SR1-DONE
6e. 用户驳回：
  - 写入 SR1-record.md 标记 FAIL + 原因
  - 回退到对应步骤重新执行

**完成输出**
```
[/pdt-propose 完成]
需求编号: {REQ-ID}
产物:
  - deliverables/sa/requirement-spec.md
  - deliverables/sa/design.md
  - deliverables/te/testcases.md
  - deliverables/plan-action.md
  - deliverables/SR1-record.md (PASS)
  - deliverables/baselines/*.v1.md
下一步: 用户输入 /pdt-apply
```

---
<!-- WORKFLOW_APPLY_PLACEHOLDER -->

## /pdt-apply 详细执行序列

### 触发条件
用户输入 `/pdt-apply`

### 执行序列

**Step 1: 前置检查**
- 验证 .state.md 中 sr_status.SR1=approved
- 验证 deliverables/sa/design.md 存在且非空
- 验证 deliverables/plan-action.md 存在且非空
- 不满足则阻塞，提示用户先完成 /pdt-propose
- 读取 .state.md 中 completed_steps，识别已完成任务，确定待开发顺序

**Step 1b: 任务编排确认（人工确认开发计划）**

`[PM] 生成任务编排计划`

PM 必须在开发循环开始前，向用户呈现完整的开发计划：

```
[任务编排计划]
需求编号: {REQ-ID}
总任务数: {N} | 已完成: {M} | 待开发: {N-M}

开发顺序:
  {序号}. {Task-ID}: {描述} — DE开发 → TE审计 → 人工检查
  {序号}. {Task-ID}: {描述} — DE开发 → TE审计 → 人工检查
  ...

循环后统一步骤:
  → SR2 人工审批（覆盖所有任务）
  → TE 最终审计
  → SR3 人工审批

请确认计划是否正确，或调整开发顺序。
```

- 用户确认：继续 Step 2
- 用户调整：按用户要求修改顺序后重新呈现

---

**Step 2-3: 逐任务开发+审计循环**

⚠️ **关键约束：以下 Step 2、Step 3、Step 3b 是一个循环体，对每个任务都必须完整执行一遍。禁止批量开发多个任务后再统一审计。每个任务必须走完 DE开发→TE审计→人工检查 后，才能开始下一个任务的开发。**

```
FOR 每个待开发任务 IN plan-action.md（跳过已完成）:
    Step 2: DE 开发该任务
    Step 3: TE 审计该任务（失败则循环修复，最多5轮，超过上升人工）
    Step 3b: 人工检查该任务（轻量确认）
    → 清洗上下文中该任务代码内容，只保留文件路径
    → 继续下一个任务
END FOR

所有任务开发+审计+人工检查完成后:
    Step 4: 人工审批 SR2（正式审批，覆盖所有任务）
    Step 5: TE 最终审计（全量）
    Step 6: 人工审批 SR3
```

---

**Step 2: DE 开发当前任务（DEV-1.N）**

`[PM] 调度 DE 开发 Task-{N}`

⚠️ **前置校验（非首个任务时）：** PM 必须检查 .state.md 中上一个任务的人工检查记录存在且结果为 PASS。如果记录不存在，禁止写入当前任务的 Handoff。

2a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-DEV1-T{N}-R1.md
- 白名单: agents/de.md, deliverables/sa/design.md（Task-{N} 部分）, 已有代码（如有）
- 输出: deliverables/output/{对应产出}, deliverables/de/code-report.md

2b. 更新 .state.md: current_role=DE, current_step=DEV-1.{N}, current_handoff={文件名}

2c. 发出调度指令:
```
[调度指令]
目标角色: DE
任务类型: 编码实现
Handoff 文件: deliverables/handoffs/{REQ-ID}-DEV1-T{N}-R1.md
输入物: deliverables/sa/design.md (Task-{N} 部分)
输出物: deliverables/output/{产出路径}
参考: skills/dev-test.md, skills/post-verify.md
```

2d. DE 完成后，PM 自检：文件存在 + 非空
2e. 更新 .state.md: current_role=PM
2f. 追加日志到 process.log

**Step 3: TE 审计当前任务（TEST-1.N）**

`[PM] 调度 TE 审计 Task-{N}`

3a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-TEST1-T{N}-R1.md
- 白名单: agents/te.md, deliverables/output/{产出}, deliverables/sa/requirement-spec.md, deliverables/te/testcases.md
- 输出: deliverables/te/temp-test-report.md

3b. 更新 .state.md: current_role=TE

3c. 发出调度指令:
```
[调度指令]
目标角色: TE
任务类型: 审计验证
Handoff 文件: deliverables/handoffs/{REQ-ID}-TEST1-T{N}-R1.md
输入物: deliverables/output/{产出}
输出物: deliverables/te/temp-test-report.md
参考: skills/post-verify.md
```

3d. TE 完成后，PM 检查审计结论
3e. 更新 .state.md: current_role=PM

**Step 3a: 审计失败处理（最多 5 轮）**

- 如果 FAIL：
  - 轮次 < 5：
    - `[PM] TE 审计失败（轮次 {R}/5），转发 DE 修复`
    - 写入新 Handoff: deliverables/handoffs/{REQ-ID}-DEV1-T{N}-R{R+1}.md
    - 白名单增加: deliverables/te/temp-test-report.md（失败详情）
    - 回到 Step 2（同一任务）
  - 轮次 >= 5：
    - `[PM] Task-{N} 超过最大重试次数，上升人工审核`
    - 暂停，等待人工决策
- 如果 PASS：继续 Step 3b

**Step 3b: 逐任务人工检查**

`[PM] 进入逐任务人工检查 Task-{N}`

向用户呈现：
```
[逐任务人工检查]
任务: Task-{N} - {描述}
产出文件: deliverables/output/{路径}
审计报告: deliverables/te/temp-test-report.md
请确认: 通过 / 驳回（请说明原因）
```

- 用户通过：
  - 追加到 .state.md completed_steps
  - 清洗上下文中当前任务代码，只保留文件路径
  - 追加日志到 process.log
  - 如果还有待开发任务 → 回到 Step 2（下一个任务）
  - 如果所有任务完成 → 继续 Step 4
- 用户驳回：
  - 记录驳回原因
  - 写入新 Handoff 给 DE 修复
  - 回到 Step 2（同一任务）
  - 注意：人工检查驳回无轮次限制

---

**Step 4: 功能评审（SR2）— 人工审批**

`[PM] 进入 SR2 人工审批（所有任务）`

向用户呈现：
```
[人工审批节点]
评审节点: SR2
审批内容摘要:
  - 已完成任务列表及各自审计结论
  - 代码报告摘要
  - 各任务人工检查结论
相关产物: deliverables/output/, deliverables/te/temp-test-report.md, deliverables/de/code-report.md
请确认: 通过 / 驳回（请说明原因）
```

- 用户通过：
  - 写入 deliverables/SR2-record.md 标记 PASS
  - 更新 .state.md: sr_status.SR2=approved
  - 继续 Step 5
- 用户驳回：
  - SR2-record.md 标记 FAIL + 原因
  - 指定需修复的任务，回退到 Step 2

**Step 5: TE 最终审计（TEST-2）**

`[PM] 调度 TE 最终审计`

5a. 写入 Handoff 文件:
- 路径: deliverables/handoffs/{REQ-ID}-TEST2-R1.md
- 白名单: agents/te.md, deliverables/output/ 下所有产出, deliverables/sa/requirement-spec.md, deliverables/te/testcases.md
- 输出: deliverables/te/final-test-report.md

5b. 发出调度指令:
```
[调度指令]
目标角色: TE
任务类型: 最终审计验证
Handoff 文件: deliverables/handoffs/{REQ-ID}-TEST2-R1.md
输入物: deliverables/output/*
输出物: deliverables/te/final-test-report.md
参考: skills/post-verify.md
```

5c. TE 完成后，PM 检查结论:
  - PASS → 继续 Step 6
  - FAIL → 回退修复（同修复循环逻辑）

**Step 6: 功能评审（SR3）— 人工审批**

`[PM] 进入 SR3 人工审批`

向用户呈现：
```
[人工审批节点]
评审节点: SR3
审批内容摘要:
  - 全部产出物清单
  - TE 最终审计报告结论
相关产物: deliverables/output/, deliverables/te/final-test-report.md
请确认: 通过 / 驳回（请说明原因）
```

- 用户通过：
  - 写入 deliverables/SR3-record.md 标记 PASS
  - 更新 .state.md: sr_status.SR3=approved, phase=apply, current_step=SR3-DONE
- 用户驳回：
  - SR3-record.md 标记 FAIL + 原因
  - 回退修复

**完成输出**

⚠️ **PM 必须在流程结束时打印以下完成通知，不得省略：**

```
[/pdt-apply 完成]
需求编号: {REQ-ID}
产物:
  - deliverables/output/*
  - deliverables/te/final-test-report.md (PASS)
  - deliverables/SR3-record.md (PASS)
下一步: 用户输入 /pdt-archive
```

---
<!-- WORKFLOW_ARCHIVE_PLACEHOLDER -->

## /pdt-archive 详细执行序列

### 触发条件
用户输入 `/pdt-archive`

### 执行序列

**Step 1: 前置检查**
- 验证 .state.md 中 sr_status.SR3=approved
- 验证 deliverables/output/ 存在且非空
- 不满足则阻塞，提示用户先完成 /pdt-apply
- 检测归档模式：
  - spec/ 下无文件 → 首次归档模式（copy）
  - spec/ 下有文件 → 变更归档模式（merge）

**Step 2: 需求归档（ARC-1）**

`[PM] 启动 ARC-1 需求归档`

- **首次模式：** cp deliverables/sa/requirement-spec.md → spec/requirement-spec.md
- **变更模式：**
  - 将 deliverables/sa/requirement-spec.md 中的变更内容 merge 到 spec/requirement-spec.md
  - 保留原有内容，追加/修改变更部分
  - 标注变更来源 REQ-ID
- 自检：文件存在 + 非空
- 追加日志到 process.log

**Step 3: 设计归档（ARC-2）**

`[PM] 启动 ARC-2 设计归档`

- **首次模式：** cp deliverables/sa/design.md → spec/design.md
- **变更模式：**
  - 将 deliverables/sa/design.md 中的变更内容 merge 到 spec/design.md
  - 新增任务追加到 Tasks 清单
  - 修改任务更新对应段落
  - 删除任务标记移除
- 自检：文件存在 + 非空

**Step 4: 代码归档（ARC-3）**

`[PM] 启动 ARC-3 代码归档`

- cp deliverables/output/* → output/final/
- 如已存在同名文件则覆盖
- 保留不冲突的已有文件
- 自检：output/final/ 非空，所有文件完整

**Step 5: 更新状态**
- 更新 .state.md: phase=archive, current_step=ARC-DONE
- 追加日志到 process.log

**Step 6: 项目结项确认（SR4）**

`[PM] 进入 SR4 人工审批`

向用户呈现：
```
[人工审批节点]
评审节点: SR4
审批内容摘要:
  - 归档模式: {首次归档/变更归档}
  - 归档文件列表
  - 变更模式下: 本次变更涉及的内容、基线版本号
  - 最终产物位置: output/final/
相关产物: spec/requirement-spec.md, spec/design.md, output/final/
请确认: 通过 / 驳回（请说明原因）
```

- 用户通过：
  - 写入 deliverables/SR4-record.md 标记 PASS
  - 更新 .state.md: sr_status.SR4=approved, phase=done
  - `[PM] 项目结项完成`
- 用户驳回：
  - SR4-record.md 标记 FAIL + 原因
  - 回退修复

**完成输出**
```
[/pdt-archive 完成]
需求编号: {REQ-ID}
模式: {首次归档/变更归档}
归档产物:
  - spec/requirement-spec.md (已{创建/merge})
  - spec/design.md (已{创建/merge})
  - output/final/*
基线版本: spec/baselines/*.v{N}.md
项目状态: DONE
```
