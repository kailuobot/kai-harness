# Skill: pdt-init

需求初始化与澄清。PM 主导，人机协作打磨 Proposal。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/{REQ-ID}/process.log`，格式：`[{时间}] [{角色}] {事件描述}`

---

## 前置检查

1. 检测 deliverables/.state.md 是否存在（全局状态指针）
2. 如存在，读取其中 req_id，检查 `deliverables/{req_id}/.state.md` 的 phase
3. 检测场景模式（按优先级从高到低判断）：
   - **RESUME**: 最近 REQ 的 phase 非空且 phase≠done → 有未完成的流程，提示用户继续或放弃
   - **CHANGE**: spec/ 目录下存在 .md 文件（即有已归档的历史需求）→ 变更模式
   - **NEW**: 以上均不满足 → 全新项目

⚠️ 关键：phase=done 且 spec/ 有文件时，必须进入 CHANGE 模式，不得识别为 NEW。

## Step 1: 初始化任务目录

**执行角色:** PM

1. 生成需求编号（REQ001, REQ002...递增）
2. 创建 `deliverables/{REQ-ID}/` 隔离目录结构：
   ```
   deliverables/{REQ-ID}/
   ├── sa/
   ├── te/
   ├── de/
   ├── output/
   ├── handoffs/
   ├── baselines/
   ├── .state.md
   └── process.log
   ```
3. 写入 `deliverables/{REQ-ID}/.state.md`:
   ```yaml
   req_id: REQ{NNN}
   mode: ""
   phase: init
   current_step: INIT-1
   current_role: PM
   ```
4. `[PM] 初始化完成，进入需求澄清`

## Step 2: 需求澄清（人机协作）

**执行角色:** PM

1. 读取 reference/ 目录下的参考资料
   - 如含图片，调用 zai-mcp-server 识别内容
2. 基于参考资料，逐轮向用户提问：
   - 每轮最多 3 个问题
   - 聚焦于消除歧义、明确边界、确认优先级
3. CHANGE 模式下：
   - 读取 spec/ 下已有规格
   - 仅围绕变更点提问，不重复已有内容
4. 根据用户回答，生成 Proposal 草稿

## Step 3: 模式选择

**执行角色:** PM（人机交互）

Proposal 草稿完成后，PM 根据需求规模向用户推荐模式：

```
[模式选择]
根据需求规模分析，建议使用 {推荐模式} 模式：

  fast     — 小调整（bug修复、≤5个文件、无需重新设计）
             流程：PM出plan → DE开发 → TE轻量审计 → 人工确认 → 归档
             预估：5-10分钟

  standard — 新功能（需设计，不跨模块）
             流程：SA设计 → TE用例 → DE开发 → TE审计 → SR2+SR3 → 归档
             预估：15-20分钟

  full     — 大型需求（跨模块、需完整评审链）
             流程：BA需求 → SA设计 → TE用例 → SR1 → DE开发 → SR2+SR3 → SR4
             预估：30+分钟

请选择模式:
```

推荐逻辑：
- 涉及文件 ≤5 且无新架构 → 推荐 fast
- 单模块新功能或中等改动 → 推荐 standard
- 跨模块、多角色协作、需完整追溯 → 推荐 full

用户选择后，写入 `deliverables/{REQ-ID}/.state.md`: `mode: {fast|standard|full}`

## Step 4: Proposal 定稿

**执行角色:** PM

1. 将 Proposal 草稿写入 `deliverables/{REQ-ID}/proposal.md`
2. 向用户呈现 Proposal 全文，请求确认
3. 用户确认通过：
   - 更新 `deliverables/{REQ-ID}/.state.md`: `phase: init, current_step: INIT-DONE`
   - 更新 `deliverables/.state.md`: `req_id: {REQ-ID}`（全局指针）
   - `[PM] Proposal 定稿完成（模式: {mode}），可执行 /pdt-propose`
4. 用户要求修改：
   - 根据反馈修改 Proposal
   - 重新呈现，循环直到确认

## Proposal 格式

```markdown
# Proposal: {项目/需求标题}

## 背景与目标
{为什么要做这件事}

## 范围
- 包含: {列举}
- 不包含: {列举}

## 关键约束
- {约束1}
- {约束2}

## 参考资料
- {来源列表}
```

## 异常处理

- reference/ 为空：提示用户补充参考资料或直接口述需求
- RESUME 模式用户选择放弃：清理未完成的 .state.md，重新进入 NEW 模式
