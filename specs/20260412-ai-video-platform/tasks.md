# Tasks: 智能视频生成平台

**Input**: Design documents from `/specs/20260412-ai-video-platform/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`, `.ttadk/memory/constitution.md`
**Tests**: 本次未单独要求 TDD，因此不单列测试任务；实现阶段需按宪章补齐关键路径验证。
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `SETUP`, `FOUND`, `US1`, `US2`, `US3`, `US4`, `POLISH`
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)
**Purpose**: 初始化前后端工程骨架与基础目录
- [x] T001 [SETUP] Create repository structure under `backend/`, `frontend/`, and `infra/` from `specs/20260412-ai-video-platform/plan.md`
- [x] T002 [SETUP] Initialize frontend workspace in `frontend/package.json`, `frontend/tsconfig.json`, and `frontend/src/pages/_app.tsx`
- [x] T003 [P] [SETUP] Initialize backend service in `backend/pyproject.toml`, `backend/src/api/app.py`, and `backend/src/settings/config.py`
- [x] T004 [P] [SETUP] Add runtime env examples in `.env.example`, `backend/.env.example`, and `frontend/.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)
**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented
**⚠️ CRITICAL**: No user story work can begin until this phase is complete
- [x] T005 [FOUND] Create initial persistence layout in `backend/src/repositories/migrations/0001_initial.sql` and `backend/src/repositories/db.py`
- [x] T006 [P] [FOUND] Implement shared enums and state machine constants in `backend/src/schemas/states.py` and `backend/src/schemas/common.py`
- [x] T007 [P] [FOUND] Scaffold API router, middleware, and error envelope in `backend/src/api/routes/__init__.py`, `backend/src/api/middleware/request_context.py`, and `backend/src/api/errors.py`
- [x] T008 [P] [FOUND] Implement logging, audit, and trace helpers in `backend/src/settings/logging.py`, `backend/src/services/audit_service.py`, and `backend/src/settings/observability.py`
- [x] T009 [P] [FOUND] Implement storage abstractions in `backend/src/media/storage.py`, `backend/src/media/cache.py`, and `backend/src/media/object_store.py`
- [x] T010 [FOUND] Bootstrap async queue and orchestration base in `backend/src/workers/queue.py`, `backend/src/workers/tasks.py`, and `backend/src/orchestrators/base.py`
- [x] T011 [P] [FOUND] Create frontend app shell and shared layout in `frontend/src/modules/layout/AppLayout.tsx`, `frontend/src/hooks/useProjectContext.ts`, and `frontend/src/services/http.ts`
**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 智能生成可审核的创意方案 (Priority: P1) 🎯 MVP
**Goal**: 支持项目创建、创意输入、场景设计生成与场景 review 闭环
**Independent Test**: 创建项目后提交创意，生成一版场景设计，并完成“通过 / 驳回 / 重新生成”流程
### Implementation for User Story 1
- [x] T012 [P] [US1] Create project and scene schemas in `backend/src/schemas/project.py` and `backend/src/schemas/scene_design.py`
- [x] T013 [P] [US1] Implement project and scene repositories in `backend/src/repositories/project_repository.py` and `backend/src/repositories/scene_repository.py`
- [x] T014 [US1] Implement scene generation and review service in `backend/src/services/scene_design_service.py`
- [x] T015 [US1] Implement project and scene endpoints in `backend/src/api/routes/projects.py` and `backend/src/api/routes/scene_design.py`
- [x] T016 [P] [US1] Build project creation and scene input UI in `frontend/src/pages/projects/index.tsx` and `frontend/src/modules/project-create/ProjectCreateForm.tsx`
- [x] T017 [US1] Build scene review page and client service in `frontend/src/pages/projects/[projectId]/scene.tsx`, `frontend/src/modules/scene-review/SceneReviewPage.tsx`, and `frontend/src/services/sceneDesign.ts`
- [x] T018 [US1] Persist scene versioning and review audit trail in `backend/src/services/scene_design_service.py` and `backend/src/services/audit_service.py`
**Checkpoint**: US1 is fully functional and demonstrable as the MVP entry flow

---

## Phase 4: User Story 2 - 生成并编辑分镜头脚本 (Priority: P1)
**Goal**: 自动生成分镜、支持逐镜编辑、时长校验与分镜 review
**Independent Test**: 在场景审核通过后生成分镜，修改单镜头字幕、配音、顺序和时长后成功提交审核
### Implementation for User Story 2
- [x] T019 [P] [US2] Create storyboard schemas and DTOs in `backend/src/schemas/storyboard.py` and `backend/src/schemas/storyboard_review.py`
- [x] T020 [P] [US2] Implement storyboard repository and version storage in `backend/src/repositories/storyboard_repository.py`
- [x] T021 [US2] Implement storyboard generation, edit, and review service in `backend/src/services/storyboard_service.py`
- [x] T022 [US2] Implement storyboard validation rules in `backend/src/services/storyboard_validation.py`
- [x] T023 [US2] Implement storyboard endpoints in `backend/src/api/routes/storyboard.py`
- [x] T024 [P] [US2] Build storyboard editor page in `frontend/src/pages/projects/[projectId]/storyboard.tsx` and `frontend/src/modules/storyboard-editor/StoryboardEditorPage.tsx`
- [x] T025 [P] [US2] Implement storyboard client service and store in `frontend/src/services/storyboard.ts` and `frontend/src/stores/storyboardStore.ts`
- [x] T026 [US2] Add reorder, duration-limit, and required-field UI logic in `frontend/src/modules/storyboard-editor/shotUtils.ts` and `frontend/src/modules/storyboard-editor/ShotCard.tsx`
**Checkpoint**: US2 supports full storyboard authoring and review without relying on later phases

---

## Phase 5: User Story 3 - 统一主体素材并行生成视频 (Priority: P1)
**Goal**: 完成主体抽取、统一出图、镜头并行渲染、缓存命中与最终拼接
**Independent Test**: 在分镜审核通过后，系统能完成主体图生成、镜头渲染、缓存复用和最终视频拼接
### Implementation for User Story 3
- [x] T027 [P] [US3] Create subject, render-task, and final-video schemas in `backend/src/schemas/subject_asset.py`, `backend/src/schemas/render_task.py`, and `backend/src/schemas/final_video.py`
- [x] T028 [P] [US3] Implement subject, render, and final video repositories in `backend/src/repositories/subject_repository.py`, `backend/src/repositories/render_repository.py`, and `backend/src/repositories/final_video_repository.py`
- [x] T029 [US3] Implement subject extraction and image generation pipeline in `backend/src/orchestrators/subject_pipeline.py`
- [x] T030 [US3] Implement cache key generation and render orchestration in `backend/src/media/cache_key.py` and `backend/src/orchestrators/render_pipeline.py`
- [x] T031 [US3] Implement composer with subtitle/voiceover/video alignment in `backend/src/media/composer.py` and `backend/src/orchestrators/compose_pipeline.py`
- [x] T032 [US3] Implement subject, render, retry, and final-video endpoints in `backend/src/api/routes/subjects.py`, `backend/src/api/routes/renders.py`, and `backend/src/api/routes/final_video.py`
- [x] T033 [P] [US3] Build render progress page in `frontend/src/pages/projects/[projectId]/renders.tsx` and `frontend/src/modules/render-progress/RenderProgressPage.tsx`
- [x] T034 [US3] Build final video result page and retry actions in `frontend/src/pages/projects/[projectId]/final-video.tsx`, `frontend/src/modules/final-video/FinalVideoPage.tsx`, and `frontend/src/services/render.ts`
**Checkpoint**: US3 produces a stored final video and supports cache-aware retries

---

## Phase 6: User Story 4 - 管理项目进度与最终交付 (Priority: P2)
**Goal**: 提供项目维度的阶段进度、镜头状态、失败入口与交付查看能力
**Independent Test**: 用户可在项目详情页查看阶段进度、镜头状态、失败原因、下载成片并触发局部重试
### Implementation for User Story 4
- [x] T035 [US4] Implement project timeline aggregation service in `backend/src/services/project_timeline_service.py`
- [x] T036 [US4] Implement project detail and timeline endpoints in `backend/src/api/routes/project_timeline.py`
- [x] T037 [P] [US4] Build project dashboard page in `frontend/src/pages/projects/[projectId]/index.tsx` and `frontend/src/modules/project-dashboard/ProjectDashboardPage.tsx`
- [x] T038 [US4] Implement polling, retry, and download hooks in `frontend/src/hooks/useProjectTimeline.ts` and `frontend/src/services/projects.ts`
**Checkpoint**: US4 makes the async pipeline transparent and operable to users

---

## Phase 7: Polish & Cross-Cutting Concerns
**Purpose**: Improvements that affect multiple user stories
- [x] T039 [POLISH] Sync final API contract with implementation in `specs/20260412-ai-video-platform/contracts/openapi.yaml`
- [x] T040 [P] [POLISH] Update operator and developer docs in `README.md` and `specs/20260412-ai-video-platform/quickstart.md`
- [x] T041 [POLISH] Validate quickstart flow and record implementation gaps in `specs/20260412-ai-video-platform/quickstart.md`

---

## Dependencies & Execution Order
### Phase Dependencies
- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - blocks all user stories
- **User Stories (Phase 3-6)**: Depend on Foundational completion
- **Polish (Phase 7)**: Depends on all targeted user stories being complete
### User Story Dependencies
- **US1 (P1)**: Starts after Foundational
- **US2 (P1)**: Starts after US1 scene approval flow is available
- **US3 (P1)**: Starts after US2 storyboard approval flow is available
- **US4 (P2)**: Depends on core events/states from US1-US3
### Parallel Opportunities
- `T003` and `T004` can run in parallel
- `T006` to `T009` and `T011` can run in parallel
- `T012`/`T013` can run in parallel with `T016`
- `T019`/`T020` can run in parallel with `T024`/`T025`
- `T027`/`T028` can run in parallel with `T033`
- `T035` can run in parallel with `T037` after event/state contracts are fixed

---

## Parallel Example: User Story 3
```bash
Task: "Create subject, render-task, and final-video schemas in backend/src/schemas/subject_asset.py, backend/src/schemas/render_task.py, and backend/src/schemas/final_video.py"
Task: "Implement subject, render, and final video repositories in backend/src/repositories/subject_repository.py, backend/src/repositories/render_repository.py, and backend/src/repositories/final_video_repository.py"
Task: "Build render progress page in frontend/src/pages/projects/[projectId]/renders.tsx and frontend/src/modules/render-progress/RenderProgressPage.tsx"
```

---

## Implementation Strategy
### MVP First
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate the scene generation + review loop as MVP
### Incremental Delivery
1. Add US2 for storyboard authoring and review
2. Add US3 for subject generation, rendering, cache, and composition
3. Add US4 for project progress and delivery operations
4. Finish with contract sync, docs, and quickstart validation

## Notes
- Total tasks: `41`
- Suggested MVP scope: `US1` only
- Story task counts: `US1=7`, `US2=8`, `US3=8`, `US4=4`
- Cross-cutting coverage: 契约同步、状态机、日志审计、失败恢复、缓存命中与失效
