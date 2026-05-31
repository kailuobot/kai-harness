# Skill: mh-apply

开发实现 → 审计验证 → 人工审批。按 mode 裁剪步骤。

**日志规则：** 见 `templates/logging-standard.md`

---

## 前置检查

1. 读取 `deliverables/.state.md` 获取当前 req_id
2. 验证 `deliverables/{REQ-ID}/.state.md` 中 current_step=PROPOSE-DONE
3. 读取 mode 字段确定流程裁剪方式
4. 验证 `deliverables/{REQ-ID}/plan-action.md` 存在且非空
5. 不满足则阻塞，提示用户先完成 /mh-propose

## 断点续作

1. 读取 `deliverables/{REQ-ID}/.state.md` 中 completed_steps
2. 读取 `repair_round` 和 `repair_task` 字段，恢复修复循环上下文
3. 跳过已完成的 Task，从未完成的 Task 继续
4. 如 repair_round > 0，从修复循环的当前轮次继续（而非从第 1 轮重新开始）
5. `[PM] 断点恢复，从 {step_id} 继续（repair_round={N}）`

---

## fast 模式

DE 一次性开发所有任务 → TE 轻量审计 → 人工确认（唯一审批点）。

**Step 1: DE 批量开发**

1. `[PM] fast 模式，DE 批量开发所有任务`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-R1.md`
   - to: DE
   - 白名单: `deliverables/{REQ-ID}/plan-action.md`, `deliverables/{REQ-ID}/proposal.md`, 已有代码
   - 期望输出: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/de/code-report.md`
3. 更新 `deliverables/{REQ-ID}/.state.md`: current_step=DEV-1, current_role=DE
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/de.md + 白名单文件
   - [Cline] 切换角色为 DE，指示读取 handoff
5. 接收回报，执行质量门禁:
   - 文件存在性: output/ 非空、de/code-report.md 存在
   - DE 质量门禁（见 agents/pm.md）：dev-test=PASS、post-verify=PASS、无 TODO 残留
   - 不满足则驳回（新 handoff，附具体缺陷描述）
6. `[PM] 开发完成`

**Step 2: TE 轻量审计**

1. `[PM] fast 模式，TE 轻量审计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-R1.md`
   - to: TE
   - 白名单: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/proposal.md`, `deliverables/{REQ-ID}/.state.md`
   - 期望输出: `deliverables/{REQ-ID}/te/temp-test-report.md`
   - 约束: 根据 .state.md 中 test_strategy 执行对应验证；如 test_strategy=manual，生成人工检查清单
3. 派发任务给 TE
4. 接收回报，执行质量门禁:
   - TE 质量门禁（见 agents/pm.md）：结论明确、PASS 时无未解决失败项、FAIL 时有复现步骤
   - PASS → 继续 Step 3
   - FAIL → 修复循环（最多5轮）

**Step 3: 人工确认（唯一审批点）**

1. `[PM] 进入人工确认`
2. 向用户呈现：
   ```
   [人工确认]
   模式: fast
   产出文件: deliverables/{REQ-ID}/output/
   审计报告: deliverables/{REQ-ID}/te/temp-test-report.md
   请确认: 通过 / 驳回（请说明原因）
   ```
3. 用户通过:
   - 更新 `deliverables/{REQ-ID}/.state.md`: sr_status.SR2=skipped, sr_status.SR3=approved, phase=apply, current_step=SR3-DONE
   - `[PM] 确认通过（fast模式），可执行 /mh-archive`
4. 用户驳回:
   - 记录原因，回退 DE 修复

---

## standard 模式

并行批次开发（按依赖分批）→ SR2 → 最终审计 → SR3。

**Step 1: 并行批次开发+审计**

> ⚡ 并行优化：无依赖的 Task 同批并行开发和审计。仅 Claude Code 模式支持并行；Cline 模式退化为逐任务串行。

```
读取 plan-action.md 中的 Task 列表和依赖关系（[deps: ...]）
计算并行批次:
  Batch-1: 所有 deps=none 的 Task
  Batch-2: 依赖仅在 Batch-1 中的 Task
  Batch-N: 依赖仅在前序 Batch 中的 Task
  （无依赖标注时，所有 Task 视为 deps=none，归入同一批次）

FOR 每个 Batch（跳过已完成的 Task）:
    并行派发 Batch 内所有 Task 给 DE
    等待所有 DE 完成
    并行派发 Batch 内所有 Task 给 TE 审计
    等待所有 TE 完成
    对失败的 Task 进入修复循环（可并行修复）
    人工批量确认本批次
    记入 completed_steps
END FOR
```

对每个 Batch-{B}：

1. `[PM] 启动 Batch-{B}，包含 Task: {列表}，并行派发给 DE`
2. 为 Batch 内每个 Task-{N} 写入 handoff:
   - `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-T{N}-R1.md`
   - to: DE
   - 白名单: `deliverables/{REQ-ID}/sa/design.md`（Task-{N} 部分）, 已有代码, 前序 Batch 产出代码
   - 期望输出: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/de/code-report.md`
3. 并行派发:
   - [Claude Code] 同时 spawn 多个 DE SubAgent，每个处理一个 Task
   - [Cline] 逐个串行执行
4. 等待所有 DE 完成，执行质量门禁:
   - 文件存在性: 各 Task 的 output/ 产出存在
   - DE 质量门禁（见 agents/pm.md）：dev-test=PASS、post-verify=PASS、无 TODO 残留
   - 不满足则驳回对应 Task（新 handoff，附具体缺陷描述）
5. `[PM] Batch-{B} 开发完成，并行派发 TE 审计`
6. 为 Batch 内每个 Task-{N} 写入 TE handoff:
   - `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-T{N}-R1.md`
   - 读取 .state.md 中 test_strategy 执行对应验证
7. 并行派发:
   - [Claude Code] 同时 spawn 多个 TE SubAgent
   - [Cline] 逐个串行执行
8. 等待所有 TE 完成，执行质量门禁并汇总审计结果:
   - TE 质量门禁（见 agents/pm.md）：结论明确、覆盖分析完整、失败项有复现步骤
   - 全部 PASS → 人工批量确认本批次
   - 部分 FAIL → 失败的 Task 进入修复循环（可并行修复），通过的 Task 等待
9. 人工批量确认:
   ```
   [人工确认 Batch-{B}]
   通过的 Task: {列表}
   审计报告: deliverables/{REQ-ID}/te/temp-test-report.md
   请确认: 通过 / 驳回（指定 Task 和原因）
   ```
10. 确认通过 → 记入 completed_steps → 下一个 Batch

**Step 2: SR2 功能评审**

1. `[PM] 所有 Task 完成，启动 SR2 功能评审`
2. 向用户呈现：
   ```
   [人工审批节点]
   评审节点: SR2
   审批内容摘要:
     - 已完成 Task 列表及各自审计结论
     - 代码报告摘要
   相关产物: deliverables/{REQ-ID}/output/, deliverables/{REQ-ID}/te/temp-test-report.md
   请确认: 通过 / 驳回（请说明原因）
   ```
3. 通过: 写入 SR2-record.md，继续
4. 驳回: 回退指定 Task

**Step 3: TE 最终审计**

1. `[PM] 启动最终审计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST2-R1.md`
   - 全量测试（E2E + 回归 + 工程验证）
   - 期望输出: `deliverables/{REQ-ID}/te/final-test-report.md`
3. 结论: PASS → SR3 / FAIL → 修复

**Step 4: SR3 最终评审**

1. `[PM] 启动 SR3 最终功能评审`
2. 向用户呈现最终测试报告 + 产出物清单
3. 通过:
   - 写入 SR3-record.md
   - 更新 `deliverables/{REQ-ID}/.state.md`: sr_status.SR3=approved, phase=apply, current_step=SR3-DONE
   - `[PM] SR3 通过，可执行 /mh-archive`
4. 驳回: 回退修复

---

## full 模式

与 standard 模式相同流程，无裁剪。

（full 模式的 apply 阶段与 standard 完全一致，区别仅在 propose 阶段有 SR1 评审）

---

## 修复循环（所有模式通用）

1. `[PM] Task-{N} 审计失败（轮次 {R}/5），派发修复给 DE`
2. 更新 `deliverables/{REQ-ID}/.state.md`: repair_round={R+1}, repair_task=Task-{N}
3. 写入新 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-T{N}-R{R+1}.md`
   - 附加: 上轮失败原因、失败报告路径
4. DE 修复 → TE 重新审计
5. 审计通过: 更新 `deliverables/{REQ-ID}/.state.md`: repair_round=0, repair_task=""
6. 轮次达 5 次仍失败: `[PM] Task-{N} 超过最大重试次数，上升人工审核`

## 异常处理

- SubAgent 回报 status=failed: 检查原因，决定重试或上升
- 浏览器环境不可用: 提示用户安装 Playwright 依赖
- 断点恢复时发现不一致: 以 `deliverables/{REQ-ID}/.state.md` 为准，重新校验文件状态
