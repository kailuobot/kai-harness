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

流程状态的唯一真相源。字段：

| 字段 | 用途 |
|------|------|
| req_id | 当前需求编号 |
| mode | 执行模式（fast/standard/full） |
| phase | 当前阶段（init/propose/apply/archive） |
| current_step | 当前步骤 ID |
| current_handoff | 当前活跃 handoff 文件名 |
| current_role | 当前执行角色 |
| completed_steps | 已完成步骤列表 |
| sr_status | 各审批节点状态 |
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
│   └── te.md
│
├── skills/                    # 第二层: Skills (SOP)
│   ├── pdt-init.md
│   ├── pdt-propose.md
│   ├── pdt-apply.md
│   ├── pdt-archive.md
│   ├── pdt-run.md
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
│   ├── pdt-init.md            → 引用 skills/pdt-init.md
│   ├── pdt-propose.md         → 引用 skills/pdt-propose.md
│   ├── pdt-apply.md           → 引用 skills/pdt-apply.md
│   ├── pdt-archive.md         → 引用 skills/pdt-archive.md
│   └── pdt-run.md             → 引用 skills/pdt-run.md
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
│       ├── output/            # 开发产出物
│       └── baselines/         # 基线快照
├── spec/                      # 用户项目归档规格
└── output/final/              # 最终交付物
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
| propose | PM 直接编排 plan-action | SA 简版设计 + TE 测试用例 + PM 编排 | BA→SA→TE→PM 编排→SR1 |
| apply | DE 批量开发→TE 轻量审计→人工确认 | 逐任务循环→SR2→最终审计→SR3 | 同 standard |
| archive | 直接归档，跳过 SR4 | 简化 SR4（一句确认） | 完整 SR4 归档摘要 |

### 8.3 Fast 模式连续流

mode=fast 时，/pdt-run 自动将 propose→apply→archive 合并为连续执行：
- 阶段间无需用户手动触发下一命令
- 仅保留 Apply 阶段的人工确认作为唯一审批点
- 全流程预期交互次数：2 次（init 确认 + apply 确认）

---

## 9. 环境预检与降级

### 9.1 环境预检（pdt-init 阶段）

init 完成后自动执行环境检测，结果写入 `.state.md` 的 `env` 字段：

| 检测项 | 方法 | 写入字段 |
|--------|------|---------|
| Node.js 版本 | `node --version` | env.node_version |
| 浏览器可用性 | `npx playwright install --dry-run` 或检测已安装浏览器 | env.browser_available |

### 9.2 E2E 测试降级策略

根据 `env.browser_available` 字段决定 TE 行为：

| 环境状态 | fast 模式 | standard/full 模式 |
|---------|-----------|-------------------|
| browser_available=true | 工程验证（跳过 E2E） | 完整审计（含 E2E） |
| browser_available=false | 工程验证（跳过 E2E） | 工程验证 + 标注 `[E2E DEGRADED - 环境不可用]` |

降级不阻塞流程，但报告中必须明确标注，供人工审批时参考。

---

## 10. 归档 Merge 策略

变更归档（spec/ 已有文件时）按以下规则合并：

### 10.1 新增内容

追加到 spec 文件末尾，用注释标注来源：
```
<!-- REQ-{ID} START -->
新增内容
<!-- REQ-{ID} END -->
```

### 10.2 修改内容

定位到对应 REQ-ID 标注的段落，替换该段落内容，更新注释标注。

### 10.3 删除内容

不物理删除原文，在对应段落开头添加：
```
[DEPRECATED by REQ-{ID}] — {废弃原因}
```

### 10.4 版本备份

归档前自动备份当前 spec/ 到 `spec/baselines/`：
- `spec/baselines/requirement-spec.v{N}.md`
- `spec/baselines/design.v{N}.md`
- 版本号自动递增（检测已有 baseline 文件确定 N）

---

## 11. Token 节流与上下文管理

| 平台 | 隔离机制 | 节流策略 |
|------|---------|---------|
| Claude Code | SubAgent 物理隔离（独立上下文） | 天然隔离，无需手动清洗 |
| Cline | 文件协议 + 行为约束 | handoff 仅引用路径，禁止粘贴代码内容 |

通用规则：
- 非 PM 角色完成后仅报告文件路径，不展开产物内容
- 修复循环中仅传递失败原因和报告路径，不重复传递全部代码

---

## 12. 日志规范

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

## 13. 扩展性考虑

- **新增角色**: 在 agents/ 下新增定义文件，在 skill 中增加调度步骤
- **新增流程阶段**: 新增 skill 文件 + .claude/commands/ 引用
- **接入外部 Agent 框架**: Handoff 协议天然兼容（如 Anthropic Agent SDK）
- **自定义校验**: 在 scripts/ 下新增脚本，在 skill 中引用
