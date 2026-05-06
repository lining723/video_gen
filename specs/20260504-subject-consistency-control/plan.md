# Implementation Plan: 主体一致性控制

**Feature**: `20260504-subject-consistency-control` | **Date**: 2026-05-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/20260504-subject-consistency-control/spec.md`
**User Feedback**: 场景与镜头一般并不会一一对应

## Summary

实现视频生成过程中的主体一致性控制，确保同一人物主体在不同镜头中保持视觉特征的一致性。核心能力包括：
1. **特征锁定**：提取并编辑主体的视觉特征描述
2. **变体生成**：为特定镜头生成保持特征一致的主体变体
3. **版本管理**：支持主体图重新生成、版本保留与回退

**重要架构调整**：根据用户反馈，场景与镜头不是一对一关系。主体应关联到镜头层面，而非场景层面，以支持一个场景对应多个镜头的灵活编排。

## Technical Context

**Language/Version**:
- 后端: Python 3.11+
- 前端: Node.js 18+ / TypeScript 5+

**Primary Dependencies**:
- 后端: 内置 `ThreadingHTTPServer`（非 Flask/FastAPI）
- 前端: Next.js 风格页面路由
- AI 集成: DeepSeek (文本)、DashScope (图片/视频)

**Storage**:
- 数据库: SQLite（通过 `migrations/*.sql` 自动迁移）
- 对象存储: 双模式适配（`filesystem` / `s3`）

**Testing**: pytest（后端）

**Target Platform**:
- 后端: Linux/macOS 服务器
- 前端: Web 浏览器

**Project Type**: Web application（前后端分离）

**Performance Goals**:
- 主体特征编辑: < 30 秒完成
- 变体生成: < 1 分钟
- 版本回退: < 10 秒

**Constraints**:
- 人工审核门禁不可跳过（场景审核、分镜审核）
- 长耗时操作必须异步执行
- API Key 鉴权必须生效

**Scale/Scope**:
- 单项目支持 50+ 镜头
- 单项目支持 10+ 主体

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 检查结果 | 状态 |
|------|----------|------|
| **I. 产品闭环优先** | 功能属于"主体出图"阶段，直接服务于完整业务闭环 | ✅ PASS |
| **II. 人工审核门禁不可跳过** | 主体生成在分镜审核通过后进行，不绕过任何门禁 | ✅ PASS |
| **III. 契约优先与跨端一致性** | 需定义清晰的 API 契约，确保前后端术语一致 | ✅ PASS |
| **IV. 异步媒体流水线可靠性** | 主体生成、变体生成均为异步任务，支持状态跟踪 | ✅ PASS |
| **V. 可观测性、版本化与简洁实现** | 主体版本化已规划，日志审计需在 tasks 中显式添加 | ⚠️ PARTIAL |

**待补充**：
- 任务日志需记录 `project_id`、`subject_id`、模型版本
- 失败重试逻辑需明确

## Project Structure

### Documentation (this feature)

```
specs/20260504-subject-consistency-control/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
│   └── subjects-api.yaml
└── tasks.md             # Phase 2 输出 (/adk:tasks)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── schemas/
│   │   └── subject_asset.py    # 主体数据模型（已有，需扩展）
│   ├── repositories/
│   │   ├── migrations/
│   │   │   └── 0007_subject_shot_scope.sql  # 已有
│   │   └── subject_repository.py  # 主体数据访问（已有，需扩展）
│   ├── services/
│   │   └── subject_service.py  # 主体业务逻辑（新增）
│   ├── orchestrators/
│   │   └── subject_pipeline.py  # 主体生成流水线（已有）
│   ├── integrations/
│   │   └── ai_gateway.py       # AI 网关（已有，需扩展）
│   └── api/routes/
│       └── subjects.py         # 主体 API 路由（已有，需扩展）
└── tests/
    └── test_subject_consistency.py  # 新增测试

frontend/
├── src/
│   ├── modules/
│   │   └── SubjectManager/     # 主体管理模块（新增/扩展）
│   ├── services/
│   │   └── subjectApi.ts       # 主体 API 调用（新增/扩展）
│   └── stores/
│       └── subjectStore.ts     # 主体状态管理（新增）
└── tests/
    └── SubjectManager.test.ts  # 新增测试
```

**Structure Decision**: 采用 Web application 结构，前后端分离。后端扩展现有主体相关模块，前端新增主体管理组件。

## Complexity Tracking

*无宪章违规，本节不适用*

---

## Phase 0: Research

### 研究问题

1. **场景-镜头关系对主体生成的影响**
   - 当前实现：每个场景生成一个镜头
   - 用户反馈：场景与镜头不是一对一
   - 影响：主体关联到镜头层面已正确实现（`shot_id` 字段），但生成入口可能需要调整

2. **特征提取最佳实践**
   - 使用什么模型提取视觉特征？
   - 特征描述的结构化格式？

3. **变体生成的 Prompt 工程**
   - 如何组合 `feature_description` + `variant_hint` + `style_prompt`？
   - 如何确保变体保持特征一致性？

### 研究结论

见 [research.md](./research.md)

---

## Phase 1: Design

### 数据模型

见 [data-model.md](./data-model.md)

### API 契约

见 [contracts/subjects-api.yaml](./contracts/subjects-api.yaml)

### 快速开始

见 [quickstart.md](./quickstart.md)

---

## Risks & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI 模型无法准确提取特征描述 | 中 | 提供用户编辑入口，允许手动调整 |
| 变体生成无法保持一致性 | 中 | 多次生成供选择，版本回退机制 |
| 场景-镜头关系重构范围大 | 高 | 本功能仅处理镜头层面主体，不修改场景逻辑 |

## Next Steps

1. 用户确认本计划是否正确理解了"场景与镜头不一一对应"的需求
2. 执行 `/adk:tasks` 生成详细任务分解
