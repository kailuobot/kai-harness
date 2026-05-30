# Mini-Harness 设计文档

## 1. 设计目标

为 PSDT 超级智能体搭建基础 Workflow 框架，实现：
- 从需求到交付各子智能体间任务编排清晰
- 各任务输入输出明确可校验
- 后续开发可相互解耦
- 跨平台可移植（Claude Code / Cline）

---

## 2. 架构：四层递进防线

```
约束力: 弱 ──────────────────────────────────────────── 强

┌─────────┐   ┌─────────┐   ┌──────────────┐   ┌──────────────┐
│  Rules  │──>│ Skills  │──>│ Agents +     │──>│ Scripts +    │
│ 行为约束 │   │ 标准SOP │   │ Workflow     │   │ 人工硬校验   │
└─────────┘   └─────────┘   └──────────────┘   └──────────────┘
  CLAUDE.md     skills/*.md    agents/*.md        scripts/*.sh
  .clinerules                  handoff 协议       人工审批(SR1-4)
```

每一层专门弥补上一层的固有缺口：
- Rules 约束行为 → 但遵守程度随上下文复杂度下降
- Skills 标准化执行 → 但仍是单一 Agent 自审
- Agents+Workflow 角色制衡 → 但"已完成"缺少客观验证
- Scripts+人工 硬校验 → 以退出码和人工判断为最终判据

---

## 3. 角色隔离方案

### 3.1 双模式设计

| 环境 | 隔离方式 | 强度 |
|------|---------|------|
| Claude Code | SubAgent 物理隔离（独立上下文） | 硬隔离 |
| Cline | 文件协议 + 行为约束 | 软隔离 |

### 3.2 PM 主会话模型

```
┌─────────────────────────────────────────────┐
│              主会话（PM 常驻）                │
│                                             │
│  读取 .state.md → 写 handoff → 派发任务     │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │SubAgent │  │SubAgent │  │SubAgent │    │
│  │  BA     │  │  SA     │  │  DE/TE  │    │
│  │(独立ctx)│  │(独立ctx)│  │(独立ctx)│    │
│  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────┘
```

- PM 保持全局视野（需要看所有产出做调度决策）
- BA/SA/DE/TE 在独立上下文中执行，天然看不到其他角色推理
- Handoff 文件是 SubAgent 的唯一输入来源

### 3.3 角色职责边界

| 角色 | 职责 | 禁止 |
|------|------|------|
| PM | 调度、检查、人机交互 | 技术判断、开发、设计、测试 |
| BA | 需求分析 | 架构设计、编码、调度 |
| SA | 架构设计 | 需求分析、编码、调度 |
| DE | 编码实现 | 设计、需求定义、调度 |
| TE | 审计验证 | 开发、设计、调度 |
| UX | 视觉/结构设计 | 编码、需求分析、技术决策 |

---

## 4. Handoff 协议

### 4.1 设计原则

- 纯文件协议，跨平台兼容
- 不可变：handoff 创建后禁止修改，重试创建新文件（追加轮次后缀）
- 双向：PM→角色（派发）+ 角色→PM（回报，填写在同一文件中）
- 状态内聚：handoff 自身携带 status 字段

### 4.2 生命周期

```
pending → accepted → done | failed
```

### 4.3 命名规则

```
{REQ-ID}-{STEP-ID}-R{轮次}.md

示例:
REQ001-REQ1-R1.md    # REQ001 的 REQ-1 步骤，第1轮
REQ001-DEV1-T2-R3.md # REQ001 的 DEV-1 步骤，Task2，第3轮修复
```

### 4.4 白名单机制

- 每个 handoff 明确列出允许读取的文件
- 隐含规则：角色始终可读自己的 agent 定义（agents/{role}.md）
- SubAgent 模式：白名单文件作为 prompt 注入
- Cline 模式：通过行为约束限制读取范围

---

## 5. 状态管理

### 5.1 .state.md

流程状态的唯一真相源（完整 schema 见 `templates/state-template.md`）。字段：

| 字段 | 用途 |
|------|------|
| req_id | 当前需求编号 |
| mode | 执行模式（fast/standard/full） |
| output_type | 产出类型（web-app/backend-api/cli-tool/...） |
| phase | 当前阶段（init/propose/apply/archive/done） |
| current_step | 当前步骤 ID |
| current_handoff | 当前活跃 handoff 文件名 |
| current_role | 当前执行角色 |
| completed_steps | 已完成步骤列表 |
| auto_advance | 是否处于 /mh-run 自动推进模式 |
| repair_round | 当前修复轮次（0=未修复，1-5=修复中） |
| repair_task | 当前修复的任务标识 |
| sr_status | 各审批节点状态 |
| tech_stack | 技术栈信息（language/package_manager/test_framework/build_tool/lint_tool） |
| test_strategy | 验证策略（e2e/unit/integration/smoke/manual/none） |
| last_updated | 最后更新时间戳（用于断点恢复超时检测） |
| env | 环境信息（browser_available 等） |

### 5.2 断点恢复

1. PM 读取 .state.md 确定位置
2. 检查 last_updated 时间戳：
   - 如距当前时间超过 30 分钟且 current_handoff status=pending → 判定超时，自动重新派发（创建新 handoff，轮次+1）
   - 如距当前时间在 30 分钟内 → 正常恢复
3. 检查 current_handoff 的 status：
   - done → 推进下一步
   - pending/accepted → 重新派发或等待
   - failed → 进入修复循环
4. 每次更新 .state.md 必须同步更新 last_updated

---

## 6. 目录结构

```
.cc-mini-harness/
├── CLAUDE.md                  # 第一层: Rules
├── .clinerules                # Cline 规则同源
├── .mcp.json                  # MCP 工具配置
├── package.json               # 依赖声明
├── .gitignore
│
├── docs/                      # 框架设计文档
│   ├── design.md              # 本文件
│   └── workflow.md            # 流程编排图
│
├── agents/                    # 第三层: Agent 角色契约
│   ├── pm.md
│   ├── ba.md
│   ├── sa.md
│   ├── de.md
│   ├── te.md
│   └── ux.md
│
├── skills/                    # 第二层: Skills (SOP)
│   ├── mh-clarify.md
│   ├── mh-propose.md
│   ├── mh-apply.md
│   ├── mh-archive.md
│   ├── mh-run.md
│   ├── mh-ppt.md
│   ├── dev-test.md
│   └── post-verify.md
│
├── scripts/                   # 第四层: 硬校验脚本
│   ├── verify.sh
│   ├── baseline.sh
│   └── check-harness.sh
│
├── templates/                 # 模板文件
│   └── handoff-template.md
│
├── .claude/commands/          # Claude Code slash command 入口
│   ├── mh-clarify.md            → 引用 skills/mh-clarify.md
│   ├── mh-propose.md         → 引用 skills/mh-propose.md
│   ├── mh-apply.md           → 引用 skills/mh-apply.md
│   ├── mh-archive.md         → 引用 skills/mh-archive.md
│   ├── mh-ppt.md             → 引用 skills/mh-ppt.md（output_type=ppt 快捷入口）
│   └── mh-run.md             → 引用 skills/mh-run.md
│
├── reference/                 # 用户输入参考资料
├── deliverables/              # 过程产物（按 REQ-ID 隔离）
│   ├── .state.md              # 全局指针（仅存 req_id）
│   └── {REQ-ID}/             # 每个需求独立目录
│       ├── .state.md          # 该需求的详细状态
│       ├── process.log        # 过程日志
│       ├── proposal.md
│       ├── plan-action.md
│       ├── SR{N}-record.md
│       ├── handoffs/          # 该需求的 handoff 文件
│       ├── ba/                # BA 产出
│       ├── sa/                # SA 产出
│       ├── te/                # TE 产出
│       ├── de/                # DE 产出
│       ├── ux/                # UX 产出
│       ├── output/            # 开发产出物
│       └── baselines/         # 基线快照
├── spec/                      # 用户项目归档规格
└── output/                    # 最终交付物
```

---

## 7. 平台适配策略

| 能力 | Claude Code | Cline |
|------|------------|-------|
| Slash command 触发 | .claude/commands/ | .clinerules 命令识别表 |
| 角色隔离 | SubAgent（物理隔离） | 文件协议+行为约束（逻辑隔离） |
| Rules 加载 | CLAUDE.md 自动加载 | .clinerules 自动加载 |
| MCP 工具 | .mcp.json | .mcp.json |
| Handoff 格式 | 统一 | 统一 |
| Skill 内容 | 统一（skills/） | 统一（skills/） |

---

## 8. 执行模式

### 8.1 三种模式定义

| 模式 | 适用场景 | 裁剪策略 |
|------|---------|---------|
| fast | 小修复、配置变更 | 跳过 BA/SA/TE propose，跳过 SR1/SR2/SR4，仅保留一个人工确认点 |
| standard | 新功能、中等需求 | 跳过 BA，SA 出简版设计（含需求映射简表），无 SR1 |
| full | 大型需求、高风险变更 | 完整流程，所有角色参与，所有审批节点 |

### 8.2 模式对各阶段的影响

| 阶段 | fast | standard | full |
|------|------|----------|------|
| init | 完整 | 完整 | 完整 |
| propose | PM 直接编排 plan-action | (SA ∥ TE) 并行 + PM 编排 | BA → (SA ∥ TE) 并行 → PM 编排 → SR1 |
| apply | DE 批量开发→TE 轻量审计→人工确认 | 并行批次循环→SR2→最终审计→SR3 | 同 standard |
| archive | 直接归档，跳过 SR4 | 简化 SR4（一句确认） | 完整 SR4 归档摘要 |

### 8.3 Fast 模式连续流

mode=fast 时，/mh-run 自动将 propose→apply→archive 合并为连续执行：
- 阶段间无需用户手动触发下一命令
- 仅保留 Apply 阶段的人工确认作为唯一审批点
- 全流程预期交互次数：2 次（init 确认 + apply 确认）

---

## 9. 产出类型体系（output_type）

### 9.1 概念

output_type 是框架的核心参数之一，与 mode 正交：
- **mode** 控制流程严谨度（多少审批节点、多少角色参与）
- **output_type** 控制产出物类型和验证方式（用什么工具、怎么测试）

### 9.2 可选值与默认 test_strategy

| output_type | 说明 | 默认 test_strategy | UX 产出 |
|-------------|------|-------------------|--------------|
| web-app | Web 应用（前端/全栈） | e2e / integration | UI wireframe |
| backend-api | 后端服务/API | integration | API 设计文档 |
| cli-tool | 命令行工具 | integration | — |
| data-pipeline | 数据管道/ETL | smoke | 数据流图 |
| infrastructure | 基础设施代码 | smoke | 架构拓扑图 |
| documentation | 文档/规格 | manual | 文档结构大纲 |
| ppt | 演示文稿/HTML slides | manual | wireframe HTML |
| library | 库/SDK | unit | — |
| custom | 自定义 | 用户指定 | 由 SA 指定 |

### 9.3 确定时机

output_type 在 clarify 阶段的"产出类型选择"步骤确定（Step 3），基于：
1. 环境自动检测结果（tech_stack）
2. 需求内容分析
3. 用户确认

确定后写入 .state.md，贯穿全流程。

---

## 10. 环境预检与技术栈检测

### 10.1 多语言环境检测（mh-clarify 阶段）

init 完成后自动执行技术栈检测，结果写入 `.state.md` 的 `tech_stack` 和 `env` 字段：

| 检测项 | 检测方式 | 写入字段 |
|--------|---------|---------|
| 语言 | pyproject.toml/package.json/go.mod/Cargo.toml/pom.xml | tech_stack.language |
| 包管理器 | lock 文件类型推断 | tech_stack.package_manager |
| 测试框架 | 配置文件解析 | tech_stack.test_framework |
| 构建工具 | 配置文件解析 | tech_stack.build_tool |
| Lint 工具 | 配置文件检测 | tech_stack.lint_tool |
| 浏览器可用性 | Playwright/Selenium/Cypress 检测（仅 UI 类型） | env.browser_available |

### 10.2 test_strategy 驱动的验证策略

根据 `test_strategy` 字段决定 TE 行为：

| test_strategy | 验证内容 | 降级条件 |
|---------------|---------|---------|
| e2e | 浏览器 E2E + 回归 + 工程验证 | browser_available=false 时标注 `[E2E DEGRADED]` |
| unit | 单元测试覆盖率 + 工程验证 | — |
| integration | 接口/集成测试 + 工程验证 | — |
| smoke | 构建成功 + 基本功能可用 | — |
| manual | 生成人工验证清单 | 标注 `[MANUAL VERIFICATION]` |
| none | 仅工程验证（lint + 构建） | 标注 `[MINIMAL VERIFICATION]` |

降级不阻塞流程，但报告中必须明确标注，供人工审批时参考。

---

## 11. 归档 Merge 策略

变更归档（spec/ 已有文件时）按以下规则合并：

### 11.1 新增内容

追加到 spec 文件末尾，用注释标注来源：
```
<!-- REQ-{ID} START -->
新增内容
<!-- REQ-{ID} END -->
```

### 11.2 修改内容

定位到对应 REQ-ID 标注的段落，替换该段落内容，更新注释标注。

### 11.3 删除内容

不物理删除原文，在对应段落开头添加：
```
[DEPRECATED by REQ-{ID}] — {废弃原因}
```

### 11.4 版本备份

归档前自动备份当前 spec/ 到 `spec/baselines/`：
- `spec/baselines/requirement-spec.v{N}.md`
- `spec/baselines/design.v{N}.md`
- 版本号自动递增（检测已有 baseline 文件确定 N）

---

## 12. Token 节流与上下文管理

| 平台 | 隔离机制 | 节流策略 |
|------|---------|---------|
| Claude Code | SubAgent 物理隔离（独立上下文） | 天然隔离，无需手动清洗 |
| Cline | 文件协议 + 行为约束 | handoff 仅引用路径，禁止粘贴代码内容 |

通用规则：
- 非 PM 角色完成后仅报告文件路径，不展开产物内容
- 修复循环中仅传递失败原因和报告路径，不重复传递全部代码

---

## 13. 日志规范

所有 Skill 执行过程中必须记录日志到 `deliverables/{REQ-ID}/process.log`。

**格式：**
```
[{timestamp}] [{角色}] {事件描述}
```

**时间戳获取：**
- 优先：`date -u +%Y-%m-%dT%H:%M:%SZ`（UTC ISO 8601）
- 兜底：递增序号 `#NNN`（date 命令不可用时）

**示例：**
```
[2026-05-20T08:30:00Z] [PM] 启动 REQ-2 架构设计，派发任务给 SA
[2026-05-20T08:31:15Z] [SA] REQ-2 完成，产出 deliverables/REQ004/sa/design.md
```

---

## 14. 并行执行机制

### 14.1 设计目标

减少串行等待时间，在保持角色隔离和审批节点不变的前提下，最大化并行度。

### 14.2 平台适配

| 平台 | 并行能力 | 退化行为 |
|------|---------|---------|
| Claude Code | SubAgent 物理并行（多个独立上下文同时执行） | — |
| Cline | 不支持并行（单线程） | 自动退化为串行执行 |

### 14.3 Propose 阶段并行

**standard 模式：** SA ∥ TE 并行
```
proposal.md ──┬──> SA（架构设计）──┐
              └──> TE（测试用例）──┤──> PM 编排
```

**full 模式：** BA → (SA ∥ TE) 并行
```
proposal.md ──> BA（需求分析）──┬──> SA（架构设计）──┐
                               └──> TE（测试用例）──┤──> PM 编排 → SR1
```

**关键决策：** TE 不依赖 SA 的 design.md，而是直接基于 proposal（standard）或 requirement-spec（full）设计测试用例。这牺牲了少量测试精度（TE 无法参考架构细节），换取约 40-50% 的 propose 阶段时间节省。

### 14.4 Apply 阶段并行批次

```
plan-action.md 中的 Task 依赖图:

  Task-1 [deps: none] ──┐
  Task-2 [deps: none] ──┤──> Batch-1（并行开发 + 并行审计）
  Task-3 [deps: Task-1] ──> Batch-2（等 Batch-1 完成后并行）
  Task-4 [deps: Task-1, Task-2] ──> Batch-2
```

**执行流程：**
1. PM 在 propose 阶段编排 plan-action.md 时标注 `[deps: ...]`
2. Apply 阶段按依赖关系计算批次
3. 同批次内的 Task 并行派发 DE → 并行派发 TE → 批量人工确认
4. 批次间串行（后序批次依赖前序批次的产出代码）

**依赖判断标准：**
- 代码级依赖（Task-B 调用 Task-A 的函数/模块）→ 标记依赖
- 逻辑关联但代码独立 → 不标记依赖
- 不确定时 → 不标记（宁可并行，由 TE 审计兜底）

### 14.5 并行修复循环

同一批次内多个 Task 审计失败时，可并行派发修复：
- 每个失败 Task 独立进入修复循环
- 各自最多 5 轮（互不影响）
- 全部通过后统一进入人工确认

### 14.6 状态管理

并行执行时 `.state.md` 的 `current_step` 使用复合值：
- `REQ-2+REQ-3`（SA 和 TE 并行中）
- `DEV-1.B{N}`（Batch-N 开发中）
- `TEST-1.B{N}`（Batch-N 审计中）

断点恢复时，PM 检测到复合 step 值，重新派发该批次中未完成的 Task。

---

## 15. 扩展性考虑

- **新增角色**: 在 agents/ 下新增定义文件，在 skill 中增加调度步骤
- **新增流程阶段**: 新增 skill 文件 + .claude/commands/ 引用
- **接入外部 Agent 框架**: Handoff 协议天然兼容（如 Anthropic Agent SDK）
- **自定义校验**: 在 scripts/ 下新增脚本，在 skill 中引用

---

## 16. PPT 子系统（output_type=ppt）

PPT 类 HTML 页面开发能力，通过 `/mh-ppt` 快捷触发或在主流程中设置 output_type=ppt 激活。

### 16.1 架构

```
/mh-ppt 快捷触发 → 自动设置 output_type=ppt → 进入 /mh-run 主流程
  主流程集成点:
    propose 阶段: SA 方案后追加 UX wireframe 步骤
    apply 阶段: DE 基于 wireframe 实现，TE 使用 verify-ppt.sh
    archive 阶段: 额外归档 ux/wireframes/
```

### 16.2 UX 角色（PPT 模式）

| 项目 | 说明 |
|------|------|
| 定义文件 | agents/ux.md |
| 职责 | 逐页版式设计，产出高保真 HTML wireframe |
| 输出 | ux/slide-spec.md + ux/wireframes/slide-{NN}.html |
| 约束 | 基于 ppt-base.css，禁止覆盖全局变量，禁止技术决策 |

### 16.3 模板体系

- 基础样式（深色暖调）: `templates/ppt-base.css`（16:9 约束 + 深色配色 + 组件类）
- 基础样式（白底商务）: `templates/ppt-light.css`（16:9 约束 + 白底蓝橙配色 + 迷你图表组件）
- 骨架模板: `templates/ppt-base.html`
- 版式库（深色）: `templates/ppt-templates/layouts/L{NN}-{name}.html`（12 套高密度版式）
- 版式库（白底）: `templates/ppt-templates/layouts/W{NN}-{name}.html`（5 套高密度版式）

### 16.4 设计规范

**通用约束：**
- 视口: 1920×1080（16:9）
- 信息密度: 高密度优先，每页承载传统 PPT 2-3 页信息量

**深色暖调主题（L 系列）：**
- 配色: 深色暖调（背景 #1A1614，主强调 #E8845F）
- 字号: 标题 26px，正文 15px，标注 12px

**白底商务主题（W 系列）：**
- 配色: 白底（背景 #FFFFFF，主强调 #2980F0，辅助 #FF7400）
- 字号: 标题 24px，正文 14px，标注 11px
- 特色: 纯 CSS 迷你图表（环形图/柱状图/进度条/趋势线）、紧凑卡片系统、蓝色竖条分区

### 16.5 与主流程的关系

- /mh-ppt 是 output_type=ppt 的快捷入口，本质上走主流程
- PPT 补充规则定义在 skills/mh-ppt.md，主流程在 output_type=ppt 时自动加载
- UX 角色仅在 output_type 需要设计制品时参与（由 PM 根据 output_type 决定）
- verify-ppt.sh 作为 PPT 特有的硬校验脚本，在 TE 审计时调用
