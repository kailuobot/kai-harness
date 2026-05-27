# Skill: mh-apply

开发实现 → 审计验证 → 人工审批。按 mode 裁剪步骤。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/{REQ-ID}/process.log`，格式：`[{timestamp}] [{角色}] {事件描述}`。timestamp 获取方式：优先使用 `date -u +%Y-%m-%dT%H:%M:%SZ`；如 date 命令不可用，使用递增序号 `#NNN`。

---

## 前置检查

1. 读取 `deliverables/.state.md` 获取当前 req_id
2. 验证 `deliverables/{REQ-ID}/.state.md` 中 current_step=PROPOSE-DONE
3. 读取 mode 字段确定流程裁剪方式
4. 验证 `deliverables/{REQ-ID}/plan-action.md` 存在且非空
5. 不满足则阻塞，提示用户先完成 /mh-propose

## 断点续作

1. 读取 `deliverables/{REQ-ID}/.state.md` 中 completed_steps
2. 跳过已完成的 Task，从未完成的 Task 继续
3. `[PM] 断点恢复，从 {step_id} 继续`

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
5. 接收回报，校验输出文件存在性
6. `[PM] 开发完成`

**Step 2: TE 轻量审计**

1. `[PM] fast 模式，TE 轻量审计`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-R1.md`
   - to: TE
   - 白名单: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/proposal.md`, `deliverables/{REQ-ID}/.state.md`
   - 期望输出: `deliverables/{REQ-ID}/te/temp-test-report.md`
   - 约束: 根据 .state.md 中 test_strategy 执行对应验证；如 test_strategy=manual，生成人工检查清单
3. 派发任务给 TE
4. 接收回报:
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

逐任务循环（DE→TE→人工确认）→ SR2 → 最终审计 → SR3。

**Step 1: 逐任务开发+审计循环**

⚠️ 每个任务必须走完 DE开发→TE审计→人工确认 后，才能开始下一个任务。

```
FOR 每个待开发任务 IN plan-action.md（跳过已完成）:
    DE 开发 → TE 审计（失败则修复，最多5轮）→ 人工确认
    → 清洗上下文，继续下一个任务
END FOR
```

对每个 Task-{N}：

1. `[PM] 启动 DEV-1.{N}，派发 Task-{N} 给 DE`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-T{N}-R1.md`
   - to: DE
   - 白名单: `deliverables/{REQ-ID}/sa/design.md`（Task-{N} 部分）, 已有代码
   - 期望输出: `deliverables/{REQ-ID}/output/`, `deliverables/{REQ-ID}/de/code-report.md`
3. 派发任务给 DE
4. DE 完成后，派发 TE 审计:
   - 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-TEST1-T{N}-R1.md`
   - 读取 .state.md 中 test_strategy:
     - test_strategy=e2e 且 env.browser_available=true: TE 执行完整审计（含 E2E）
     - test_strategy=e2e 且 env.browser_available=false: TE 执行工程验证，跳过 E2E，标注 `[E2E DEGRADED]`
     - test_strategy=unit/integration/smoke: TE 执行对应级别测试 + 工程验证
     - test_strategy=manual: TE 生成人工验证清单，标注 `[MANUAL VERIFICATION REQUIRED]`
     - test_strategy=none: TE 仅执行工程验证（lint + 构建）
5. 审计结果:
   - PASS → 人工确认该任务 → 记入 completed_steps → 下一个 Task
   - FAIL → 修复循环（最多5轮）

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
2. 写入新 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-T{N}-R{R+1}.md`
   - 附加: 上轮失败原因、失败报告路径
3. DE 修复 → TE 重新审计
4. 轮次达 5 次仍失败: `[PM] Task-{N} 超过最大重试次数，上升人工审核`

## 异常处理

- SubAgent 回报 status=failed: 检查原因，决定重试或上升
- 浏览器环境不可用: 提示用户安装 Playwright 依赖
- 断点恢复时发现不一致: 以 `deliverables/{REQ-ID}/.state.md` 为准，重新校验文件状态
