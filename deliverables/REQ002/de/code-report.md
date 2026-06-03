# Code Report: REQ002

## 概要

在 REQ001 NAS MCP Server 基础上完成 3 个下载工具的集成，并编写完整测试覆盖。

## 完成内容

### Task-1: 代码迁移

将 REQ001/output 完整代码复制到 REQ002/output，包含：
- `src/nas_mcp_server/download_tools.py` — 3 个下载工具实现
- `src/nas_mcp_server/config.py` — 含 aria2 配置字段
- `src/nas_mcp_server/tools.py` — 集成下载工具注册
- `pyproject.toml` — 含 aiohttp 依赖

代码变更：将 `aiohttp` 的 import 从函数内移至模块顶层，便于测试 mock。

### Task-2: 集成测试

新增 `tests/test_download_tools.py`，9 个测试用例覆盖：

| 测试 | 场景 |
|------|------|
| test_add_download_success | aria2 RPC 正常添加下载（mock aiohttp） |
| test_aria2_rpc_connection_failure | aria2 RPC 连接失败 |
| test_invalid_url_rejected | 非法 URL 拒绝 |
| test_download_dir_path_traversal | 下载目录路径穿越拒绝 |
| test_subliminal_success | subliminal 正常下载字幕（mock subprocess） |
| test_subliminal_not_installed | subliminal 未安装（FileNotFoundError） |
| test_subliminal_file_not_exists | subliminal 目标文件不存在 |
| test_status_single_gid | download_status 查询单个 GID |
| test_status_all_active | download_status 查询全部活跃任务 |

### 已有测试修复

- `test_config.py` — ServerConfig 调用补充 aria2_host/aria2_port/aria2_secret 参数
- `test_server.py` — 同上
- `test_tools.py` — 同上
- `conftest.py` — 新增 aiohttp 模块 mock

## 测试结果

```
98 passed in 0.08s
```

## 文件清单

- `deliverables/REQ002/output/src/nas_mcp_server/download_tools.py`
- `deliverables/REQ002/output/src/nas_mcp_server/config.py`
- `deliverables/REQ002/output/src/nas_mcp_server/tools.py`
- `deliverables/REQ002/output/src/nas_mcp_server/server.py`
- `deliverables/REQ002/output/src/nas_mcp_server/sandbox.py`
- `deliverables/REQ002/output/src/nas_mcp_server/__init__.py`
- `deliverables/REQ002/output/src/nas_mcp_server/__main__.py`
- `deliverables/REQ002/output/pyproject.toml`
- `deliverables/REQ002/output/tests/test_download_tools.py` (新增)
- `deliverables/REQ002/output/tests/test_config.py` (修改)
- `deliverables/REQ002/output/tests/test_server.py` (修改)
- `deliverables/REQ002/output/tests/test_tools.py` (修改)
- `deliverables/REQ002/output/tests/conftest.py` (修改)
