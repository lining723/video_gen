# Research: 主体一致性控制

**Feature**: `20260504-subject-consistency-control`
**Date**: 2026-05-05

## 研究问题与结论

### R1: 场景-镜头关系对主体生成的影响

**问题**：用户反馈"场景与镜头一般并不会一一对应"，当前实现是一对一映射。

**发现**：
- 当前 `storyboard_service.py` 强制每个场景生成一个镜头
- 场景存储为 JSON 数组，无独立 ID
- 镜头与场景通过数组索引关联
- AI Gateway prompt 强制 `shots 数量与场景数量一致`

**结论**：
- **Decision**: 本功能聚焦主体一致性，不修改场景-镜头映射逻辑
- **Rationale**: 主体已通过 `shot_id` 关联到镜头层面，现有设计已支持一个场景多个镜头的情况（镜头是独立实体）
- **Alternatives considered**:
  - 修改 AI Gateway prompt 允许生成更多镜头 → 范围过大，应作为独立需求
  - 在场景设计阶段拆分场景 → 前端改动大

**影响范围**：无需修改场景-镜头映射逻辑，主体关联逻辑已正确实现。

---

### R2: 视觉特征提取方案

**问题**：如何从主体图提取视觉特征描述？

**发现**：
- 项目已有 `extract_subject_features` 方法 (`ai_gateway.py:157-192`)
- 支持字段：性别、年龄段、发色、发型、肤色、体型、服装风格、显著特征
- 使用 DeepSeek 文本模型处理结构化提取

**结论**：
- **Decision**: 扩展现有 `extract_subject_features` 方法，增加细粒度字段
- **Rationale**: 现有实现已验证可行，扩展成本低
- **扩展字段建议**：
  - `facial_shape` - 脸型（圆脸、方脸、瓜子脸等）
  - `eye_shape` - 眼型（杏仁眼、丹凤眼等）
  - `accessories` - 配饰（眼镜、耳环、项链等）
  - `posture` - 常见姿态

---

### R3: Prompt 工程最佳实践

**问题**：如何组合 feature_description + variant_hint + style_prompt 保持一致性？

**发现**：
- DashScope wan2.7-image 支持多模态输入（参考图 + 文本）
- 权重模板：`[feature:1.3], [variant:1.1], [style:1.0]`
- 参考图比纯文本更能保持视觉一致性

**结论**：
- **Decision**: 采用"参考图 + 特征描述"双保险策略
- **Rationale**: 参考图提供视觉锚定，特征描述提供语义约束
- **实现方案**：

```python
# 首次生成：纯文本 prompt
prompt = f"{feature_description}。{style_prompt}"

# 变体生成：参考图 + 特征描述
payload = {
    "model": "wan2.7-image-pro",
    "input": {
        "messages": [{
            "role": "user",
            "content": [
                {"image": base_subject_image_url},
                {"text": f"{feature_description}。{variant_hint}"}
            ]
        }]
    }
}
```

---

### R4: 一致性保持技术

**问题**：DashScope wan2.7-image 是否支持参考图？

**发现**：
- ✅ 支持最多 9 张参考图
- ✅ 支持公网 URL、本地路径、Base64
- ✅ `thinking_mode=true` 增强推理能力
- ⚠️ 当前 `dashscope_client.py` 的 `generate_image` 仅支持文本 prompt

**结论**：
- **Decision**: 扩展 `DashScopeClient.generate_image` 支持多模态输入
- **Rationale**: 参考图功能是保证一致性的关键能力
- **实现优先级**: P1（变体生成依赖此能力）

---

### R5: 变体生成失败处理

**问题**：变体生成失败时如何处理？

**结论**：
- **Decision**: 回退使用基础主体图，记录失败原因
- **Rationale**: 保证渲染流程不中断
- **实现**：
  ```python
  try:
      variant = generate_variant(base_subject, variant_hint)
  except GenerationError as e:
      log_event('subject.variant_failed', subject_id=base_subject['id'], error=str(e))
      return base_subject['image_path']  # fallback
  ```

---

## 技术依赖

| 依赖 | 当前状态 | 改动需求 |
|------|----------|----------|
| DeepSeek API | 已集成 | 无需改动 |
| DashScope API | 已集成 | 需扩展多模态输入支持 |
| `extract_subject_features` | 已实现 | 需扩展字段 |
| `subject_versions` 表 | 已存在 | 无需改动 |

## 风险与缓解

| 风险 | 概率 | 缓解措施 |
|------|------|----------|
| AI 无法准确提取特征 | 中 | 用户可手动编辑特征描述 |
| 参考图模式失败 | 低 | 回退到纯文本 prompt |
| 变体一致性不达标 | 中 | 多次生成供用户选择 |
