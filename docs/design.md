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
| phase | 当前阶段（init/propose/apply/archive） |
| current_step | 当前步骤 ID |
| current_handoff | 当前活跃 handoff 文件名 |
| current_role | 当前执行角色 |
| completed_steps | 已完成步骤列表 |
| sr_status | 各审批节点状态 |

### 5.2 断点恢复

1. PM 读取 .state.md 确定位置
2. 检查 current_handoff 的 status
3. 如果 done → 推进下一步
4. 如果 pending/accepted → 重新派发或等待
5. 如果 failed → 进入修复循环

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
│   ├── dev-test.md
│   └── post-verify.md
│
├── scripts/                   # 第四层: 硬校验脚本
│   ├── verify.sh
│   ├── baseline.sh
│   └── check-harness.sh
│
├── .claude/commands/          # Claude Code slash command 入口
│   ├── pdt-init.md            → 引用 skills/pdt-init.md
│   ├── pdt-propose.md         → 引用 skills/pdt-propose.md
│   ├── pdt-apply.md           → 引用 skills/pdt-apply.md
│   └── pdt-archive.md         → 引用 skills/pdt-archive.md
│
├── reference/                 # 用户输入参考资料
├── deliverables/              # 过程产物（工作区）
│   ├── .state.md
│   ├── handoffs/
│   ├── sa/
│   ├── te/
│   ├── de/
│   └── output/
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

## 8. 扩展性考虑

- **新增角色**: 在 agents/ 下新增定义文件，在 skill 中增加调度步骤
- **新增流程阶段**: 新增 skill 文件 + .claude/commands/ 引用
- **接入外部 Agent 框架**: Handoff 协议天然兼容（如 Anthropic Agent SDK）
- **自定义校验**: 在 scripts/ 下新增脚本，在 skill 中引用
