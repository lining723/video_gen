---
description: "Task list for subject consistency control feature"
---

# Tasks: 主体一致性控制

**Feature**: `20260504-subject-consistency-control`
**Input**: Design documents from `/specs/20260504-subject-consistency-control/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

## 格式说明

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 路径使用 Web app 结构：`backend/src/`, `frontend/src/`

---

## Phase 1: Setup (基础准备)

**目的**: 数据库迁移和基础结构扩展

- [x] T001 Create database migration for subjects table extension in `backend/src/repositories/migrations/0013_subject_consistency.sql`
- [x] T002 Create database migration for subject_versions table in `backend/src/repositories/migrations/0014_subject_versions.sql`
- [x] T003 [P] Extend SubjectAsset schema with new fields in `backend/src/schemas/subject_asset.py`

**Checkpoint**: ✅ 数据库和模型准备就绪

---

## Phase 2: Foundational (基础设施)

**目的**: Repository 层扩展，所有 US 依赖的基础

**⚠️ 关键**: 此阶段完成前，无法开始任何用户故事

- [x] T004 Extend SubjectRepository with version management methods in `backend/src/repositories/subject_repository.py`
  - `save_version(subject_id, version_data)`
  - `list_versions(subject_id)`
  - `get_version(subject_id, version)`
- [x] T005 [P] Extend SubjectRepository with feature description methods in `backend/src/repositories/subject_repository.py`
  - `update_feature_description(subject_id, description)`
  - `lock_subject(subject_id)`
  - `unlock_subject(subject_id)`
  - `list_base_subjects(project_id)`

**Checkpoint**: ✅ Repository 层就绪 - 用户故事实现可以开始

---

## Phase 3: User Story 1 - 主体特征锁定 (Priority: P1) 🎯 MVP

**目标**: 实现主体特征提取、编辑和锁定功能

**独立测试**: 创建项目 → 生成分镜 → 生成主体 → 验证特征描述生成 → 编辑特征描述 → 锁定特征

### 后端实现 (US1)

- [x] T006 [US1] Implement feature extraction method in `backend/src/integrations/ai_gateway.py`
  - `extract_subject_features(image_path_or_url) -> str`
  - 调用文本模型分析图片，返回特征描述
- [x] T007 [US1] Modify SubjectPipeline.run() to extract features after generation in `backend/src/orchestrators/subject_pipeline.py`
  - 生成主体图后调用 `extract_subject_features`
  - 保存特征描述到 subject 记录
- [x] T008 [US1] Add PUT endpoint for updating subject feature description in `backend/src/api/routes/subjects.py`
  - `PUT /api/projects/{projectId}/subjects/{subjectId}`
  - 支持更新 `feature_description` 字段
- [x] T009 [US1] Add POST endpoints for locking/unlocking subject in `backend/src/api/routes/subjects.py`
  - `POST /api/projects/{projectId}/subjects/{subjectId}:lock`
  - `POST /api/projects/{projectId}/subjects/{subjectId}:unlock`

### 前端实现 (US1)

- [x] T010 [US1] Display feature description in RenderProgressPage in `frontend/src/modules/render-progress/RenderProgressPage.tsx`
  - 显示特征描述文本
  - 显示版本号徽章
  - 显示锁定状态
- [x] T011 [US1] Add API service functions for subject operations in `frontend/src/services/render.ts`:
  - `lockSubject(projectId, subjectId)`
  - `unlockSubject(projectId, subjectId)`
  - `updateSubjectFeature(projectId, subjectId, body)`
- [x] T012 [US1] Add event handlers for lock/unlock/edit buttons in `frontend/src/pages/projects/[projectId]/renders.tsx`
  - 绑定 `.lock-subject-btn` 点击事件
  - 绑定 `.unlock-subject-btn` 点击事件
  - 绑定 `.edit-feature-btn` 点击事件（弹出编辑对话框）

**Checkpoint**: 🔶 后端完成，前端事件处理待实现

---

## Phase 4: User Story 2 - 主体变体生成 (Priority: P2)

**目标**: 实现基于锁定特征的变体生成功能

**独立测试**: 锁定基础主体 → 为镜头生成变体 → 验证变体保持特征一致性

**依赖**: US1 完成（需要特征锁定功能）

### 后端实现 (US2)

- [x] T013 [US2] Extend AIGateway.generate_subject_image() to accept feature_description in `backend/src/integrations/ai_gateway.py`
  - 添加 `feature_description` 参数
  - 构建 prompt 时组合特征描述
- [x] T014 [US2] Modify generate_shot_subject endpoint to support variant generation in `backend/src/api/routes/subjects.py`
  - 添加 `variant_hint` 参数处理
  - 获取基础主体特征描述
  - 设置 `base_subject_id` 和 `variant_type`
- [x] T015 [US2] Implement variant prompt composition in `backend/src/integrations/ai_gateway.py`
  ```
  基础特征：{feature_description}
  变体要求：{variant_hint}
  风格要求：{style_prompt}
  ```

### 前端实现 (US2)

- [x] T016 [US2] Display variant type badge in subject list UI in `frontend/src/modules/render-progress/RenderProgressPage.tsx`
  - 显示"变体"标签
- [x] T017 [US2] Add variant generation UI controls in `frontend/src/pages/projects/[projectId]/renders.tsx`
  - 在镜头主体图面板添加"生成变体"按钮
  - 添加变体方向选择器（预设 + 自定义输入）
  - 调用 `generateShotSubject` 时传入 `mode: 'variant'` 和 `variant_hint`

**Checkpoint**: 🔶 后端完成，前端变体 UI 待实现

---

## Phase 5: User Story 3 - 主体更新确认流程 (Priority: P3)

**目标**: 实现版本管理和更新确认流程

**独立测试**: 重新生成主体 → 确认对话框 → 版本递增 → 查看历史 → 回退版本

**依赖**: US1 完成（需要主体数据结构）

### 后端实现 (US3)

- [x] T018 [US3] Implement save_version logic in SubjectRepository in `backend/src/repositories/subject_repository.py`
  - 重新生成前保存当前版本到 subject_versions 表
  - 递增 image_version
- [x] T019 [US3] Add regenerate endpoint with confirmation in `backend/src/api/routes/subjects.py`
  - `POST /api/projects/{projectId}/subjects/{subjectId}:regenerate`
  - 请求体：`{ "cascade_render": boolean }`
  - 返回：新版本主体信息
- [x] T020 [US3] Add version history endpoint in `backend/src/api/routes/subjects.py`
  - `GET /api/projects/{projectId}/subjects/{subjectId}/versions`
  - 返回版本列表
- [x] T021 [US3] Add rollback endpoint in `backend/src/api/routes/subjects.py`
  - `POST /api/projects/{projectId}/subjects/{subjectId}:rollback`
  - 参数：`{ "target_version": int }`

### 前端实现 (US3)

- [x] T022 [US3] Display version number and history button in `frontend/src/modules/render-progress/RenderProgressPage.tsx`
  - 显示版本号徽章 `v${imageVersion}`
  - 显示"历史版本"按钮
  - 显示"重新生成"按钮
- [x] T023 [US3] Add API service functions for version operations in `frontend/src/services/render.ts`:
  - `regenerateSubject(projectId, subjectId, body)`
  - `getSubjectVersions(projectId, subjectId)`
  - `rollbackSubjectVersion(projectId, subjectId, body)`
- [x] T024 [US3] Add event handlers for regenerate/versions/rollback in `frontend/src/pages/projects/[projectId]/renders.tsx`
  - 绑定 `.regenerate-subject-btn` 点击事件（确认对话框）
  - 绑定 `.subject-versions-btn` 点击事件（显示版本列表弹窗）
  - 实现版本回退逻辑

**Checkpoint**: 🔶 后端完成，前端版本管理 UI 待实现

---

## Phase 6: Polish & Cross-Cutting Concerns

**目的**: 测试、文档和优化

- [x] T025 [P] Add integration tests for subject consistency flow in `backend/tests/test_subject_consistency.py`
  - 特征提取测试
  - 变体生成测试
  - 版本管理测试
- [x] T026 [P] Update API documentation/contracts if needed
- [x] T027 Add logging for subject operations in `backend/src/api/routes/subjects.py`
  - 特征锁定/解锁
  - 变体生成
  - 版本回退

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ✅
    ↓
Phase 2 (Foundational) ✅
    ↓
┌───────────────────────────────────────┐
│  Phase 3 (US1) 🔶 后端完成             │
│      ↓                                 │
│  Phase 4 (US2) 🔶 后端完成             │
│      ↓                                 │
│  Phase 5 (US3) 🔶 后端完成             │
└───────────────────────────────────────┘
    ↓
Phase 6 (Polish)
```

### User Story Dependencies

| 故事 | 依赖 | 状态 |
|------|------|------|
| US1 (P1) | Phase 2 | 🔶 后端完成 |
| US2 (P2) | US1 | 🔶 后端完成 |
| US3 (P3) | US1 | 🔶 后端完成 |

---

## Implementation Strategy

### 当前进度

- ✅ **后端完成**: 所有 API 端点已实现
- 🔶 **前端部分完成**: UI 已渲染，事件处理待绑定

### 剩余工作

1. **T011-T012** (US1): 前端锁定/解锁/编辑事件处理
2. **T017** (US2): 前端变体生成 UI
3. **T023-T024** (US3): 前端版本管理事件处理
4. **T025-T027** (Polish): 测试和日志

### 建议执行顺序

```
1. T011 + T012 (US1 前端) → 验证特征锁定
2. T017 (US2 前端) → 验证变体生成
3. T023 + T024 (US3 前端) → 验证版本管理
4. T025-T027 (Polish) → 最终验证
```

---

## Task Summary

| Phase | 总任务 | 已完成 | 待完成 |
|-------|--------|--------|--------|
| Phase 1: Setup | 3 | 3 | 0 |
| Phase 2: Foundational | 2 | 2 | 0 |
| Phase 3: US1 | 6 | 4 | 2 |
| Phase 4: US2 | 5 | 4 | 1 |
| Phase 5: US3 | 7 | 5 | 2 |
| Phase 6: Polish | 3 | 0 | 3 |
| **Total** | **26** | **18** | **8** |

### By User Story

| 故事 | 后端 | 前端 | 状态 |
|------|------|------|------|
| US1 (P1) | ✅ 4/4 | 🔶 0/2 | MVP 待完成 |
| US2 (P2) | ✅ 3/3 | 🔶 0/1 | 依赖 US1 |
| US3 (P3) | ✅ 4/4 | 🔶 0/2 | 依赖 US1 |

---

## Notes

- 后端 API 全部实现完成
- 前端 UI 模板已渲染，需要添加事件处理逻辑
- 建议先完成 US1 前端，验证 MVP 功能
- 提交频率：每个任务或逻辑组完成后提交
