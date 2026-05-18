# Research: 九宫格关键帧生成

**Feature**: `20260506-subject-keyframe-grid` | **Date**: 2026-05-06

本文档记录技术实现过程中需要研究的关键问题和决策。

## 1. DashScope API 并发限制与最佳实践

### 决策

使用 DashScope `wan2.7-image` 模型生成关键帧图片，采用顺序生成 + 并发控制策略。

### 理由

- **API限流**: DashScope 对图片生成API有并发限制（通常为5-10个并发请求）
- **成本控制**: 顺序生成可更好控制成本，避免突发大量请求
- **错误处理**: 顺序生成更容易实现错误隔离和重试

### 实现方案

```python
# 并发控制配置
KEYFRAME_GENERATION_CONCURRENCY = 3  # 最多3个并发请求
KEYFRAME_GENERATION_DELAY = 0.5      # 每个请求间隔0.5秒

# 使用信号量控制并发
async def generate_frames_with_concurrency(frames_to_generate, max_concurrent=3):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_with_limit(frame_data):
        async with semaphore:
            await asyncio.sleep(KEYFRAME_GENERATION_DELAY)
            return await generate_single_frame(frame_data)

    return await asyncio.gather(*[generate_with_limit(f) for f in frames_to_generate])
```

### 备选方案

1. **完全并发**: 直接并发所有请求
   - 拒绝原因: 可能触发API限流，导致整体失败

2. **完全顺序**: 一个接一个生成
   - 拒绝原因: 16帧需要等待时间过长，用户体验差

## 2. 关键帧生成失败重试策略

### 决策

采用指数退避 + 最大重试次数策略。

### 理由

- **可靠性**: AI服务可能临时不可用，重试提高成功率
- **资源保护**: 限制重试次数避免无限重试消耗资源
- **用户体验**: 用户可手动重试失败帧，不阻塞整体流程

### 实现方案

```python
# 重试配置
MAX_RETRY_COUNT = 3
RETRY_DELAYS = [1, 2, 4]  # 指数退避：1秒、2秒、4秒

async def generate_frame_with_retry(frame_data, retry_count=0):
    try:
        return await generate_single_frame(frame_data)
    except Exception as error:
        if retry_count >= MAX_RETRY_COUNT:
            # 记录失败，返回失败状态
            return FrameResult(status='failed', error=str(error), retry_count=retry_count)

        # 等待后重试
        await asyncio.sleep(RETRY_DELAYS[retry_count])
        return await generate_frame_with_retry(frame_data, retry_count + 1)
```

### 备选方案

1. **立即重试**: 失败后立即重试
   - 拒绝原因: 可能加剧服务负载，导致级联失败

2. **固定间隔重试**: 每次间隔固定时间
   - 拒绝原因: 不如指数退避有效，可能错过服务恢复窗口

## 3. 动态网格布局前端最佳实践

### 决策

使用CSS Grid + 内联样式动态设置列数。

### 理由

- **灵活性**: CSS Grid原生支持动态列数
- **性能**: 浏览器原生实现，性能最优
- **兼容性**: 现代浏览器广泛支持

### 实现方案

```typescript
// 根据grid_type计算列数
const getGridColumns = (gridType: string): string => {
  const cols = parseInt(gridType.split('x')[0], 10);
  return `repeat(${cols}, 1fr)`;
};

// 渲染网格
<div
  className="grid-container"
  style={{
    display: 'grid',
    gridTemplateColumns: getGridColumns(keyframes.grid_type),
    gap: '8px',
  }}
>
  {keyframes.frames.map((frame, index) => (
    <div key={index} className="grid-item">
      <img src={frame.image_url} alt={`帧 ${index + 1}`} />
      <span className="time-label">{(frame.time_ratio * 100).toFixed(0)}%</span>
    </div>
  ))}
</div>
```

### 备选方案

1. **Flexbox布局**: 使用Flexbox + flex-wrap
   - 拒绝原因: 需要手动计算宽度百分比，不如Grid简洁

2. **CSS类切换**: 预定义多个CSS类（.grid-2x2, .grid-3x3, .grid-4x4）
   - 拒绝原因: 维护成本高，内联样式更灵活

## 4. 图片合并下载技术方案

### 决策

前端使用Canvas API合并图片，触发下载。

### 理由

- **浏览器原生**: 无需额外依赖
- **性能良好**: Canvas处理图片性能优秀
- **跨平台**: 所有现代浏览器支持

### 实现方案

```typescript
async function downloadGridAsImage(keyframes: KeyframeData, shotId: string): Promise<void> {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  // 计算网格尺寸
  const cols = parseInt(keyframes.grid_type.split('x')[0], 10);
  const rows = parseInt(keyframes.grid_type.split('x')[1], 10);
  const frameSize = 300; // 每帧大小300x300

  canvas.width = cols * frameSize;
  canvas.height = rows * frameSize;

  // 加载所有图片
  const images = await Promise.all(
    keyframes.frames.map(frame => loadImage(frame.image_url))
  );

  // 绘制到Canvas
  images.forEach((img, index) => {
    const col = index % cols;
    const row = Math.floor(index / cols);
    ctx.drawImage(img, col * frameSize, row * frameSize, frameSize, frameSize);
  });

  // 触发下载
  const url = canvas.toDataURL('image/png');
  const a = document.createElement('a');
  a.href = url;
  a.download = `keyframe-grid-${shotId}.png`;
  a.click();
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous'; // 处理跨域
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}
```

### 备选方案

1. **后端合并**: 服务器端合并图片返回
   - 拒绝原因: 增加服务器负载，网络传输大图片耗时

2. **第三方库**: 使用html2canvas或dom-to-image
   - 拒绝原因: 引入额外依赖，Canvas原生实现足够

## 5. 关键帧Prompt构建策略

### 决策

采用模板化Prompt构建，结合镜头设计和时间进度。

### 理由

- **一致性**: 模板确保Prompt结构一致
- **可控性**: 可调整模板优化生成效果
- **可测试**: 模板便于单元测试

### 实现方案

```python
KEYFRAME_PROMPT_TEMPLATE = '''
角色：{subject_name}，特征：{feature_description}
镜头类型：{shot_type}
运镜：{camera_hint}（{progress}%进度）
背景：{background}
动作指导：{action_direction}（当前阶段：{action_phase}）
场景描述：{description}
时间：{scene_time}
'''.strip()

def build_frame_prompt(shot: dict, subject: SubjectAsset, time_ratio: float, duration: int) -> str:
    # 推断动作阶段
    if time_ratio < 0.33:
        action_phase = "动作起始阶段"
    elif time_ratio < 0.67:
        action_phase = "动作进行中"
    else:
        action_phase = "动作结束阶段"

    # 推断运镜状态
    camera_movement = shot.get('camera_movement', '')
    if '推进' in camera_movement:
        camera_hint = "镜头逐渐推进，画面逐渐放大"
    elif '拉远' in camera_movement:
        camera_hint = "镜头逐渐拉远，画面逐渐缩小"
    elif '平移' in camera_movement:
        camera_hint = "镜头平移中"
    else:
        camera_hint = "镜头固定"

    return KEYFRAME_PROMPT_TEMPLATE.format(
        subject_name=subject.name,
        feature_description=subject.feature_description,
        shot_type=shot.get('shot_type', ''),
        camera_hint=camera_hint,
        progress=int(time_ratio * 100),
        background=shot.get('background', ''),
        action_direction=shot.get('action_direction', ''),
        action_phase=action_phase,
        description=shot.get('description', ''),
        scene_time=shot.get('scene_time', ''),
    )
```

### 备选方案

1. **AI生成Prompt**: 使用LLM根据镜头设计生成Prompt
   - 拒绝原因: 增加延迟和成本，模板化已足够

2. **简单拼接**: 直接拼接镜头字段
   - 拒绝原因: 缺乏时间进度信息，生成效果不理想

## 6. 缓存策略

### 决策

复用现有RenderPipeline缓存机制，基于镜头ID + 主体版本 + 网格类型计算缓存Key。

### 理由

- **一致性**: 与现有视频渲染缓存策略一致
- **可靠性**: 已验证的缓存失效逻辑
- **简洁性**: 无需引入新机制

### 实现方案

```python
def build_keyframe_cache_key(shot: dict, subject_version: int, grid_type: str) -> str:
    """
    构建关键帧缓存Key

    格式: keyframe:{shot_id}:{subject_version}:{grid_type}
    """
    return f"keyframe:{shot['id']}:{subject_version}:{grid_type}"

# 当镜头或主体变化时，缓存自动失效（版本号变化）
```

### 备选方案

1. **独立缓存系统**: 单独实现关键帧缓存
   - 拒绝原因: 增加复杂度，复用现有机制更简洁

2. **无缓存**: 每次重新生成
   - 拒绝原因: 浪费资源，用户体验差

## 总结

所有关键技术决策已完成，无需额外澄清。可直接进入Phase 1设计阶段，生成数据模型、API契约和快速入门文档。
