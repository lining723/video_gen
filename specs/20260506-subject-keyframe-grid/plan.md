# Implementation Plan: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/20260506-subject-keyframe-grid/spec.md`

## Summary

实现关键帧动态网格生成功能，根据镜头时长自动计算网格大小（2×2、3×3或4×4），为每个镜头生成对应数量的关键帧图片。核心功能包括：网格大小计算逻辑、关键帧生成流水线、动态网格前端展示、失败处理与重试机制。该功能让用户在长耗时的视频渲染前预览镜头效果，提前发现问题并调整。

## Technical Context

**Language/Version**: Python 3.11+ (后端), TypeScript 5.x (前端)
**Primary Dependencies**:
- 后端：内置 ThreadingHTTPServer, SQLite, DashScope SDK
- 前端：Next.js, React, Ant Design

**Storage**: SQLite（元数据） + 文件系统/S3（图片存储）
**Testing**: pytest (后端), Jest + React Testing Library (前端)
**Target Platform**: Linux/macOS server (后端), 现代浏览器 (前端)
**Project Type**: Web application (前后端分离)
**Performance Goals**:
- 单个关键帧生成时间 < 20秒
- 整个网格生成时间 < 5分钟（最长16帧）
- 前端加载时间 < 2秒

**Constraints**:
- AI服务API限流：DashScope 并发限制
- 存储空间：每个项目最多数百MB关键帧图片
- 网络带宽：图片上传下载

**Scale/Scope**:
- 单项目：平均5-10个镜头，每个镜头4-16帧
- 并发：支持多项目同时生成

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. 产品闭环优先

✅ **通过** - 关键帧生成明确服务于"场景设计 → 分镜审核 → 主体出图 → 镜头渲染 → 最终拼接 → 成片交付"闭环中的"主体出图"和"镜头渲染"阶段。用户可在视频渲染前预览镜头效果，提前发现并修正问题，减少返工。

### II. 人工审核门禁不可跳过

✅ **通过** - 本功能不涉及场景设计审核和分镜审核门禁。关键帧生成在分镜审核通过后、视频渲染前进行，不绕过任何审核环节。

### III. 契约优先与跨端一致性

✅ **通过** - 已定义清晰的数据模型（KeyframeGrid、KeyframeFrame）和API接口契约。前后端术语一致（grid_type、frame_count、time_ratio等），状态机扩展考虑向后兼容。

### IV. 异步媒体流水线可靠性

✅ **通过** - 关键帧生成作为异步任务执行，支持状态跟踪、失败处理和重试。单帧失败不影响整体流程，支持部分成功和单帧重试。

### V. 可观测性、版本化与简洁实现

✅ **通过** - 记录项目ID、镜头ID、网格类型、帧数量、模型版本等关键信息。关键帧图片存储路径规范，支持版本化。实现简洁，复用现有SubjectPipeline和AIGateway。

**结论**: 所有宪章检查通过，可进入Phase 0研究阶段。

## Project Structure

### Documentation (this feature)

```
specs/20260506-subject-keyframe-grid/
├── spec.md              # 功能规格说明
├── plan.md              # 本文件 (/adk:plan 输出)
├── research.md          # Phase 0 输出 (/adk:plan 输出)
├── data-model.md        # Phase 1 输出 (/adk:plan 输出)
├── quickstart.md        # Phase 1 输出 (/adk:plan 输出)
├── contracts/           # Phase 1 输出 (/adk:plan 输出)
└── tasks.md             # Phase 2 输出 (/adk:tasks 命令)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── schemas/
│   │   └── keyframe_grid.py          # 新增：KeyframeGrid、KeyframeFrame 数据模型
│   ├── repositories/
│   │   └── keyframe_repository.py    # 新增：关键帧数据访问层
│   ├── orchestrators/
│   │   └── keyframe_pipeline.py      # 新增：关键帧生成流水线
│   ├── api/routes/
│   │   └── keyframes.py              # 新增：关键帧API路由
│   ├── workers/
│   │   └── tasks.py                  # 修改：添加关键帧任务
│   └── schemas/states.py             # 修改：添加 keyframe_generating 状态
└── migrations/
    └── 005_keyframe_grids.sql        # 新增：数据库迁移文件

frontend/
├── src/
│   ├── modules/project/
│   │   ├── components/
│   │   │   └── KeyframeGrid.tsx      # 新增：关键帧网格组件
│   │   └── pages/
│   │       └── ShotDetailPage.tsx    # 修改：集成关键帧预览
│   ├── services/
│   │   └── keyframeService.ts        # 新增：关键帧API服务
│   └── styles/
│       └── keyframe.css              # 新增：关键帧样式
└── tests/
    └── KeyframeGrid.test.tsx         # 新增：关键帧组件测试
```

**Structure Decision**: 采用现有Web应用结构，后端Python负责业务逻辑和数据持久化，前端TypeScript/React负责界面展示。新增代码遵循现有目录规范。

## Complexity Tracking

*无违规项，无需说明*

---

## Phase 0: Research (Completed)

**输出**: [research.md](./research.md)

**研究成果**:
1. ✅ DashScope API并发限制与最佳实践 - 采用顺序生成+并发控制策略
2. ✅ 关键帧生成失败重试策略 - 指数退避+最大重试次数
3. ✅ 动态网格布局前端最佳实践 - CSS Grid + 内联样式
4. ✅ 图片合并下载技术方案 - Canvas API前端合并
5. ✅ 关键帧Prompt构建策略 - 模板化Prompt构建
6. ✅ 缓存策略 - 复用现有RenderPipeline缓存机制

**结论**: 所有技术决策已完成，无需额外澄清。

---

## Phase 1: Design & Contracts (Completed)

**输出**:
- [data-model.md](./data-model.md) - 数据模型定义
- [contracts/openapi.yaml](./contracts/openapi.yaml) - API契约
- [quickstart.md](./quickstart.md) - 快速入门指南

**数据模型**:
- `KeyframeGrid` - 关键帧网格实体
- `KeyframeFrame` - 单个关键帧实体
- 项目状态机扩展：新增 `keyframe_generating` 状态

**API契约**:
- `GET /projects/{id}/shots/{id}/keyframes` - 获取关键帧
- `GET /projects/{id}/shots/{id}/keyframes/download` - 下载网格图片
- `POST /projects/{id}/shots/{id}/keyframes/{position}/retry` - 重试关键帧
- `GET /projects/{id}/keyframes/status` - 获取项目关键帧状态

**前端组件**:
- `KeyframeGrid` - 动态网格展示组件
- `keyframeService` - API服务封装

---

## Constitution Re-Check (Post-Design)

*GATE: Re-validate after Phase 1 design.*

### I. 产品闭环优先

✅ **通过** - 关键帧生成已完整集成到业务闭环中，位于主体图生成和视频渲染之间。

### II. 人工审核门禁不可跳过

✅ **通过** - 未涉及审核门禁，关键帧生成在分镜审核通过后进行。

### III. 契约优先与跨端一致性

✅ **通过** - API契约已定义（OpenAPI规范），前后端术语一致，数据模型清晰。

### IV. 异步媒体流水线可靠性

✅ **通过** - 关键帧生成作为异步任务执行，支持状态跟踪、失败处理和重试机制。

### V. 可观测性、版本化与简洁实现

✅ **通过** - 记录项目ID、镜头ID、网格类型等关键信息，存储路径规范，实现简洁。

**结论**: 所有宪章检查通过，设计已完成，可进入 `/adk:tasks` 阶段生成任务分解。
