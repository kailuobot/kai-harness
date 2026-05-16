# Skill: pdt-init

需求初始化与澄清。PM 主导，人机协作打磨 Proposal。

---

## 前置检查

1. 检测 deliverables/.state.md 是否存在
2. 检测场景模式（按优先级从高到低判断）：
   - **RESUME**: .state.md 中 phase 非空且 phase≠done → 有未完成的流程，提示用户继续或放弃
   - **CHANGE**: spec/ 目录下存在 .md 文件（即有已归档的历史需求）→ 变更模式
   - **NEW**: 以上均不满足（.state.md 为空/不存在/phase=done，且 spec/ 为空）→ 全新项目

⚠️ 关键：phase=done 或 phase=archive 且 spec/ 有文件时，必须进入 CHANGE 模式，不得识别为 NEW。

## Step 1: 初始化任务目录

**执行角色:** PM

1. 生成需求编号（REQ001, REQ002...递增）
2. 创建 deliverables/ 子目录结构（如不存在）
3. 更新 .state.md:
   ```yaml
   req_id: REQ{NNN}
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

## Step 3: Proposal 定稿

**执行角色:** PM

1. 将 Proposal 草稿写入 deliverables/proposal.md
2. 向用户呈现 Proposal 全文，请求确认
3. 用户确认通过：
   - 更新 .state.md: `phase: init, current_step: INIT-DONE`
   - `[PM] Proposal 定稿完成，可执行 /pdt-propose`
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
