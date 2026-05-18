# Quick Start: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid` | **Date**: 2026-05-06

本文档帮助开发者快速理解和使用关键帧生成功能。

## 功能概述

关键帧生成功能为每个镜头根据时长自动生成对应数量的关键帧图片：
- **短镜头**（1-3秒）：2×2 网格（4帧）
- **中等镜头**（4-6秒）：3×3 网格（9帧）
- **长镜头**（7-10秒）：4×4 网格（16帧）

关键帧帮助用户在视频渲染前预览镜头效果，提前发现问题并调整。

## 快速开始

### 1. 后端设置

#### 1.1 数据库迁移

运行数据库迁移创建关键帧表：

```bash
cd backend
python migrations/migrate.py
```

迁移脚本会创建 `keyframe_grids` 表。

#### 1.2 启动后端服务

```bash
make backend
```

后端服务将在 http://127.0.0.1:8100 启动。

### 2. 前端设置

#### 2.1 安装依赖

```bash
cd frontend
npm install
```

#### 2.2 启动前端服务

```bash
make frontend
```

前端服务将在 http://127.0.0.1:3100 启动。

### 3. 使用流程

#### 3.1 创建项目并完成分镜审核

1. 创建新项目，输入创意需求
2. 系统自动生成场景设计
3. 审核并批准场景设计
4. 系统自动生成分镜脚本
5. 审核并批准分镜脚本

#### 3.2 触发主体生成和关键帧生成

分镜审核通过后，系统自动触发主体图生成，随后生成关键帧：

```
分镜审核通过 → 主体图生成 → 关键帧生成 → 视频渲染
```

#### 3.3 查看关键帧预览

访问镜头详情页，查看关键帧网格预览：

```
http://localhost:3100/projects/{project_id}/shots/{shot_id}
```

## API 使用示例

### 获取镜头关键帧

**请求**:
```bash
curl -X GET "http://127.0.0.1:8100/api/projects/{project_id}/shots/{shot_id}/keyframes" \
  -H "Authorization: Bearer {api_key}"
```

**响应**:
```json
{
  "grid_type": "3x3",
  "frame_count": 9,
  "frames": [
    {
      "position": 0,
      "time_ratio": 0.0,
      "image_url": "/media/projects/proj-123/keyframes/shot-456/frame_0.png",
      "status": "succeeded"
    },
    {
      "position": 1,
      "time_ratio": 0.125,
      "image_url": "/media/projects/proj-123/keyframes/shot-456/frame_1.png",
      "status": "succeeded"
    }
    // ... 更多关键帧
  ]
}
```

### 下载关键帧网格

**请求**:
```bash
curl -X GET "http://127.0.0.1:8100/api/projects/{project_id}/shots/{shot_id}/keyframes/download" \
  -H "Authorization: Bearer {api_key}" \
  -o keyframe-grid.png
```

**响应**: PNG图片文件

### 重试失败的关键帧

**请求**:
```bash
curl -X POST "http://127.0.0.1:8100/api/projects/{project_id}/shots/{shot_id}/keyframes/5/retry" \
  -H "Authorization: Bearer {api_key}"
```

**响应**:
```json
{
  "status": "retrying",
  "retry_count": 1,
  "message": "关键帧重新生成任务已提交"
}
```

## 前端组件使用

### 基本用法

```tsx
import { KeyframeGrid } from '@/modules/project/components/KeyframeGrid';

const ShotDetailPage: React.FC = () => {
  const { projectId, shotId } = useParams();

  return (
    <div>
      <h2>镜头详情</h2>

      {/* 关键帧预览 */}
      <section>
        <h3>镜头关键帧预览</h3>
        <KeyframeGrid
          projectId={projectId}
          shotId={shotId}
          onLoad={() => console.log('关键帧加载完成')}
        />
      </section>
    </div>
  );
};
```

### 自定义样式

```tsx
import { KeyframeGrid } from '@/modules/project/components/KeyframeGrid';
import './custom-keyframe.css';

const CustomKeyframePage: React.FC = () => {
  return (
    <div className="custom-keyframe-container">
      <KeyframeGrid projectId="proj-123" shotId="shot-456" />
    </div>
  );
};
```

```css
/* custom-keyframe.css */
.custom-keyframe-container .grid-container {
  max-width: 1000px;
  gap: 12px;
}

.custom-keyframe-container .grid-item {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

## 开发指南

### 添加新的网格类型

1. **修改网格计算函数**（后端）：

```python
# backend/src/orchestrators/keyframe_pipeline.py

def calculate_grid_size(duration: int) -> tuple[str, int]:
    if duration <= 3:
        return "2x2", 4
    elif duration <= 6:
        return "3x3", 9
    elif duration <= 10:
        return "4x4", 16
    # 新增：超长镜头
    elif duration <= 15:
        return "4x5", 20
    else:
        return "5x5", 25
```

2. **更新数据模型验证**：

```python
# backend/src/schemas/keyframe_grid.py

@dataclass(slots=True)
class KeyframeGrid(BaseRecord):
    grid_type: str = "3x3"  # 扩展为支持 "4x5", "5x5" 等
    frame_count: int = 9     # 扩展为支持 20, 25 等
```

3. **更新前端组件**：

```typescript
// frontend/src/modules/project/components/KeyframeGrid.tsx

const getGridColumns = (gridType: string): string => {
  const cols = parseInt(gridType.split('x')[0], 10);
  return `repeat(${cols}, 1fr)`;
};
```

### 自定义Prompt模板

修改关键帧Prompt构建函数：

```python
# backend/src/orchestrators/keyframe_pipeline.py

KEYFRAME_PROMPT_TEMPLATE = '''
{custom_style_instruction}

角色：{subject_name}，特征：{feature_description}
镜头类型：{shot_type}
运镜：{camera_hint}（{progress}%进度）
背景：{background}
动作指导：{action_direction}（当前阶段：{action_phase}）
场景描述：{description}
时间：{scene_time}
'''.strip()
```

## 测试

### 运行后端测试

```bash
cd backend
pytest tests/test_keyframe_pipeline.py -v
```

### 运行前端测试

```bash
cd frontend
npm test -- KeyframeGrid.test.tsx
```

## 常见问题

### Q: 关键帧生成失败怎么办？

A: 系统支持部分成功和单帧重试。在镜头详情页查看失败的关键帧，点击"重试"按钮重新生成。如重试次数达到上限，请联系管理员。

### Q: 如何调整网格大小规则？

A: 修改 `calculate_grid_size()` 函数中的时长阈值和网格类型映射。

### Q: 关键帧图片存储在哪里？

A: 关键帧图片存储在对象存储中，路径格式：`{project_id}/keyframes/{shot_id}/frame_{position}.png`

### Q: 关键帧生成需要多长时间？

A: 单帧生成约20秒，整个网格生成时间取决于帧数量：
- 2×2（4帧）：约1-2分钟
- 3×3（9帧）：约3-4分钟
- 4×4（16帧）：约5分钟

## 下一步

- 查看 [API文档](./contracts/openapi.yaml) 了解完整API接口
- 查看 [数据模型](./data-model.md) 了解数据结构
- 查看 [研究成果](./research.md) 了解技术决策

## 支持

如有问题，请联系开发团队或提交Issue。
