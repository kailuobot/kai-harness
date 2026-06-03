---
handoff_id: "REQ002-DEV1-R1"
from: PM
to: DE
status: done
task_type: "编码实现"
output_type: "backend-api"
tech_stack: "python/pip"
created_at: "2026-06-03T10:08:00Z"
completed_at: ""
---

## 任务描述

在 REQ001 已有 NAS MCP Server 基础上新增 3 个下载工具（download_movie, download_subtitle, download_status）。代码已在本次会话中预先实现，需要：
1. 将 REQ001/output 完整代码（含新增修改）复制到 REQ002/output
2. 编写集成测试 test_download_tools.py，覆盖 aria2 RPC mock、subliminal 调用 mock、路径沙箱校验
3. 确保所有已有测试和新测试通过

## 输入文件（白名单）

- deliverables/REQ002/plan-action.md
- deliverables/REQ002/proposal.md
- deliverables/REQ001/output/src/nas_mcp_server/download_tools.py
- deliverables/REQ001/output/src/nas_mcp_server/tools.py
- deliverables/REQ001/output/src/nas_mcp_server/config.py
- deliverables/REQ001/output/src/nas_mcp_server/server.py
- deliverables/REQ001/output/src/nas_mcp_server/sandbox.py
- deliverables/REQ001/output/src/nas_mcp_server/__init__.py
- deliverables/REQ001/output/src/nas_mcp_server/__main__.py
- deliverables/REQ001/output/pyproject.toml
- deliverables/REQ001/output/tests/conftest.py
- deliverables/REQ001/output/tests/test_tools.py
- deliverables/REQ001/output/tests/test_config.py
- deliverables/REQ001/output/tests/test_sandbox.py
- deliverables/REQ001/output/tests/test_server.py
- deliverables/REQ001/output/tests/test_manifest.py

## 期望输出

- `deliverables/REQ002/output/` (完整项目代码)
- `deliverables/REQ002/de/code-report.md`

## 约束

- 所有文件路径操作必须经过安全沙箱校验
- 新增测试必须 mock aria2 RPC 和 subliminal 子进程，不依赖外部服务
- 测试覆盖：正常输入、非法 URL、路径穿越、aria2 连接失败、subliminal 未安装等场景
- 匹配已有代码风格（async handlers, json 响应格式）

## 参考 Skill

- `agents/de.md` TDD 流程

## 轮次信息

- 当前轮次: 1/5
- 上轮失败原因: N/A
- 失败报告路径: N/A

## 完成回报（执行角色必填 — 未填写则任务视为未完成）

- status: done
- output_files: ["deliverables/REQ002/output/src/nas_mcp_server/download_tools.py", "deliverables/REQ002/output/tests/test_download_tools.py", "deliverables/REQ002/output/tests/test_config.py", "deliverables/REQ002/output/tests/test_server.py", "deliverables/REQ002/output/tests/test_tools.py", "deliverables/REQ002/output/tests/conftest.py", "deliverables/REQ002/de/code-report.md"]
- read_files: ["deliverables/REQ002/plan-action.md", "deliverables/REQ001/output/src/nas_mcp_server/download_tools.py", "deliverables/REQ001/output/src/nas_mcp_server/tools.py", "deliverables/REQ001/output/src/nas_mcp_server/config.py", "deliverables/REQ001/output/src/nas_mcp_server/server.py", "deliverables/REQ001/output/src/nas_mcp_server/sandbox.py", "deliverables/REQ001/output/pyproject.toml", "deliverables/REQ001/output/tests/conftest.py", "deliverables/REQ001/output/tests/test_tools.py"]
- summary: "迁移 REQ001 代码至 REQ002/output，新增 9 个下载工具集成测试，全部 98 个测试通过"
- issues: "N/A"
