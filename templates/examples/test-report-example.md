# 金标准示例：测试报告

> 场景：Task-1 注册接口审计。展示需求覆盖分析、明确结论、失败项完整复现信息。

---

# 测试报告

## 概要

- 执行时间: 2026-05-28T14:30:00Z
- test_strategy: integration
- 总用例数: 14
- 通过: 13
- 失败: 1
- 阻塞: 0
- 需求覆盖率: 3/4（FR-1 部分覆盖，FR-2 待 Task-2，FR-3 待 Task-3，NFR-1 待负载测试）

## 结论: FAIL

Task-1 存在 1 个 Major 缺陷：密码长度上限校验未生效（接受 65 字符密码）。

## 需求覆盖分析

| 需求ID | 验证状态 | 对应用例 | 备注 |
|--------|---------|---------|------|
| FR-1 | 部分覆盖 | TC-1~TC-8 | 接口骨架已验证，service 为 mock |
| FR-2 | 未覆盖 | — | 待 Task-2 实现后验证 |
| FR-3 | 未覆盖 | — | 待 Task-3 实现后验证 |
| NFR-1 | 未覆盖 | — | 待全部实现后负载测试 |

## 失败详情

### FAIL-1: 密码长度上限校验未生效

- 严重程度: Major
- 关联需求: FR-1（密码规则：8-64 字符）
- 复现步骤:
  1. 发送 POST /api/register
  2. 请求体: `{"email": "test@example.com", "password": "Aa1" + "x".repeat(62)}`（共 65 字符）
  3. 观察响应
- 期望结果: 返回 422，错误信息包含 "password: max_length_64"
- 实际结果: 返回 201，账户创建成功
- 日志/截图: `tests/controllers/auth.test.ts:45` 断言失败

## 环境信息

- 语言: javascript (Node.js 20.x)
- 测试框架: vitest
- 运行平台: macOS Darwin 25.5.0
