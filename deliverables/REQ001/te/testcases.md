# 测试用例

> 降级说明：browser_available=false，无法执行浏览器 E2E 测试。所有 E2E 用例降级为基于 HTTP 客户端（curl / httpx / pytest）的接口级验证，标注 [降级] 标记。

---

## TC-01: list_directory 正常列出目录内容

- 关联需求: T2 — list_directory 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱根目录下存在子目录和文件
- 步骤:
  1. 通过 SSE 建立连接，发送 JSON-RPC 请求调用 list_directory，参数为沙箱内有效目录路径
  2. 接收响应
- 期望结果: 返回 JSON-RPC 成功响应，result 包含目录下所有文件和子目录的列表，条目信息正确

---

## TC-02: read_file 正常读取文件

- 关联需求: T2 — read_file 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱根目录下存在已知内容的文本文件
- 步骤:
  1. 发送 JSON-RPC 请求调用 read_file，参数为该文件路径
  2. 接收响应
- 期望结果: 返回 JSON-RPC 成功响应，result 包含文件的完整文本内容，与预期一致

---

## TC-03: write_file 正常创建/覆盖文件

- 关联需求: T2 — write_file 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱根目录可写
- 步骤:
  1. 发送 JSON-RPC 请求调用 write_file，参数为目标路径和写入内容
  2. 接收响应
  3. 通过 read_file 或直接文件系统验证文件内容
- 期望结果: 返回成功响应；目标文件被创建（或覆盖），内容与写入参数一致

---

## TC-04: delete_file 正常删除文件

- 关联需求: T2 — delete_file 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在待删除的文件
- 步骤:
  1. 发送 JSON-RPC 请求调用 delete_file，参数为目标文件路径
  2. 接收响应
  3. 验证文件已不存在
- 期望结果: 返回成功响应；文件从文件系统中移除

---

## TC-05: create_directory 正常创建目录

- 关联需求: T2 — create_directory 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内目标目录不存在
- 步骤:
  1. 发送 JSON-RPC 请求调用 create_directory，参数为新目录路径
  2. 接收响应
  3. 验证目录已创建
- 期望结果: 返回成功响应；目录在文件系统中存在

---

## TC-06: delete_directory 正常删除目录

- 关联需求: T2 — delete_directory 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在空目录
- 步骤:
  1. 发送 JSON-RPC 请求调用 delete_directory，参数为目标目录路径
  2. 接收响应
  3. 验证目录已不存在
- 期望结果: 返回成功响应；目录从文件系统中移除

---

## TC-07: move_file 正常移动/重命名

- 关联需求: T2 — move_file 工具
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在源文件
- 步骤:
  1. 发送 JSON-RPC 请求调用 move_file，参数为源路径和目标路径
  2. 接收响应
  3. 验证源路径不存在，目标路径存在且内容正确
- 期望结果: 返回成功响应；文件从源路径移动到目标路径

---

## TC-08: read_file 读取不存在的文件

- 关联需求: T2 — read_file 异常路径
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；目标文件路径在沙箱内但不存在
- 步骤:
  1. 发送 JSON-RPC 请求调用 read_file，参数为不存在的文件路径
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，错误信息明确指出文件不存在

---

## TC-09: delete_file 删除不存在的文件

- 关联需求: T2 — delete_file 异常路径
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；目标文件不存在
- 步骤:
  1. 发送 JSON-RPC 请求调用 delete_file，参数为不存在的文件路径
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，错误信息明确指出文件不存在

---

## TC-10: delete_directory 删除非空目录

- 关联需求: T2 — delete_directory 异常路径
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在包含文件的非空目录
- 步骤:
  1. 发送 JSON-RPC 请求调用 delete_directory，参数为非空目录路径
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，拒绝删除非空目录（或根据设计递归删除并成功，需与设计确认）

---

## TC-11: move_file 源文件不存在

- 关联需求: T2 — move_file 异常路径
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；源路径不存在
- 步骤:
  1. 发送 JSON-RPC 请求调用 move_file，源路径为不存在的文件
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，错误信息指出源文件不存在

---

## TC-12: write_file 写入只读目录

- 关联需求: T2 — write_file 异常路径（权限问题）
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在只读目录
- 步骤:
  1. 发送 JSON-RPC 请求调用 write_file，目标路径位于只读目录下
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，错误信息指出权限不足

---

## TC-13: 路径穿越攻击 — 使用 .. 越界

- 关联需求: T3 — 安全沙箱层
- 类型: 工程验证
- 前置条件: MCP Server 已启动；配置根目录为 /data/sandbox
- 步骤:
  1. 发送 JSON-RPC 请求调用 read_file，路径参数为 `../../etc/passwd`
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，拒绝访问；不返回任何沙箱外文件内容

---

## TC-14: 路径穿越攻击 — 绝对路径越界

- 关联需求: T3 — 安全沙箱层
- 类型: 工程验证
- 前置条件: MCP Server 已启动；配置根目录为 /data/sandbox
- 步骤:
  1. 发送 JSON-RPC 请求调用 read_file，路径参数为 `/etc/passwd`
  2. 接收响应
- 期望结果: 返回 JSON-RPC error 响应，拒绝访问沙箱外路径

---

## TC-15: 路径穿越攻击 — 符号链接指向沙箱外

- 关联需求: T3 — 安全沙箱层
- 类型: 工程验证
- 前置条件: MCP Server 已启动；沙箱内存在指向沙箱外目录的符号链接
- 步骤:
  1. 发送 JSON-RPC 请求调用 read_file，路径参数为该符号链接
  2. 接收响应
- 期望结果: 路径 resolve 后检测到越界，返回 error 响应，拒绝访问

---

## TC-16: 路径穿越攻击 — move_file 目标路径越界

- 关联需求: T3 — 安全沙箱层
- 类型: 工程验证
- 前置条件: MCP Server 已启动；沙箱内存在源文件
- 步骤:
  1. 发送 JSON-RPC 请求调用 move_file，源路径为沙箱内文件，目标路径为 `../../tmp/stolen`
  2. 接收响应
- 期望结果: 返回 error 响应，拒绝将文件移动到沙箱外；源文件保持不变

---

## TC-17: SSE 连接建立与保持

- 关联需求: T1 — MCP Server 核心框架（SSE transport）
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动，监听配置端口
- 步骤:
  1. 使用 HTTP 客户端向 SSE endpoint 发起 GET 请求
  2. 验证响应 Content-Type 为 text/event-stream
  3. 保持连接 10 秒，观察心跳或初始化事件
- 期望结果: 成功建立 SSE 连接；Content-Type 正确；连接保持活跃

---

## TC-18: JSON-RPC 2.0 请求格式合规

- 关联需求: T1 — MCP 协议合规性
- 类型: 工程验证
- 前置条件: MCP Server 已启动且 SSE 连接已建立
- 步骤:
  1. 发送符合 JSON-RPC 2.0 格式的 tools/list 请求（含 jsonrpc: "2.0", method, id）
  2. 接收响应
- 期望结果: 响应包含 jsonrpc: "2.0"、与请求匹配的 id、result 字段列出所有 7 个工具

---

## TC-19: JSON-RPC 2.0 错误格式合规

- 关联需求: T1 — MCP 协议合规性
- 类型: 工程验证
- 前置条件: MCP Server 已启动且 SSE 连接已建立
- 步骤:
  1. 发送调用不存在方法的 JSON-RPC 请求（method: "nonexistent_tool"）
  2. 接收响应
- 期望结果: 响应包含 jsonrpc: "2.0"、匹配的 id、error 对象含 code 和 message 字段，符合 JSON-RPC 2.0 错误规范

---

## TC-20: JSON-RPC 请求缺少必填字段

- 关联需求: T1 — MCP 协议合规性
- 类型: 工程验证
- 前置条件: MCP Server 已启动且 SSE 连接已建立
- 步骤:
  1. 发送缺少 jsonrpc 字段的请求
  2. 发送缺少 method 字段的请求
- 期望结果: 均返回 JSON-RPC Invalid Request 错误（code: -32600）

---

## TC-21: MCP tools/list 返回完整工具列表

- 关联需求: T1, T2 — 工具注册与发现
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动
- 步骤:
  1. 发送 tools/list JSON-RPC 请求
  2. 解析响应中的工具列表
- 期望结果: 返回 7 个工具（list_directory, read_file, write_file, delete_file, create_directory, delete_directory, move_file），每个工具包含 name、description、inputSchema

---

## TC-22: 配置根目录通过环境变量指定

- 关联需求: T1, T3 — 配置加载
- 类型: 工程验证
- 前置条件: 设置环境变量指定根目录路径
- 步骤:
  1. 设置环境变量（如 MCP_ROOT_DIR=/tmp/test_sandbox）
  2. 启动 MCP Server
  3. 调用 list_directory，路径为根目录
- 期望结果: Server 正常启动；list_directory 返回指定根目录的内容

---

## TC-23: 配置端口通过环境变量指定

- 关联需求: T1 — 配置加载
- 类型: 工程验证
- 前置条件: 设置端口环境变量为非默认值（如 9090）
- 步骤:
  1. 设置环境变量（如 MCP_PORT=9090）
  2. 启动 MCP Server
  3. 向 localhost:9090 发起 SSE 连接
- 期望结果: Server 在指定端口 9090 监听并正常响应

---

## TC-24: Server 启动时根目录不存在

- 关联需求: T1, T3 — 启动校验
- 类型: 工程验证
- 前置条件: 配置的根目录路径不存在
- 步骤:
  1. 设置根目录为不存在的路径
  2. 尝试启动 MCP Server
- 期望结果: Server 启动失败或报错，明确提示根目录不存在；不会以无效状态运行

---

## TC-25: list_directory 列出目录树（递归）

- 关联需求: T2 — list_directory 目录树功能
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在多层嵌套目录结构
- 步骤:
  1. 发送 JSON-RPC 请求调用 list_directory，启用递归/树形参数（如有）
  2. 接收响应
- 期望结果: 返回包含子目录及其内容的完整目录树结构

---

## TC-26: write_file 覆盖已存在文件

- 关联需求: T2 — write_file 覆盖语义
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在已有内容的文件
- 步骤:
  1. 发送 write_file 请求，路径为已存在文件，内容为新内容
  2. 通过 read_file 验证文件内容
- 期望结果: 文件内容被完全覆盖为新内容，旧内容不再存在

---

## TC-27: move_file 移动目录

- 关联需求: T2 — move_file 支持目录
- 类型: E2E [降级]
- 前置条件: MCP Server 已启动；沙箱内存在包含文件的目录
- 步骤:
  1. 发送 move_file 请求，源为目录路径，目标为新路径
  2. 验证源路径不存在，目标路径存在且内部文件完整
- 期望结果: 目录及其内容被完整移动到新路径

---

## TC-28: Skill Manifest 文件格式验证

- 关联需求: T4 — SkillHub manifest
- 类型: 工程验证
- 前置条件: manifest 文件已生成
- 步骤:
  1. 读取 manifest 文件
  2. 验证 JSON/YAML 格式合法
  3. 验证包含必要字段：server 地址、工具列表、每个工具的参数 JSON Schema
- 期望结果: manifest 格式合法，包含全部 7 个工具描述，参数 schema 与实际工具入参一致
