# 智能视频生成平台 Reliability

## Core Practices

### I. Fault Tolerance

设计变更时确保故障被隔离，恢复路径保持清晰。镜头级失败不应破坏整体项目推进。

### II. Degradation Strategy

优先采用优雅降级和回滚友好的变更，而非全有或全无的行为。当模型或云端服务不可用时，通过 `ALLOW_MODEL_FALLBACK=true` 自动回退到占位输出，保证联调不断链。

### III. Monitoring Patterns

关键工作流应暴露有助于检测故障和确认健康运行的信号：
- 项目 ID、镜头 ID、任务 ID、模型版本、缓存命中情况
- 关键错误摘要

### IV. Graceful Startup and Shutdown

初始化和关闭路径应避免使系统处于部分或不一致状态。

## Fixed Rules

- **Availability Target**: 可靠性决策应支持 99.9% 服务可用性目标。
- **Rollback Readiness**: 部署应保持实用的回滚路径。
- **Incident Response**: 可靠性事件必须被检测、分类、缓解和审查。
- **Async Task Tracking**: 视频生成、主体出图、拼接等长耗时工作必须通过可追踪的异步任务执行，支持状态跟踪、超时处理和重试。

## Governance

- 可靠性指导应在设计、实现、部署和事件后续期间考虑。
- 降低可观测性或回滚信心的变更需要明确审查。
- 事件后的学习应反馈到工具、自动化或文档中。

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
