# Data Model: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance`
**Date**: 2026-05-06

## 概述

本功能不引入新的数据库表或修改现有数据库 schema。数据模型变更仅限于：
1. 后端 `ProjectRepository.list()` 增加查询参数（分页、搜索）
2. 前端新增浏览器端存储的键值对（主题偏好）
3. URL hash 查询参数规范（分页、搜索状态）

## 浏览器端存储

### localStorage

| Key | Type | Values | Default | Description |
|-----|------|--------|---------|-------------|
| `theme-preference` | string | `"light"` \| `"dark"` | (none, follows system) | 用户手动选择的主题模式。不存在时跟随 `prefers-color-scheme` |

### sessionStorage

| Key | Type | Values | Default | Description |
|-----|------|--------|---------|-------------|
| `sidebar-collapsed` | string | `"true"` \| `"false"` | `"false"` | 侧边栏折叠状态（已存在，本次重构不改动 key） |

## URL Hash 查询参数

所有参数为可选，附加在 hash 路由的 `?` 之后：

```
#/projects?page=1&page_size=20&search=keyword
```

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | integer | `1` | ≥ 1 | 当前页码 |
| `page_size` | integer | `20` | 10, 20, 50 | 每页条数 |
| `search` | string | `""` | any | 项目名称搜索关键词（URL 编码） |

**状态协同规则**:
- 搜索变化时 → `page` 重置为 `1`
- `page_size` 变化时 → `page` 重置为 `1`
- 清除搜索时 → `search` 移除，`page` 重置为 `1`
- 浏览器前进/后退 → 从 URL 重新解析所有参数并重新加载数据

## API 数据结构

### 项目列表响应（扩展）

现有响应格式:
```json
{
  "ok": true,
  "items": [...]
}
```

分页模式响应（新增字段）:
```json
{
  "ok": true,
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

| Field | Type | Always Present | Description |
|-------|------|---------------|-------------|
| `ok` | boolean | Yes | 请求是否成功 |
| `items` | array | Yes | 项目对象列表 |
| `total` | integer | Only with `page` param | 符合条件的总条数 |
| `page` | integer | Only with `page` param | 当前页码 |
| `page_size` | integer | Only with `page` param | 每页条数 |
| `total_pages` | integer | Only with `page` param | 总页数 |

**向后兼容**: 不传 `page` 参数时，响应保持原有格式（仅 `ok` + `items`），行为不变。

## 项目对象（Project）

现有结构，本次无变更。关键字段：

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | UUID 主键 |
| `name` | string | 项目名称（搜索目标字段） |
| `prompt` | string | 项目提示词 |
| `status` | string | 项目状态 |
| `current_stage` | string | 当前阶段 |
| `created_at` | string | 创建时间（排序字段，ISO 8601） |
| ... | | （其他字段不变） |

## 主题 CSS 变量

亮色和暗色模式共用同一套变量名，通过 `[data-theme]` 选择器覆写值。

| Variable | Light (default) | Dark | Usage |
|----------|-----------------|------|-------|
| `--bg` | `#f4efe7` | `#1a1a1a` | 页面背景 |
| `--bg-deep` | `#e8dfd2` | `#0d0d0d` | 深层背景 |
| `--surface` | `rgba(255,252,247,0.82)` | `rgba(30,30,30,0.82)` | 卡片表面 |
| `--surface-strong` | `rgba(255,251,245,0.94)` | `rgba(40,40,40,0.94)` | 强调表面 |
| `--surface-border` | `rgba(34,29,24,0.1)` | `rgba(255,255,255,0.08)` | 表面边框 |
| `--text` | `#1d1a17` | `#e8e4df` | 正文颜色 |
| `--text-muted` | `#6c6258` | `#9d958b` | 次要文字 |
| `--accent` | `#b85c38` | `#d4754e` | 强调色 |
| `--accent-soft` | `rgba(184,92,56,0.14)` | `rgba(212,117,78,0.18)` | 柔和强调 |
| `--accent-strong` | `#9f4927` | `#e08a60` | 强调色深色 |
| `--success` | `#2f6b53` | `#4d9b7e` | 成功色 |
| `--warning` | `#af5a2a` | `#d48a5a` | 警告色 |
| `--shadow` | `0 24px 80px rgba(72,49,30,0.12)` | `0 24px 80px rgba(0,0,0,0.3)` | 阴影 |
| `--topbar-height` | `64px` | `64px` | 顶栏高度（不变） |

## 路由元数据

路由配置集中定义在 `_app.tsx` 中：

| Path | Title | Stage | requiresProject |
|------|-------|-------|-----------------|
| `/projects` | 项目列表 | — | No |
| `/projects/:projectId` | 项目总览 | overview | Yes |
| `/projects/:projectId/scene` | 场景审核 | scene | Yes |
| `/projects/:projectId/storyboard` | 分镜编辑 | storyboard | Yes |
| `/projects/:projectId/renders` | 渲染控制 | renders | Yes |
| `/projects/:projectId/final-video` | 最终成片 | final-video | Yes |
