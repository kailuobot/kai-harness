---
handoff_id: "{REQ-ID}-{STEP-ID}-R{N}"
from: PM
to: "{BA|SA|DE|TE|Designer}"
status: pending
task_type: "{需求分析|架构设计|编码实现|审计验证|测试用例设计|设计}"
output_type: "{web-app|backend-api|cli-tool|data-pipeline|infrastructure|documentation|ppt|library|custom}"
tech_stack: "{language}/{package_manager}"
created_at: "{YYYY-MM-DDTHH:MM:SSZ}"
completed_at: ""
---

## 任务描述

{一段话描述本次任务的目标和范围}

## 输入文件（白名单）

仅以下文件可被读取，禁止读取白名单外的任何文件：

- {file_path_1}
- {file_path_2}

## 期望输出

- 路径: `{output_path}`
- 格式: {模板引用或格式描述}

## 约束

- {constraint_1}
- {constraint_2}

## 参考 Skill

- `skills/{skill-file}.md` 中的 {Step N}

## 完成回报（由执行角色填写）

- status: {done | failed}
- output_files: []
- summary: ""
- issues: ""

## 轮次信息

- 当前轮次: {N}/5
- 上轮失败原因: {摘要或 N/A}
- 失败报告路径: {path 或 N/A}
