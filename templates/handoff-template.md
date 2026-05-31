<!-- 协议规则：
  1. 本文件一旦创建不可修改 — 重试时创建新文件（追加轮次后缀 R2, R3...）
  2. 白名单必须逐文件列出，禁止使用通配符（如 *.md）
  3. 执行角色仅可读取白名单中的文件，禁止读取其他任何文件
-->
---
handoff_id: "{REQ-ID}-{STEP-ID}-R{N}"
from: PM
to: "{BA|SA|DE|TE|UX}"
status: pending
task_type: "{需求分析|架构设计|编码实现|审计验证|测试用例设计|设计}"
output_type: "{output_type}"
tech_stack: "{language}/{package_manager}"
created_at: "{YYYY-MM-DDTHH:MM:SSZ}"
completed_at: ""
---

## 任务描述

{一段话描述本次任务的目标和范围}

## 输入文件（白名单）

- {file_path_1}
- {file_path_2}

## 期望输出

- `{output_path}`

## 约束

- {constraint_1}
- {constraint_2}

## 参考 Skill

- `skills/{skill-file}.md` Step {N}

## 轮次信息

- 当前轮次: {N}/5
- 上轮失败原因: {摘要或 N/A}
- 失败报告路径: {path 或 N/A}

## 修复上下文（仅修复轮次填写，R1 时删除本节）

- 失败特征: {错误类型 + 关键错误信息}
- 根因假设: {PM 基于 TE 报告的分析}
- 建议修复方向: {具体指导}
- 历史尝试: {前几轮尝试了什么，为什么没成功}

## 完成回报（由执行角色填写）

- status: {done | failed}
- output_files: ["{file_path}"]
- summary: "{一句话描述}"
- issues: "{错误信息或 N/A}"

> 回报格式示例见 `templates/handoff-examples.md`
