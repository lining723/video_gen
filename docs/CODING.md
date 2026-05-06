# 智能视频生成平台 Coding Standards

## Core Conventions

### I. Naming Conventions

使用清晰、一致的名称，与周围语言和仓库约定匹配。

### II. Error Handling

以保持可调试性和明确失败路径的方式处理错误。

### III. Logging Standards

使用结构化、有目的的日志记录，帮助操作人员和开发人员理解系统行为。

### IV. 架构边界

- 缓存目录、对象存储/文件存储、数据库元数据必须保持三层职责边界
- 字幕、配音、视频三轨在拼接阶段必须保持时间对齐

## Fixed Rules

- **Style Guides**: 遵循每个服务已使用的语言特定风格指南。
  - 后端：Python（使用内置 `ThreadingHTTPServer`，非 Flask/FastAPI）
  - 前端：Node.js + TypeScript（Next.js 风格页面路由）
- **Formatting Tools**: 一致使用 linter 和 formatter。
- **Atomic Commits**: 保持提交专注和范围明确，尽可能限定在单一连贯变更。

## Governance

- 在引入新抽象之前优先使用仓库中已建立的模式。
- 代码审查应检查正确性、样式和足够的验证。
- 分支和提交实践应保持 `main` 可部署，变更易于审查。

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
