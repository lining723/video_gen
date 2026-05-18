# Quickstart: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance`
**Date**: 2026-05-06

## 概述

本文档描述如何验证本次前端 UX 增强功能的四大特性：菜单导航、暗黑模式、列表分页和全局搜索。

## 启动环境

```bash
# 启动后端 (http://127.0.0.1:8100)
make backend

# 启动前端 (http://127.0.0.1:3100)
make frontend
```

## 验证清单

### 1. 全局菜单导航

1. 访问 `http://127.0.0.1:3100` → 顶部导航栏始终可见，包含 "Frame Flow" 品牌标识
2. 点击 "项目首页" 链接 → 跳转到 `#/projects`
3. 进入任意项目 → 左侧出现侧边栏，包含项目名称、状态徽标和 5 个阶段导航链接
4. 侧边栏点击折叠按钮 → 侧边栏收起为图标模式，内容区域扩展
5. 刷新页面 → 折叠状态保持
6. 将浏览器窗口缩小至 < 768px → 侧边栏隐藏，顶部出现汉堡菜单按钮

### 2. 暗黑模式

1. 点击顶部导航栏主题切换按钮 → 页面切换为暗色/亮色模式，过渡平滑
2. 刷新页面 → 主题偏好保持
3. 清除 `localStorage` 中的 `theme-preference` → 页面跟随系统主题
4. 修改操作系统主题设置 → 页面自动跟随（未手动设置时）
5. 检查任意页面 → 文字清晰可读，对比度充足

### 3. 列表分页

1. 创建 25+ 个项目（通过 API 或 UI）
2. 访问项目列表页 → 默认显示前 20 个项目和分页组件
3. 点击 "下一页" → 显示第 2 页数据，URL hash 包含 `?page=2`
4. 切换每页条数为 10 → 数据重载，每页 10 条
5. 访问 `#/projects?page=99` → 自动修正为最后一页
6. 创建 ≤ 5 个项目 → 分页组件仅显示记录信息，不显示页码

### 4. 全局搜索

1. 在顶部导航栏搜索框输入项目名称关键词 → 300ms 后列表过滤
2. 按 `Ctrl+K`（或 `Cmd+K`） → 搜索框获得焦点
3. 搜索后确认 URL hash 包含 `search` 参数
4. 在搜索状态下点击分页 → 保留搜索关键词
5. 搜索不存在的名称 → 显示 "未找到匹配的项目"
6. 按 `Escape` → 清空搜索，恢复完整列表

## API 测试

```bash
# 全量查询（向后兼容）
curl -s http://127.0.0.1:8100/api/projects | jq '.items | length'

# 分页查询
curl -s "http://127.0.0.1:8100/api/projects?page=1&page_size=10" | jq '{total,page,total_pages,count: (.items|length)}'

# 搜索查询
curl -s "http://127.0.0.1:8100/api/projects?search=test" | jq '.items'

# 搜索 + 分页
curl -s "http://127.0.0.1:8100/api/projects?search=test&page=1&page_size=10" | jq '{total,page,total_pages}'
```

## 关键文件

| File | Change | Description |
|------|--------|-------------|
| `frontend/src/modules/layout/AppLayout.tsx` | MODIFY | TopNav + sidebar 重构 |
| `frontend/src/styles/app.css` | MODIFY | Dark theme variables, TopNav styles |
| `frontend/src/utils/theme.ts` | NEW | Theme init, toggle, system follow |
| `frontend/src/utils/url.ts` | NEW | URL hash query param parser |
| `frontend/src/modules/pagination/Pagination.tsx` | NEW | Pagination component |
| `frontend/src/pages/projects/index.tsx` | MODIFY | Pagination + search integration |
| `frontend/src/pages/_app.tsx` | MODIFY | Route metadata, hash query parse |
| `frontend/server.js` | MODIFY | Inline FOUC script in index.html |
| `backend/src/repositories/project_repository.py` | MODIFY | Paginated list with search |
| `backend/src/api/routes/projects.py` | MODIFY | page, page_size, search params |
