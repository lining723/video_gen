# Tasks: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance`
**Input**: Design documents from `specs/20260506-frontend-ux-enhance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in spec — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/src/`, `backend/src/`
- New modules: `frontend/src/modules/pagination/`, `frontend/src/utils/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project structure and create new utility directory scaffolding

- [x] T001 [P] Create `frontend/src/utils/theme.ts` placeholder file (theme system entry point)
- [x] T002 [P] Create `frontend/src/utils/url.ts` placeholder file (URL hash query parser entry point)
- [x] T003 [P] Create `frontend/src/modules/pagination/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [US3/US4] Implement backend paginated list with search in `backend/src/repositories/project_repository.py`: update `list()` method to accept optional `page`, `page_size`, `search` parameters. Use SQL `LIMIT ? OFFSET ?` for pagination and `WHERE name LIKE ?` for search. Return `total`, `page`, `page_size`, `total_pages` fields when `page` is provided; return `items` only when no page param (backward compatible). Use `SELECT COUNT(*)` for total count.

- [x] T005 [US3/US4] Update `GET /api/projects` route in `backend/src/api/routes/projects.py`: extract `page`, `page_size`, `search` from query string, parse `page`/`page_size` to int with defaults (page=1, page_size=20), pass to `project_repo.list()`, return paginated response when `page` param present. Maintain backward compatibility when no pagination params.

- [x] T006 [US3/US4] Add AbortController support to `frontend/src/services/http.ts`: update `request()` function to accept optional `{ signal }` in options, pass `signal` to `fetch()`. Expose `createAbortController()` helper. Update `frontend/src/services/projects.ts`: add `page`, `page_size`, `search`, `signal` params to `listProjects()`, build query string from params.

- [x] T007 [US1/US3/US4] Implement URL hash query param parser in `frontend/src/utils/url.ts`: export `parseRoute()` returning `{ parts: string[], params: URLSearchParams }`, split hash on `?` to separate path from query, use `URLSearchParams` for query parsing. Export `buildHash(path, params)` to construct hash URL with query params.

- [x] T008 [US1] Define route metadata map in `frontend/src/pages/_app.tsx`: register all 6 routes (`/projects`, `/projects/:projectId`, `/projects/:projectId/scene`, `/projects/:projectId/storyboard`, `/projects/:projectId/renders`, `/projects/:projectId/final-video`) with `title`, `stage`, `requiresProject` fields. Update `parseRoute()` call site to use new `url.ts` parser. Export route metadata for consumption by AppLayout.

- [x] T009 [US2] Implement theme system in `frontend/src/utils/theme.ts`: export `initTheme()` (reads `localStorage` key `theme-preference`, falls back to `matchMedia('(prefers-color-scheme: dark)')`, sets `document.documentElement.dataset.theme`), `toggleTheme()` (flips between 'light'/'dark', persists to `localStorage`), `getCurrentTheme()` (returns 'light'|'dark'). Listen to `matchMedia` change events when no explicit preference set.

- [x] T010 [US2] Add FOUC prevention inline script: update `frontend/index.html` to include blocking `<script>` in `<head>` that reads `localStorage['theme-preference']` and sets `data-theme` on `<html>` before first paint. Use the exact script from research.md.

**Checkpoint**: Foundation ready — all 4 user stories can now begin implementation in priority order

---

## Phase 3: User Story 1 — 全局菜单导航 (Priority: P1) 🎯 MVP

**Goal**: 用户在任何页面都能看到顶部导航栏，项目内页面显示可折叠的侧边栏，支持移动端抽屉式导航

**Independent Test**: 访问首页确认顶部导航栏可见；进入项目确认侧边栏显示 5 个阶段链接并能折叠/展开；缩小窗口至 < 768px 确认抽屉式导航

### Implementation for User Story 1

- [x] T011 [US1] Refactor TopNav in `frontend/src/modules/layout/AppLayout.tsx`: replace current simple topbar with full TopNav component containing:
  - Left: brand mark (keep existing "Frame Flow" logo linking to `#/projects`)
  - Center: current project name (when `projectId` present, show `projectName` text)
  - Right: search input placeholder (visual only, wired in US4), theme toggle button placeholder (visual only, wired in US2), "项目首页" link
  - Style: fixed height `var(--topbar-height)`, full width, z-index above content, border-bottom separator
  - When not in project context, brand mark still links to `#/projects`

- [x] T012 [US1] Refactor Sidebar in `frontend/src/modules/layout/AppLayout.tsx`: update sidebar logic to:
  - Only render when `projectId` is present (existing behavior, keep)
  - Keep project meta section (project name, status pill, stage pill) and stage navigation (5 links with icons, labels, codes)
  - Use route metadata from `_app.tsx` (T008) to determine active nav item via `currentView` matching
  - Keep collapse/expand toggle button with `sessionStorage` persistence (key: `sidebar-collapsed`)
  - Update toggle icon: `◀` when expanded, `▶` when collapsed
  - Add hamburger menu button for mobile (visible only at < 768px): toggles sidebar as drawer overlay

- [x] T013 [US1] Add TopNav and sidebar CSS to `frontend/src/styles/app.css`:
  - `.topbar-new`: full-width, flexbox layout, height `var(--topbar-height)`, background `var(--bg)`, border-bottom `1px solid var(--surface-border)`, z-index 50, fixed top
  - `.topbar-left`, `.topbar-center`, `.topbar-right`: flex sections
  - `.topbar-search`: search input styling (placeholder for US4), height 40px, border-radius 20px, background `var(--surface)`
  - `.sidebar-drawer`: overlay mode for mobile (< 768px), transform slide-in/out
  - Adjust `.page-shell` `padding-top` to account for fixed TopNav height
  - Adjust existing `.sidebar` `top` offset to `var(--topbar-height)` so it sits below TopNav
  - Update existing responsive breakpoints to handle new topbar

- [x] T014 [US1] Update all page render functions to use new `appShell()` signature:
  - Pass `projectName` to AppLayout for TopNav center display (pages that already pass it: dashboard, scene, storyboard, renders, final-video — verify all of them)
  - Ensure project list page (`projects/index.tsx`) correctly renders without sidebar (no projectId context)
  - Verify `initSidebarState()` and `toggleSidebar()` are called after each page render in `_app.tsx`

**Checkpoint**: US1 complete — 全局菜单导航功能独立可用，顶部导航始终可见，项目内左侧边栏可折叠，移动端适配正常

---

## Phase 4: User Story 2 — 暗黑模式切换 (Priority: P2)

**Goal**: 用户可一键切换亮色/暗色主题，系统记住偏好，首次加载无闪烁

**Independent Test**: 点击主题切换按钮验证页面切换为暗色；刷新页面验证偏好保持；清除 localStorage 后验证跟随系统主题

### Implementation for User Story 2

- [x] T015 [US2] Add dark theme CSS variable overrides to `frontend/src/styles/app.css`:
  - Add `[data-theme="dark"]` selector block with all variable overrides per data-model.md color mapping table (14 variables: `--bg`, `--bg-deep`, `--surface`, `--surface-strong`, `--surface-border`, `--text`, `--text-muted`, `--accent`, `--accent-soft`, `--accent-strong`, `--success`, `--warning`, `--shadow`, plus body gradient)
  - Add `[data-theme="dark"]` body gradient (dark neutral tones instead of warm cream)
  - Add `[data-theme="dark"]` adjustments for: `.hero-panel` background/gradient, `.ambient-orb` colors, input/textarea backgrounds, `.modal-panel` background, `.notice` colors, `.preview-frame` background
  - Add `html { transition: background-color 200ms, color 200ms; }` for smooth theme switching
  - Ensure all existing selectors use CSS variables (audit for hardcoded colors in `app.css`)

- [x] T016 [US2] Add theme toggle button to TopNav in `frontend/src/modules/layout/AppLayout.tsx`:
  - Add theme toggle button in topbar-right section (between search placeholder and projects link)
  - Icon: show ☀️ when current theme is dark (indicating "switch to light"), show 🌙 when current theme is light (indicating "switch to dark")
  - On click: call `toggleTheme()` from `theme.ts` (T009), update icon
  - Initial icon state set by reading `getCurrentTheme()` after `initTheme()`

- [x] T017 [US2] Wire theme initialization in `frontend/src/pages/_app.tsx`:
  - Call `initTheme()` from `theme.ts` before `render()` on app startup to ensure theme is applied
  - Listen to `hashchange` — no re-init needed (theme persists across navigations)
  - Ensure `initTheme()` is importable and tree-shakeable by esbuild

- [x] T018 [US2] Verify FOUC prevention: test that `index.html` inline script (T010) correctly prevents flash of wrong theme on cold load, reload, and when `localStorage` has explicit preference

**Checkpoint**: US2 complete — 暗黑模式在全部页面正常工作，切换平滑，刷新无闪烁，系统主题跟随

---

## Phase 5: User Story 3 — 列表分页 (Priority: P3)

**Goal**: 项目列表支持分页浏览，每页 20 条，可切换每页条数，URL hash 同步分页状态

**Independent Test**: 创建 25+ 项目后访问列表页，验证默认显示 20 条并有分页控件；点击第 2 页验证数据切换；直接访问 `#/projects?page=2` 验证显示第 2 页

### Implementation for User Story 3

- [x] T019 [US3] Build pagination component in `frontend/src/modules/pagination/Pagination.tsx`:
  - Export `renderPagination(total, page, pageSize)` function returning HTML string
  - Page number list: show all pages when ≤ 7, show `1 ... current-1 current current+1 ... last` when > 7
  - Previous button: disabled when `page === 1`
  - Next button: disabled when `page === totalPages`
  - Current page: highlighted with `.active` class
  - Record info: display "第 X-Y 条，共 Z 条" (X = (page-1)*pageSize+1, Y = min(page*pageSize, total), Z = total)
  - Page size selector: dropdown with options 10 / 20 / 50, on change resets to page 1 and re-navigates
  - Each page link: `href="#/projects?page=N&page_size=S&search=..."` preserving current search
  - When `total <= pageSize`: only show record info, hide page numbers and prev/next buttons

- [x] T020 [US3] Update project list page in `frontend/src/pages/projects/index.tsx` to integrate pagination:
  - Parse `page`, `page_size`, `search` from URL hash using `parseRoute()` from `url.ts` (T007)
  - Call `listProjects({ page, page_size, search })` instead of current `listProjects()`
  - Extract `items`, `total`, `page`, `page_size`, `total_pages` from response (handle both paginated and non-paginated response shapes)
  - Render pagination component at bottom of project list using `renderPagination()`
  - Add AbortController: cancel previous request on page/size change before making new request
  - Update `total`/`active`/`completed` metrics: when paginated, `total` comes from response; `active`/`completed` remain client-side from `items` only (scope: current page)
  - Loading state: show "加载中..." text overlay or disable pagination buttons during request

- [x] T021 [US3] Add pagination CSS to `frontend/src/styles/app.css`:
  - `.pagination`: flex container, centered, gap 8px, margin-top 24px
  - `.pagination button`, `.pagination .page-link`: min-width 40px, height 40px, border-radius 12px, border 1px solid var(--surface-border), background var(--surface), color var(--text)
  - `.pagination .page-link.active`: background var(--accent), color #fff
  - `.pagination .page-link:disabled`: opacity 0.4, cursor not-allowed
  - `.page-size-select`: inline select, margin-left 16px, padding 8px 12px
  - `.record-info`: color var(--text-muted), font-size 0.88rem

**Checkpoint**: US3 complete — 项目列表支持分页，URL 同步，每页条数可切换

---

## Phase 6: User Story 4 — 全局搜索 (Priority: P4)

**Goal**: 用户可通过顶部搜索框按名称搜索项目，支持快捷键唤起，与分页协同

**Independent Test**: 在搜索框输入关键词验证列表过滤；按 Ctrl+K 验证搜索框聚焦；按 Escape 验证清空搜索

### Implementation for User Story 4

- [x] T022 [US4] Wire search input in TopNav in `frontend/src/modules/layout/AppLayout.tsx`:
  - Replace placeholder search input (from T011) with functional search input
  - Input placeholder text: "搜索项目... (Ctrl+K)"
  - On input: 300ms debounce before triggering search (use `setTimeout` + clear on new input)
  - On search submit (Enter or debounce fire): navigate to `#/projects?search=<value>&page=1` (reset to page 1)
  - On Escape in search input: clear input and navigate to `#/projects` (no search)
  - Search input should be visible and functional on ALL pages (not just project list) — typing Enter navigates to project list with search

- [x] T023 [US4] Add keyboard shortcut handler in `frontend/src/pages/_app.tsx`:
  - Listen for `keydown` event on `document`
  - `Ctrl+K` or `Cmd+K`: prevent default, focus the TopNav search input (querySelector `.topbar-search input`)
  - `Escape` when search input is focused: blur input and clear search (handled in T022)
  - Register handler once on app init, do not re-register on `hashchange`

- [x] T024 [US4] Update project list page in `frontend/src/pages/projects/index.tsx` for search integration:
  - Parse `search` param from URL hash (already handled in T020)
  - Pass `search` to `listProjects()` (already handled in T020)
  - When search results are empty: show "未找到匹配的项目" empty state with "清除搜索" button
  - "清除搜索" button: navigates to `#/projects` (removes search and page params)
  - Preserve search keyword in pagination links (Pagination component from T019 already handles this)
  - When user is on search results page, pre-fill the TopNav search input with current search value

- [x] T025 [US4] Add search-related CSS to `frontend/src/styles/app.css`:
  - `.topbar-search input`: full styling for the functional search input (background var(--surface), border 1px solid var(--surface-border), border-radius 20px, padding 8px 16px, width 240px, transition)
  - `.topbar-search input:focus`: border-color var(--accent), box-shadow accent glow
  - `.search-empty`: centered flex column, padding 48px 0, text-align center
  - `.search-empty p`: color var(--text-muted), margin-bottom 16px

**Checkpoint**: US4 complete — 搜索功能完整可用，支持快捷键、防抖、与分页协同、空状态提示

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge case handling, and validation

- [x] T026 Verify all edge cases from spec.md are handled:
  - Theme FOUC: test cold load, reload, system theme change
  - Sidebar/content layout transition smoothness
  - Pagination boundary values (page=0, page=999, page_size=1000)
  - Search + pagination interaction (search resets page, pagination preserves search)
  - Mobile search: search input collapses to icon below 768px
  - Empty project list: no pagination shown, correct "还没有项目" message
  - Concurrent requests: fast page switching doesn't show stale results

- [x] T027 [P] Run through quickstart.md validation checklist: test all 4 user stories per quickstart.md verification steps

- [x] T028 [P] Code cleanup: remove any unused CSS classes, ensure consistent code style across new files, verify all TypeScript compiles without errors with `npx tsc --noEmit`

- [x] T029 Build verification: run `make frontend` to esbuild bundle, ensure no build errors, verify dist output includes all new modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Phase 2 completion
  - US1 → US2 → US3 → US4 (sequential, each builds on prior)
  - US2 can partially overlap with US1 (theme toggle placeholder exists in US1)
  - US4 depends on US3 (pagination infrastructure) and US1 (TopNav search input)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories. Needs: route metadata (T008)
- **US2 (P2)**: Can start after US1 TopNav is done (needs theme toggle button slot). Needs: theme.ts (T009), FOUC script (T010), dark CSS (T015). TopNav placeholder from US1 T011 provides the button slot.
- **US3 (P3)**: Can start after Phase 2 (US1 not required for backend + pagination component). Needs: url.ts (T007), backend pagination (T004/T005), http.ts (T006). Optional: US1 TopNav for search slot (not blocking).
- **US4 (P4)**: Directly depends on US3 (pagination/search infrastructure) and US1 (TopNav search input). Can begin after US1 T011 and US3 T019-T021.

### Within Each User Story

- Backend before frontend (backend tasks in Phase 2)
- Shared utilities before consuming code
- Component before page integration
- CSS alongside component implementation

### Parallel Opportunities

- Phase 1: T001, T002, T003 all [P] (different files)
- Phase 2: T004, T005 are sequential (T005 depends on T004); T006, T007, T008, T009, T010 are all [P] independent of each other
- Phase 3 (US1): T011 and T013 can be started together (component + CSS); T012 depends on T011; T014 is integration after T011/T012
- Phase 4 (US2): T015 [P] CSS only, can run in parallel with T016 (AppLayout button) and T017 (app init); T018 is verification
- Phase 5 (US3): T019 [P] pagination component, can run in parallel with T021 [P] CSS; T020 depends on T019
- Phase 6 (US4): T022 and T023 and T025 [P] (different files); T024 depends on T022
- Phase 7: T027, T028 [P] can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch backend tasks sequentially (dependencies):
Task: "T004: Backend pagination + search in project_repository.py"
# → Then:
Task: "T005: Backend route update in projects.py"

# Launch all independent frontend tasks together:
Task: "T006: AbortController in http.ts + update projects.ts service"
Task: "T007: URL hash query parser in url.ts"
Task: "T008: Route metadata in _app.tsx"
Task: "T009: Theme system in theme.ts"
Task: "T010: FOUC script in index.html"
```

## Parallel Example: User Story 3 (分页)

```bash
# Launch in parallel:
Task: "T019: Pagination component in Pagination.tsx"
Task: "T021: Pagination CSS in app.css"
# → Then:
Task: "T020: Integrate pagination into projects/index.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T011-T014)
4. **STOP and VALIDATE**: Test navigation independently — TopNav visible on all pages, sidebar correct, mobile responsive
5. Deploy/demo if ready — this delivers immediate value (improved navigation)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → **Navigation MVP ready**
3. Add US2 → Test independently → **Dark mode added**
4. Add US3 → Test independently → **Pagination added**
5. Add US4 → Test independently → **Search added**
6. Each story adds user-visible value without breaking previous stories

### File Modification Summary

| File | US1 | US2 | US3 | US4 | Polish |
|------|-----|-----|-----|-----|--------|
| `frontend/src/utils/url.ts` | | | 🆕 | | |
| `frontend/src/utils/theme.ts` | | 🆕 | | | |
| `frontend/src/modules/pagination/Pagination.tsx` | | | 🆕 | | |
| `frontend/src/pages/_app.tsx` | 🔧 | 🔧 | 🔧 | 🔧 | |
| `frontend/src/modules/layout/AppLayout.tsx` | 🔧 | 🔧 | | 🔧 | |
| `frontend/src/pages/projects/index.tsx` | | | 🔧 | 🔧 | |
| `frontend/src/styles/app.css` | 🔧 | 🔧 | 🔧 | 🔧 | |
| `frontend/src/services/http.ts` | | | 🔧 | | |
| `frontend/src/services/projects.ts` | | | 🔧 | | |
| `frontend/index.html` | | 🔧 | | | |
| `backend/src/repositories/project_repository.py` | | | 🔧 | | |
| `backend/src/api/routes/projects.py` | | | 🔧 | | |

🆕 = New file | 🔧 = Modified file

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability (US1-US4)
- Each user story should be independently completable and testable
- Commit after each user story phase completes
- Stop at any checkpoint to validate story independently
- Key constraint: keep custom hash router + template string architecture, no SPA framework
- Backend API changes are backward compatible (no page param = full list as before)
