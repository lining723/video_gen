# Quick Start: 主体一致性控制

**Feature**: `20260504-subject-consistency-control`
**Date**: 2026-05-05

## 前置条件

1. 项目已创建并完成场景设计审核
2. 项目已生成分镜脚本并通过审核
3. 后端服务运行在 `http://127.0.0.1:8100`
4. 前端服务运行在 `http://127.0.0.1:3100`

## 快速开始

### 1. 生成基础主体

```bash
# 为项目生成全局主体图
curl -X POST "http://127.0.0.1:8100/api/projects/{projectId}/subjects:generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json"
```

**响应示例**:
```json
{
  "ok": true,
  "items": [
    {
      "id": "subject-001",
      "name": "主角",
      "profile": "项目核心人物",
      "image_path": "projects/proj-001/subject-main-v1.png",
      "source_url": "https://...",
      "feature_description": "25岁亚洲女性，椭圆脸型，杏仁眼...",
      "variant_type": "base",
      "image_version": 1
    }
  ]
}
```

### 2. 编辑特征描述

```bash
# 更新主体的特征描述
curl -X PUT "http://127.0.0.1:8100/api/projects/{projectId}/subjects/{subjectId}" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_description": "25岁亚洲女性，椭圆脸型，杏仁眼，高鼻梁，黑色长发微卷，左眼角有小痣，职业装扮"
  }'
```

### 3. 锁定主体特征

```bash
# 锁定特征，防止意外修改
curl -X POST "http://127.0.0.1:8100/api/projects/{projectId}/subjects/{subjectId}:lock" \
  -H "X-API-Key: your-api-key"
```

### 4. 生成镜头变体

```bash
# 为特定镜头生成主体变体
curl -X POST "http://127.0.0.1:8100/api/projects/{projectId}/subjects/shots/{shotId}:generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "variant",
    "variant_hint": "微笑表情，穿着休闲服装"
  }'
```

**响应示例**:
```json
{
  "ok": true,
  "item": {
    "id": "subject-variant-001",
    "name": "镜头 3",
    "profile": "变体：微笑表情，穿着休闲服装",
    "base_subject_id": "subject-001",
    "variant_type": "variant",
    "variant_hint": "微笑表情，穿着休闲服装",
    "image_version": 1
  }
}
```

### 5. 重新生成主体

```bash
# 重新生成主体图（会创建新版本）
curl -X POST "http://127.0.0.1:8100/api/projects/{projectId}/subjects/{subjectId}:regenerate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "cascade_render": false
  }'
```

### 6. 查看版本历史

```bash
# 获取主体的版本历史
curl "http://127.0.0.1:8100/api/projects/{projectId}/subjects/{subjectId}/versions" \
  -H "X-API-Key: your-api-key"
```

### 7. 回退到历史版本

```bash
# 回退到指定版本
curl -X POST "http://127.0.0.1:8100/api/projects/{projectId}/subjects/{subjectId}:rollback" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "target_version": 1
  }'
```

## 工作流图

```
┌─────────────────┐
│ 分镜审核通过    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 生成基础主体    │ ◄── POST /subjects:generate
│ + 提取特征      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 编辑特征描述    │ ◄── PUT /subjects/{id}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 锁定特征        │ ◄── POST /subjects/{id}:lock
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│渲染   │ │变体   │ ◄── POST /subjects/shots/{shotId}:generate
└───────┘ └───────┘
```

## 错误处理

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 404 | 主体不存在 | 检查 subjectId 是否正确 |
| 400 | 主体已锁定 | 先解锁再编辑 |
| 400 | 变体缺少基础主体 | 确保项目有全局主体 |
| 500 | AI 生成失败 | 重试或使用 fallback |
