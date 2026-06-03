# Proposal: NAS MCP Server 下载功能扩展

## 背景与目标

在 REQ001 已交付的 NAS MCP Server（7个文件操作工具）基础上，新增 3 个下载相关 MCP 工具，使 AI 客户端能够通过 MCP 协议控制 NAS 上的电影下载和字幕获取。

增量开发，基于 deliverables/REQ001/output/ 已有代码。

## 功能模块

- download_movie: 通过 aria2 JSON-RPC 添加下载任务，支持 HTTP/HTTPS URL 和磁力链接
- download_subtitle: 通过 subliminal CLI 为指定视频文件下载中文字幕
- download_status: 查询 aria2 下载任务进度（单个 GID 或全部活跃任务）

## 范围

- 包含:
  - aria2 JSON-RPC 客户端封装
  - subliminal CLI 调用封装
  - 3 个 MCP 工具注册到现有 tool router
  - 配置扩展（ARIA2_HOST, ARIA2_PORT, ARIA2_SECRET）
  - aiohttp 依赖添加
- 不包含:
  - 电影资源搜索功能
  - aria2 进程管理/安装
  - subliminal 安装自动化
  - Web UI

## 关键约束

- 所有文件路径操作必须经过已有安全沙箱校验
- aria2 RPC 调用使用 aiohttp 异步客户端
- subliminal 通过子进程调用，不引入为 Python 依赖
- 下载目标目录受 root_dir 沙箱限制

## 参考资料

- REQ001 已有代码: deliverables/REQ001/output/
- aria2 JSON-RPC 文档
- subliminal CLI 用法
