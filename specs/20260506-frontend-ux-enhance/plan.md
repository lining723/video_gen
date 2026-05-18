# Implementation Plan: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/20260506-frontend-ux-enhance/spec.md`

## Summary

对现有前端单页应用进行全面 UX 重构，在不引入 SPA 框架的前提下，基于现有自定义 hash 路由和模板字符串渲染架构，增加全局菜单导航（顶部导航栏 + 项目侧边栏）、暗黑模式（CSS 变量双主题 + FOUC 防护）、项目列表分页（前后端协同）和全局搜索（防抖 + 服务端 LIKE 查询）。后端 `GET /api/projects` 扩展 `page`、`page_size`、`search` 查询参数，保持向后兼容。

## Technical Context

**Language/Version**: TypeScript (frontend, ES2022 target), Python 3 (backend)
**Primary Dependencies**: esbuild (bundle), custom hash-based router, CSS custom properties, SQLite (backend)
**Storage**: SQLite (`projects` table), `localStorage` (theme preference), `sessionStorage` (sidebar state), URL hash (pagination/search state)
**Testing**: Manual browser testing (no existing test framework in frontend)
**Target Platform**: Web browser (Chrome/Firefox/Safari/Edge recent 2 versions), Node.js 22 server
**Project Type**: web (frontend + backend)
**Performance Goals**: Project list page < 2s initial load, pagination switch < 1s, theme switch < 300ms, search results < 500ms after input
**Constraints**: No SPA framework (keep custom router), FOUC-free theme loading, backward-compatible API changes, CSS variables for theming, responsive layout (768px breakpoint)
**Scale/Scope**: ~7 pages, 4 user stories, < 1000 projects in MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. 产品闭环优先 | ✅ PASS | 纯 UI/UX 增强，支持但不改变现有业务闭环。导航改进使用户在闭环各阶段间切换更高效 |
| II. 人工审核门禁不可跳过 | ✅ PASS | 未修改场景审核、分镜审核的流程或门禁逻辑 |
| III. 契约优先与跨端一致性 | ✅ PASS | API 分页/搜索参数在 contracts/ 中明确定义；URL hash 参数规范与后端查询参数保持一致 |
| IV. 异步媒体流水线可靠性 | ✅ PASS | 未涉及视频生成、主体出图、拼接等异步任务 |
| V. 可观测性、版本化与简洁实现 | ✅ PASS | 主题/导航状态通过浏览器存储持久化；分页/搜索状态通过 URL hash 可追踪；实现基于现有 `innerHTML` 模板模式，不引入框架 |

Gate result: **ALL PASS** — 可以进入 Phase 0。

## Project Structure

### Documentation (this feature)

```
specs/20260506-frontend-ux-enhance/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.yaml         # API contracts (OpenAPI)
└── tasks.md             # Phase 2 output (/adk:tasks)
```

### Source Code (repository root)

```
frontend/
├── src/
│   ├── pages/
│   │   ├── _app.tsx                    # [MODIFY] Add route metadata map, URL hash query parsing
│   │   └── projects/
│   │       └── index.tsx               # [MODIFY] Pagination + search integration
│   ├── modules/
│   │   ├── layout/
│   │   │   └── AppLayout.tsx           # [MODIFY] TopNav + sidebar refactor, theme toggle, search input
│   │   └── pagination/
│   │       └── Pagination.tsx          # [NEW] Pagination component
│   ├── services/
│   │   ├── http.ts                     # [MODIFY] Add query params support, AbortController
│   │   └── projects.ts                # [MODIFY] Update listProjects with pagination + search params
│   ├── styles/
│   │   └── app.css                     # [MODIFY] Dark theme CSS variables, TopNav styles, search/pagination styles
│   └── utils/
│       ├── theme.ts                    # [NEW] Theme init, toggle, system follow
│       └── url.ts                      # [NEW] URL hash query param parser
├── server.js                           # [MODIFY] Inline FOUC script in HTML <head>
└── index.html                          # [MODIFY] data-theme attribute support

backend/
└── src/
    ├── api/
    │   └── routes/
    │       └── projects.py             # [MODIFY] Add page, page_size, search query params
    └── repositories/
        └── project_repository.py       # [MODIFY] Add paginated list with search support
```

**Structure Decision**: 保持现有 frontend/backend 结构，在前端 `modules/` 下新增 `pagination/` 模块，在 `utils/` 下新增 `theme.ts` 和 `url.ts` 工具。后端仅修改项目路由和仓库层。

## Complexity Tracking

*无违例需要说明——所有实现均在现有架构约束内，不引入新框架或新服务层。*
