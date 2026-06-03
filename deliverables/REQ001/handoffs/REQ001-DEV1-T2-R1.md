---
handoff_id: "REQ001-DEV1-T2-R1"
from: PM
to: DE
status: pending
task_type: "编码实现"
created_at: "2026-05-26T09:17:56Z"
completed_at: ""
---

## 任务描述

实现 Task T2：7 个文件操作工具，注册到 MCP tool router。每个工具必须集成 T3 安全沙箱层进行路径校验。

## 输入文件（白名单）

仅以下文件可被读取，禁止读取白名单外的任何文件：

- deliverables/REQ001/sa/design.md
- deliverables/REQ001/output/（已有代码，含 T1 骨架和 T3 安全层）

## 期望输出

- 路径: `deliverables/REQ001/output/`（新增工具模块）
- 路径: `deliverables/REQ001/de/code-report.md`（更新）

## 约束

- 实现 7 个 MCP 工具并注册到 server：
  1. `list_directory` — 列出目录内容（支持递归/非递归）
  2. `read_file` — 读取文件内容（文本文件）
  3. `write_file` — 创建或覆盖写入文件
  4. `delete_file` — 删除文件
  5. `create_directory` — 创建文件夹（支持递归创建）
  6. `delete_directory` — 删除文件夹（支持递归删除）
  7. `move_file` — 移动/重命名文件或文件夹
- 每个工具必须：
  - 使用 T3 sandbox.validate_path() 校验路径
  - 捕获 sandbox 异常并返回 MCP 错误响应
  - 有清晰的参数 schema（name, description, inputSchema）
- 使用 mcp Python SDK 的 @server.tool() 装饰器注册
- 编写对应的单元测试
- 代码输出到 deliverables/REQ001/output/ 目录下

## 参考 Skill

- `skills/pdt-apply.md` 中的 standard 模式 Step 1

## 完成回报（由执行角色填写）

- status: 
- output_files: []
- summary: ""
- issues: ""

## 轮次信息

- 当前轮次: 1/5
- 上轮失败原因: N/A
- 失败报告路径: N/A
