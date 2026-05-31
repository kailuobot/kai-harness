# 金标准示例：技术设计方案

> 场景：用户注册功能。展示技术决策有理由、对照表完整、Task 拆分合理。

---

# 技术设计方案

## 1. 架构概述

采用分层架构实现用户注册模块：Controller → Service → Repository。密码哈希在 Service 层处理，邮件发送通过异步队列解耦，避免阻塞注册响应。

## 2. 关键技术决策

| 决策点 | 选择 | 理由 | 备选方案 |
|--------|------|------|---------|
| 密码哈希 | bcrypt (cost=12) | 业界标准，抗 GPU 暴力破解，cost=12 在现代硬件上约 250ms | argon2（更新但库成熟度不足）|
| 邮件发送 | 异步队列（Bull/Celery） | 解耦注册响应，避免 SMTP 超时影响用户体验 | 同步发送（简单但阻塞） |
| 输入校验 | Controller 层 + zod/pydantic | 类型安全，错误信息结构化，可复用 | 手动 if/else（易遗漏） |
| Token 生成 | UUID v4 | 足够随机，无需加密，24h 过期降低碰撞风险 | JWT（过重，确认场景不需要 payload） |

## 3. 需求-技术对照表

| 需求ID | 需求描述 | 技术实现方案 | 对应 Task | 验证方式 |
|--------|---------|-------------|-----------|---------|
| FR-1 | 邮箱注册 | POST /api/register → validate → hash → save → 201 | Task-1, Task-2 | 单元测试 + 集成测试 |
| FR-2 | 密码安全存储 | bcrypt.hash(password, 12) 后存入 users.password_hash | Task-2 | 单元测试：验证 hash 格式 |
| FR-3 | 注册确认邮件 | 注册成功后 enqueue(sendConfirmEmail) → 异步消费 | Task-3 | 集成测试：mock 队列验证入队 |
| NFR-1 | P95 < 500ms | 邮件异步化，DB 索引 email 字段 | Task-1 | 负载测试（可选） |

## 4. 时序图

```
User        Controller      Service         Repository      Queue
 |              |              |                |              |
 |--POST /register-->|         |                |              |
 |              |--validate--->|                |              |
 |              |              |--hashPassword->|              |
 |              |              |<--hash---------|              |
 |              |              |--createUser--->|              |
 |              |              |<--user---------|              |
 |              |              |--enqueue(email)-------------->|
 |              |<--201--------|                |              |
 |<--201--------|              |                |              |
 |              |              |                |     (async)  |
 |              |              |                |<--consume----|
 |              |              |                |--sendEmail-->SMTP
```

## 5. Tasks 清单

| Task ID | 描述 | 输入 | 输出 | 依赖 | 验证方式 | 预估复杂度 |
|---------|------|------|------|------|---------|-----------|
| Task-1 | 注册接口骨架（Controller + 路由 + 输入校验） | 无 | src/controllers/auth.ts, src/routes/auth.ts, src/validators/register.ts | [deps: none] | 单元测试：校验通过/拒绝 | 低 |
| Task-2 | 用户 Service + Repository（含密码哈希） | Task-1 的接口定义 | src/services/user.ts, src/repositories/user.ts | [deps: Task-1] | 单元测试：创建用户、重复邮箱409、hash格式 | 中 |
| Task-3 | 确认邮件异步发送（队列 + consumer） | Task-2 的用户创建事件 | src/queues/email.ts, src/consumers/confirm-email.ts | [deps: Task-2] | 集成测试：mock 队列验证入队和消费 | 中 |
