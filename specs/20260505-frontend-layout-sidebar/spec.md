# Feature Specification: 前端页面框架优化 - 左侧固定菜单栏

**Feature**: `20260505-frontend-layout-sidebar`
**Created**: 2026-05-05
**Status**: Draft
**Input**: User description: "前端页面框架优化, 采用左边固定菜单栏,菜单栏支持收起,其他区域为对应的菜单渲染区域"

## 用户需求概述

优化前端页面布局结构，实现：
- **左侧固定菜单栏**：将现有侧边栏改为固定定位，始终可见
- **菜单栏收起/展开**：用户可控制菜单栏宽度，收起时仅显示图标
- **主内容区域自适应**：菜单栏收起时，主内容区域自动扩展

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 左侧固定菜单栏布局 (Priority: P1)

用户进入项目页面，左侧显示固定的导航菜单栏，包含制作流程的各个阶段（项目总览、场景审核、分镜编辑、渲染控制、最终成片）。菜单栏在页面滚动时保持固定，不随内容滚动。

**Why this priority**: 这是整个布局优化的基础。固定菜单栏是用户导航的核心入口，必须首先实现才能支持后续的收起/展开功能。

**Technical Implementation**:

1. **CSS 布局调整**：
   - 修改 `.app-shell` 使用 flex 布局
   - 侧边栏使用 `position: fixed` + `left: 0` + `top: 0` + `height: 100vh`
   - 主内容区域添加 `margin-left` 为侧边栏宽度
   - 顶部工具栏 (`topbar`) 需要调整 `left` 偏移以避免被侧边栏遮挡

2. **HTML 结构调整**：
   - 在 `frontend/src/modules/layout/AppLayout.tsx` 中修改 `appShell` 函数
   - 将 sidebar 提升为与 topbar 同级，而非嵌套在 content-grid 内

3. **CSS 变量定义**：
   ```css
   --sidebar-width: 280px;
   --sidebar-collapsed-width: 64px;
   --topbar-height: 64px;
   ```

4. **关键样式**：
   ```css
   .app-shell {
     display: flex;
     flex-direction: column;
   }
   
   .sidebar {
     position: fixed;
     left: 0;
     top: 0;
     height: 100vh;
     width: var(--sidebar-width);
     z-index: 100;
     transition: width 0.3s ease;
   }
   
   .topbar {
     margin-left: var(--sidebar-width);
     transition: margin-left 0.3s ease;
   }
   
   .page-shell {
     margin-left: var(--sidebar-width);
     transition: margin-left 0.3s ease;
   }
   ```

**Independent Test**: 打开任意项目页面，滚动页面内容，验证左侧菜单栏保持固定不动。

**Acceptance Scenarios**:

1. **Given** 用户进入项目页面，**When** 页面加载完成，**Then** 左侧显示固定菜单栏，包含所有导航项
2. **Given** 用户在项目页面滚动内容，**When** 滚动到页面底部，**Then** 左侧菜单栏仍然可见，未随内容滚动
3. **Given** 项目页面包含长内容，**When** 用户滚动时，**Then** 菜单栏始终吸附在视口左侧

---

### User Story 2 - 菜单栏收起/展开功能 (Priority: P2)

用户可以通过点击菜单栏底部的收起按钮，将菜单栏收起为仅显示图标的窄条模式。收起后，主内容区域自动扩展以利用更多屏幕空间。用户再次点击可展开恢复完整菜单。

**Why this priority**: 收起/展开是重要的用户体验增强功能，允许用户根据需要调整工作空间大小，但不影响核心导航功能。

**Technical Implementation**:

1. **状态管理**：
   - 使用 `sessionStorage` 存储菜单栏展开/收起状态
   - Key: `sidebar-collapsed`

2. **切换按钮**：
   - 在侧边栏底部添加切换按钮
   - 收起状态：显示展开图标 (→)
   - 展开状态：显示收起图标 (←)

3. **CSS 状态切换**：
   ```css
   .sidebar.collapsed {
     width: var(--sidebar-collapsed-width);
   }
   
   .sidebar.collapsed .nav-link span {
     display: none;
   }
   
   .sidebar.collapsed ~ .page-shell {
     margin-left: var(--sidebar-collapsed-width);
   }
   ```

4. **JavaScript 实现**：
   ```typescript
   const SIDEBAR_STATE_KEY = 'sidebar-collapsed';
   
   function toggleSidebar() {
     const sidebar = document.querySelector('.sidebar');
     const isCollapsed = sidebar.classList.toggle('collapsed');
     sessionStorage.setItem(SIDEBAR_STATE_KEY, String(isCollapsed));
   }
   
   function initSidebarState() {
     const isCollapsed = sessionStorage.getItem(SIDEBAR_STATE_KEY) === 'true';
     if (isCollapsed) {
       document.querySelector('.sidebar')?.classList.add('collapsed');
     }
   }
   ```

5. **图标设计**：
   - 为每个菜单项添加图标（使用 CSS 或 SVG）
   - 收起状态下仅显示图标，hover 时显示 tooltip

**Independent Test**: 点击收起按钮，验证菜单栏宽度变窄且仅显示图标；点击展开按钮，验证菜单栏恢复完整宽度。

**Acceptance Scenarios**:

1. **Given** 菜单栏处于展开状态，**When** 用户点击收起按钮，**Then** 菜单栏宽度变为 64px，仅显示图标
2. **Given** 菜单栏处于收起状态，**When** 用户点击展开按钮，**Then** 菜单栏宽度恢复为 280px，显示完整菜单项
3. **Given** 用户收起菜单栏后刷新页面，**When** 页面重新加载，**Then** 菜单栏保持收起状态
4. **Given** 菜单栏收起时，**When** 用户 hover 某个菜单图标，**Then** 显示该菜单项的 tooltip 提示

---

### User Story 3 - 菜单切换和内容渲染 (Priority: P3)

用户点击菜单项后，主内容区域切换显示对应的内容页面，当前选中的菜单项高亮显示。页面切换时保持菜单栏状态不变。

**Why this priority**: 这是导航功能的核心，确保用户能够通过菜单栏流畅地在不同功能模块间切换。

**Technical Implementation**:

1. **当前实现分析**：
   - 现有 `stageItems` 数组定义了导航项
   - 使用 `currentView` 参数标记当前选中项
   - 通过 hash 路由 (`#/projects/{projectId}/{view}`) 切换页面

2. **高亮状态增强**：
   - 收起状态下，选中项通过背景色或边框指示
   - 展开状态下，选中项保持现有 `.nav-link.active` 样式

3. **页面切换逻辑**：
   - 当前已通过 `<a>` 标签的 `href` 实现路由跳转
   - 无需额外 JavaScript 处理，保持现有行为

4. **图标添加**：
   ```typescript
   const stageItems = [
     { key: 'overview', label: '项目总览', icon: '📊', href: ... },
     { key: 'scene', label: '场景审核', icon: '🎬', href: ... },
     { key: 'storyboard', label: '分镜编辑', icon: '📝', href: ... },
     { key: 'renders', label: '渲染控制', icon: '⚙️', href: ... },
     { key: 'final-video', label: '最终成片', icon: '🎬', href: ... },
   ];
   ```

**Independent Test**: 点击不同的菜单项，验证主内容区域正确切换，当前菜单项高亮显示。

**Acceptance Scenarios**:

1. **Given** 用户在"场景审核"页面，**When** 点击"分镜编辑"菜单项，**Then** 页面切换到分镜编辑，且"分镜编辑"菜单项高亮
2. **Given** 菜单栏处于收起状态，**When** 用户点击某个菜单图标，**Then** 页面正确切换，选中的图标高亮
3. **Given** 用户切换页面后，**When** 页面刷新，**Then** 菜单栏的选中状态与当前页面一致

---

### Edge Cases

- 当屏幕宽度小于 768px 时如何处理？→ 菜单栏自动收起或隐藏，提供汉堡菜单按钮
- 当用户快速连续点击收起/展开按钮时如何处理？→ 使用 CSS transition 防止动画重叠
- 当页面内容高度不足一屏时，菜单栏底部如何对齐？→ 使用 `height: 100vh` 确保菜单栏撑满视口
- 项目列表页（非项目内页）是否显示菜单栏？→ 不显示，保持现有布局

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在项目页面显示左侧固定菜单栏
- **FR-002**: 菜单栏 MUST 包含完整的制作流程导航项（项目总览、场景审核、分镜编辑、渲染控制、最终成片）
- **FR-003**: 菜单栏 MUST 在页面滚动时保持固定位置
- **FR-004**: 用户 MUST 能够收起菜单栏至图标模式
- **FR-005**: 用户 MUST 能够展开收起的菜单栏
- **FR-006**: 菜单栏收起状态 MUST 在页面刷新后保持
- **FR-007**: 菜单栏收起时 MUST 显示每个菜单项的图标
- **FR-008**: 主内容区域 MUST 根据菜单栏状态自适应宽度
- **FR-009**: 当前页面菜单项 MUST 高亮显示
- **FR-010**: 项目列表页 MUST NOT 显示侧边菜单栏

### Key Entities

- **SidebarState**: 菜单栏展开/收起状态，存储于 sessionStorage
- **NavigationItem**: 导航菜单项，包含 key、label、icon、href 属性

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可以在 1 秒内完成菜单栏收起/展开操作
- **SC-002**: 页面切换时菜单栏状态保持不变
- **SC-003**: 90% 的用户在首次使用后理解菜单栏的收起/展开功能
- **SC-004**: 菜单栏收起后，主内容区域宽度增加至少 200px
