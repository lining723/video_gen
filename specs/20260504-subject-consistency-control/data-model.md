# Data Model: 主体一致性控制

**Feature**: `20260504-subject-consistency-control`
**Date**: 2026-05-05

## 实体关系图

```
┌─────────────────┐
│     Project     │
│─────────────────│
│ id              │
│ scene_version   │
│ storyboard_ver  │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────┐
│ StoryboardShot  │       │     Subject     │
│─────────────────│       │─────────────────│
│ id              │◄──────│ shot_id         │ (镜头专属主体)
│ project_id      │       │ project_id      │
│ sequence        │       │ id              │
│ subject_refs    │───────│ name            │
│ scene_index     │       │ feature_desc    │
└─────────────────┘       │ base_subject_id │──────┐
                          │ variant_type    │      │
                          │ image_version   │      │
                          │ image_path      │      │
                          │ source_url      │      │
                          └─────────────────┘      │
                                   ▲               │
                                   │ N:1           │
                          ┌────────┴────────┐      │
                          │Subject (Base)   │◄─────┘
                          │variant_type='   │
                          │  base'          │
                          └─────────────────┘
                                   │
                                   │ 1:N
                                   ▼
                          ┌─────────────────┐
                          │ SubjectVersion  │
                          │─────────────────│
                          │ id              │
                          │ subject_id      │
                          │ version         │
                          │ image_path      │
                          │ feature_desc    │
                          │ created_at      │
                          └─────────────────┘
```

## 核心实体

### Subject（主体）

**表名**: `subjects`

**用途**: 表示视频中的角色/人物，支持基础主体和变体主体

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | TEXT | ✓ | UUID | 主键 |
| `project_id` | TEXT | ✓ | - | 所属项目 |
| `shot_id` | TEXT | ✓ | '' | 关联镜头（空=全局主体） |
| `name` | TEXT | ✓ | - | 主体名称（如"主角"、"配角A"） |
| `profile` | TEXT | ✓ | '' | 角色简介 |
| `image_path` | TEXT | ✓ | '' | 图片存储路径 |
| `source_url` | TEXT | ✓ | '' | 原始图片 URL |
| `image_version` | INTEGER | ✓ | 1 | 当前图片版本号 |
| `feature_description` | TEXT | ✓ | '' | 视觉特征描述 |
| `base_subject_id` | TEXT | ✓ | '' | 基础主体 ID（变体专用） |
| `variant_type` | TEXT | ✓ | 'base' | 类型：`base`/`variant` |
| `variant_hint` | TEXT | ✓ | '' | 变体方向提示 |
| `is_locked` | INTEGER | ✓ | 0 | 是否锁定 |
| `created_at` | TEXT | ✓ | - | 创建时间 ISO |
| `updated_at` | TEXT | ✓ | - | 更新时间 ISO |

**索引**:
- `idx_subjects_project_shot`: `(project_id, shot_id, image_version)`
- `idx_subjects_base`: `(base_subject_id)`

**状态转换**:
```
[新建] → [生成图片] → [提取特征] → [用户编辑] → [锁定]
                                    ↓
                              [重新生成] → [版本递增]
                                    ↓
                              [回退版本]
```

---

### SubjectVersion（主体版本）

**表名**: `subject_versions`

**用途**: 存储主体的历史版本记录，支持回退

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | TEXT | ✓ | UUID | 主键 |
| `subject_id` | TEXT | ✓ | - | 关联主体 |
| `version` | INTEGER | ✓ | - | 版本号 |
| `image_path` | TEXT | ✓ | - | 历史图片路径 |
| `source_url` | TEXT | ✓ | '' | 历史图片 URL |
| `feature_description` | TEXT | ✓ | '' | 历史特征描述 |
| `created_at` | TEXT | ✓ | - | 创建时间 ISO |

**索引**:
- `idx_subject_versions_subject`: `(subject_id, version)`

---

## 数据模型代码

### SubjectAsset Schema

```python
# backend/src/schemas/subject_asset.py

from dataclasses import dataclass, field
from backend.src.schemas.common import BaseRecord


@dataclass(slots=True)
class SubjectAsset(BaseRecord):
    """主体资产数据模型"""
    project_id: str = ""
    shot_id: str = ""  # 空字符串表示全局主体
    name: str = ""
    profile: str = ""
    image_path: str = ""
    source_url: str = ""
    image_version: int = 1
    feature_description: str = ""
    base_subject_id: str = ""  # 变体关联的基础主体
    variant_type: str = "base"  # 'base' | 'variant'
    variant_hint: str = ""  # 变体方向提示
    is_locked: bool = False

    def is_variant(self) -> bool:
        return self.variant_type == 'variant'

    def is_global(self) -> bool:
        return not self.shot_id
```

### SubjectVersion Schema

```python
# backend/src/schemas/subject_version.py

from dataclasses import dataclass
from backend.src.schemas.common import BaseRecord


@dataclass(slots=True)
class SubjectVersion(BaseRecord):
    """主体版本历史"""
    subject_id: str = ""
    version: int = 1
    image_path: str = ""
    source_url: str = ""
    feature_description: str = ""
```

---

## 数据库迁移

现有迁移已覆盖大部分需求，以下为新增字段确认：

### 已存在字段（无需迁移）

```sql
-- 0007_subject_shot_scope.sql 已添加
ALTER TABLE subjects ADD COLUMN shot_id TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_subjects_project_shot ON subjects(project_id, shot_id, image_version);
```

### 需确认/新增字段

```sql
-- 检查 feature_description 字段是否存在
-- 如果不存在，需要添加：
-- ALTER TABLE subjects ADD COLUMN feature_description TEXT NOT NULL DEFAULT '';

-- 检查 base_subject_id 和 variant_type 字段
-- 如果不存在，需要添加：
-- ALTER TABLE subjects ADD COLUMN base_subject_id TEXT NOT NULL DEFAULT '';
-- ALTER TABLE subjects ADD COLUMN variant_type TEXT NOT NULL DEFAULT 'base';
-- ALTER TABLE subjects ADD COLUMN variant_hint TEXT NOT NULL DEFAULT '';
-- CREATE INDEX IF NOT EXISTS idx_subjects_base ON subjects(base_subject_id);
```

---

## 验证规则

| 字段 | 规则 | 错误信息 |
|------|------|----------|
| `feature_description` | 最大 1000 字符 | "特征描述不能超过 1000 字符" |
| `variant_type` | 枚举值 | "variant_type 必须为 base 或 variant" |
| `base_subject_id` | 变体时必填 | "变体主体必须关联基础主体" |
| `image_version` | 正整数 | "版本号必须为正整数" |
