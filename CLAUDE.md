# 全局纪律（Rules）

本文件是所有 Agent 角色的最高约束，任何 Skill 或 Agent 定义不得与此冲突。

---

## 1. 流程纪律

- 严格按 init → propose → apply → archive 顺序执行，禁止跳步
- 每步结束必须返回 PM，PM 检查通过后才启动下一步
- 禁止跳过人工审批节点（SR1/SR2/SR3/SR4）
- PM 每次调度前必须打印心跳：`[PM] {动作描述}`
- /pdt-run 模式下允许阶段间自动推进，但阶段内审批节点仍禁止跳过

## 2. 角色隔离

- 五个角色（PM/BA/SA/DE/TE）职责严格分离，禁止越权
- 角色间信息传递必须经 PM 中转，通过 handoff 文件实现
- 非 PM 角色仅读取 handoff 白名单中的文件
- 非 PM 角色禁止引用对话历史中其他角色的推理或产出
- 非 PM 角色完成后仅报告文件路径，不展开产物内容

## 3. 产物保护

- 禁止修改上游制品（已交付的 handoff、已审批的 baseline）
- handoff 文件不可修改，重试创建新文件（追加轮次后缀）
- 归档后的 spec/ 文件仅通过 CHANGE 模式的 merge 流程修改

## 4. 自检纪律

- 任何文件写入后必须验证文件存在且非空
- DE 编码后必须执行 dev-test skill
- TE 审计必须使用真实浏览器执行 E2E 测试
- 交付判定依赖脚本退出码，不依赖 Agent 自述

## 5. 断点恢复

- PM 恢复时仅依据 .state.md 和 handoff 文件状态，禁止依赖对话历史
- .state.md 是流程状态的唯一真相源

## 6. 平台适配

- Claude Code 环境：BA/SA/DE/TE 通过 SubAgent 执行（物理隔离）
- Cline 环境：通过文件协议 + 行为约束实现角色隔离（逻辑隔离）
- 两种模式共享同一套 handoff 格式和 skill 内容
