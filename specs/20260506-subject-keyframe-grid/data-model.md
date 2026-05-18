# Data Model: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid` | **Date**: 2026-05-06

本文档定义关键帧生成功能涉及的数据实体、字段、关系和验证规则。

## Entity Definitions

### 1. KeyframeGrid（关键帧网格）

**描述**: 代表一个镜头的所有关键帧集合。

**字段**:

| 字段名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | string | 是 | UUID | 主键 |
| project_id | string | 是 | - | 关联项目ID |
| shot_id | string | 是 | - | 关联镜头ID |
| subject_name | string | 是 | - | 关联主体名称 |
| grid_type | string | 是 | "3x3" | 网格类型：2x2、3x3、4x4 |
| frame_count | integer | 是 | 9 | 关键帧数量：4、9、16 |
| frames | array | 是 | [] | 关键帧列表（JSON） |
| generated_at | string | 是 | - | 生成时间（ISO 8601） |
| source_model | string | 否 | "" | 生成使用的模型版本 |
| created_at | string | 是 | - | 创建时间（ISO 8601） |
| updated_at | string | 是 | - | 更新时间（ISO 8601） |

**验证规则**:
- `grid_type` 必须为 "2x2"、"3x3" 或 "4x4"
- `frame_count` 必须为 4、9 或 16
- `frame_count` 必须与 `grid_type` 匹配（如 "3x3" 对应 9）
- `frames` 数组长度必须等于 `frame_count`

**索引**:
- `idx_keyframe_project`: `project_id`
- `idx_keyframe_shot`: `shot_id`

**关系**:
- 属于一个 Project（多对一）
- 属于一个 StoryboardShot（多对一）

### 2. KeyframeFrame（单个关键帧）

**描述**: 代表网格中的一个关键帧位置。

**字段**:

| 字段名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| position | integer | 是 | - | 网格位置（0到frame_count-1） |
| time_ratio | float | 是 | - | 时间进度比例（0.0-1.0） |
| image_path | string | 否 | "" | 图片存储路径 |
| source_url | string | 否 | "" | 图片源URL |
| prompt_used | string | 否 | "" | 生成该帧使用的Prompt |
| status | string | 是 | "pending" | 状态：pending、generating、succeeded、failed |
| error_message | string | 否 | "" | 错误信息 |
| retry_count | integer | 是 | 0 | 重试次数 |

**验证规则**:
- `position` 必须为非负整数
- `time_ratio` 必须在 0.0 到 1.0 之间
- `status` 必须为 "pending"、"generating"、"succeeded" 或 "failed"
- `retry_count` 必须为非负整数且 ≤ 3

**状态转换**:
```
pending → generating → succeeded
                    → failed → generating（重试）
```

## State Machine

### Project State Extension

在现有项目状态机基础上扩展：

```
storyboard_approved
  ↓
subject_generating（现有状态）
  ↓
keyframe_generating（新增状态）
  ↓
subject_ready（现有状态，包含关键帧完成）
  ↓
video_rendering
```

**状态说明**:
- `keyframe_generating`: 关键帧正在生成中
- 进入条件：主体图生成完成
- 退出条件：所有镜头的关键帧生成完成（或失败处理完成）

## Validation Rules

### 网格大小计算规则

```python
def calculate_grid_size(duration: int) -> tuple[str, int]:
    """
    根据镜头时长计算网格大小

    Args:
        duration: 镜头时长（秒）

    Returns:
        (grid_type, frame_count): 网格类型和帧数量

    Rules:
        - duration <= 3: 2x2（4帧）
        - duration <= 6: 3x3（9帧）
        - duration <= 10: 4x4（16帧）
        - duration > 10: 按10处理
        - duration <= 0: 使用默认值6秒
    """
    if duration <= 0:
        duration = 6  # 默认值

    if duration > 10:
        duration = 10  # 最大值

    if duration <= 3:
        return "2x2", 4
    elif duration <= 6:
        return "3x3", 9
    else:
        return "4x4", 16
```

### 时间进度分布规则

```python
def calculate_time_ratios(frame_count: int) -> list[float]:
    """
    根据帧数量计算时间进度分布

    Args:
        frame_count: 关键帧数量

    Returns:
        时间进度列表（0.0到1.0）

    Example:
        frame_count=9 → [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
        frame_count=4 → [0.0, 0.333, 0.667, 1.0]
        frame_count=1 → [0.0]
    """
    if frame_count <= 1:
        return [0.0]

    return [i / (frame_count - 1) for i in range(frame_count)]
```

## Database Schema

### SQLite Migration

```sql
-- 创建关键帧网格表
CREATE TABLE keyframe_grids (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    grid_type TEXT DEFAULT '3x3' CHECK (grid_type IN ('2x2', '3x3', '4x4')),
    frame_count INTEGER DEFAULT 9 CHECK (frame_count IN (4, 9, 16)),
    frames TEXT NOT NULL,  -- JSON array
    generated_at TEXT NOT NULL,
    source_model TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (shot_id) REFERENCES storyboard_shots(id)
);

-- 创建索引
CREATE INDEX idx_keyframe_project ON keyframe_grids(project_id);
CREATE INDEX idx_keyframe_shot ON keyframe_grids(shot_id);

-- 创建唯一约束（每个镜头只能有一个关键帧网格）
CREATE UNIQUE INDEX idx_keyframe_shot_unique ON keyframe_grids(shot_id);
```

## Python Data Models

```python
from dataclasses import dataclass, field
from typing import List

@dataclass(slots=True)
class KeyframeFrame:
    """单个关键帧"""
    position: int
    time_ratio: float
    image_path: str = ""
    source_url: str = ""
    prompt_used: str = ""
    status: str = "pending"
    error_message: str = ""
    retry_count: int = 0

    def validate(self) -> bool:
        """验证字段有效性"""
        if self.position < 0:
            raise ValueError("position must be non-negative")
        if not 0.0 <= self.time_ratio <= 1.0:
            raise ValueError("time_ratio must be between 0.0 and 1.0")
        if self.status not in ["pending", "generating", "succeeded", "failed"]:
            raise ValueError(f"invalid status: {self.status}")
        if self.retry_count < 0 or self.retry_count > 3:
            raise ValueError("retry_count must be between 0 and 3")
        return True

@dataclass(slots=True)
class KeyframeGrid(BaseRecord):
    """关键帧网格"""
    project_id: str = ""
    shot_id: str = ""
    subject_name: str = ""
    grid_type: str = "3x3"
    frame_count: int = 9
    frames: List[KeyframeFrame] = field(default_factory=list)
    generated_at: str = ""
    source_model: str = ""

    def validate(self) -> bool:
        """验证字段有效性"""
        valid_grid_types = {"2x2": 4, "3x3": 9, "4x4": 16}
        if self.grid_type not in valid_grid_types:
            raise ValueError(f"invalid grid_type: {self.grid_type}")
        if self.frame_count != valid_grid_types[self.grid_type]:
            raise ValueError(f"frame_count {self.frame_count} does not match grid_type {self.grid_type}")
        if len(self.frames) != self.frame_count:
            raise ValueError(f"frames length {len(self.frames)} does not match frame_count {self.frame_count}")
        return True
```

## TypeScript Interfaces

```typescript
/**
 * 关键帧状态
 */
export type KeyframeStatus = 'pending' | 'generating' | 'succeeded' | 'failed';

/**
 * 单个关键帧
 */
export interface KeyframeFrame {
  position: number;
  time_ratio: number;
  image_path?: string;
  source_url?: string;
  prompt_used?: string;
  status: KeyframeStatus;
  error_message?: string;
  retry_count: number;
}

/**
 * 关键帧网格
 */
export interface KeyframeGrid {
  id: string;
  project_id: string;
  shot_id: string;
  subject_name: string;
  grid_type: '2x2' | '3x3' | '4x4';
  frame_count: 4 | 9 | 16;
  frames: KeyframeFrame[];
  generated_at: string;
  source_model?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 关键帧API响应
 */
export interface KeyframeAPIResponse {
  grid_type: string;
  frame_count: number;
  frames: Array<{
    position: number;
    time_ratio: number;
    image_url: string;
    thumbnail_url?: string;
    status: KeyframeStatus;
    error_message?: string;
  }>;
}
```

## Relationships Diagram

```
Project (1) ──────< (N) KeyframeGrid
    │                       │
    │                       │
    ▼                       ▼
StoryboardShot (1) ──< (1) KeyframeGrid
    │                       │
    │                       │
    ▼                       ▼
SubjectAsset (1) ───────< (N) KeyframeGrid
                            │
                            │
                            ▼
                        KeyframeFrame (embedded in frames array)
```

## Notes

- KeyframeGrid 与 StoryboardShot 是一对一关系（每个镜头一个网格）
- KeyframeFrame 以JSON数组形式存储在KeyframeGrid中，非独立表
- 网格大小计算规则应封装为独立函数，便于测试和调整
- 时间进度分布采用均匀分布策略，未来可扩展为自定义分布
