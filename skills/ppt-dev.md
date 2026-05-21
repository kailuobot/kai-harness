# Skill: ppt-dev

PPT 类 HTML 页面开发的独立流程。通过 `/ppt-dev` 触发，不影响常规开发流程。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/{REQ-ID}/process.log`，格式：`[{timestamp}] [{角色}] {事件描述}`。timestamp 获取方式：优先使用 `date -u +%Y-%m-%dT%H:%M:%SZ`；如 date 命令不可用，使用递增序号 `#NNN`。

---

## 前置条件

1. 用户已描述 PPT 内容需求（直接描述或已有 proposal.md）
2. 如无 REQ-ID，PM 自动分配并创建 `deliverables/{REQ-ID}/` 目录结构

## 模式裁剪

| 模式 | SA | UX | 审批 | DE |
|------|----|----|------|----|
| fast | 跳过 | 直接从需求设计 | 1次人工确认 | 批量实现 |
| standard | 简版方案 | 基于方案设计 | wireframe审批 + 完成确认 | 逐页实现 |
| full | 完整方案 | 基于方案设计 | SR1 + wireframe审批 + SR3 | 逐页实现 |

---

## fast 模式

**Step 1: 需求确认**

1. `[PM] 启动 PPT 开发（fast 模式）`
2. 确认内容需求（用户描述或 proposal.md）
3. 创建目录结构：`deliverables/{REQ-ID}/ux/wireframes/`
4. 更新 `.state.md`: phase=apply, task_type=ppt, mode=fast

**Step 2: UX 设计 Wireframe**

1. `[PM] 派发 UX 设计任务`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-UX1-R1.md`
   - to: UX
   - 白名单: `deliverables/{REQ-ID}/proposal.md`, `templates/ppt-base.css`, `templates/ppt-templates/layouts/`
   - 期望输出: `deliverables/{REQ-ID}/ux/slide-spec.md`, `deliverables/{REQ-ID}/ux/wireframes/`
3. 派发任务给 UX
4. 接收回报，校验 wireframe 文件存在且非空
5. `[PM] UX 设计完成，共 {N} 页`

**Step 3: 用户审批 Wireframe**

1. `[PM] 请在浏览器中预览 wireframe，确认版式`
2. 向用户呈现：
   ```
   [版式审批]
   Wireframe 文件: deliverables/{REQ-ID}/ux/wireframes/
   版式规格: deliverables/{REQ-ID}/ux/slide-spec.md
   请在浏览器中打开 wireframe HTML 文件预览。
   确认: 通过 / 修改（请说明哪页需要调整）
   ```
3. 通过 → Step 4
4. 修改 → 重新派发 UX（轮次+1，附修改意见）

**Step 4: DE 批量实现**

1. `[PM] 派发 DE 实现任务`
2. 写入 handoff: `deliverables/{REQ-ID}/handoffs/{REQ-ID}-DEV1-R1.md`
   - to: DE
   - 白名单: `deliverables/{REQ-ID}/ux/wireframes/`, `deliverables/{REQ-ID}/ux/slide-spec.md`, `templates/ppt-base.css`
   - 期望输出: `deliverables/{REQ-ID}/output/`
   - 约束: 基于 wireframe 精装实现，填充真实数据，接入图表库，保持 16:9 约束
3. 派发任务给 DE
4. 接收回报，校验输出文件存在
5. `[PM] DE 实现完成`

**Step 5: 人工确认**

1. `[PM] 请在浏览器中预览最终产出`
2. 向用户呈现：
   ```
   [人工确认]
   模式: fast
   产出文件: deliverables/{REQ-ID}/output/
   请在浏览器中打开确认最终效果。
   确认: 通过 / 驳回（请说明原因）
   ```
3. 通过 → 更新 `.state.md`: phase=done
4. 驳回 → 回退 DE 修复

---

## standard 模式

**Step 1: 需求确认**

1. `[PM] 启动 PPT 开发（standard 模式）`
2. 确认内容需求
3. 创建目录结构
4. 更新 `.state.md`: phase=propose, task_type=ppt, mode=standard

**Step 2: SA 技术方案**

1. `[PM] 派发 SA 技术方案`
2. 写入 handoff（白名单含 proposal.md）
   - 约束: 简版方案，重点为图表库选型、数据结构设计、组件复用策略
   - 期望输出: `deliverables/{REQ-ID}/sa/design.md`
3. 派发任务给 SA
4. 校验产出
5. `[PM] SA 方案完成`

**Step 3: UX 设计 Wireframe**

1. `[PM] 派发 UX 设计任务`
2. 写入 handoff（白名单含 proposal.md + sa/design.md + 模板库）
   - 期望输出: slide-spec.md + wireframes/
3. 派发任务给 UX
4. 校验产出
5. `[PM] UX 设计完成`

**Step 4: 用户审批 Wireframe**

同 fast 模式 Step 3。

**Step 5: DE 逐页实现**

```
FOR 每页 slide IN slide-spec.md:
    DE 实现该页 → TE 校验（verify-ppt.sh）→ 人工确认
    → 记入 completed_steps，继续下一页
END FOR
```

**Step 6: 最终确认**

1. `[PM] 所有页面完成，请确认最终产出`
2. 用户确认 → 更新 `.state.md`: phase=done
3. 驳回 → 回退指定页面修复

---

## full 模式

与 standard 模式相同，额外增加：
- Step 2 后增加 SR1 评审（SA 方案 + UX wireframe 一并评审）
- Step 6 改为 SR3 最终评审（完整呈现所有产出）

---

## TE 校验规则

TE 使用 `scripts/verify-ppt.sh` 执行硬校验：
- 每页 HTML 必须包含 viewport meta（width=1920）
- 每页必须有 .slide 容器
- 每页必须引用 ppt-base.css
- 页数与 slide-spec.md 一致
- 无占位符残留（检测 "Lorem"、"placeholder"、"TODO"）

## 修复循环

同主流程修复循环规则：最多 5 轮，超过上升人工。

## 异常处理

- UX wireframe 审批驳回: 记录修改意见，重新派发 UX
- DE 实现与 wireframe 不符: TE 标记差异，回退 DE
- verify-ppt.sh 失败: 按失败项逐一修复
