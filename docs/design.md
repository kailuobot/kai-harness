# Mini-Harness 设计文档

> ⚠️ 执行权威为 skills/*.md 和 agents/*.md。本文档为设计参考，如有冲突以 skills/agents 为准。

---

## 1. 整体设计目标

### 1.1 核心诉求

- **标准化编排**：按 clarify → propose → apply → archive 固定流程执行
- **角色真隔离**：6 个 SubAgent 在独立子会话中执行，互不可见
- **质量驱动**：每个角色有思考框架 + 质量标准 + 反模式，PM 有内容级质量门禁
- **人工可控**：4 个 SR 门强制人工审批，AI 不可自主跨越
- **渐进完善**：任何组件未就绪时人工兜底，workflow 不阻塞

### 1.2 设计原则：四层递进防线

```
第一层 Rules（行为约束）— CLAUDE.md
  ↓ 固有局限：自然语言指令，遵守程度随上下文复杂度下降
第二层 Skills（标准操作规程）— skills/*.md
  ↓ 固有局限：仍属指令层，Agent 可能声称完成但实际未达标
第三层 Agents + Workflow（角色制衡）— agents/*.md + handoff 协议
  ↓ 固有局限：角色和流程仍属指令约束，缺少独立客观验证
第四层 Scripts + 人工（硬校验）— scripts/*.sh + SR1-4
  → 程序退出码为唯一判据，不依赖 Agent 自述
```

**递进关系，非替代关系。** 四层合并形成闭环。

---

## 2. 一级架构总览

### 2.1 模块全景

| 模块 | 功能 | 文件 |
|------|------|------|
| 全局规则 | 行为约束（最高优先级） | CLAUDE.md, .clinerules |
| 角色契约 | 6 角色的身份/职责/质量标准 | agents/*.md |
| 执行规程 | 各阶段的标准操作流程 | skills/*.md |
| 命令入口 | Claude Code slash command | .claude/commands/*.md |
| 硬校验 | 退出码驱动的客观验证 | scripts/*.sh |
| 模板体系 | handoff/state/日志/示例/结构参考 | templates/ |
| 文档 | 设计参考 + 流程图 | docs/ |

### 2.2 目录结构

```
mini-harness/
├── CLAUDE.md                          全局规则（98行，精简）
├── .clinerules                        Cline 特有协议
├── README.md                          项目介绍 + 使用指南
│
├── agents/                            角色契约（含质量框架）
│   ├── pm.md                          PM: 调度 + 质量门禁
│   ├── ba.md                          BA: 需求分析 + 思考框架
│   ├── sa.md                          SA: 架构设计 + 思考框架
│   ├── de.md                          DE: 编码实现 + TDD + 思考框架
│   ├── te.md                          TE: 审计验证 + 思考框架
│   └── ux.md                          UX: 视觉设计 + 思考框架
│
├── skills/                            执行规程
│   ├── mh-clarify.md                  需求初始化与澄清
│   ├── mh-propose.md                  分析→设计→用例→评审
│   ├── mh-apply.md                    开发→审计→人工审批
│   ├── mh-archive.md                  归档+结项
│   ├── mh-run.md                      全流程自动推进
│   ├── mh-ppt.md                      PPT 补充规则
│   ├── dev-test.md                    DE 开发自测
│   └── post-verify.md                 DE 交付前校验
│
├── scripts/                           硬校验层
│   ├── verify.sh                      产出物校验（A/B/C/D 四类）
│   ├── baseline.sh                    基线对比
│   ├── check-harness.sh               框架自检
│   └── verify-ppt.sh                  PPT 专项校验
│
├── templates/                         模板体系
│   ├── handoff-template.md            任务派发模板
│   ├── handoff-examples.md            回报格式示例
│   ├── state-template.md              状态 schema 定义
│   ├── logging-standard.md            日志格式标准
│   ├── examples/                      金标准产出示例
│   ├── output-guides/                 产出结构参考
│   ├── ppt-base.css / ppt-base.html   PPT 基础模板
│   └── ppt-templates/layouts/         PPT 版式库
│
├── docs/                              文档
│   ├── design.md                      本文档
│   └── workflow.md                    流程图集
│
├── .claude/commands/                  Claude Code 命令入口
├── deliverables/                      运行时产物（按 REQ-ID 隔离）
├── spec/                              归档规格
└── output/                            最终产物
```

---

## 3. 角色与隔离设计

### 3.1 六大角色

| 角色 | 身份 | 核心职责 | 禁止事项 |
|------|------|----------|----------|
| PM | 调度中枢 | 派发任务、质量门禁、人机交互、流程推进 | 技术判断、开发、设计、测试 |
| BA | 需求分析师 | 模糊需求→结构化 SHALL+GWT 规格 | 架构设计、编码、调度 |
| SA | 方案架构师 | 需求→技术方案→可执行 Tasks | 需求修改、编码、调度 |
| DE | 开发工程师 | TDD 编码实现 + 自测 + 交付校验 | 设计修改、调度、跳过测试 |
| TE | 测试工程师 | 独立验证 + 需求覆盖分析 + 缺陷报告 | 修改代码、调度、虚报 PASS |
| UX | 设计师 | 视觉/结构设计制品 | 编码、需求分析、技术决策 |

所有非 PM 角色共同禁止：修改上游产出物、引用对话历史中其他角色的内容。

### 3.2 双模式隔离

| 环境 | 隔离方式 | 强度 |
|------|---------|------|
| Claude Code | SubAgent 物理隔离（独立上下文） | 硬隔离 |
| Cline | 文件协议 + 行为约束 | 软隔离 |

### 3.3 PM 主会话模型

```
┌─────────────────────────────────────────────┐
│              主会话（PM 常驻）                │
│                                             │
│  读取 .state.md → 质量门禁 → 写 handoff     │
│  → 派发任务 → 验收 → 推进                   │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │SubAgent │  │SubAgent │  │SubAgent │    │
│  │  BA/SA  │  │  DE     │  │  TE     │    │
│  │(独立ctx)│  │(独立ctx)│  │(独立ctx)│    │
│  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────┘
```

---

## 4. 开发流程设计

### 4.1 PM 调度核心设计

**PM 是调度者，Scripts 是护栏。** PM 做判断（重试还是升级），Scripts 防遗漏（文件是否存在、格式是否正确）。

#### PM 调度循环

```
loop:
  1. 读取 .state.md              → 确认当前位置
  2. 写入 handoff                → 创建任务派发
  3. 检查停止条件                → 触发则暂停
  4. 派发 SubAgent               → 真隔离执行
  5. SubAgent 完成               → 产出物写入
  6. 执行质量门禁                → 内容级验收
  7. 验收通过 → 更新 .state.md → 回到 1
  8. 验收失败 → 根因分析 → 修复循环
```

#### 停止条件（PM 暂停并等待用户）

- SR gate 阻塞 — 需要人工审批
- 修复循环发散 — 需要人工判断
- mode=manual 步骤 — 需要人机协作
- Proposal/模式确认 — 需要用户决策

#### 六条流程铁律

| 铁律 | 含义 |
|------|------|
| ① 严格顺序 | clarify → propose → apply → archive，禁止跳步 |
| ② PM 只做调度 | 不写需求、不定方案、不给技术建议、不评价代码 |
| ③ 每棒必须有文档 | handoff 是角色间唯一通信通道 |
| ④ SR 不可自主跨越 | 必须人工审核后才能继续 |
| ⑤ 下游不改上游 | 发现问题只能回报 PM，由 PM 正式打回 |
| ⑥ PM 心跳 ↔ 动作一对一 | 每次调度前打印 `[PM] {动作}` |

### 4.2 四阶段流程

```
/mh-clarify          /mh-propose              /mh-apply                    /mh-archive
───────────        ─────────────────        ────────────────────────      ─────────────
[人机协作]         [自动化+SR1]             [自动化+修复+SR2+SR3]         [归档+SR4]

 场景检测            BA需求(full)             Batch并行开发                 需求归档
 环境预检            SA∥TE 并行              Batch并行审计                 设计归档
 需求澄清            PM编排                  修复循环(收敛追踪)            产出归档
 类型选择           ★SR1                    ★SR2                        ★SR4
 模式选择                                   最终审计
 Proposal定稿                              ★SR3
```

★ = 人工审批节点（停止条件）

### 4.3 三档 Mode

| Mode | 适用场景 | 差异 | 预估时间 |
|------|----------|------|---------|
| fast | 小调整（≤5文件，无重设计） | 跳过 BA/SA/TE propose，合并审批 | 5-10 min |
| standard | 新功能（单模块） | 跳过 BA，SA∥TE 并行，无 SR1 | 15-20 min |
| full | 大需求（跨模块，完整审计链） | 完整流程，无裁剪 | 30+ min |

### 4.4 状态机

```
init ──────> propose ──────> apply ──────> archive ──────> DONE
  │              │              │              │
  │ (RESUME)     │ (SR1驳回)    │ (SR2/3驳回)  │ (SR4驳回)
  └──> init      └──> propose   └──> apply     └──> apply
```

状态持久化于 `deliverables/{REQ-ID}/.state.md`，完整 schema 见 `templates/state-template.md`。

### 4.5 SR Gate 决策标准

| Gate | 审批时机 | 通过标准 |
|------|----------|----------|
| SR1 | propose 完成后 | 需求规格完整 + 设计覆盖所有需求 + 计划可执行 |
| SR2 | apply 开发完成后 | 所有 Task 通过审计 + 代码质量达标 |
| SR3 | 最终审计后 | 全量测试通过 + 需求覆盖无遗漏 + 无 Critical/Major 缺陷 |
| SR4 | 归档后 | 归档完整 + 产出物可用 |

### 4.6 断点恢复

PM 恢复时仅依据 `.state.md`，禁止依赖对话历史：
1. 读取 phase + current_step 确定位置
2. 检查 current_handoff 状态（done/pending/failed）
3. pending 且超 30 分钟 → 重新派发
4. 检查 repair_round + repair_history → 恢复修复上下文

### 4.7 并行批次

apply 阶段按 Task 依赖关系分批并行：
- Batch-1: 所有 `[deps: none]` 的 Task
- Batch-N: 依赖仅在前序 Batch 中的 Task
- 每个 Batch 内 DE 并行 → TE 并行 → 人工确认 → 下一 Batch

仅 Claude Code 模式支持真并行；Cline 退化为串行。

---

## 5. 上下文管控设计

### 5.1 隔离机制

| 约束 | 实现方式 |
|------|----------|
| 不读对话历史 | SubAgent 独立子会话天然隔离 |
| 不改上游文件 | agents/*.md 禁止事项 + PM 验收检查 |
| 不引用其他角色推理 | prompt 中仅包含 handoff + 本角色契约 |
| 不展开产物内容给 PM | 角色完成后仅报告文件路径 |

### 5.2 SubAgent Prompt 构成

PM spawn SubAgent 时注入以下内容：

```
1. 角色契约 (agents/<role>.md) — 含思考框架+质量标准+反模式
2. Handoff 文件 — 任务描述+白名单+约束+修复上下文
3. 白名单文件内容 — SubAgent 自行 Read
4. 金标准示例 (可选) — templates/examples/ 中对应文件
```

SubAgent 看不到：其他角色的产出物全文、对话历史、.state.md 全貌。

### 5.3 Handoff 协议

Handoff 是角色间的唯一通信通道。

**文件路径：** `deliverables/{REQ-ID}/handoffs/{REQ-ID}-{STEP-ID}-R{轮次}.md`

**生命周期：** `pending → done | failed`

**协议规则：**
1. 不可修改 — 重试创建新文件（追加轮次后缀）
2. 白名单精确 — 禁止通配符，逐文件列出
3. 双向 — PM→角色（派发）+ 角色→PM（回报在同一文件）
4. 修复上下文 — 修复轮次时附带根因分析和建议方向

**模板：** `templates/handoff-template.md`

---

## 6. Skill 设计

### 6.1 Skill 与 Agent 的关系

- **Agent** 定义"是谁、能做什么、不能做什么、怎么思考"（角色规格）
- **Skill** 定义"具体按什么步骤执行"（操作规程）
- 两者通过 PM 调度关联：PM 读取 skill 确定流程，spawn SubAgent 时注入 agent 契约

### 6.2 文件清单

| Skill | 触发命令 | 执行者 |
|-------|---------|--------|
| mh-clarify.md | /mh-clarify | PM（人机协作） |
| mh-propose.md | /mh-propose | PM 调度 BA/SA/TE |
| mh-apply.md | /mh-apply | PM 调度 DE/TE |
| mh-archive.md | /mh-archive | PM |
| mh-run.md | /mh-run | PM（自动推进） |
| mh-ppt.md | /mh-ppt | PM 调度 UX/DE/TE |
| dev-test.md | DE 内部调用 | DE |
| post-verify.md | DE 内部调用 | DE |

### 6.3 Mode 感知

每个 Skill 内部按 mode 裁剪步骤（fast 跳过非必要步骤，full 完整执行）。fast 模式还有专属的轻量化路径（dev-test 快速路径、TE 轻量审计）。

---

## 7. 质量管控设计

### 7.1 三层质量注入（Agent 层）

每个 Agent 定义包含三层质量指导，spawn 时注入一次：

| 层次 | 作用 | 示例 |
|------|------|------|
| 思考框架 | "先想什么再想什么" | SA: 先识别复杂度→再选方案→再拆 Task |
| 反模式 | "不要做什么" | DE: ❌ 只实现 happy path |
| 交付自检 | 提交前 checklist | TE: 结论是否明确？覆盖是否完整？ |

### 7.2 PM 质量门禁（流程层）

PM 接收回报后执行内容质量快扫（不做技术判断，只检查结构完整性）：

| 角色 | 门禁要点 |
|------|---------|
| BA | SHALL+GWT 完整、无模糊词、无矛盾 |
| SA | 对照表覆盖完整、Task 有依赖标注和验证方式 |
| DE | dev-test=PASS、post-verify=PASS、无 TODO 残留 |
| TE | 结论明确、FAIL 有复现步骤、覆盖分析完整 |

不满足则驳回，附带具体缺陷描述。

### 7.3 修复收敛机制

```
TE 报告失败 → PM 根因分析 → 结构化修复上下文 → DE 定向修复
                                                    ↓
                              repair_history 追踪收敛性
                                                    ↓
                              收敛 → 继续 / 发散 → 提前升级人工
```

**提前升级条件（不等到第 5 轮）：**
- 连续 2 轮 failed_count 增加
- 连续 2 轮 error_type 变化
- 第 3 轮同一错误无进展

### 7.4 硬校验脚本（Scripts 层）

| 脚本 | 检查内容 |
|------|---------|
| verify.sh A 类 | 文件存在性（.state.md、proposal.md） |
| verify.sh B 类 | 阶段产出物完整性（mode + output_type 感知） |
| verify.sh C 类 | 流程一致性（必填字段、phase-产物对齐） |
| verify.sh D 类 | 流程健康度（修复耗尽、handoff 超时、TODO 残留） |
| baseline.sh | 基线对比（检测未授权的 spec 修改） |
| check-harness.sh | 框架自检（所有文件完整性） |
| verify-ppt.sh | PPT 专项（viewport、.slide 容器、CSS 引用） |

### 7.5 金标准示例

`templates/examples/` 存放每个角色的金标准产出示例，SubAgent 可参考：
- requirement-spec-example.md（BA）
- design-example.md（SA）
- code-report-example.md（DE）
- test-report-example.md（TE）

### 7.6 兜底策略

| 未就绪场景 | 兜底方式 |
|-----------|----------|
| 浏览器环境不可用 | TE 降级为工程验证，标注 DEGRADED |
| test_strategy=manual | TE 生成人工检查清单 |
| test_strategy=none | 仅 lint + 构建 |
| 修复循环发散 | 提前升级人工 |
| SubAgent 回报 failed | PM 判断重试或升级 |

---

## 8. 审批决策设计

### 8.1 决策上下文卡

每个审批节点呈现结构化决策上下文，让人工从"盲批"变为"知情决策"：

```
[人工审批节点]
评审节点: {SR-N}

变更摘要: {文件数、新增/修改/删除}
质量状态: {测试通过率、覆盖率}
风险评估: {修复轮次、降级验证项}
PM 建议: {通过/建议复查} ({理由})

请确认: 通过 / 驳回（请说明原因）
```

### 8.2 审批呈现原则

- 信息充分：人工能基于呈现内容做出判断，不需要自己去翻文件
- 风险突出：高修复次数、降级验证、覆盖遗漏等风险项优先展示
- PM 建议：PM 基于质量门禁结果给出建议，但最终决策权在人工

---

## 9. 模板体系

### 9.1 模板清单

| 模板 | 用途 | 使用时机 |
|------|------|---------|
| handoff-template.md | 任务派发格式 | PM 每次调度时 |
| handoff-examples.md | 回报格式参考 | 角色填写回报时 |
| state-template.md | .state.md schema 定义 | 初始化和更新时 |
| logging-standard.md | 日志格式标准 | 所有步骤执行时 |
| examples/*.md | 金标准产出示例 | SubAgent 参考 |
| output-guides/*.md | 产出结构参考 | DE 实现时参考 |

### 9.2 产出结构参考

`templates/output-guides/` 为高频 output_type 提供结构指南：
- web-app.md — 推荐目录结构 + 关键文件 + 质量检查点
- backend-api.md — 分层架构 + API 规范 + 质量检查点
- cli-tool.md — 命令结构 + 配置优先级 + 质量检查点

---

## 10. 产出类型体系

### 10.1 output_type 与 test_strategy

| output_type | 说明 | 默认 test_strategy |
|-------------|------|-------------------|
| web-app | Web 应用 | e2e / integration |
| backend-api | 后端 API | integration |
| cli-tool | 命令行工具 | integration |
| data-pipeline | 数据管道 | smoke |
| infrastructure | 基础设施代码 | smoke |
| documentation | 文档 | manual |
| ppt | HTML slides | manual |
| library | 库/SDK | unit |
| custom | 自定义 | 用户指定 |

output_type 与 mode 正交：mode 控制流程严谨度，output_type 控制产出物和验证方式。

### 10.2 环境检测

clarify 阶段自动检测技术栈（Python/Node/Go/Rust/Java），写入 .state.md：
- language / package_manager / test_framework / build_tool / lint_tool
- env.browser_available（UI 类型时检测）

检测结果驱动 dev-test 命令路由和 TE 验证方式选择。

---

## 11. PPT 子系统

### 11.1 与主流程的关系

/mh-ppt 是 output_type=ppt 的快捷入口，本质上走主流程 + PPT 补充规则（skills/mh-ppt.md）。

### 11.2 模板体系

- 基础样式: `templates/ppt-base.css`（深色暖调）+ `templates/ppt-light.css`（白底商务）
- 骨架模板: `templates/ppt-base.html`
- 版式库: `templates/ppt-templates/layouts/`（L 系列深色 12 套 + W 系列白底 5 套）

### 11.3 设计规范

- 视口: 1920×1080（16:9），禁止滚动
- 信息密度: 高密度优先，每页承载传统 PPT 2-3 页信息量
- UX 产出 wireframe → DE 精装实现 → TE 用 verify-ppt.sh 校验
