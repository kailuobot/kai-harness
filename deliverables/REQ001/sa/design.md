# 技术设计方案

## 1. 架构概述

### 整体方案

基于 MCP Python SDK 构建一个轻量级 MCP Server，通过 SSE（Server-Sent Events）传输层对外暴露 7 个文件操作工具。Server 以单进程方式直接运行在极空间 Z4Pro NAS 上，无需容器化。

### 技术栈

| 层次 | 选型 | 说明 |
|------|------|------|
| 协议层 | JSON-RPC 2.0 over SSE | MCP 标准传输方式 |
| 框架层 | mcp (Python SDK) | 官方 SDK，内置 SSE server 支持 |
| 运行时 | Python 3.10+ | NAS 上直接运行 |
| 文件操作 | pathlib + os | 标准库，零额外依赖 |
| 进程管理 | systemd / supervisord | 保活与自动重启 |

### 核心架构

```
OpenClaw / AI Client
        │
        │  HTTP (SSE + JSON-RPC 2.0)
        ▼
┌─────────────────────────────┐
│      MCP Server (Python)    │
│  ┌───────────────────────┐  │
│  │   SSE Transport Layer │  │  ← mcp SDK 内置
│  ├───────────────────────┤  │
│  │   Tool Router         │  │  ← 工具注册与分发
│  ├───────────────────────┤  │
│  │   Security Sandbox    │  │  ← 路径校验、根目录限制
│  ├───────────────────────┤  │
│  │   File Operations     │  │  ← 7 个工具实现
│  └───────────────────────┘  │
└─────────────────────────────┘
        │
        ▼
   NAS 文件系统（受限根目录）
```

### 安全设计

- 所有文件路径在操作前经过 `resolve()` + `is_relative_to(root)` 校验
- 拒绝包含 `..` 的路径穿越尝试
- 根目录通过配置文件或环境变量指定，运行时不可变

### 部署模型

- 直接在 NAS 上以 Python 进程运行
- 通过 systemd service 或 supervisord 管理进程生命周期
- 监听内网端口（默认 8080），无需 HTTPS

### Skill 发布

- 提供符合 SkillHub 规范的 manifest 文件
- 描述 server 地址、工具列表、参数 schema
- 支持 OpenClaw 自动发现与安装

## 2. 需求映射简表（standard 模式）

| Proposal 要点 | 对应 Task | 验证方式 |
|--------------|-----------|---------|
| MCP Server 核心框架（SSE transport） | T1 | 启动 server，客户端成功建立 SSE 连接 |
| list_directory 工具 | T2 | 调用工具返回正确目录列表 |
| read_file 工具 | T2 | 调用工具返回正确文件内容 |
| write_file 工具 | T2 | 调用工具后文件被正确创建/覆盖 |
| delete_file 工具 | T2 | 调用工具后文件被删除 |
| create_directory 工具 | T2 | 调用工具后目录被创建 |
| delete_directory 工具 | T2 | 调用工具后目录被删除 |
| move_file 工具 | T2 | 调用工具后文件/目录被移动 |
| 根目录沙箱限制 | T3 | 路径穿越请求被拒绝，返回错误 |
| MCP skill manifest | T4 | manifest 符合 SkillHub 规范，可被解析 |
| 部署运行 | T5 | NAS 上进程启动并响应请求 |

## 3. Tasks 清单

| Task ID | 描述 | 依赖 | 预估复杂度 |
|---------|------|------|-----------|
| T1 | 搭建项目骨架与 MCP Server 核心框架：项目结构、依赖管理（pyproject.toml）、基于 mcp SDK 的 SSE server 启动入口、配置加载（根目录路径、端口） | 无 | 中 |
| T2 | 实现 7 个文件操作工具：list_directory、read_file、write_file、delete_file、create_directory、delete_directory、move_file，注册到 MCP tool router | T1 | 中 |
| T3 | 实现安全沙箱层：路径规范化、根目录边界校验、路径穿越防护、错误响应格式化 | T1 | 低 |
| T4 | 编写 SkillHub manifest 文件：工具描述、参数 JSON Schema、server 元信息，确保符合发布规范 | T2 | 低 |
| T5 | 编写部署配置与说明：systemd service 文件、启动脚本、环境变量配置模板、README | T1, T2, T3 | 低 |
