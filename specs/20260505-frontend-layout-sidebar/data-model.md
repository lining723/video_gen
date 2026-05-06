# Data Model: 前端页面框架优化

**Feature**: `20260505-frontend-layout-sidebar`
**Date**: 2026-05-05

## 概述

本功能为纯前端 UI 改进，无后端数据模型。所有状态存储在浏览器 sessionStorage 中。

## 前端状态

### SidebarState

**存储位置**: `sessionStorage`

**Key**: `sidebar-collapsed`

**Value**:
- `"true"` - 菜单栏收起
- `"false"` - 菜单栏展开
- 未设置 - 默认展开

**生命周期**:
- 页面刷新后保持
- 标签页关闭后清除
- 不同标签页独立

## 数据流

```
用户点击收起按钮
    ↓
toggleSidebar()
    ↓
sidebar.classList.toggle('collapsed')
    ↓
sessionStorage.setItem('sidebar-collapsed', 'true')
    ↓
CSS transition 动画
    ↓
主内容区域 margin-left 调整
```

## CSS 变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `--sidebar-width` | 280px | 菜单栏展开宽度 |
| `--sidebar-collapsed-width` | 64px | 菜单栏收起宽度 |
| `--topbar-height` | 64px | 顶部工具栏高度 |

## DOM 结构

```html
<div class="app-shell">
  <aside class="sidebar">...</aside>
  <header class="topbar">...</header>
  <main class="page-shell">...</main>
</div>
```

## 状态类

| 类名 | 触发条件 | 效果 |
|------|----------|------|
| `.sidebar.collapsed` | 用户收起菜单栏 | 宽度变为 64px |
| `.nav-link.active` | 当前页面菜单项 | 高亮显示 |
