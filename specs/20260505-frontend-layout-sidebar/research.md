# Research: 前端页面框架优化

**Feature**: `20260505-frontend-layout-sidebar`
**Date**: 2026-05-05

## 研究问题与结论

### R1: CSS 固定定位最佳实践

**问题**：如何实现左侧固定菜单栏，同时避免内容被遮挡？

**发现**：
- `position: fixed` 元素脱离正常文档流
- 需要为相邻元素添加 `margin-left` 预留空间
- 使用 CSS 变量管理宽度，便于维护

**结论**：
- **Decision**: 使用 `position: fixed` + `margin-left` 方案
- **Rationale**: 实现简单，兼容性好，无需引入额外布局框架
- **实现方案**:
  ```css
  :root {
    --sidebar-width: 280px;
    --sidebar-collapsed-width: 64px;
  }
  
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: var(--sidebar-width);
    z-index: 100;
  }
  
  .topbar, .page-shell {
    margin-left: var(--sidebar-width);
  }
  ```

---

### R2: sessionStorage 状态管理

**问题**：如何持久化菜单栏展开/收起状态？

**发现**：
- sessionStorage 在页面刷新后保持
- 在页面标签页关闭后清除（符合预期）
- 需要在 DOM 渲染前初始化状态，避免闪烁

**结论**：
- **Decision**: 使用 sessionStorage 存储状态
- **Rationale**: 简单直接，无需后端支持
- **实现方案**:
  ```typescript
  const SIDEBAR_STATE_KEY = 'sidebar-collapsed';
  
  // 初始化（在 DOMContentLoaded 前）
  function initSidebarState() {
    const isCollapsed = sessionStorage.getItem(SIDEBAR_STATE_KEY) === 'true';
    document.documentElement.classList.toggle('sidebar-collapsed', isCollapsed);
  }
  
  // 切换
  function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const isCollapsed = sidebar.classList.toggle('collapsed');
    sessionStorage.setItem(SIDEBAR_STATE_KEY, String(isCollapsed));
  }
  ```

---

### R3: 响应式布局处理

**问题**：小屏幕设备如何处理固定菜单栏？

**发现**：
- 常见断点：768px（平板）、1024px（桌面）
- 小屏幕可自动收起菜单栏
- 使用 CSS media query 处理

**结论**：
- **Decision**: 屏幕宽度 < 768px 时自动收起菜单栏
- **Rationale**: 保持功能可用，同时不占用过多屏幕空间
- **实现方案**:
  ```css
  @media (max-width: 768px) {
    .sidebar {
      width: var(--sidebar-collapsed-width);
    }
    .topbar, .page-shell {
      margin-left: var(--sidebar-collapsed-width);
    }
  }
  ```

---

### R4: 动画过渡优化

**问题**：收起/展开动画如何平滑过渡？

**发现**：
- CSS `transition` 性能优于 JavaScript 动画
- 需要同时过渡 width 和 margin-left
- 使用 `ease` 或 `ease-in-out` 缓动函数

**结论**：
- **Decision**: 使用 CSS transition 实现动画
- **Rationale**: 性能最佳，代码简洁
- **实现方案**:
  ```css
  .sidebar, .topbar, .page-shell {
    transition: width 0.3s ease, margin-left 0.3s ease;
  }
  ```

---

## 技术依赖

| 依赖 | 当前状态 | 改动需求 |
|------|----------|----------|
| AppLayout.tsx | 已存在 | 需修改结构 |
| app.css | 已存在 | 需添加样式 |
| sessionStorage | 浏览器原生 | 无需改动 |

## 风险与缓解

| 风险 | 概率 | 缓解措施 |
|------|------|----------|
| 初始加载闪烁 | 低 | 在 `<head>` 中注入初始化脚本 |
| 移动端显示异常 | 中 | 设置响应式断点 |
| 浏览器兼容性 | 低 | 使用标准 CSS 属性 |
