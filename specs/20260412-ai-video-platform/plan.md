# Implementation Plan: 智能视频生成平台

**Feature**: `20260412-ai-video-platform` | **Date**: 2026-04-12 | **Spec**: `specs/20260412-ai-video-platform/spec.md`
**Input**: Feature specification from `/specs/20260412-ai-video-platform/spec.md`

## Summary

构建一个前端基于 Node.js、后端基于 Python 的智能视频生成平台，围绕“创意输入 → 场景设计 → 分镜审核 → 主体出图 → 镜头渲染 → 最终拼接 → 成片交付”的流程，优先实现可审核、可编辑、可缓存、可重试的 MVP 闭环。技术上采用 Web 前后端分层架构：前端负责项目管理、审核与进度展示；后端负责模型编排、任务调度、缓存复用、媒资存储和最终拼接。

## Technical Context

**Language/Version**: Frontend `Node.js 20+` + TypeScript；Backend `Python 3.11+`  
**Primary Dependencies**: Frontend `React/Next.js`、状态管理库、上传/播放器组件；Backend `FastAPI`、`Pydantic`、任务队列（Celery / Arq）、FFmpeg、对象存储 SDK  
**Storage**: PostgreSQL（元数据）、对象存储/文件存储（图片/视频）、本地或挂载缓存目录（镜头缓存）、日志系统  
**Testing**: Frontend `Vitest` + `Testing Library`；Backend `pytest`；契约测试与集成测试  
**Target Platform**: Linux server，浏览器端 Web 应用  
**Project Type**: Web application（frontend + backend + async worker）  
**Performance Goals**: 页面交互 < `2s`；状态查询接口平均 < `500ms`；单项目支持至少 `20` 个镜头并行渲染  
**Constraints**: 单镜头默认最大时长 `10s`；缓存降级可用；任务级重试最多 `3` 次；敏感配置不可暴露前端  
**Scale/Scope**: MVP 支持单项目 1–20 个镜头；单租户级内部使用；支持单人创作 + 审核闭环

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `.ttadk/memory/constitution.md` 当前为空，暂无额外项目级强制原则。
- 计划遵循现有规格中的功能、非功能、状态流、缓存与恢复约束。
- Gate 结果：**PASS**。
- Phase 1 复检结果：规划产物未引入与规格冲突的技术选择，**PASS**。

## Project Structure

### Documentation (this feature)

```
specs/20260412-ai-video-platform/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── orchestrators/
│   ├── workers/
│   ├── repositories/
│   ├── media/
│   └── settings/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
├── src/
│   ├── pages/
│   ├── components/
│   ├── modules/
│   ├── services/
│   ├── stores/
│   └── hooks/
└── tests/
    ├── integration/
    └── unit/

infra/
├── docker/
├── scripts/
└── ffmpeg/
```

**Structure Decision**: 采用标准 Web 双端架构，并额外引入异步 worker/编排层处理主体出图、镜头渲染和拼接任务，避免将长耗时任务阻塞在线 API。

## Phase 0: Research Plan

1. 确认前端框架与 SSR/CSR 策略，优先保证项目管理与任务状态页开发效率。
2. 确认后端异步任务框架，比较 `Celery` 与 `Arq` 在 Python 生态、重试和并发控制方面的适配性。
3. 确认媒资存储方案，明确本地缓存目录与对象存储的边界。
4. 确认 FFmpeg 拼接方案，明确字幕轨、配音轨和视频轨的时间对齐方式。
5. 确认缓存键与版本策略，保证模型升级、素材变更后能准确失效。
6. 确认契约优先的 API 组织方式，确保前后端并行开发。

## Phase 1: Design Plan

1. 设计核心数据模型：Project、SceneDesign、StoryboardShot、SubjectAsset、ShotRenderTask、FinalVideo。
2. 设计状态机：项目主流程状态、镜头任务状态、review 状态与版本流转规则。
3. 设计 API 契约：项目、场景、分镜、主体、渲染、成片六类核心接口。
4. 设计异步编排链路：场景生成 → 分镜生成 → 主体抽取/出图 → 配音 → 镜头渲染 → 拼接。
5. 设计前端页面结构：项目列表、项目详情、场景 review、分镜编辑、渲染进度、成片详情。
6. 设计可观测性：任务日志、trace id、项目维度告警与失败重试入口。

## Implementation Strategy

### MVP Slice 1
- 创建项目、输入创意、生成场景设计、完成场景 review。

### MVP Slice 2
- 生成分镜、编辑分镜、完成分镜 review、保存版本。

### MVP Slice 3
- 抽取主体、统一出图、并行生成镜头视频、记录缓存命中。

### MVP Slice 4
- 触发拼接、存储成片、展示项目进度与最终结果、支持局部重试。

## Testing Strategy

- **Contract Tests**: 校验 `contracts/openapi.yaml` 中的核心接口与后端实现一致。
- **Unit Tests**: 覆盖状态机、缓存键计算、版本规则、任务编排辅助函数。
- **Integration Tests**: 覆盖项目主流程、单镜头失败重试、缓存命中与拼接流程。
- **Frontend Tests**: 覆盖分镜编辑器、审核流、进度页状态渲染。
- **Manual Verification**: 以一个 3 镜头样例项目走完整流程，验证审核、渲染、缓存与成片输出。

## Risks & Mitigations

- **模型调用不稳定**：通过任务重试、超时与失败队列降低影响。
- **镜头一致性不足**：通过统一主体出图和版本化缓存降低角色漂移。
- **拼接复杂度高**：优先采用 FFmpeg 标准化管线，并固定首版输出规格。
- **缓存误命中**：严格使用内容哈希 + 模型版本 + 配置组合键。
- **长链路排障困难**：全链路记录项目 ID、镜头 ID、任务 ID 与 trace ID。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 异步 worker / 编排层 | 视频生成与拼接为长耗时任务 | 纯同步 API 会阻塞请求且难以并发控制 |
| 多存储分层 | 缓存、媒资、元数据职责不同 | 单一存储无法同时满足成本、检索与复用需求 |
