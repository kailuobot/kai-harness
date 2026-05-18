# Skill: pdt-archive

产物归档 + 结项确认。PM 执行，支持首次归档和变更归档两种模式。

**日志规则：** 每个步骤执行前后必须追加日志到 `deliverables/{REQ-ID}/process.log`，格式：`[{时间}] [{角色}] {事件描述}`

---

## 前置检查

1. 读取 `deliverables/.state.md` 获取当前 req_id
2. 读取 `deliverables/{REQ-ID}/.state.md` 中 mode 和 sr_status.SR3
3. 验证 sr_status.SR3=approved（standard/full）或 sr_status.SR3=approved（fast，在apply中已设置）
4. 验证 `deliverables/{REQ-ID}/output/` 存在且非空
5. 不满足则阻塞，提示用户先完成 /pdt-apply

## 归档模式检测

- **首次归档**: spec/ 目录为空 → 直接复制
- **变更归档**: spec/ 目录已有文件 → merge 模式

## Step ARC-1: 需求归档

**执行角色:** PM

1. `[PM] 启动 ARC-1 需求归档`
2. fast 模式: 跳过（无 requirement-spec.md）
3. standard 模式: 跳过（无 requirement-spec.md，仅有 design.md）
4. full 模式:
   - 首次归档: 复制 `deliverables/{REQ-ID}/ba/requirement-spec.md` → `spec/requirement-spec.md`
   - 变更归档: merge 到 `spec/requirement-spec.md`
5. 校验目标文件存在且非空（full 模式）
6. `[PM] ARC-1 完成`

## Step ARC-2: 设计归档

**执行角色:** PM

1. `[PM] 启动 ARC-2 设计归档`
2. fast 模式: 跳过（无 design.md）
3. standard/full 模式:
   - 首次归档: 复制 `deliverables/{REQ-ID}/sa/design.md` → `spec/design.md`
   - 变更归档: 合并新设计内容到 `spec/design.md`，更新 Tasks 清单和对照表
4. 校验目标文件存在且非空（standard/full 模式）
5. `[PM] ARC-2 完成`

## Step ARC-3: 代码归档

**执行角色:** PM

1. `[PM] 启动 ARC-3 代码归档`
2. 将 `deliverables/{REQ-ID}/output/` 内容复制到 `output/final/`
3. 首次归档: 直接复制全部文件
4. 变更归档: 覆盖已有同名文件，保留不冲突的已有文件
5. 校验 `output/final/` 非空
6. `[PM] ARC-3 完成`

## Step SR4: 项目结项确认（人工审批）

**执行角色:** PM（人机交互）

**fast 模式：** 跳过 SR4，直接结项。
- 更新 `deliverables/{REQ-ID}/.state.md`: phase=done, sr_status.SR4=skipped
- `[PM] 项目结项完成（fast模式）。需求 {REQ-ID} 已归档。`

**standard 模式：** 简化 SR4（一句确认）。
- `[PM] 归档完成，请确认结项（Y/N）`
- 用户确认:
  - 更新 `deliverables/{REQ-ID}/.state.md`: phase=done, sr_status.SR4=approved
  - `[PM] 项目结项完成。需求 {REQ-ID} 已归档。`

**full 模式：** 完整 SR4。
1. `[PM] 启动 SR4 项目结项确认`
2. 向用户呈现归档摘要：
   - 归档模式（首次/变更）
   - 需求规格: spec/requirement-spec.md
   - 技术设计: spec/design.md
   - 最终产物: output/final/ 文件清单
   - 本次需求编号: {REQ-ID}
3. 等待用户决策：
   - **确认结项**:
     - 写入 `deliverables/{REQ-ID}/SR4-record.md`
     - 更新 `deliverables/{REQ-ID}/.state.md`:
       ```yaml
       phase: done
       current_step: SR4-DONE
       sr_status.SR4: approved
       ```
     - `[PM] 项目结项完成。需求 {REQ-ID} 已归档。`
   - **驳回**:
     - 记录原因，根据问题回退到对应阶段

## CHANGE 模式特殊处理

1. 归档前自动备份当前 spec/ 到 spec/baselines/
   - spec/baselines/requirement-spec.v{N}.md
   - spec/baselines/design.v{N}.md
2. 版本号自动递增（检测已有 baseline 文件确定 N）
3. merge 时保持已有内容结构，仅追加或更新变更部分

## 异常处理

- 目标目录不存在: 自动创建
- 文件复制失败: 重试一次，仍失败则报错上升人工
- merge 冲突（变更归档）: 呈现冲突内容，请求人工决策
