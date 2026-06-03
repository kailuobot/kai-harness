# 执行计划: REQ002

## 概述

在 REQ001 已有 NAS MCP Server 基础上新增 3 个下载工具。代码已在本次会话中预先实现，需要将其从 REQ001/output 迁移到 REQ002/output 并完成集成验证。

## Tasks

- Task-1: 迁移 REQ001 完整代码到 REQ002/output，包含新增的 download_tools.py 及已修改的 config.py/tools.py/pyproject.toml [deps: none]
- Task-2: 编写 download 工具的集成测试（test_download_tools.py），覆盖 aria2 RPC mock 测试、subliminal 调用 mock 测试、路径沙箱校验 [deps: Task-1]

## 批次计算

- Batch-1: Task-1（代码迁移）
- Batch-2: Task-2（测试，依赖 Task-1 的代码）

## 验证方式

| Task | 验证方式 |
|------|---------|
| Task-1 | 语法检查通过 + 模块导入成功 |
| Task-2 | pytest 全部通过 |
