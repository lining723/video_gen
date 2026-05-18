# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

智能视频生成平台——前端 Node.js + TypeScript，后端 Python，实现从创意输入到成片交付的完整业务闭环。

## 常用命令

```bash
# 启动后端 (http://127.0.0.1:8100)
make backend

# 启动前端 (http://127.0.0.1:3100)
make frontend

# 运行测试
make test

# Docker 部署
make docker-up    # 启动 backend + frontend + minio
make docker-down  # 停止并清理
```

## 架构要点

### 后端结构 (Python)

- `backend/src/api/` - HTTP 路由入口，使用内置 `ThreadingHTTPServer`（非 Flask/FastAPI）
- `backend/src/api/routes/` - 各业务模块路由处理器
- `backend/src/repositories/` - SQLite 数据访问层，迁移文件在 `migrations/`
- `backend/src/schemas/` - 数据模型定义，`states.py` 定义项目状态机
- `backend/src/services/` - 业务逻辑层
- `backend/src/orchestrators/` - 异步流水线编排（主体生成、渲染、合成）
- `backend/src/integrations/` - 外部服务集成（DeepSeek、DashScope、Ollama）
- `backend/src/workers/` - 后台任务队列

### 前端结构 (Node.js + TypeScript)

- `frontend/src/pages/` - Next.js 风格页面路由
- `frontend/src/modules/` - 页面级组件（按业务功能划分）
- `frontend/src/services/` - API 调用封装
- `frontend/src/stores/` - 状态管理
- `frontend/src/hooks/` - 自定义 Hooks

### 核心业务流程

项目状态流转（定义在 `backend/src/schemas/states.py`）：

```
idea_submitted → scene_generated → scene_reviewing → scene_approved
→ storyboard_generated → storyboard_reviewing → storyboard_approved
→ subject_generating → subject_ready → video_rendering
→ compositing → completed
```

**关键门禁**：场景审核和分镜审核不可跳过，必须显式通过。

### 存储层

- **数据库**：SQLite，通过 `migrations/*.sql` 自动迁移
- **对象存储**：双模式适配
  - `filesystem`：本地文件系统
  - `s3`：S3/MinIO/OSS 兼容对象存储
- 配置通过 `OBJECT_STORE_PROVIDER` 环境变量切换

### AI 模型集成

- **文本生成**：DeepSeek `deepseek-reasoner`（场景设计、分镜脚本）
- **图片生成**：阿里云 DashScope `wan2.7-image`（主体图）
- **视频生成**：阿里云 DashScope `wan2.7-i2v`（镜头视频）
- 统一网关：`backend/src/integrations/ai_gateway.py`

## 环境配置

在仓库根目录 `.env` 维护配置。关键变量：

```bash
# 端口
APP_PORT=8100
FRONTEND_PORT=3100

# 鉴权
APP_API_KEY=dev-secret-key-change-me

# 存储
OBJECT_STORE_PROVIDER=filesystem  # 或 s3

# DeepSeek
TEXT_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_TEXT_MODEL=deepseek-reasoner

# DashScope
DASHSCOPE_API_KEY=你的密钥
```

## 开发规范

### 提交代码

当用户请求提交代码时，执行 `/adk:commit` 进行规范化提交。

### 代码一致性

实现功能时优先参考现有代码库中的模式、编码风格和架构设计。

### 知识检索

遇到陌生概念时，优先使用 `tiksearch` MCP 检索内部文档，使用 `lark-docs` MCP 读取飞书文档。

### 人工审核门禁

场景设计和分镜审核是强制性门禁，实现不得绕过 review 环节直接进入下游。

### 异步任务处理

视频生成、主体出图、拼接等长耗时操作必须通过可追踪的异步任务执行，支持状态跟踪、超时处理和重试。

## 测试

测试文件位于 `backend/tests/`，覆盖：
- 健康检查与鉴权验证
- 完整业务流水线验证
- 模型回退链路验证
