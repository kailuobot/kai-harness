---
handoff_id: "REQ001-DEV1-T1-R2"
from: PM
to: DE
status: pending
task_type: "编码实现"
created_at: "2026-05-26T09:04:35Z"
completed_at: ""
---

## 任务描述

修复 Task T1 审计失败项：`__main__.py` 在 NAS_ROOT_DIR 不存在时应终止进程，而非仅打印警告继续运行。

## 输入文件（白名单）

仅以下文件可被读取，禁止读取白名单外的任何文件：

- deliverables/REQ001/output/（全部代码）
- deliverables/REQ001/te/temp-test-report.md

## 期望输出

- 路径: `deliverables/REQ001/output/src/nas_mcp_server/__main__.py`（修复后）
- 路径: `deliverables/REQ001/de/code-report.md`（更新）

## 约束

- 仅修复指定问题，不做其他改动
- `__main__.py` 中当 `config.root_dir.exists()` 为 False 时，应输出错误到 stderr 并调用 sys.exit(1) 终止启动
- 修复后确保相关测试通过

## 参考 Skill

- `skills/pdt-apply.md` 修复循环

## 完成回报（由执行角色填写）

- status: 
- output_files: []
- summary: ""
- issues: ""

## 轮次信息

- 当前轮次: 2/5
- 上轮失败原因: TC-24 失败 — NAS_ROOT_DIR 不存在时仅打印 Warning 继续运行，未终止进程
- 失败报告路径: deliverables/REQ001/te/temp-test-report.md
