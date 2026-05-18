# Tasks: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid` | **Date**: 2026-05-06 | **Plan**: [plan.md](./plan.md)

本文档包含实现关键帧生成功能的所有开发任务，按用户故事优先级组织。

## Overview

**总任务数**: 25个任务
**用户故事数**: 3个（P1、P2、P3）
**并行机会**: 8个任务可并行执行
**MVP范围**: User Story 1（P1）即可交付核心价值

---

## Phase 1: Setup & Foundational

**目标**: 建立共享基础设施，为所有用户故事提供支撑

### T001: 数据库迁移 - 关键帧表 ✅
**[Story: Foundational]**
- **文件**: `backend/src/repositories/migrations/0007_keyframe_grids.sql`
- **描述**: 创建 `keyframe_grids` 表，包含索引和约束
- **验收标准**:
  - [x] 表创建成功，包含所有必需字段
  - [x] 索引创建成功：`idx_keyframe_project`, `idx_keyframe_shot`
  - [x] 唯一约束：`idx_keyframe_shot_unique`
- **依赖**: 无

### T002: 数据模型定义 ✅
**[Story: Foundational]**
- **文件**: `backend/src/schemas/keyframe_grid.py`
- **描述**: 定义 `KeyframeGrid` 和 `KeyframeFrame` 数据模型
- **验收标准**:
  - [x] 数据类定义完整，包含所有字段
  - [x] `validate()` 方法实现完整
  - [x] 类型注解正确
- **依赖**: 无

### T003: 状态机扩展 ✅
**[Story: Foundational]**
- **文件**: `backend/src/schemas/states.py`
- **描述**: 添加 `keyframe_generating` 状态到项目状态机
- **验收标准**:
  - [x] `PROJECT_STATES` 包含 `keyframe_generating`
  - [x] 状态流转逻辑正确
  - [x] 向后兼容现有状态
- **依赖**: 无

### T004: 数据访问层 ✅
**[Story: Foundational]**
- **文件**: `backend/src/repositories/keyframe_repository.py`
- **描述**: 实现关键帧数据访问层
- **验收标准**:
  - [x] `save(grid)` 方法实现
  - [x] `get_by_shot(project_id, shot_id)` 方法实现
  - [x] `list_by_project(project_id)` 方法实现
  - [x] `delete(shot_id)` 方法实现
- **依赖**: T001, T002

---

## Phase 2: User Story 1 - 镜头关键帧自动生成 (P1)

**故事目标**: 为每个镜头根据时长自动生成对应网格大小的关键帧图片

**独立测试标准**: 创建测试项目，完成分镜审核后触发主体生成，验证是否成功为每个镜头生成对应网格大小的关键帧图片

### T005: 网格大小计算函数 [P] ✅
**[Story: US1]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 实现 `calculate_grid_size(duration)` 函数
- **验收标准**:
  - [x] 1-3秒返回 ("2x2", 4)
  - [x] 4-6秒返回 ("3x3", 9)
  - [x] 7-10秒返回 ("4x4", 16)
  - [x] 异常值处理正确（0、负数、超大值）
- **依赖**: 无

### T006: 时间进度分布函数 [P] ✅
**[Story: US1]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 实现 `calculate_time_ratios(frame_count)` 函数
- **验收标准**:
  - [x] frame_count=9 返回 [0.0, 0.125, ..., 1.0]
  - [x] frame_count=4 返回 [0.0, 0.333, 0.667, 1.0]
  - [x] frame_count=1 返回 [0.0]
- **依赖**: 无

### T007: 关键帧Prompt构建函数 ✅
**[Story: US1]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 实现 `_build_frame_prompt(shot, subject, time_ratio, duration)` 方法
- **验收标准**:
  - [x] Prompt包含所有必要信息（角色、镜头、运镜、背景、动作等）
  - [x] 时间进度百分比计算正确
  - [x] 动作阶段推断正确
  - [x] 运镜状态推断正确
- **依赖**: T005, T006

### T008: 关键帧生成流水线 ✅
**[Story: US1]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 实现 `KeyframePipeline` 类和 `generate_keyframes_for_shot()` 方法
- **验收标准**:
  - [x] 调用AI网关生成图片
  - [x] 存储图片到对象存储
  - [x] 创建 `KeyframeGrid` 记录
  - [x] 支持并发控制（最多3并发）
- **依赖**: T004, T007

### T009: 异步任务集成 ✅
**[Story: US1]**
- **文件**: `backend/src/workers/tasks.py`
- **描述**: 添加 `submit_keyframe_generation()` 任务函数
- **验收标准**:
  - [x] 任务提交成功
  - [x] 任务状态可跟踪
  - [x] 任务队列正确
- **依赖**: T008

### T010: 主体生成流程集成 ✅
**[Story: US1]**
- **文件**: `backend/src/orchestrators/subject_pipeline.py`
- **描述**: 在主体生成完成后触发关键帧生成
- **验收标准**:
  - [x] 状态流转正确：`subject_generating` → `keyframe_generating` → `subject_ready`
  - [x] 每个镜头生成关键帧
  - [x] 错误处理正确
- **依赖**: T008, T009

### T011: API端点 - 获取关键帧 ✅
**[Story: US1]**
- **文件**: `backend/src/api/routes/keyframes.py`
- **描述**: 实现 `GET /projects/{id}/shots/{id}/keyframes` 接口
- **验收标准**:
  - [x] 返回 `KeyframeGrid` 数据
  - [x] 包含所有帧信息
  - [x] 错误处理正确
- **依赖**: T004

### T012: API端点 - 项目关键帧状态 ✅
**[Story: US1]**
- **文件**: `backend/src/api/routes/keyframes.py`
- **描述**: 实现 `GET /projects/{id}/keyframes/status` 接口
- **验收标准**:
  - [x] 返回项目所有镜头的关键帧状态汇总
  - [x] 包含总数、成功数、失败数
  - [x] 每个镜头的状态详情
- **依赖**: T004

**✅ Checkpoint US1**: User Story 1 完成，可独立测试和交付

---

## Phase 3: User Story 2 - 关键帧预览与下载 (P2)

**故事目标**: 用户可以在前端界面查看每个镜头的关键帧网格预览，支持单张图片查看和整宫格下载

**独立测试标准**: 在前端页面验证九宫格展示是否正确，点击单帧是否能放大查看，下载功能是否正常工作

### T013: 前端API服务 ✅
**[Story: US2]**
- **文件**: `frontend/src/services/keyframeService.ts`
- **描述**: 实现关键帧API服务封装
- **验收标准**:
  - [x] `getKeyframes(projectId, shotId)` 方法实现
  - [x] `downloadGrid(projectId, shotId)` 方法实现
  - [x] TypeScript接口定义完整
- **依赖**: T011

### T014: 动态网格组件 [P] ✅
**[Story: US2]**
- **文件**: `frontend/src/modules/project/components/KeyframeGrid.tsx`
- **描述**: 实现关键帧网格展示组件
- **验收标准**:
  - [x] 支持动态网格布局（2×2、3×3、4×4）
  - [x] 每帧显示时间进度标签
  - [x] 加载状态展示
  - [x] 大图预览Modal
- **依赖**: T013

### T015: 样式文件 [P] ✅
**[Story: US2]**
- **文件**: `frontend/src/styles/KeyframeGrid.css`
- **描述**: 关键帧组件样式
- **验收标准**:
  - [x] 网格布局样式正确
  - [x] 时间标签样式美观
  - [x] 响应式布局支持
- **依赖**: 无

### T016: 镜头详情页集成 ✅
**[Story: US2]**
- **文件**: `frontend/src/modules/project/pages/ShotDetailPage.tsx`
- **描述**: 在镜头详情页集成关键帧预览组件
- **验收标准**:
  - [x] 关键帧预览区域展示
  - [x] 下载按钮功能正常
  - [x] 与现有页面布局协调
- **依赖**: T014, T015

### T017: 图片合并下载功能 ✅
**[Story: US2]**
- **文件**: `frontend/src/services/keyframeService.ts`
- **描述**: 实现Canvas合并图片下载功能
- **验收标准**:
  - [x] 使用Canvas API合并所有关键帧
  - [x] 根据网格类型计算布局
  - [x] 触发PNG格式下载
- **依赖**: T013

**✅ Checkpoint US2**: User Story 2 完成，可独立测试和交付

---

## Phase 4: User Story 3 - 关键帧生成失败处理 (P3)

**故事目标**: 系统支持关键帧生成失败的部分成功处理，用户可以单独重新生成失败的关键帧

**独立测试标准**: 模拟AI服务失败场景，验证系统记录失败状态，前端展示失败占位图，重试功能正常工作

### T018: 失败状态记录 ✅
**[Story: US3]**
- **文件**: `backend/src/schemas/keyframe_grid.py`
- **描述**: 扩展 `KeyframeFrame` 模型，添加失败状态字段
- **验收标准**:
  - [x] 添加 `status` 字段（pending、generating、succeeded、failed）
  - [x] 添加 `error_message` 字段
  - [x] 添加 `retry_count` 字段
- **依赖**: T002

### T019: 部分失败处理逻辑 ✅
**[Story: US3]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 修改 `generate_keyframes_for_shot()` 支持部分失败
- **验收标准**:
  - [x] 单帧失败不影响其他帧
  - [x] 失败帧记录错误信息
  - [x] 整体任务返回部分成功状态
- **依赖**: T018

### T020: 重试机制实现 ✅
**[Story: US3]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 实现单帧重试逻辑，支持指数退避
- **验收标准**:
  - [x] 重试次数限制为3次
  - [x] 指数退避延迟：1秒、2秒、4秒
  - [x] 重试成功更新状态
- **依赖**: T019

### T021: API端点 - 重试关键帧 ✅
**[Story: US3]**
- **文件**: `backend/src/api/routes/keyframes.py`
- **描述**: 实现 `POST /projects/{id}/shots/{id}/keyframes/{position}/retry` 接口
- **验收标准**:
  - [x] 提交重试任务
  - [x] 返回重试状态和次数
  - [x] 达到上限时返回错误
- **依赖**: T020

### T022: 前端失败展示 ✅
**[Story: US3]**
- **文件**: `frontend/src/modules/project/components/KeyframeGrid.tsx`
- **描述**: 添加失败帧展示和重试按钮
- **验收标准**:
  - [x] 失败帧显示占位图和警告图标
  - [x] 显示"生成失败"文本
  - [x] 重试按钮功能正常
- **依赖**: T021

**✅ Checkpoint US3**: User Story 3 完成，可独立测试和交付

---

## Phase 5: Polish & Cross-Cutting Concerns

**目标**: 完善日志、审计、性能优化等跨切面关注点

### T023: 审计日志集成
**[Story: Polish]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 集成审计服务，记录关键帧生成日志
- **验收标准**:
  - 记录项目ID、镜头ID、网格类型、帧数量
  - 记录生成时间、模型版本
  - 记录成功/失败状态
- **依赖**: T008

### T024: 缓存机制集成
**[Story: Polish]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 集成缓存机制，支持关键帧缓存和失效
- **验收标准**:
  - 缓存Key计算正确
  - 镜头或主体变化时缓存失效
  - 缓存命中时直接返回
- **依赖**: T008

### T025: 性能优化 - 缩略图生成
**[Story: Polish]**
- **文件**: `backend/src/orchestrators/keyframe_pipeline.py`
- **描述**: 为关键帧图片生成缩略图，优化前端加载
- **验收标准**:
  - 生成缩略图（宽度300px）
  - 存储路径正确
  - API返回缩略图URL
- **依赖**: T008

---

## Dependencies & Execution Strategy

### User Story Dependency Graph

```
Foundational (T001-T004)
  ↓
US1: 镜头关键帧自动生成 (T005-T012) ← MVP
  ↓
US2: 关键帧预览与下载 (T013-T017)
  ↓
US3: 关键帧生成失败处理 (T018-T022)
  ↓
Polish (T023-T025)
```

### Parallel Execution Opportunities

**Phase 1 (Foundational)**:
- T001, T002, T003 可并行执行（不同文件）
- T004 需等待 T001, T002 完成

**Phase 2 (US1)**:
- T005, T006 可并行执行（独立函数）
- T007 需等待 T005, T006 完成

**Phase 3 (US2)**:
- T014, T015 可并行执行（组件和样式分离）
- T016 需等待 T014, T015 完成

### MVP Implementation Strategy

**最小可行产品 (MVP)**:
- 完成 Phase 1 (Foundational) + Phase 2 (US1)
- 总计 12 个任务（T001-T012）
- 即可交付核心价值：镜头关键帧自动生成

**增量交付策略**:
1. **Sprint 1**: Phase 1 + Phase 2 (US1) - MVP交付
2. **Sprint 2**: Phase 3 (US2) - 前端预览和下载
3. **Sprint 3**: Phase 4 (US3) - 失败处理
4. **Sprint 4**: Phase 5 (Polish) - 性能优化

---

## Task Summary

| 阶段 | 任务数 | 可并行 | 故事 |
|------|--------|--------|------|
| Phase 1: Foundational | 4 | 3 | 基础设施 |
| Phase 2: US1 | 8 | 2 | P1 - 核心功能 |
| Phase 3: US2 | 5 | 2 | P2 - 前端展示 |
| Phase 4: US3 | 5 | 0 | P3 - 失败处理 |
| Phase 5: Polish | 3 | 0 | 跨切面优化 |
| **总计** | **25** | **8** | **3个用户故事** |

---

## Next Steps

1. **执行 `/adk:implement`** 开始实现任务
2. **按阶段交付**：优先完成 MVP (Phase 1 + Phase 2)
3. **持续集成**：每个 User Story 完成后进行集成测试
