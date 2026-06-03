# Proposal: NAS MCP Server（文件管理服务）

## 背景与目标

在极空间 Z4Pro NAS 上部署一个遵循 Anthropic MCP 协议的 Server，通过 SSE（HTTP-based）传输方式对外提供文件管理能力。最终以 skill 形式发布到 SkillHub，供 OpenClaw 等 AI 工具发现、安装并调用，实现"对话式文件管理"体验。

## 范围

### 包含
- MCP Server 核心框架（Python，SSE transport）
- 文件操作工具集：
  - `list_directory` — 列出目录内容/目录树
  - `read_file` — 读取文件内容
  - `write_file` — 创建或覆盖写入文件
  - `delete_file` — 删除文件
  - `create_directory` — 创建文件夹
  - `delete_directory` — 删除文件夹
  - `move_file` — 移动/重命名文件或文件夹
- 可配置的根目录限制（沙箱化，防止越界访问）
- MCP skill manifest（符合主流规范，支持 SkillHub 发布与 OpenClaw 安装）
- 部署说明（直接在 NAS 上运行 Python 进程）

### 不包含
- Docker 容器化部署（因沙箱限制无法访问 NAS 文件）
- 认证/鉴权机制（当前仅内网使用）
- 文件内容搜索、版本管理等高级功能
- 外网穿透/HTTPS 配置

## 关键约束

- 严格遵循 Anthropic MCP 协议规范（JSON-RPC 2.0 + SSE transport）
- 文件操作限制在配置的根目录内，禁止路径穿越
- Python 实现，依赖尽量精简（适配 NAS 有限资源）
- NAS 环境：极空间 Z4Pro（ARM/x86 架构待确认）

## 参考资料

- Anthropic MCP 协议规范（https://modelcontextprotocol.io）
- MCP Python SDK（mcp python package）
- SkillHub 主流 skill 发布规范（待调研确认）
