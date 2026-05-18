# Feature Specification: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid`
**Created**: 2026-05-06
**Status**: Draft
**Input**: 在生成主体图图时,根据镜头设计生成系列九宫格关键帧图片

## Clarifications

### Session 2026-05-06

- Q: 关键帧网格是否固定为3×3？ → A: 不是固定的，根据镜头时长动态调整。可能为2×2、3×3、3×4、4×4等，镜头最长时长为10秒。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 镜头关键帧自动生成 (Priority: P1)

**描述**：
当项目进入主体图生成阶段时，系统不仅为每个主体生成统一形象图，还会根据每个镜头的时长和设计（动作指导、运镜方式、镜头描述等）自动生成关键帧图片网格。网格大小根据镜头时长动态调整：短镜头（1-3秒）生成2×2网格（4帧），中等镜头（4-6秒）生成3×3网格（9帧），长镜头（7-10秒）生成4×4网格（16帧）。这些关键帧帮助用户在视频渲染前直观了解每个镜头的画面走向。

**为什么是这个优先级**：
这是核心功能价值所在——让用户在长耗时的视频渲染前就能预览镜头效果，提前发现问题并调整，避免资源浪费。独立实现即可交付完整的"镜头预览"能力。

**技术实现**：

**1. 数据模型扩展**

在 `SubjectAsset` 模型基础上新增 `KeyframeGrid` 模型：

```python
@dataclass(slots=True)
class KeyframeGrid(BaseRecord):
    project_id: str = ""
    shot_id: str = ""
    subject_name: str = ""  # 关联的主体名称
    grid_type: str = "3x3"  # 网格类型：2x2、3x3、3x4、4x4等，根据镜头时长动态计算
    frame_count: int = 9  # 关键帧数量：4、9、12、16等
    frames: list = field(default_factory=list)  # 关键帧信息列表
    generated_at: str = ""
    source_model: str = ""  # 生成使用的模型版本

@dataclass(slots=True)
class KeyframeFrame:
    position: int  # 网格位置（0到frame_count-1）
    time_ratio: float  # 0.0-1.0，时间进度比例
    image_path: str = ""
    source_url: str = ""
    prompt_used: str = ""  # 生成该帧使用的prompt
```

**2. 状态机扩展**

在 `states.py` 中扩展主体生成阶段：

```python
PROJECT_STATES = {
    # ... existing states ...
    "subject_generating",      # 现有
    "keyframe_generating",     # 新增：关键帧生成中
    "subject_ready",           # 现有（包含关键帧完成）
    # ...
}
```

**3. 关键帧生成逻辑**

在 `SubjectPipeline` 或新建 `KeyframePipeline` 中实现：

```python
def calculate_grid_size(duration: int) -> tuple[str, int]:
    """
    根据镜头时长计算网格大小和关键帧数量

    规则：
    - 1-3秒：2x2（4帧）
    - 4-6秒：3x3（9帧）
    - 7-10秒：4x4（16帧）

    Returns:
        (grid_type, frame_count): 网格类型和帧数量
    """
    if duration <= 3:
        return "2x2", 4
    elif duration <= 6:
        return "3x3", 9
    else:  # 7-10秒
        return "4x4", 16

def generate_keyframes_for_shot(self, shot: dict, subject: SubjectAsset, project: dict) -> KeyframeGrid:
    """
    为单个镜头生成关键帧网格
    """
    duration = shot.get('duration', 6)  # 镜头时长（秒），最长10秒
    grid_type, frame_count = calculate_grid_size(duration)

    # 根据帧数量均匀分布时间进度
    time_ratios = [i / (frame_count - 1) for i in range(frame_count)] if frame_count > 1 else [0.0]

    frames = []
    for i, time_ratio in enumerate(time_ratios):
        # 构建关键帧prompt
        frame_prompt = self._build_frame_prompt(shot, subject, time_ratio, duration)

        # 调用图片生成API
        result = self.ai_gateway.generate_subject_image(
            subject_name=subject.name,
            profile=frame_prompt,
            style_prompt=f"项目风格：{project.get('prompt', '')}",
            feature_description=subject.feature_description,  # 保持主体一致性
        )

        # 存储图片
        storage_path = self.object_store.save_from_url(
            project['id'],
            f'keyframes/{shot["id"]}/frame_{i}.png',
            result.get('provider_url'),
            content_type='image/png'
        )

        frames.append(KeyframeFrame(
            position=i,
            time_ratio=time_ratio,
            image_path=storage_path,
            source_url=result.get('provider_url', ''),
            prompt_used=frame_prompt,
        ).to_dict())

    return KeyframeGrid(
        project_id=project['id'],
        shot_id=shot['id'],
        subject_name=subject.name,
        grid_type=grid_type,
        frame_count=frame_count,
        frames=frames,
        generated_at=utc_now_iso(),
        source_model=result.get('model', ''),
    )
```

**4. 关键帧Prompt构建**

```python
def _build_frame_prompt(self, shot: dict, subject: SubjectAsset, time_ratio: float, duration: int) -> str:
    """
    根据镜头设计和时间进度构建关键帧prompt
    """
    # 根据时间比例推断动作阶段
    if time_ratio < 0.33:
        action_phase = "动作起始阶段"
    elif time_ratio < 0.67:
        action_phase = "动作进行中"
    else:
        action_phase = "动作结束阶段"

    # 运镜状态推断
    camera_movement = shot.get('camera_movement', '')
    if '推进' in camera_movement:
        camera_hint = "镜头逐渐推进，画面逐渐放大"
    elif '拉远' in camera_movement:
        camera_hint = "镜头逐渐拉远，画面逐渐缩小"
    elif '平移' in camera_movement:
        camera_hint = "镜头平移中"
    else:
        camera_hint = "镜头固定"

    prompt = f'''
    角色：{subject.name}，特征：{subject.feature_description}
    镜头类型：{shot.get('shot_type', '')}
    运镜：{camera_hint}（{time_ratio*100:.0f}%进度）
    背景：{shot.get('background', '')}
    动作指导：{shot.get('action_direction', '')}（当前阶段：{action_phase}）
    场景描述：{shot.get('description', '')}
    时间：{shot.get('scene_time', '')}
    '''.strip()

    return prompt
```

**5. 数据库迁移**

新增 `keyframe_grids` 表：

```sql
CREATE TABLE keyframe_grids (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    grid_type TEXT DEFAULT '3x3',  -- 2x2、3x3、3x4、4x4等
    frame_count INTEGER DEFAULT 9,  -- 4、9、12、16等
    frames TEXT NOT NULL,  -- JSON array
    generated_at TEXT NOT NULL,
    source_model TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (shot_id) REFERENCES storyboard_shots(id)
);

CREATE INDEX idx_keyframe_project ON keyframe_grids(project_id);
CREATE INDEX idx_keyframe_shot ON keyframe_grids(shot_id);
```

**6. API端点**

新增获取关键帧接口：

```python
# GET /api/projects/{project_id}/shots/{shot_id}/keyframes
def get_shot_keyframes(project_id: str, shot_id: str) -> dict:
    """
    获取指定镜头的关键帧网格

    返回格式：
    {
        "grid_type": "3x3",  # 或 "2x2"、"4x4"等
        "frame_count": 9,    # 或 4、16等
        "frames": [
            {
                "position": 0,
                "time_ratio": 0.0,
                "image_url": "/media/...",
                "thumbnail_url": "/media/..."
            },
            ...
        ]
    }
    """
```

**7. 异步任务处理**

关键帧生成作为异步任务执行：

```python
# 在 workers/tasks.py 中新增
def submit_keyframe_generation(project: dict, shot: dict, subject: SubjectAsset) -> str:
    """
    提交关键帧生成任务到后台队列
    """
    task = KeyframeTask(
        project_id=project['id'],
        shot_id=shot['id'],
        subject_name=subject.name,
    )
    # 保存任务并返回task_id
    return task.id
```

**独立测试**：
可以通过创建测试项目，完成分镜审核后触发主体生成，验证是否成功为每个镜头根据时长生成对应网格大小的关键帧图片（2×2、3×3或4×4），并通过API获取关键帧预览。

**验收场景**：

1. **Given** 项目状态为 `storyboard_approved`，**When** 触发主体生成，**Then** 系统为每个镜头根据时长生成对应网格大小的关键帧图片（短镜头2×2、中等镜头3×3、长镜头4×4），状态流转为 `subject_ready`
2. **Given** 项目有3个镜头（时长分别为2秒、5秒、8秒），**When** 主体生成完成，**Then** 系统生成 4 + 9 + 16 = 29 张关键帧图片
3. **Given** 关键帧生成任务正在运行，**When** 调用 `/api/projects/{id}/shots/{shot_id}/keyframes`，**Then** 返回已生成的关键帧列表、网格类型和进度状态

---

### User Story 2 - 关键帧预览与下载 (Priority: P2)

**描述**：
用户可以在前端界面上查看每个镜头的关键帧网格预览，支持单张图片查看和整宫格下载。网格布局根据镜头时长动态调整（2×2、3×3或4×4）。用户可以通过关键帧预览判断镜头效果是否符合预期，决定是否需要调整镜头设计或重新生成。

**为什么是这个优先级**：
这是用户交互的关键界面，让关键帧生成的价值得以体现。独立于生成逻辑，可以单独开发和测试前端展示能力。

**技术实现**：

**1. 前端组件设计**

```typescript
// frontend/src/modules/project/components/KeyframeGrid.tsx
interface KeyframeGridProps {
  projectId: string;
  shotId: string;
  onLoad?: () => void;
}

interface KeyframeData {
  grid_type: string;  // "2x2" | "3x3" | "4x4"
  frame_count: number;
  frames: Frame[];
}

const KeyframeGrid: React.FC<KeyframeGridProps> = ({ projectId, shotId, onLoad }) => {
  const [keyframes, setKeyframes] = useState<KeyframeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFrame, setSelectedFrame] = useState<number | null>(null);

  // 获取关键帧数据
  useEffect(() => {
    fetchKeyframes(projectId, shotId).then(data => {
      setKeyframes(data);
      setLoading(false);
      onLoad?.();
    });
  }, [projectId, shotId]);

  // 根据grid_type计算列数
  const getGridColumns = (gridType: string): string => {
    const cols = gridType.split('x')[0];  // 提取列数
    return `repeat(${cols}, 1fr)`;
  };

  // 渲染动态网格布局
  return (
    <div className="keyframe-grid">
      {loading ? (
        <Spin tip="关键帧加载中..." />
      ) : (
        <div
          className="grid-container"
          style={{
            display: 'grid',
            gridTemplateColumns: getGridColumns(keyframes?.grid_type || '3x3'),
            gap: '8px',
            maxWidth: '800px'
          }}
        >
          {keyframes?.frames.map((frame, index) => (
            <div
              key={index}
              className="grid-item"
              onClick={() => setSelectedFrame(index)}
            >
              <img src={frame.image_url} alt={`帧 ${index + 1}`} />
              <span className="time-label">{(frame.time_ratio * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}

      {/* 大图预览 */}
      <Modal
        visible={selectedFrame !== null}
        onCancel={() => setSelectedFrame(null)}
        footer={null}
      >
        {selectedFrame !== null && (
          <img
            src={keyframes?.frames[selectedFrame].image_url}
            alt={`关键帧 ${selectedFrame + 1}`}
            style={{ width: '100%' }}
          />
        )}
      </Modal>
    </div>
  );
};
```

**2. API服务封装**

```typescript
// frontend/src/services/keyframeService.ts
export const keyframeService = {
  getKeyframes: async (projectId: string, shotId: string): Promise<KeyframeData> => {
    const response = await fetch(`/api/projects/${projectId}/shots/${shotId}/keyframes`);
    return response.json();
  },

  downloadGrid: async (projectId: string, shotId: string): Promise<void> => {
    const response = await fetch(`/api/projects/${projectId}/shots/${shotId}/keyframes/download`);
    const blob = await response.blob();
    // 触发下载
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `keyframe-grid-${shotId}.png`;
    a.click();
  },
};
```

**3. 样式设计**

```css
/* frontend/src/modules/project/styles/keyframe.css */
.keyframe-grid {
  margin: 16px 0;
}

.grid-container {
  gap: 8px;
  max-width: 800px;
  /* grid-template-columns 通过内联样式动态设置 */
}

.grid-item {
  position: relative;
  aspect-ratio: 1;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
}

.grid-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.grid-item .time-label {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 6px;
  border-radius: 2px;
  font-size: 12px;
}
```

**4. 页面集成**

在镜头详情页展示关键帧：

```typescript
// frontend/src/modules/project/pages/ShotDetailPage.tsx
const ShotDetailPage: React.FC = () => {
  const { projectId, shotId } = useParams();

  return (
    <div className="shot-detail">
      <h2>镜头详情</h2>

      {/* 现有镜头信息展示 */}
      <ShotInfo shotId={shotId} />

      {/* 新增：关键帧预览 */}
      <section className="keyframe-section">
        <h3>镜头关键帧预览</h3>
        <KeyframeGrid projectId={projectId} shotId={shotId} />
        <Button onClick={() => keyframeService.downloadGrid(projectId, shotId)}>
          下载九宫格
        </Button>
      </section>

      {/* 现有视频渲染控制 */}
      <RenderControl projectId={projectId} shotId={shotId} />
    </div>
  );
};
```

**独立测试**：
可以通过创建测试数据，在前端页面验证九宫格展示是否正确，点击单帧是否能放大查看，下载功能是否正常工作。

**验收场景**：

1. **Given** 镜头已生成关键帧，**When** 用户访问镜头详情页，**Then** 页面展示动态网格关键帧预览（根据镜头时长显示2×2、3×3或4×4布局），每帧显示时间进度标签
2. **Given** 用户查看关键帧网格预览，**When** 点击某一张关键帧，**Then** 弹出大图预览模态框
3. **Given** 用户点击"下载关键帧网格"按钮，**When** 下载完成，**Then** 获得包含所有关键帧的合并图片文件

---

### User Story 3 - 关键帧生成失败处理 (Priority: P3)

**描述**：
当关键帧生成过程中出现失败（如AI服务不可用、网络超时等），系统应能够优雅降级，部分成功的关键帧仍可展示，失败的关键帧显示占位图并提示重试。用户可以单独重新生成失败的关键帧。

**为什么是这个优先级**：
这是系统健壮性保障，确保即使在部分失败的情况下，用户仍能获得可用的预览。不影响核心功能的独立测试和交付。

**技术实现**：

**1. 失败状态记录**

```python
@dataclass(slots=True)
class KeyframeFrame:
    position: int
    time_ratio: float
    image_path: str = ""
    source_url: str = ""
    prompt_used: str = ""
    status: str = "pending"  # pending, generating, succeeded, failed
    error_message: str = ""
    retry_count: int = 0
```

**2. 部分失败处理**

```python
def generate_keyframes_for_shot(self, shot: dict, subject: SubjectAsset, project: dict) -> KeyframeGrid:
    duration = shot.get('duration', 6)
    grid_type, frame_count = calculate_grid_size(duration)
    time_ratios = [i / (frame_count - 1) for i in range(frame_count)] if frame_count > 1 else [0.0]

    frames = []
    for i, time_ratio in enumerate(time_ratios):
        try:
            # 尝试生成关键帧
            result = self.ai_gateway.generate_subject_image(...)
            frame = KeyframeFrame(
                position=i,
                time_ratio=time_ratio,
                status='succeeded',
                ...
            )
        except Exception as error:
            # 记录失败，继续生成下一帧
            log_event('keyframe.generation_failed', project_id=project['id'], shot_id=shot['id'], position=i, error=str(error))
            frame = KeyframeFrame(
                position=i,
                time_ratio=time_ratio,
                status='failed',
                error_message=str(error),
            )
        frames.append(frame)

    # 即使部分失败，仍返回整个Grid
    return KeyframeGrid(grid_type=grid_type, frame_count=frame_count, frames=frames, ...)
```

**3. 重试机制**

```python
# POST /api/projects/{project_id}/shots/{shot_id}/keyframes/{position}/retry
def retry_keyframe(project_id: str, shot_id: str, position: int) -> dict:
    """
    重新生成指定的关键帧
    """
    grid = keyframe_repo.get_by_shot(project_id, shot_id)
    frame = grid.frames[position]

    if frame.retry_count >= MAX_RETRY_COUNT:
        raise ValueError(f"重试次数已达上限 {MAX_RETRY_COUNT}")

    # 更新状态并重新提交任务
    frame.status = 'generating'
    frame.retry_count += 1
    keyframe_repo.save(grid)

    # 异步重新生成
    submit_task(generate_single_keyframe, project_id, shot_id, position)

    return {"status": "retrying", "retry_count": frame.retry_count}
```

**4. 前端失败展示**

```typescript
const KeyframeGrid: React.FC<KeyframeGridProps> = ({ projectId, shotId }) => {
  const [keyframes, setKeyframes] = useState<KeyframeData | null>(null);

  const handleRetry = async (position: number) => {
    await keyframeService.retryKeyframe(projectId, shotId, position);
    message.success('正在重新生成关键帧...');
    // 重新加载数据
    loadKeyframes();
  };

  return (
    <div className="grid-container">
      {keyframes?.frames.map((frame, index) => (
        <div key={index} className="grid-item">
          {frame.status === 'succeeded' ? (
            <img src={frame.image_url} alt={`帧 ${index + 1}`} />
          ) : frame.status === 'failed' ? (
            <div className="failed-frame">
              <WarningOutlined />
              <span>生成失败</span>
              <Button size="small" onClick={() => handleRetry(index)}>
                重试
              </Button>
            </div>
          ) : (
            <Spin />
          )}
        </div>
      ))}
    </div>
  );
};
```

**独立测试**：
可以通过模拟AI服务失败场景，验证系统是否能够记录失败状态，前端是否正确展示失败占位图，重试功能是否正常工作。

**验收场景**：

1. **Given** 关键帧生成过程中第3、5、7帧失败，**When** 生成完成，**Then** 系统返回包含9帧的Grid，其中3帧状态为failed，其余为succeeded
2. **Given** 用户查看失败的关键帧，**When** 点击重试按钮，**Then** 系统重新提交该帧生成任务，前端显示加载状态
3. **Given** 某关键帧重试次数已达上限，**When** 用户点击重试，**Then** 系统提示"重试次数已达上限，请联系管理员"

---

### Edge Cases

- **场景1：镜头时长边界值**
  - 问题：镜头时长为1秒或10秒等边界值时
  - 处理：按照网格大小计算规则，1-3秒使用2×2，7-10秒使用4×4

- **场景2：镜头时长为0或负数**
  - 问题：镜头时长异常值
  - 处理：使用默认时长6秒，生成3×3网格

- **场景3：镜头无主体引用**
  - 问题：镜头的 `subject_refs` 为空，无法关联主体特征
  - 处理：使用项目默认主体或提示用户需要先添加主体

- **场景4：主体特征描述为空**
  - 问题：`feature_description` 未生成或生成失败
  - 处理：使用主体名称和profile作为fallback，确保关键帧仍可生成

- **场景5：并发生成资源限制**
  - 问题：同时生成大量关键帧（特别是4×4网格的16帧）可能触发API限流
  - 处理：实现队列机制，控制并发数，避免触发限流

- **场景6：用户中途取消项目**
  - 问题：关键帧生成任务仍在运行
  - 处理：实现任务取消机制，清理已生成的临时文件

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须为每个已审核通过的镜头根据时长自动生成对应网格大小的关键帧图片（1-3秒：2×2共4张，4-6秒：3×3共9张，7-10秒：4×4共16张）
- **FR-002**: 系统必须根据镜头设计（镜头类型、运镜方式、动作指导、背景、时长等）构建关键帧生成Prompt
- **FR-003**: 系统必须确保同一镜头的关键帧保持主体视觉一致性（使用主体特征描述）
- **FR-004**: 系统必须按时间进度均匀分布关键帧（根据网格大小计算时间间隔）
- **FR-005**: 系统必须支持关键帧图片的持久化存储（对象存储或文件系统）
- **FR-006**: 系统必须提供API接口获取指定镜头的关键帧列表（包含网格类型和帧数量）
- **FR-007**: 系统必须在前端界面展示动态网格关键帧预览（根据网格类型调整布局）
- **FR-008**: 系统必须支持关键帧的单张查看和整宫格下载
- **FR-009**: 系统必须支持关键帧生成失败的部分成功处理（记录失败状态，不影响其他帧）
- **FR-010**: 系统必须支持失败关键帧的单帧重试（最多重试3次）
- **FR-011**: 系统必须将关键帧生成作为异步任务执行，支持状态跟踪
- **FR-012**: 系统必须记录关键帧生成日志（项目ID、镜头ID、网格类型、帧数量、生成时间、模型版本、成功/失败状态）

### Key Entities

- **KeyframeGrid（关键帧网格）**: 代表一个镜头的所有关键帧集合，根据镜头时长包含4、9或16个KeyframeFrame，关联到项目ID和镜头ID，包含网格类型（2x2、3x3、4x4）和帧数量字段
- **KeyframeFrame（单个关键帧）**: 代表网格中的一个位置，包含时间进度比例、图片路径、生成状态、Prompt等信息
- **SubjectAsset（主体资产）**: 现有实体，关键帧生成需引用主体的特征描述以保持一致性
- **StoryboardShot（镜头设计）**: 现有实体，关键帧生成基于镜头设计构建Prompt，时长字段决定网格大小

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可在视频渲染前查看镜头关键帧预览，90%的用户能在关键帧阶段发现并修正明显问题
- **SC-002**: 关键帧生成成功率达到95%以上（单帧成功率），整个网格全部成功的比例达到85%以上
- **SC-003**: 单个关键帧网格生成时间在5分钟以内（最长镜头4×4共16张图片）
- **SC-004**: 前端关键帧预览加载时间在2秒以内（使用缩略图优化）
- **SC-005**: 关键帧生成失败后重试成功率达到80%以上
- **SC-006**: 关键帧展示能帮助用户在视频渲染前减少至少50%的明显错误返工

## Assumptions

- 假设AI图片生成服务（DashScope）支持足够的并发和速率限制，可支持同时生成多个关键帧（最长镜头需生成16张）
- 假设用户认可根据镜头时长动态调整网格大小的方式，不需要手动指定网格类型
- 假设关键帧仅用于预览和参考，不直接用于最终视频渲染（视频渲染仍使用主体图作为首帧）
- 假设关键帧生成在主体图生成之后、视频渲染之前进行，不改变现有主体图生成流程
- 假设关键帧图片采用PNG格式存储，分辨率与主体图一致
- 假设关键帧网格下载功能输出单张合并图片，而非多个独立文件
- 假设镜头时长最长为10秒，超出部分按10秒处理（生成4×4网格）

## Dependencies

- 依赖现有主体图生成流程（SubjectPipeline）和主体资产（SubjectAsset）
- 依赖现有AI网关（AIGateway）的图片生成能力
- 依赖现有对象存储服务（ObjectStore）的文件存储能力
- 依赖现有异步任务机制（workers/tasks）的任务调度能力

## Out of Scope

- 基于关键帧直接生成视频（关键帧仅用于预览，视频生成仍使用现有i2v流程）
- 用户手动编辑或调整关键帧（自动生成，不支持手动修改）
- 关键帧的时间线编辑功能（不支持拖拽调整关键帧位置）
- 用户自定义网格大小（固定按照时长规则：1-3秒→2×2，4-6秒→3×3，7-10秒→4×4）
- 超过4×4网格的关键帧数量
- 关键帧与最终视频的自动对齐验证

## Technical Notes

- 关键帧生成应考虑与现有RenderPipeline的缓存机制集成，当镜头或主体变化时失效关键帧缓存
- 前端展示关键帧时应使用缩略图优化加载速度，避免一次性加载大量大图（特别是4×4网格的16张图片）
- 关键帧存储路径应遵循现有目录结构规范：`{project_id}/keyframes/{shot_id}/frame_{position}.png`
- 关键帧生成日志应集成到现有审计服务（AuditService）中，包含网格类型和帧数量信息
- 状态机扩展需要考虑向后兼容，现有项目状态应能正常迁移
- 网格大小计算规则应封装为独立函数，便于后续调整和测试
- 对于4×4网格（16帧），需要特别注意API限流和并发控制策略
