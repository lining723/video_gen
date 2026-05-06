# Tasks: 前端页面框架优化

**Feature**: `20260505-frontend-layout-sidebar`
**Input**: Design documents from `/specs/20260505-frontend-layout-sidebar/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

## 格式说明

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 路径使用 Web app 结构：`frontend/src/`

---

## Phase 1: Setup (基础准备)

**目的**: 定义 CSS 变量，为后续改动做准备

- [x] T001 Add CSS variables for sidebar dimensions in `frontend/src/styles/app.css`:
  - `--sidebar-width: 280px`
  - `--sidebar-collapsed-width: 64px`
  - `--topbar-height: 64px`

**Checkpoint**: CSS 变量定义完成

---

## Phase 2: Foundational (基础设施)

**目的**: 无需额外基础设施（纯前端功能）

**⚠️ 无阻塞任务，可直接开始用户故事**

---

## Phase 3: User Story 1 - 左侧固定菜单栏布局 (Priority: P1) 🎯 MVP

**目标**: 实现左侧固定菜单栏，滚动时保持可见

**独立测试**: 打开项目页面，滚动内容，验证菜单栏固定不动

### CSS 实现 (US1)

- [x] T002 [US1] Add fixed positioning styles for sidebar in `frontend/src/styles/app.css`:
  - `.sidebar { position: fixed; left: 0; top: 0; height: 100vh; width: var(--sidebar-width); z-index: 100; }`
  - Add `transition: width 0.3s ease` for future collapse animation
- [x] T003 [US1] Add margin-left for topbar and page-shell in `frontend/src/styles/app.css`:
  - `.topbar { margin-left: var(--sidebar-width); transition: margin-left 0.3s ease; }`
  - `.page-shell { margin-left: var(--sidebar-width); transition: margin-left 0.3s ease; }`

### HTML 结构调整 (US1)

- [x] T004 [US1] Modify sidebar HTML structure in `frontend/src/modules/layout/AppLayout.tsx`:
  - Move `<aside class="sidebar">` outside of `.content-grid`, make it sibling of `.topbar`
  - Update `appShell` function to output sidebar at top level

**Checkpoint**: ✅ 左侧固定菜单栏完成，MVP 可演示

---

## Phase 4: User Story 2 - 菜单栏收起/展开功能 (Priority: P2)

**目标**: 用户可收起/展开菜单栏，状态持久化

**独立测试**: 点击收起按钮，验证菜单栏变窄且状态保持

**依赖**: US1 完成（需要固定菜单栏）

### CSS 实现 (US2)

- [x] T005 [US2] Add collapsed state styles in `frontend/src/styles/app.css`:
  - `.sidebar.collapsed { width: var(--sidebar-collapsed-width); }`
  - `.sidebar.collapsed .nav-link span { display: none; }`
  - `.sidebar.collapsed ~ .page-shell { margin-left: var(--sidebar-collapsed-width); }`
  - `.sidebar.collapsed ~ .topbar { margin-left: var(--sidebar-collapsed-width); }`
- [x] T006 [US2] Add responsive styles for small screens in `frontend/src/styles/app.css`:
  - `@media (max-width: 768px)` auto-collapse sidebar

### JavaScript 实现 (US2)

- [x] T007 [US2] Add toggle button HTML in sidebar in `frontend/src/modules/layout/AppLayout.tsx`:
  - Add `<button class="sidebar-toggle">` at bottom of sidebar
  - Icon changes based on collapsed state
- [x] T008 [US2] Add JavaScript toggle function in `frontend/src/modules/layout/AppLayout.tsx`:
  - `toggleSidebar()` function
  - `initSidebarState()` function
  - Store state in `sessionStorage`
- [x] T009 [US2] Add event handler for toggle button in page render functions:
  - Bind click event to `.sidebar-toggle`
  - Call `toggleSidebar()` and update UI

**Checkpoint**: ✅ 收起/展开功能完成

---

## Phase 5: User Story 3 - 菜单切换和内容渲染 (Priority: P3)

**目标**: 菜单项点击切换页面，当前项高亮

**独立测试**: 点击不同菜单项，验证页面切换和高亮状态

**依赖**: US1 完成（需要菜单栏存在）

### 图标添加 (US3)

- [x] T010 [US3] Add icons to navigation items in `frontend/src/modules/layout/AppLayout.tsx`:
  - Add `icon` property to `stageItems` array
  - Display icon in `.nav-link`

### 高亮状态增强 (US3)

- [x] T011 [US3] Enhance active state styles in `frontend/src/styles/app.css`:
  - `.nav-link.active { background-color: var(--accent-soft); }`
  - Add visual indicator for collapsed state (border or background)

**Checkpoint**: ✅ 导航功能完整

---

## Phase 6: Polish & Cross-Cutting Concerns

**目的**: 最终验证和优化

- [x] T012 [P] Add tooltip for collapsed menu items in `frontend/src/styles/app.css`:
  - Show tooltip on hover when sidebar is collapsed
- [x] T013 Verify all pages work correctly with new layout:
  - Project list page (no sidebar)
  - All project pages (with sidebar)
- [x] T014 Test responsive behavior on different screen sizes

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) 
    ↓
Phase 2 (Foundational) - 无阻塞
    ↓
┌───────────────────────────────────────┐
│  Phase 3 (US1) ← MVP                   │
│      ↓                                 │
│  Phase 4 (US2) ← depends on US1        │
│      ↓                                 │
│  Phase 5 (US3) ← depends on US1        │
└───────────────────────────────────────┘
    ↓
Phase 6 (Polish)
```

### User Story Dependencies

| 故事 | 依赖 | 可并行 |
|------|------|--------|
| US1 (P1) | Phase 1 完成 | ✅ MVP 优先 |
| US2 (P2) | US1 完成 | ❌ 需固定菜单栏 |
| US3 (P3) | US1 完成 | ✅ 与 US2 可并行 |

### Parallel Opportunities

**US2 和 US3 可并行**:
- T005-T006 (US2 CSS) 和 T010 (US3 图标) 可并行
- T007-T009 (US2 JS) 和 T011 (US3 高亮) 可并行

---

## Parallel Example: US2 + US3

```bash
# 并行任务组 1:
Task: "Add collapsed state styles (T005)"
Task: "Add icons to navigation items (T010)"

# 并行任务组 2:
Task: "Add toggle button HTML (T007)"
Task: "Enhance active state styles (T011)"
```

---

## Implementation Strategy

### MVP First (仅 User Story 1)

1. 完成 Phase 1: Setup (CSS 变量)
2. 完成 Phase 3: User Story 1
3. **验证**: 固定菜单栏功能
4. 部署/演示

### Incremental Delivery

1. Setup → 基础就绪
2. US1 → 固定菜单栏可用 → **MVP!**
3. US2 → 收起/展开功能
4. US3 → 图标和高亮增强
5. Polish → 生产就绪

---

## Task Summary

| Phase | 总任务 | 说明 |
|-------|--------|------|
| Phase 1: Setup | 1 | CSS 变量定义 |
| Phase 2: Foundational | 0 | 无阻塞任务 |
| Phase 3: US1 | 3 | 固定菜单栏 (MVP) |
| Phase 4: US2 | 5 | 收起/展开功能 |
| Phase 5: US3 | 2 | 菜单切换增强 |
| Phase 6: Polish | 3 | 最终验证 |
| **Total** | **14** | |

### By User Story

| 故事 | CSS | HTML/JS | 总计 |
|------|-----|---------|------|
| US1 (P1) | 2 | 1 | 3 |
| US2 (P2) | 2 | 3 | 5 |
| US3 (P3) | 1 | 1 | 2 |

---

## Notes

- 纯前端功能，无后端改动
- 主要改动文件：`AppLayout.tsx` 和 `app.css`
- 建议先完成 US1 验证 MVP
- 提交频率：每个任务完成后提交
