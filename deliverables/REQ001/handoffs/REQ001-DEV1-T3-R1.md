---
handoff_id: "REQ001-DEV1-T3-R1"
from: PM
to: DE
status: pending
task_type: "编码实现"
created_at: "2026-05-26T09:11:03Z"
completed_at: ""
---

## 任务描述

实现 Task T3：安全沙箱层。包括路径规范化、根目录边界校验、路径穿越防护、错误响应格式化。所有文件操作工具（T2）将依赖此安全层。

## 输入文件（白名单）

仅以下文件可被读取，禁止读取白名单外的任何文件：

- deliverables/REQ001/sa/design.md
- deliverables/REQ001/output/（已有代码）

## 期望输出

- 路径: `deliverables/REQ001/output/`（新增安全模块）
- 路径: `deliverables/REQ001/de/code-report.md`（更新）

## 约束

- 实现路径安全校验模块（如 sandbox.py 或 security.py）
- 所有路径在操作前经过 resolve() + is_relative_to(root) 校验
- 拒绝包含 .. 的路径穿越尝试
- 根目录通过配置指定（已在 T1 config.py 中实现），运行时不可变
- 提供统一的错误响应格式（供 T2 工具调用时使用）
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
