# 测试报告

## 概要
- 执行时间: 2026-05-27
- 总用例数: 4
- 通过: 4
- 失败: 0
- 阻塞: 1（回归测试 — 环境缺少 pytest 及 Python 3.10+）

## 结论: PASS

## 功能验证（TC-25~28 — T5 部署配置与说明）

### TC-25: systemd service 文件格式正确

- 结果: PASS
- 验证项:
  - [x] 包含 [Unit] 段（Description, After=network.target）
  - [x] 包含 [Service] 段（Type=simple, User, ExecStart, Restart=on-failure, RestartSec=5）
  - [x] 包含 [Install] 段（WantedBy=multi-user.target）
  - [x] Restart=on-failure 已配置
  - [x] EnvironmentFile=/opt/nas-mcp-server/.env 已配置
  - [x] StandardOutput/StandardError 输出到 journal

### TC-26: 启动脚本语法正确

- 结果: PASS
- 验证项:
  - [x] `bash -n start.sh` 语法检查通过（exit code 0）
  - [x] `bash -n deploy/install.sh` 语法检查通过（exit code 0）
  - [x] start.sh 逻辑合理：set -euo pipefail → 加载 .env → 激活 venv → exec 启动 server
  - [x] install.sh 逻辑合理：创建目录 → 创建 venv → 安装依赖 → 复制配置模板
  - [x] start.sh 缺少 .env 时有明确错误提示并退出

### TC-27: .env.example 包含 NAS_ROOT_DIR 和 MCP_PORT

- 结果: PASS
- 验证项:
  - [x] NAS_ROOT_DIR=/path/to/nas/files（已配置，含注释说明）
  - [x] MCP_PORT=8080（已配置）
  - [x] 额外包含 LOG_LEVEL=INFO

### TC-28: README 包含完整部署步骤

- 结果: PASS
- 验证项:
  - [x] Python 安装说明（"部署到极空间 Z4Pro" 第 1 节）
  - [x] 依赖安装（第 3 节 — 运行 install.sh）
  - [x] 配置说明（第 4 节 — 编辑 .env）
  - [x] 启动方法（第 5 节 — 手动启动测试）
  - [x] systemd 注册（第 6 节 — 完整命令序列）
  - [x] 验证部署（第 7 节 — 状态检查、日志查看、SSE 测试）
  - [x] 常见问题排查表

## 工程验证

| 检查项 | 结果 | 说明 |
|--------|------|------|
| bash -n start.sh | PASS | 语法无错误 |
| bash -n deploy/install.sh | PASS | 语法无错误 |
| systemd service 配置合理性 | PASS | Type=simple, on-failure 重启, 5s 间隔, journal 日志 |
| 文件权限 | PASS | start.sh: rwxr-xr-x, install.sh: rwxr-xr-x（可执行） |

## 回归验证

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 全量 pytest 测试 | BLOCKED | 环境缺少 pytest 模块且 Python 版本为 3.9.6（项目要求 3.10+），无法执行 |

## 失败详情

| 用例ID | 描述 | 实际结果 | 截图/日志 |
|--------|------|---------|----------|
| （无） | — | — | — |

## 环境信息
- 浏览器: [E2E DEGRADED - 环境不可用]
- 运行平台: macOS (Darwin 25.5.0)
- Python: 3.9.6（系统自带，低于项目要求 3.10+）
- pytest: 不可用（无虚拟环境）
