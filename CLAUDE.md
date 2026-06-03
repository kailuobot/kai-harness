# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 开发命令

```bash
# 框架自检（验证所有框架文件完整性）
npm run check        # 或 ./scripts/check-harness.sh

# 产出物校验（按检查类型运行，支持 A/B/C/D/E/all）
npm run verify       # 或 ./scripts/verify.sh [A|B|C|D|E|all] [REQ-ID]

# 基线对比
npm run baseline     # 或 ./scripts/baseline.sh

# PPT 产出物校验
./scripts/verify-ppt.sh [REQ-ID]
```

校验脚本以退出码判定：0=通过，1=失败。verify.sh 会自动从 `deliverables/.state.md` 读取当前 REQ-ID。

## 架构概览

AI-Harness 是一个 Agent 驱动的研发流程框架，通过四层递进防线保证交付质量：

1. **Rules**（CLAUDE.md）— 全局行为约束，最高优先级
2. **Skills**（skills/*.md）— 标准操作规程 SOP，每个 skill 封装固定步骤
3. **Agents + Workflow**（agents/*.md + docs/workflow.md）— 6 角色制衡，通过 handoff 文件传递信息
4. **Scripts + 人工**（scripts/*.sh）— 硬校验，退出码为唯一判据

核心流程：`/mh-clarify` → `/mh-propose` → `/mh-apply` → `/mh-archive`（或 `/mh-run` 全自动推进）

### 角色

| 角色 | 职责 | 定义文件 |
|------|------|---------|
| PM | 调度、检查、人机交互 | agents/pm.md |
| BA | 需求分析 | agents/ba.md |
| SA | 架构设计 | agents/sa.md |
| DE | 编码实现 | agents/de.md |
| TE | 审计验证 | agents/te.md |
| UX | 视觉/结构设计 | agents/ux.md |

### 命令

| 命令 | 作用 | Skill 文件 |
|------|------|-----------|
| /mh-clarify | 需求初始化与澄清 | skills/mh-clarify.md |
| /mh-propose | 分析→设计→用例→评审 | skills/mh-propose.md |
| /mh-apply | 开发→审计→人工审批 | skills/mh-apply.md |
| /mh-archive | 归档+结项 | skills/mh-archive.md |
| /mh-run | 全流程自动推进 | skills/mh-run.md |
| /mh-ppt | PPT 类 HTML 页面开发 | skills/mh-ppt.md |

### 执行模式（mode）

| mode | 说明 |
|------|------|
| fast | 精简流程，跳过部分审批节点（SR1/SR2 可 skip），适合小需求快速迭代 |
| standard | 标准流程，保留核心审批节点，适合大多数需求 |
| full | 完整流程，所有审批节点强制执行，BA 需求分析独立执行，适合复杂/高风险需求 |

mode 在 clarify 阶段确定，写入 .state.md，控制流程严谨度。与 output_type 正交。

### Handoff 命名约定

格式：`{REQ-ID}-{STEP}{轮次}-R{round}.md`

示例：`REQ002-DEV1-R1.md`、`REQ002-TEST1-R1.md`

handoff 文件不可修改，重试时创建新文件（递增 round 后缀）。

### 关键目录
- `deliverables/` — 活跃需求的工作目录，每个 REQ-ID 一个子目录
- `deliverables/{REQ-ID}/.state.md` — 该需求的完整流程状态（唯一真相源）
- `deliverables/{REQ-ID}/handoffs/` — 角色间信息传递文件
- `deliverables/{REQ-ID}/output/` — 开发产出物
- `spec/` — 归档后的需求/设计基线
- `output/` — 归档后的最终产出物
- `reference/` — 用户提供的需求参考资料
- `templates/` — handoff 模板、状态 schema、PPT 模板等

状态管理：`deliverables/.state.md` 存储全局活跃 REQ-ID 指针，各需求详细状态在 `deliverables/{REQ-ID}/.state.md`（schema 定义见 `templates/state-template.md`）。

---

# Rules（全局纪律）

本文件是所有 Agent 角色的最高约束，任何 Skill 或 Agent 定义不得与此冲突。

---

## 1. 流程纪律

- 严格按 clarify → propose → apply → archive 顺序执行，禁止跳步
- 每步结束必须返回 PM，PM 检查通过后才启动下一步
- 禁止跳过人工审批节点（SR1/SR2/SR3/SR4）
- PM 每次调度前必须打印心跳：`[PM] {动作描述}`
- /mh-run 模式下允许阶段间自动推进，但阶段内审批节点仍禁止跳过

## 2. 角色隔离

- 六个角色（PM/BA/SA/DE/TE/UX）职责严格分离，禁止越权
- 角色间信息传递必须经 PM 中转，通过 handoff 文件实现
- 非 PM 角色仅读取 handoff 白名单中的文件
- 非 PM 角色禁止引用对话历史中其他角色的推理或产出
- 非 PM 角色完成后仅报告文件路径，不展开产物内容

## 3. 产物保护

- 禁止修改上游制品（已交付的 handoff、已审批的 baseline）
- handoff 文件不可修改，重试创建新文件（追加轮次后缀）
- 归档后的 spec/ 文件仅通过 CHANGE 模式的 merge 流程修改

## 4. 自检纪律

- 任何文件写入后必须验证文件存在且非空
- DE 编码后必须执行 dev-test skill（根据 tech_stack 路由测试命令）
- TE 审计根据 test_strategy 选择验证方法；E2E 环境不可用时降级并标注
- 交付判定依赖脚本退出码，不依赖 Agent 自述

## 5. 断点恢复

- PM 恢复时仅依据 .state.md 和 handoff 文件状态，禁止依赖对话历史
- .state.md 是流程状态的唯一真相源（完整 schema 见 `templates/state-template.md`）
- 每次更新 .state.md 必须同步更新 last_updated 时间戳
- 修复循环中每轮开始时必须更新 repair_round 字段，任务通过后重置为 0
- 恢复时如 handoff 为 pending 且 last_updated 超过 30 分钟，自动重新派发
- 恢复时必须读取 repair_round 字段，避免重复修复或超限

## 6. 平台适配

- Claude Code 环境：BA/SA/DE/TE/UX 通过 SubAgent 执行（物理隔离）
- Cline 环境：通过文件协议 + 行为约束实现角色隔离（逻辑隔离）
- 两种模式共享同一套 handoff 格式和 skill 内容

## 7. 产出类型体系（output_type）

框架支持任意类型的需求开发，通过 output_type 参数驱动流程适配：

| output_type | 说明 | 默认 test_strategy |
|-------------|------|-------------------|
| web-app | Web 应用（前端/全栈） | e2e / integration |
| backend-api | 后端服务/API | integration |
| cli-tool | 命令行工具 | integration |
| data-pipeline | 数据管道/ETL | smoke |
| infrastructure | 基础设施代码 | smoke |
| documentation | 文档/规格 | manual |
| ppt | 演示文稿/HTML slides | manual |
| library | 库/SDK | unit |
| custom | 自定义 | 用户指定 |

- output_type 与 mode 正交：mode 控制流程严谨度，output_type 控制产出物类型和验证方式
- output_type 在 clarify 阶段确定，写入 .state.md，贯穿全流程
- 各角色根据 output_type 和 tech_stack 选择对应的工具和验证方法
