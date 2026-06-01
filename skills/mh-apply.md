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
5. 接收回报，执行质量门禁（agents/pm.md "DE 产出验收"清单）:
   - 全部通过 → 继续
   - 不通过 → 驳回（新 handoff 附未通过项 + 位置 + 修正方向）
6. `[PM] 开发完成`

**Step 2: TE 轻量审计**

1. `[PM] fast 模式，TE 轻量审计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-R1.md`
   - to: TE
   - 白名单: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/proposal.md`, `deliverables/{REQ-ID}/.state.md`
   - 期望输出: `deliverables/{REQ-ID}/te/temp-test-report.md`
   - 约束: fast 模式轻量验证——工程检查（lint+构建）+ 关键路径抽查（验证核心功能可用），不要求完整覆盖分析。根据 .state.md 中 test_strategy 执行对应验证；如 test_strategy=manual，生成人工检查清单（仅核心项）
3. 派发任务给 TE
4. 接收回报，执行质量门禁（agents/pm.md "TE 产出验收"清单）:
   - PASS → 继续 Step 3
   - FAIL → 修复循环（最多5轮）

**Step 3: 人工确认（唯一审批点）**

1. `[PM] 进入人工确认`
2. 向用户呈现决策上下文：
   ```
   [人工确认]
   模式: fast
   
   变更摘要:
     - 文件数: {N} 个文件
     - 新增/修改/删除: +{N} / ~{N} / -{N}
   
   质量状态:
     - 测试: {通过数}/{总数} 通过
     - dev-test: PASS
     - TE 审计: {PASS/FAIL} ({一句话结论})
   
   修复历史: {首次通过 / 经 {N} 轮修复后通过}
   
   产出文件: deliverables/{REQ-ID}/output/
   审计报告: deliverables/{REQ-ID}/te/temp-test-report.md
   
   PM 建议: {通过/建议人工复查} ({理由})
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
>
> code-report 规则：每个 Task 独立 code-report（`code-report-t{N}.md`）。同批并行的 Task 不得合并 code-report。如 SubAgent 合并产出，PM 在质量门禁时要求补充独立报告。

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
4. 等待所有 DE 完成，执行质量门禁（agents/pm.md "DE 产出验收"清单）:
   - 全部通过 → 继续
   - 不通过 → 驳回对应 Task（新 handoff 附未通过项 + 位置 + 修正方向）
5. `[PM] Batch-{B} 开发完成，并行派发 TE 审计`
6. 为 Batch 内每个 Task-{N} 写入 TE handoff:
   - `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-T{N}-R1.md`
   - 读取 .state.md 中 test_strategy 执行对应验证
7. 并行派发:
   - [Claude Code] 同时 spawn 多个 TE SubAgent
   - [Cline] 逐个串行执行
8. 等待所有 TE 完成，执行质量门禁（agents/pm.md "TE 产出验收"清单）并汇总:
   - 全部 PASS → 人工批量确认本批次
   - 部分 FAIL → 失败的 Task 进入修复循环（可并行修复），通过的 Task 等待
9. 人工批量确认:
   ```
   [人工确认 Batch-{B}]
   
   通过的 Task: {列表}
   变更摘要:
     - 总文件数: {N}
     - 各 Task 概要: {Task-1: +X行, Task-2: +Y行, ...}
   
   质量状态:
     - 测试覆盖: {已验证需求数}/{总需求数}
     - 修复轮次: {各 Task 的修复次数，0=首次通过}
   
   审计报告: deliverables/{REQ-ID}/te/temp-test-report.md
   PM 建议: {通过/建议复查} ({理由})
   请确认: 通过 / 驳回（指定 Task 和原因）
   ```
10. 确认通过 → 记入 completed_steps → 下一个 Batch

**Step 2: SR2 功能评审**

1. `[PM] 所有 Task 完成，启动 SR2 功能评审`
2. PM 逐项核对 SR2 通过标准：
   ```
   SR2 通过标准:
   - [ ] 所有 Task 通过 TE 审计（无 Critical/Major 缺陷）
   - [ ] 代码质量达标（所有 Task 的 dev-test=PASS, post-verify=PASS）
   - [ ] 无 TODO/FIXME 残留（verify.sh D 类检查通过）
   - [ ] 需求覆盖无明显遗漏
   ```
3. 向用户呈现决策上下文：
   ```
   [人工审批节点]
   评审节点: SR2
   
   完成概况:
     - 已完成 Task: {列表及各自审计结论}
     - 总文件变更: {N} 个文件
     - 测试覆盖: {已验证需求数}/{总需求数}
   
   风险评估:
     - 修复轮次统计: {各 Task 修复次数，高修复次数=高风险}
     - 降级验证: {有/无，如有列出未覆盖项}
   
   相关产物: deliverables/{REQ-ID}/output/, deliverables/{REQ-ID}/te/temp-test-report.md
   PM 建议: {通过/建议复查} ({理由})
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
2. PM 逐项核对 SR3 通过标准：
   ```
   SR3 通过标准:
   - [ ] 全量测试通过（TE final-test-report 结论=PASS）
   - [ ] 需求覆盖率 ≥ 95%，且未覆盖项均有降级机制或补充计划
   - [ ] 无 Critical/Major 缺陷
   - [ ] 回归测试通过（已有功能未被破坏）
   ```
3. 向用户呈现决策上下文：
   ```
   [人工审批节点]
   评审节点: SR3（最终评审）
   
   最终审计结论: {PASS/FAIL}
   需求覆盖: {已验证}/{总数} ({百分比})
   
   质量总结:
     - 全量测试: {通过数}/{总数}
     - 回归测试: {通过/未执行}
     - 工程验证: {lint + 构建状态}
   
   降级项确认（覆盖率 < 100% 时必填）:
     - {未覆盖需求}: {降级机制/补充计划}
   
   风险项（如有）:
     - {降级验证项}
     - {高修复次数的 Task}
   
   产出物清单: deliverables/{REQ-ID}/output/ ({N} 个文件)
   最终报告: deliverables/{REQ-ID}/te/final-test-report.md
   PM 建议: {通过/建议复查} ({理由})
   请确认: 通过 / 驳回（请说明原因）
   ```
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

### 根因分析（PM 执行）

PM 在派发修复前，必须基于 TE 报告进行根因分析：

1. `[PM] Task-{N} 审计失败（轮次 {R}/5），执行根因分析`
2. 读取 TE 报告，提取：
   - 失败特征：错误类型（test_failure / lint_error / build_error / logic_error）
   - 关键错误信息：具体的报错内容（前 2-3 条）
   - 影响范围：失败数量 / 总数量
3. 对比历史（如 repair_round > 1）：
   - 与上轮相比，失败数是增加还是减少？（收敛判断）
   - 错误类型是否变化？（新问题 vs 同一问题）
4. 形成修复指导：根因假设 + 建议修复方向

### 收敛追踪与提前升级

更新 `.state.md` 中 repair_history（每轮追加）：
```yaml
repair_history:
  - round: 1
    error_type: "test_failure"
    failed_count: 3
    summary: "API endpoint 返回 500"
    root_cause_hypothesis: "UserService.create() 返回 null"
    action_taken: "修复 create() 返回值，确保返回 user 对象"
  - round: 2
    error_type: "test_failure"
    failed_count: 2
    summary: "修复了连接问题，仍有 2 个断言失败"
    root_cause_hypothesis: "返回值修复后，响应体序列化缺少 user_id 字段"
    action_taken: "补充响应体映射，确保包含 user_id"
```

**提前升级条件**（不等到第 5 轮）：
- 连续 2 轮 failed_count 增加（发散）→ 立即升级人工
- 连续 2 轮 error_type 变化（修一个坏一个）→ 立即升级人工
- 第 3 轮仍为同一错误且无进展 → 升级人工

### 修复派发

> repair_snapshots 用途：PM 对比各轮 hash 确认产出物在变化；发散升级时附带快照历史让用户看到完整变化轨迹；如需回退可定位对应 code-report-r{N}.md。

1. 修复派发前，PM 执行快照：
   - 计算当前 output/ 的文件 hash（`find output/ -type f | xargs md5sum | md5sum`）
   - 将 hash 和当前 code-report 路径追加到 `.state.md` repair_snapshots
2. 更新 `deliverables/{REQ-ID}/.state.md`: repair_round={R+1}, repair_task=Task-{N}
3. 写入新 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-T{N}-R{R+1}.md`
   - 使用 handoff 模板中的"修复上下文"节，填写：
     - 失败特征：{错误类型 + 关键错误信息}
     - 根因假设：{PM 的分析}
     - 建议修复方向：{具体指导，不是"请修复"}
     - 历史尝试：{前几轮做了什么、为什么没成功}
   - 白名单追加：TE 的失败报告路径
4. `[PM] 派发修复给 DE（轮次 {R+1}/5，{收敛/发散}）`
5. DE 修复 → TE 重新审计
5. 审计通过:
   - 更新 `.state.md`: repair_round=0, repair_task="", repair_history=[]
6. 达到升级条件:
   - `[PM] Task-{N} 修复未收敛，上升人工审核`
   - 向用户呈现完整修复历史和失败模式

## 异常处理

- SubAgent 回报 status=failed: 检查原因，决定重试或上升
- SubAgent 超时但产出物已存在:
  - PM 检查 output/ 中对应 Task 的文件是否完整（与 plan-action.md 描述匹配）
  - 完整 → 视为成功，PM 代填 code-report（标注"[PM 代填] Agent 超时，产出物完整"）
  - 不完整 → 重试一次
- 浏览器环境不可用: 提示用户安装 Playwright 依赖
- 断点恢复时发现不一致: 以 `deliverables/{REQ-ID}/.state.md` 为准，重新校验文件状态
