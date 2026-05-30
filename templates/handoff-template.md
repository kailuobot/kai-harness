---
handoff_id: "{REQ-ID}-{STEP-ID}-R{N}"
from: PM
to: "{BA|SA|DE|TE|UX}"
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
  - `done`: 任务成功完成，所有期望输出已生成
  - `failed`: 任务失败，无法在当前轮次内完成（附 issues 说明原因）
- output_files: ["{file_path_1}", "{file_path_2}"]
  - 实际生成的文件路径列表（必须与"期望输出"对应）
- summary: "{一句话描述完成情况或失败原因}"
- issues: "{具体错误信息或阻塞原因，无问题时填 N/A}"

示例（成功）：
```
- status: done
- output_files: ["deliverables/REQ001/sa/design.md"]
- summary: "架构设计完成，含 3 个 Task 和需求映射表"
- issues: "N/A"
```

示例（失败）：
```
- status: failed
- output_files: []
- summary: "lint 检查失败，3 次自修未能解决"
- issues: "ESLint error: no-unused-vars in src/utils.ts:42, 自动修复引入新错误"
```

## 轮次信息

- 当前轮次: {N}/5
- 上轮失败原因: {摘要或 N/A}
- 失败报告路径: {path 或 N/A}
