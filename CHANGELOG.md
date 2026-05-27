# Changelog

## [0.3.0] - 2026-05-27

框架泛化改造：从 Web/JavaScript 专用升级为格式无关的通用研发执行框架。

### 核心新增

- **output_type 体系**: 新增产出类型概念（web-app/backend-api/cli-tool/data-pipeline/infrastructure/documentation/ppt/library/custom），与 mode 正交，驱动全流程适配
- **test_strategy 机制**: TE 验证方式由 test_strategy 参数驱动（e2e/unit/integration/smoke/manual/none），替代原有的 browser_available 二分逻辑
- **多语言环境检测**: 支持 Python/Node.js/Go/Rust/Java 自动检测（语言、包管理器、测试框架、构建工具、lint 工具）
- **Designer 角色**: 新增泛化设计师角色（agents/designer.md），根据 output_type 产出不同设计制品

### 流程变更

- **mh-clarify**: 新增"产出类型选择"步骤（Step 3），环境预检泛化为多语言检测
- **mh-apply**: TE 派发逻辑改为 test_strategy 路由
- **mh-archive**: ARC-3 步骤增加 output_type 感知归档策略
- **mh-ppt**: 重构为主流程补充规则，/mh-ppt 作为 output_type=ppt 的快捷入口

### 技术改进

- **dev-test.md**: 完全重写，按 tech_stack.language 路由测试/lint/构建命令
- **verify.sh**: check_b() 增加 output_type 和 test_strategy 感知，动态校验产出物
- **handoff 模板**: 新增 output_type 和 tech_stack 字段
- **.state.md schema**: 新增 output_type、tech_stack（对象）、test_strategy 字段

### 角色变更

- 新增 Designer 角色（agents/designer.md）
- UX 角色标记为 DEPRECATED（agents/ux.md），兼容已有 handoff
- 角色隔离规则更新为六角色（PM/BA/SA/DE/TE/Designer）

### 命名变更

- /pdt-init → /mh-clarify
- /pdt-propose → /mh-propose
- /pdt-apply → /mh-apply
- /pdt-archive → /mh-archive
- /pdt-run → /mh-run
- /ppt-dev → /mh-ppt

---

## [0.2.0] - 2026-05-20

十项结构性优化，修复三轮实际使用（REQ001-REQ003）中暴露的问题。

### 基础设施修复

- **Handoff 模板迁移**: `deliverables/handoffs/.handoff-template.md` → `templates/handoff-template.md`，消除运行时目录与模板混放
- **verify.sh 重写**: 支持 REQ-ID 参数化、mode 感知检查、修复 macOS bash 3.2 兼容性
- **check-harness.sh 修复**: 移除旧的运行时目录检查，新增 templates/ 检查
- **baseline.sh 修复**: 路径适配 REQ-ID 隔离模式

### 路径一致性

- 所有 agent 定义文件（ba/sa/de/te/pm.md）路径统一加 `{REQ-ID}/` 前缀
- `.gitignore` 精简，移除旧扁平路径规则，新增 MCP 自动生成目录屏蔽
- README.md 路径表更新

### Skill 功能增强

- **mh-run**: 新增 fast 模式连续流（propose→apply→archive 自动串联，仅一个人工确认点）
- **mh-archive**: 新增变更归档 Merge 策略（REQ-ID 标注、段落替换、DEPRECATED 标记）
- **mh-clarify**: 新增环境预检（Node.js 版本、浏览器可用性检测，写入 .state.md env 字段）
- **mh-propose**: standard 模式 SA handoff 约束新增需求映射简表要求
- **mh-apply**: 新增浏览器降级逻辑（env.browser_available=false 时跳过 E2E，标注 DEGRADED）

### Agent 定义更新

- **te.md**: E2E 从硬性阻塞改为降级条件（优先真实浏览器，不可用时降级并标注）
- **sa.md**: 输出格式新增"需求映射简表"（standard 模式必填）

### 文档精简

- **docs/workflow.md**: 834 行 → 288 行，删除与 skills/*.md 重复的详细执行序列，替换为索引表
- **docs/design.md**: 新增 §8-§12（执行模式、环境预检与降级、归档 Merge 策略、Token 节流、日志规范）
- **CLAUDE.md**: 新增项目描述、角色速查表、命令速查表，保持 < 80 行

### 日志与恢复

- 统一日志格式: `[{timestamp}] [{角色}] {事件描述}`，时间戳优先 `date -u`，序号兜底
- 断点恢复增强: .state.md 新增 `last_updated` 字段，pending + 超 30 分钟自动重新派发

---

## [0.1.0] - 2026-05-18

初始框架发布。

- 四层防线架构（Rules → Skills → Agents+Workflow → Scripts+人工）
- 五角色体系（PM/BA/SA/DE/TE）
- 四阶段流程（init → propose → apply → archive）
- 三种执行模式（fast/standard/full）
- REQ-ID 隔离的 deliverables 目录结构
- Handoff 文件协议
- 跨平台支持（Claude Code / Cline）
