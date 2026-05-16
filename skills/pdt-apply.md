# Skill: pdt-apply

开发实现 → 审计验证 → 人工审批。PM 调度，DE/TE 分步执行，支持多轮修复和断点续作。

---

## 前置检查

1. 验证 .state.md 中 phase=propose 且 sr_status.SR1=approved
2. 验证 deliverables/sa/design.md 存在且非空
3. 验证 deliverables/plan-action.md 存在且非空
4. 不满足则阻塞，提示用户先完成 /pdt-propose

## 断点续作

1. 读取 .state.md 中 completed_steps
2. 跳过已完成的 Task，从未完成的 Task 继续
3. `[PM] 断点恢复，从 {step_id} 继续`

## Step DEV-1: 编码实现（逐任务循环）

**调度角色:** PM → DE

对 plan-action.md 中的每个 Task 循环执行：

### DEV-1.{N}: 单任务开发

1. `[PM] 启动 DEV-1.{N}，派发 Task-{N} 给 DE`
2. 写入 handoff: `deliverables/handoffs/{REQ-ID}-DEV1-T{N}-R1.md`
   - to: DE
   - 白名单: deliverables/sa/design.md（Task-{N} 部分）, 已有代码
   - 期望输出: deliverables/output/, deliverables/de/code-report.md
3. 更新 .state.md: current_step=DEV-1.{N}
4. 派发任务:
   - [Claude Code] spawn SubAgent，注入 handoff + agents/de.md + 白名单文件
   - [Cline] 切换角色为 DE，指示读取 handoff
5. 接收回报，校验输出文件存在性

### DEV-1.{N} 审计（TE 验证）

6. `[PM] Task-{N} 开发完成，派发审计给 TE`
7. 写入 handoff: `deliverables/handoffs/{REQ-ID}-TEST-T{N}-R1.md`
   - to: TE
   - 白名单: deliverables/output/, deliverables/sa/requirement-spec.md, deliverables/te/testcases.md
   - 期望输出: deliverables/te/temp-test-report.md
8. 派发任务给 TE
9. 接收回报，检查测试结论:
   - **PASS**: `[PM] Task-{N} 审计通过` → 记入 completed_steps → 下一个 Task
   - **FAIL**: 进入修复循环

### 修复循环（最多 5 轮）

10. `[PM] Task-{N} 审计失败（轮次 {R}/5），派发修复给 DE`
11. 写入新 handoff: `deliverables/handoffs/{REQ-ID}-DEV1-T{N}-R{R+1}.md`
    - 附加: 上轮失败原因、失败报告路径
12. DE 修复 → TE 重新审计
13. 轮次达 5 次仍失败: `[PM] Task-{N} 超过最大重试次数，上升人工审核`

### 人工逐任务确认

14. 每个 Task 审计通过后，向用户简要呈现结果
15. 用户确认 OK → 继续下一个 Task
16. 用户发现问题 → 记录问题，进入修复循环

## Step SR2: 功能评审（人工审批）

**执行角色:** PM（人机交互）

1. `[PM] 所有 Task 开发+审计完成，启动 SR2 功能评审`
2. 向用户呈现：
   - 已完成 Task 列表及各自测试结论
   - 代码报告摘要
   - 临时测试报告摘要
3. 等待用户决策：
   - **通过**:
     - 写入 deliverables/SR2-record.md
     - 更新 .state.md: sr_status.SR2=approved
     - `[PM] SR2 通过，执行最终审计`
   - **驳回**:
     - 记录驳回原因，回退到指定 Task 重新开发

## Step TEST-2: 最终审计

**调度角色:** PM → TE

1. `[PM] 启动 TEST-2 最终审计`
2. 写入 handoff: `deliverables/handoffs/{REQ-ID}-TEST2-R1.md`
   - to: TE
   - 白名单: deliverables/output/, deliverables/sa/requirement-spec.md, deliverables/te/testcases.md
   - 期望输出: deliverables/te/final-test-report.md
3. 派发任务给 TE（全量测试：E2E + 回归 + 工程验证）
4. 接收回报，检查结论:
   - **PASS**: 进入 SR3
   - **FAIL**: 回退修复（同修复循环逻辑）

## Step SR3: 最终功能评审（人工审批）

**执行角色:** PM（人机交互）

1. `[PM] 启动 SR3 最终功能评审`
2. 向用户呈现：
   - 最终测试报告
   - 全部产出物清单
3. 等待用户决策：
   - **通过**:
     - 写入 deliverables/SR3-record.md
     - 更新 .state.md: sr_status.SR3=approved, phase=apply, current_step=SR3-DONE
     - `[PM] SR3 通过，可执行 /pdt-archive`
   - **驳回**:
     - 记录驳回原因，回退修复

## 异常处理

- SubAgent 回报 status=failed: 检查原因，决定重试或上升
- 浏览器环境不可用: 提示用户安装 Playwright 依赖
- 断点恢复时发现不一致: 以 .state.md 为准，重新校验文件状态
