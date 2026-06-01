# Skill: mh-apply

开发实现 → 审计验证 → 人工审批。按 mode 路由到对应子文件。

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

## 模式路由

- **fast 模式**: 读取 `skills/mh-apply-fast.md` 执行
- **standard/full 模式**: 读取 `skills/mh-apply-standard.md` 执行
- **修复循环**（任何模式 TE 审计 FAIL 时）: 读取 `skills/mh-apply-repair.md` 执行

> full 模式的 apply 阶段与 standard 完全一致，区别仅在 propose 阶段有 SR1 评审。

---

## 异常处理

- SubAgent 回报 status=failed: 检查原因，决定重试或上升
- SubAgent 超时但产出物已存在:
  - PM 检查 output/ 中对应 Task 的文件是否完整（与 plan-action.md 描述匹配）
  - 完整 → 视为成功，PM 代填 code-report（标注"[PM 代填] Agent 超时，产出物完整"）
  - 不完整 → 重试一次
- 浏览器环境不可用: 提示用户安装 Playwright 依赖
- 断点恢复时发现不一致: 以 `deliverables/{REQ-ID}/.state.md` 为准，重新校验文件状态
