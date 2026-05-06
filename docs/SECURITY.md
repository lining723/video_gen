# 智能视频生成平台 Security

## Core Practices

### I. Authentication Mechanisms

业务接口默认启用 `X-API-Key` 鉴权。健康检查端点 (`/healthz`, `/readyz`) 和媒体服务 (`/media/`) 豁免鉴权。

### II. Authorization Patterns

访问应遵循最小权限原则，仅限于所需的最小范围。

### III. Encryption Practices

敏感数据在传输和存储时应使用批准的机制保护。

### IV. Secrets Protection

所有敏感配置、存储密钥、模型访问凭据不得暴露到前端或提交到仓库。

## Fixed Rules

- **Least Privilege**: 访问控制必须遵循最小权限原则。
- **Secrets Protection**: 密钥绝不能提交到源代码管理。
- **Dependency Audits**: 依赖项应定期扫描已知漏洞。
- **API Key Required**: 所有业务 API 请求必须携带有效的 `X-API-Key` 头。

## Governance

- 安全要求适用于源代码、生成的资产、依赖项和操作工作流。
- 可疑的安全事件应被报告、跟踪和紧急解决。
- 安全控制的例外需要明确审查和记录的理由。

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
