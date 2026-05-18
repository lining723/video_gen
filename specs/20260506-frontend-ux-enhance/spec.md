# Feature Specification: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "前端页面重构，增加菜单导航，支持暗黑模式，支持列表分页，支持搜索"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 全局菜单导航 (Priority: P1)

用户访问平台时，需要一个始终可见的全局导航菜单，用于在不同页面和项目之间快速切换。当前侧边栏仅在进入具体项目后才显示，缺乏顶层导航能力。重构后的菜单导航应作为应用外壳的一部分，提供项目列表入口、当前项目内各阶段（概览、场景、分镜、渲染、成片）的导航，以及全局设置入口。

**Why this priority**: 菜单导航是整个前端页面重构的结构性基础，后续所有页面布局和功能都依赖导航框架。没有全局导航，用户无法在不同项目间高效切换。

**Technical Implementation**:

- 重构 `frontend/src/modules/layout/AppLayout.tsx` 中的 `appShell()` 函数，将导航拆分为两层：
  - **顶部导航栏（TopNav）**：始终可见，包含 Logo/品牌标识（"Frame Flow"）、项目列表入口、全局搜索入口（见 User Story 4）、主题切换按钮（见 User Story 2）。当前路由为项目内页面时，顶部导航栏显示当前项目名称
  - **左侧边栏（Sidebar）**：仅在项目上下文中显示，包含项目名称、状态徽标（对应 `projectStatus` 和 `projectStage`）、5 个阶段导航链接（概览 → 场景 → 分镜 → 渲染 → 成片），支持折叠/展开。折叠状态持久化到 `sessionStorage`（key: `sidebar-collapsed`）
- 路由配置集中管理：
  - 在 `frontend/src/pages/_app.tsx` 中定义路由元数据映射，包含每个路由的 `title`、`stage`（所属阶段）、`requiresProject`（是否需要项目上下文）
  - 路由表：`/projects`（项目列表）、`/projects/:projectId`（项目概览）、`/projects/:projectId/scene`（场景）、`/projects/:projectId/storyboard`（分镜）、`/projects/:projectId/renders`（渲染）、`/projects/:projectId/final-video`（成片）
- 移动端适配：屏幕宽度 < 768px 时，侧边栏变为抽屉式（通过 hamburger 按钮触发展开覆盖），顶部导航栏保持可见
- 当前激活的导航项高亮显示（通过对比当前 `window.location.hash` 与导航项路由）
- 侧边栏折叠状态保持现有 `sessionStorage` 持久化机制

**Independent Test**: 在浏览器中访问平台任意页面，验证顶部导航栏始终可见且可点击；进入项目后验证侧边栏显示正确的阶段导航并能正常折叠/展开。

**Acceptance Scenarios**:

1. **Given** 用户访问平台首页（`#/projects`），**When** 页面加载完成，**Then** 顶部导航栏显示 Frame Flow 品牌标识和项目列表入口链接，左侧无侧边栏
2. **Given** 用户进入某个项目（`#/projects/:projectId`），**When** 页面加载完成，**Then** 左侧显示项目侧边栏，包含项目名称、状态徽标和 5 个阶段导航链接（概览、场景、分镜、渲染、成片）
3. **Given** 用户在项目内，**When** 点击侧边栏折叠按钮，**Then** 侧边栏收起为图标模式（仅显示阶段图标），内容区域自动扩展；刷新页面后折叠状态保持
4. **Given** 用户在项目场景页面（`#/projects/:projectId/scene`），**When** 观察侧边栏，**Then** "场景"导航项处于高亮激活状态
5. **Given** 用户屏幕宽度 < 768px，**When** 进入项目，**Then** 侧边栏默认隐藏，顶部导航栏显示汉堡菜单按钮，点击后侧边栏以抽屉形式从左侧滑出覆盖内容区

---

### User Story 2 - 暗黑模式切换 (Priority: P2)

用户可以在亮色模式和暗色模式之间切换，系统记住用户的主题偏好。暗黑模式覆盖所有页面和组件，包括项目列表、项目详情、场景审核、分镜编辑、渲染进度、成片查看等全部页面。

**Why this priority**: 暗黑模式是用户强烈的视觉偏好需求，且技术上依赖 CSS 变量体系的建立，需要在导航重构完成后尽早实施，避免后续重复适配。

**Technical Implementation**:

- 建立 CSS 变量双主题体系（在 `frontend/src/styles/app.css` 中）：
  - 在 `:root`（即 `[data-theme="light"]`）中保留现有亮色主题变量（`--bg-primary`、`--text-primary` 等 20+ 变量）
  - 新增 `[data-theme="dark"]` 暗色主题变量覆盖（背景色转为深灰/黑，文字色转为浅灰/白，强调色适当降低饱和度以适应暗色背景）
  - 所有组件样式统一使用 CSS 变量引用颜色，禁止在组件中硬编码颜色值
- 主题切换按钮位于顶部导航栏（使用太阳 ☀️ / 月亮 🌙 图标表示当前可切换到的目标主题）
- 主题偏好持久化：
  - 用户手动切换后存储到 `localStorage`（key: `theme-preference`，value: `"light"` | `"dark"`）
  - 页面加载时读取 `localStorage` 中的偏好；无存储值时通过 `matchMedia('(prefers-color-scheme: dark)')` 检测系统主题
  - 系统主题变化时（用户未手动设置偏好的情况下），监听 `change` 事件自动跟随
- FOUC 防护：在 `frontend/server.js` 返回的 HTML `<head>` 中内联一个阻塞 `<script>`，同步读取 `localStorage` 中的 `theme-preference` 并在 `<html>` 上设置 `data-theme` 属性，确保 CSS 在首帧渲染前拿到正确的主题
- 过渡动画：在 `<html>` 上设置 `transition: background-color 200ms, color 200ms`，主题切换时平滑过渡

**Independent Test**: 点击顶部导航栏主题切换按钮，验证页面从亮色变为暗色；刷新页面后验证主题偏好保持；修改操作系统主题偏好后验证自动跟随（未手动设置时）。

**Acceptance Scenarios**:

1. **Given** 用户首次访问平台（`localStorage` 中无 `theme-preference`），系统主题为亮色，**When** 页面加载完成，**Then** 页面以亮色主题展示
2. **Given** 用户首次访问平台（无存储偏好），系统主题为暗色，**When** 页面加载完成，**Then** 页面以暗色主题展示
3. **Given** 用户在亮色模式下，**When** 点击主题切换按钮（月亮图标），**Then** 页面平滑切换为暗色模式，`theme-preference` 保存到 `localStorage`
4. **Given** 用户在暗色模式下刷新页面，**When** 页面重新加载，**Then** 页面直接以暗色模式呈现，无亮色闪烁
5. **Given** 用户未手动设置过主题偏好，**When** 操作系统主题从亮色切换到暗色，**Then** 页面自动跟随切换为暗色模式

---

### User Story 3 - 列表分页 (Priority: P3)

用户在查看项目列表时，系统提供分页功能而非一次性加载所有数据。当数据量较大时，分页可以显著提升页面加载速度和浏览体验。

**Why this priority**: 分页直接影响列表页面的性能和可用性。随着项目数量增长，一次性加载全部数据将导致页面响应变慢、DOM 节点过多。分页可在菜单导航和暗黑模式稳定后实施。

**Technical Implementation**:

- 范围：本期对**项目列表页**（`frontend/src/pages/projects/index.tsx`）实施分页
- 后端 API 改造（`backend/src/api/routes/projects.py`）：
  - `GET /api/projects` 增加查询参数 `page`（页码，从 1 开始，默认 1）和 `page_size`（每页条数，默认 20，最大 100）
  - 响应体增加字段：`total`（总条数）、`page`（当前页）、`page_size`（每页条数）、`total_pages`（总页数）
  - 保持向后兼容：不传分页参数时返回全部数据（行为不变）
- 前端分页组件（在 `frontend/src/modules/project-list/` 中新建，或直接在项目列表页内实现）：
  - 页码导航栏：上一页按钮、页码列表、下一页按钮
  - 当前页高亮，页码过多时显示省略号（如：`1 ... 5 6 7 ... 20`）
  - 显示 "第 X-Y 条，共 Z 条" 的记录信息
  - 每页条数切换下拉框（10 / 20 / 50）
- 分页状态通过 URL hash 参数同步（如 `#/projects?page=2&page_size=20`），支持浏览器前进/后退按钮
- 加载状态：切换页码时显示 loading 指示器（禁用分页按钮 + 列表区域显示加载中），防止重复请求
- 页面加载时从 URL hash 解析分页参数，若无则使用默认值

**Independent Test**: 创建超过 20 个项目后访问项目列表页，验证默认只显示前 20 个；点击"下一页"验证显示后续项目；直接访问 `#/projects?page=2` 验证显示第二页。

**Acceptance Scenarios**:

1. **Given** 系统中项目总数 ≤ 20 个，**When** 用户访问项目列表页，**Then** 显示全部项目，分页组件仅显示"共 X 条"记录信息，不显示页码按钮
2. **Given** 系统中项目总数 > 20 个，**When** 用户访问项目列表页，**Then** 默认显示第 1 页（前 20 条），底部分页组件显示页码、记录信息和每页条数切换
3. **Given** 用户在项目列表第 1 页，**When** 点击"下一页"按钮，**Then** 显示第 2 页数据，URL hash 更新为 `#/projects?page=2`，页码 2 高亮
4. **Given** 用户在项目列表页，**When** 将每页条数从 20 切换为 10，**Then** 重新加载数据，每页显示 10 条，`page_size` 反映在 URL 中
5. **Given** 用户直接访问 `#/projects?page=99`（超出总页数），**When** 页面加载，**Then** 自动修正为显示最后一页数据

---

### User Story 4 - 全局搜索 (Priority: P4)

用户可以通过搜索快速找到目标项目。搜索功能位于顶部导航栏，支持按项目名称模糊搜索。搜索结果实时更新，与分页协同工作。

**Why this priority**: 搜索是提升大批量数据查找效率的关键功能，但在项目数量不多的初期阶段并非最紧急需求。在分页功能完成后，搜索可与分页协同工作，提供完整的数据浏览体验。

**Technical Implementation**:

- 搜索范围：本期对**项目列表**实施搜索
- 前端搜索入口：顶部导航栏搜索框（见 User Story 1），支持 `Ctrl+K` / `Cmd+K` 快捷键唤起聚焦
- 搜索方式：
  - 项目数少时前端过滤：一次性拉取全部项目数据，前端本地过滤，即时响应
  - 项目数多时后端搜索：调用 `GET /api/projects?search=<keyword>` 进行服务端模糊搜索
  - 实际上统一使用后端搜索以保持一致性——搜索时调用后端 API 传入 `search` 参数，后端在数据库层做 `LIKE '%keyword%'` 模糊匹配
- 后端 API 改造（`backend/src/api/routes/projects.py`）：
  - `GET /api/projects` 增加查询参数 `search`（按项目名称模糊匹配，不区分大小写）
  - 搜索与分页可同时使用：`GET /api/projects?search=test&page=1&page_size=20`
  - 搜索时后端在 `name` 字段上执行 `LIKE` 查询
- 前端搜索交互：
  - 搜索框内输入关键词，300ms 防抖后触发搜索请求
  - 搜索时页码重置为 1，分页重置
  - 搜索关键词通过 URL hash 参数同步（如 `#/projects?search=test&page=1`）
  - 清空搜索框后恢复完整项目列表
- 搜索空状态：无匹配结果时显示"未找到匹配的项目"提示，提供"清除搜索"按钮
- 快捷键：`Escape` 键清空搜索并恢复完整列表

**Independent Test**: 在顶部搜索框输入项目名称关键词，验证列表实时筛选出匹配的项目；按 `Ctrl+K` 验证搜索框自动聚焦；按 `Escape` 验证清空搜索。

**Acceptance Scenarios**:

1. **Given** 用户在任意页面，**When** 按下 `Ctrl+K`（或 `Cmd+K`），**Then** 顶部搜索框获得焦点，光标定位到输入框
2. **Given** 用户在项目列表页，**When** 在搜索框输入关键词并停止输入，**Then** 300ms 后列表过滤为匹配项目，分页重置到第 1 页，URL hash 包含 `search` 参数
3. **Given** 用户输入了搜索关键词且结果多于 1 页，**When** 点击第 2 页，**Then** 显示第 2 页搜索结果，搜索关键词保留
4. **Given** 用户搜索一个不存在的项目名称，**When** 搜索完成，**Then** 显示"未找到匹配的项目"空状态提示和"清除搜索"按钮
5. **Given** 用户在搜索状态下，**When** 按下 `Escape` 键或点击"清除搜索"，**Then** 搜索框清空，恢复完整项目列表，URL 中搜索参数移除

---

### Edge Cases

- **主题切换闪烁（FOUC）**：页面初次加载时，在 JS 执行前可能出现亮色主题短暂闪现。通过在 HTML `<head>` 中内联同步脚本读取 `localStorage` 的 `theme-preference` 并同步设置 `<html data-theme>` 属性来避免
- **系统主题运行时变更**：用户未手动设置主题偏好时，若操作系统主题在页面打开期间变化，通过监听 `matchMedia('(prefers-color-scheme: dark)')` 的 `change` 事件实时跟随
- **侧边栏与内容区布局**：侧边栏折叠/展开时，内容区域宽度通过 CSS transition 平滑过渡，避免内容突然跳变
- **分页参数边界**：请求页码为 0、负数、非数字时，后端默认返回第 1 页；`page_size` 超过 100 时后端限制为 100
- **搜索与分页交互**：搜索时页码重置为 1；切换页码时保留搜索关键词（URL hash 中同时保留 `search` 和 `page` 参数）；清除搜索时页码重置为 1
- **移动端搜索**：屏幕宽度 < 768px 时，搜索框默认折叠为搜索图标，点击后展开为全宽搜索框覆盖顶部导航栏
- **空项目列表**：项目列表为空时（`total: 0`），不显示分页组件，正确展示空状态（现有 "还没有项目" 提示）
- **并发请求**：快速切换页码或搜索时，使用请求标识或 AbortController 取消前一个未完成的请求，避免结果覆盖

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须提供始终可见的顶部导航栏，包含品牌标识（"Frame Flow"）、项目列表入口链接、搜索入口和主题切换按钮
- **FR-002**: 系统必须在项目上下文中显示左侧边栏，包含项目名称、状态徽标和 5 个阶段导航链接（概览、场景、分镜、渲染、成片）
- **FR-003**: 侧边栏必须支持折叠/展开切换，折叠状态持久化到 `sessionStorage`（key: `sidebar-collapsed`）
- **FR-004**: 当前激活的导航项必须有视觉高亮样式（active 状态），通过对比当前路由与导航项路由判定
- **FR-005**: 屏幕宽度 < 768px 时，侧边栏必须变为抽屉式展开（hamburger 触发），顶部导航栏保持可见
- **FR-006**: 系统必须支持亮色和暗色两种主题，通过 `data-theme` 属性配合 CSS 变量体系实现
- **FR-007**: 主题切换按钮必须位于顶部导航栏，一键切换亮色/暗色模式
- **FR-008**: 用户手动设置的主题偏好必须持久化到 `localStorage`（key: `theme-preference`，value: `"light"` | `"dark"`）
- **FR-009**: 用户未手动设置偏好时，主题必须跟随操作系统 `prefers-color-scheme` 媒体查询
- **FR-010**: 主题首次加载必须无闪烁（FOUC-free），切换时必须有 200ms 过渡动画
- **FR-011**: 项目列表 API（`GET /api/projects`）必须支持 `page` 和 `page_size` 查询参数进行分页
- **FR-012**: 分页 API 响应必须包含 `total`、`page`、`page_size`、`total_pages` 元数据字段
- **FR-013**: 前端项目列表页必须显示分页导航组件，包含：上一页/下一页按钮、页码列表（含省略号）、每页条数切换（10/20/50）、记录信息（"第 X-Y 条，共 Z 条"）
- **FR-014**: 分页状态必须通过 URL hash 查询参数同步（`page`、`page_size`），支持浏览器前进/后退
- **FR-015**: 分页切换时必须显示 loading 状态并禁用重复请求
- **FR-016**: 顶部导航栏搜索框必须支持 `Ctrl+K`（Windows/Linux）和 `Cmd+K`（Mac）快捷键唤起聚焦
- **FR-017**: 搜索输入必须进行 300ms 防抖处理后触发搜索请求
- **FR-018**: 项目列表 API 必须支持 `search` 查询参数进行服务端模糊搜索（`LIKE '%keyword%'`，不区分大小写）
- **FR-019**: 搜索与分页必须协同工作：搜索时页码重置为 1，切换页码时保留搜索关键词；两者通过 URL hash 同步
- **FR-020**: 搜索无结果时必须显示"未找到匹配的项目"空状态提示，并提供清除搜索的操作
- **FR-021**: 按 `Escape` 键必须清空当前搜索并恢复完整列表

### Key Entities

- **主题偏好（Theme Preference）**：`localStorage` 键值对（`theme-preference: "light" | "dark"`），表示用户显式选择的主题模式，优先级高于系统主题设置
- **导航状态（Navigation State）**：当前 hash 路由、侧边栏折叠状态（`sessionStorage: sidebar-collapsed`），驱动导航 UI 渲染
- **分页参数（Pagination Params）**：URL hash 查询参数（`page`、`page_size`），API 请求参数和响应元数据（`total`、`total_pages`），共同驱动分页组件和数据加载
- **搜索参数（Search Params）**：URL hash 查询参数（`search`）和 API 请求参数，驱动搜索过滤和结果展示

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可在任意页面通过顶部导航栏一键跳转到项目列表或切换主题，无需手动输入 URL
- **SC-002**: 主题切换操作在 300ms 内完成视觉切换（含 200ms 过渡动画），无明显卡顿或闪烁
- **SC-003**: 项目列表页首屏加载时间（含前 20 条数据）不超过 2 秒
- **SC-004**: 分页切换响应时间不超过 1 秒（含 API 请求和 DOM 渲染）
- **SC-005**: 搜索操作在用户停止输入后 500ms 内（300ms 防抖 + 200ms 请求）返回过滤结果
- **SC-006**: 所有页面在亮色和暗色模式下均可正常阅读，文字与背景对比度符合 WCAG AA 标准（4.5:1）
- **SC-007**: 移动端（宽度 < 768px）下所有核心功能可正常使用，导航可折叠，无横向滚动条

## Assumptions

- 现有 CSS 变量体系在 `frontend/src/styles/app.css` 中已有基础，本重构将在此之上扩展暗色主题覆盖变量
- 后端 `listProjects` API 返回项目列表数据结构已知，新增 `page`、`page_size`、`search` 参数为向后兼容的可选参数
- 项目列表数据量在 MVP 阶段预估 < 1000 条，分页默认每页 20 条是合理的默认值
- 搜索功能本期仅覆盖项目名称搜索（`LIKE '%keyword%'`），不涉及场景内容、分镜内容的全文搜索
- 移动端适配目标为响应式布局，非独立移动端应用，断点为 768px
- 浏览器兼容目标：最近 2 个主要版本的 Chrome、Firefox、Safari、Edge
