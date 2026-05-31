# 权威源映射表（Source of Truth）

本文件定义每个设计概念的权威文件。当多个文件描述同一概念时，以权威源为准。

---

## 核心映射

| 设计概念 | 权威源 | 辅助参考 |
|---------|--------|---------|
| 全局纪律（流程/隔离/保护） | CLAUDE.md | docs/design.md §4.1 |
| 角色职责与禁止事项 | agents/*.md | docs/design.md §3 |
| 角色质量标准与思考框架 | agents/*.md | — |
| 流程步骤与 mode 裁剪 | skills/mh-*.md | docs/design.md §4 |
| PM 调度协议 | templates/pm-dispatch-protocol.md | docs/design.md §4.1 |
| PM 质量门禁清单 | agents/pm.md "质量门禁"节 | skills 中引用 |
| SR Gate 通过标准 | skills/mh-propose.md, mh-apply.md, mh-archive.md | docs/design.md §4.5 |
| 状态 schema | templates/state-template.md | docs/design.md §4.4 |
| Handoff 协议与格式 | templates/handoff-template.md | docs/design.md §5.3 |
| 日志格式 | templates/logging-standard.md | — |
| 修复收敛机制 | skills/mh-apply.md "修复循环"节 | docs/design.md §7.3 |
| 硬校验规则 | scripts/*.sh | docs/design.md §7.4 |
| output_type 体系 | CLAUDE.md §7 | docs/design.md §10 |
| PPT 补充规则 | skills/mh-ppt.md | docs/design.md §11 |
| 金标准示例 | templates/examples/*.md | — |
| 产出结构参考 | templates/output-guides/*.md | — |

---

## 三层一致性保障

```
第一层：结构化约束（预防）
  ├─ check-harness.sh — 框架文件完整性自检
  ├─ Handoff 协议 — 角色间信息传递必须结构化
  ├─ 模板约束 — 产出物必须按模板格式
  └─ PM 调度协议 — 标准化调度行为

第二层：自动检测（发现）
  ├─ verify.sh A/B/C/D — 产出物校验（退出码驱动）
  ├─ 本文件 — 权威源映射（冲突时查阅）
  └─ design.md 权威声明 — "如有冲突以 skills/agents 为准"

第三层：人工评审（兜底）
  ├─ SR1-4 审批节点（决策上下文卡辅助判断）
  ├─ PM 质量门禁（内容级验收）
  └─ 用户最终确认
```

---

## 冲突解决规则

1. **skills/*.md vs docs/design.md** → 以 skills 为准（skills 是执行权威）
2. **agents/*.md vs docs/design.md** → 以 agents 为准（agents 是角色契约）
3. **CLAUDE.md vs 其他所有文件** → 以 CLAUDE.md 为准（最高约束）
4. **templates/ vs skills/** → templates 定义格式，skills 定义何时使用
5. **scripts/*.sh vs Agent 自述** → 以 scripts 退出码为准（硬校验 > 自述）

---

## 维护规则

- 修改 skills/agents 后，检查 design.md 对应章节是否需要同步
- 新增模板文件后，更新本文件的映射表
- 新增 scripts 检查项后，更新 design.md §7.4
- 发现映射表与实际不符时，以实际文件为准，更新映射表
