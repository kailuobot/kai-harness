# TE 轻量审计报告

## 结论: PASS

## 工程检查
- 语法检查: PASS（15 个 .py 文件全部通过 ast.parse）
- 测试执行: 98 passed / 0 failed

## 关键路径抽查
- download_movie: URL 校验逻辑正确，仅允许 http://、https://、magnet: 三种协议。aria2 RPC 调用通过 aiohttp.ClientSession.post 发送 JSON-RPC，token 以 "token:{secret}" 格式传递，无拼接注入风险。下载目录经 validate_path 沙箱校验，路径遍历被拒绝。
- download_subtitle: 使用 asyncio.create_subprocess_exec 列表形式调用 subliminal，无 shell=True，无字符串拼接，命令注入风险为零。路径先经 validate_path(must_exist=True) 校验，确认文件存在且在沙箱内后才传给子进程。路径沙箱有效。
- download_status: 返回结构化 JSON，包含 gid/status/progress/totalLength/completedLength/downloadSpeed/files 字段。单任务和批量查询格式一致，合理。

## 测试覆盖
- download_movie: 4 个测试（正常添加、RPC 连接失败、非法 URL 拒绝、目录路径遍历拒绝）— 正常+异常路径完整
- download_subtitle: 3 个测试（正常下载、subliminal 未安装、文件不存在）— 正常+异常路径完整
- download_status: 2 个测试（单 GID 查询、全量活跃任务查询）— 正常路径覆盖

## 问题列表（如有）
- N/A
