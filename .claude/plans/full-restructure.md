# 全面重构计划：让实现与设计完全对齐

## 目标
消除 design.md 与实际 skills/templates 之间的所有 GAP，让框架"说到做到"。

---

## Step 1: SR Gate 标准化（HIGH）

在每个 SR 审批节点中，将 design.md §4.5 的通过标准写成明确的 checklist。

**mh-propose.md (SR1)**：
```
SR1 通过标准:
- [ ] 需求规格覆盖所有 Proposal 要点
- [ ] 设计方案覆盖所有需求（对照表无空行）
- [ ] 每个 Task 有依赖标注和验证方式
- [ ] 计划可执行（无循环依赖、粒度合理）
```

**mh-apply.md (SR2)**：
```
SR2 通过标准:
- [ ] 所有 Task 通过 TE 审计（无 Critical/Major）
- [ ] 代码质量达标（dev-test=PASS, post-verify=PASS）
- [ ] 无 TODO/FIXME 残留
```

**mh-apply.md (SR3)**：
```
SR3 通过标准:
- [ ] 全量测试通过
- [ ] 需求覆盖无遗漏（TE 报告中覆盖率 = 100%）
- [ ] 无 Critical/Major 缺陷
- [ ] 回归测试通过
```

**mh-archive.md (SR4)**：
```
SR4 通过标准:
- [ ] 归档完整（spec/ 和 output/ 非空）
- [ ] 产出物可用（output/ 中文件与 plan-action.md 对应）
- [ ] 文档一致（spec/ 内容与实际实现匹配）
```

涉及文件：skills/mh-propose.md, skills/mh-apply.md, skills/mh-archive.md

## Step 2: PM 调度协议标准化（MEDIUM）

创建 `templates/pm-dispatch-protocol.md`，定义 PM 调度循环的标准模板 + 停止条件清单。各 skill 引用此文件而非各自重复。

内容：
- PM 调度循环 8 步标准流程
- 停止条件完整清单（4 类）
- 质量门禁执行指引（何时执行、怎么执行）
- 心跳打印规范

涉及文件：templates/pm-dispatch-protocol.md（新建）

## Step 3: 六条铁律强化（HIGH）

**Law ①** "严格顺序"的澄清：mode 裁剪是"跳过某些步骤"而非"打乱顺序"。在 CLAUDE.md 中已有，但需在 skills 的 mode 裁剪处明确标注"跳过≠乱序"。

**Law ⑤** "下游不改上游"：在所有 agent 的禁止事项中统一添加明确表述。当前 agents 已有"禁止修改需求规格或设计方案"等，但缺少统一的"下游不改上游"原则声明。

涉及文件：agents/ba.md, agents/sa.md, agents/de.md, agents/te.md, agents/ux.md（微调禁止事项措辞）

## Step 4: 质量门禁操作化（MEDIUM）

在 skills 中 PM 执行质量门禁的位置，增加明确的执行指引：
- "打开 agents/pm.md 中对应角色的质量门禁清单"
- "逐项检查，不满足则驳回"
- "驳回时在新 handoff 中列出未通过的检查项"

当前 skills 只写了"执行质量门禁（见 agents/pm.md）"，缺少 HOW。

涉及文件：skills/mh-apply.md, skills/mh-propose.md（微调措辞）

## Step 5: 决策上下文卡补全（MEDIUM）

**SR1**（mh-propose.md）：当前 SR1 呈现格式过于简略，补充为完整的决策上下文卡。
**SR4**（mh-archive.md）：当前 full 模式 SR4 缺少质量状态，补充。

涉及文件：skills/mh-propose.md, skills/mh-archive.md

## Step 6: Handoff 模板完善（LOW）

在 handoff-template.md 中增加协议规则提醒（作为注释）：
- 不可修改提醒
- 白名单禁止通配符提醒

涉及文件：templates/handoff-template.md

## Step 7: mh-run 错误处理补全（MEDIUM）

在 mh-run.md 中增加：
- 各阶段 SubAgent 失败时的处理逻辑
- 修复循环与自动推进的交互规则
- 停止条件完整枚举

涉及文件：skills/mh-run.md

## Step 8: 根因分析模板（MEDIUM）

在 templates/ 中增加根因分析的示例，让 PM 有参考：
- 2-3 个典型场景的根因分析示例

涉及文件：templates/examples/repair-context-example.md（新建）

## Step 9: 文档一致性设计（参考 ref-design §11.1）

吸收 ref-design 的"分布式设计文档"理念和三层一致性保障机制。

### 9.1 设计哲学

**契约即文档、模板即标准、脚本即验证。**

项目采用"分布式设计文档"策略——设计意图分散在 agents（角色契约）、skills（操作规程）、templates（格式标准）中，design.md 只是概述索引。

### 9.2 权威源映射表

创建 `docs/source-of-truth.md`，明确每个设计概念的权威文件：

| 设计概念 | 权威源 | 辅助参考 |
|---------|--------|---------|
| 角色职责与禁止事项 | agents/*.md | design.md §3 |
| 流程步骤与裁剪 | skills/mh-*.md | design.md §4 |
| 质量门禁标准 | agents/pm.md | design.md §7 |
| 状态 schema | templates/state-template.md | design.md §4.4 |
| Handoff 协议 | templates/handoff-template.md | design.md §5.3 |
| 日志格式 | templates/logging-standard.md | — |
| 硬校验规则 | scripts/*.sh | design.md §7.4 |
| output_type 体系 | CLAUDE.md §7 | design.md §10 |

### 9.3 三层一致性保障

```
第一层：结构化约束（预防）
  ├─ check-harness.sh — 框架文件完整性自检
  ├─ Handoff 协议 — 角色间信息传递必须结构化
  └─ 模板约束 — 产出物必须按模板格式

第二层：自动检测（发现）
  ├─ verify.sh A/B/C/D — 产出物校验
  ├─ source-of-truth.md — 权威源映射（人工查阅）
  └─ design.md 权威声明 — 冲突时以 skills/agents 为准

第三层：人工评审（兜底）
  ├─ SR1-4 审批节点
  ├─ PM 质量门禁
  └─ 用户最终确认
```

### 9.4 在 design.md 中新增 §12 文档一致性

在 design.md 末尾新增一个章节，描述上述设计。

涉及文件：
- docs/source-of-truth.md（新建）
- docs/design.md（新增 §12）

---

## 不改动的
- CLAUDE.md（不增加大小）
- agents/pm.md（质量门禁已完善）
- 流程顺序和审批节点数量
- scripts/*.sh
