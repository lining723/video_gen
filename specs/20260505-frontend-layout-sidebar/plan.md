# Implementation Plan: 前端页面框架优化 - 左侧固定菜单栏

**Feature**: `20260505-frontend-layout-sidebar` | **Date**: 2026-05-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/20260505-frontend-layout-sidebar/spec.md`

## Summary

优化前端页面布局，实现左侧固定菜单栏，支持收起/展开功能。这是一个纯前端 UI 改进，主要涉及 CSS 布局调整和 JavaScript 状态管理。

核心改动：
1. 将现有侧边栏改为 `position: fixed` 固定定位
2. 添加收起/展开按钮和状态管理
3. 主内容区域自适应宽度

## Technical Context

**Language/Version**: TypeScript 5+ / Node.js 18+

**Primary Dependencies**:
- 现有前端框架（原生 TypeScript + HTML 模板）
- 无额外依赖

**Storage**: sessionStorage（菜单栏状态持久化）

**Testing**: 手动测试（前端 UI 功能）

**Target Platform**: Web 浏览器（Chrome, Firefox, Safari）

**Project Type**: Web application（前端）

**Performance Goals**:
- 收起/展开动画 < 300ms
- 页面加载时菜单栏状态恢复 < 100ms

**Constraints**:
- 保持现有路由结构不变
- 项目列表页不显示菜单栏
- 最小屏幕宽度 768px（低于此宽度自动收起）

**Scale/Scope**:
- 修改 2 个主要文件
- 影响 5 个项目内页面

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 检查结果 | 状态 |
|------|----------|------|
| **I. 产品闭环优先** | 布局优化提升用户体验，间接支持业务闭环 | ✅ PASS |
| **II. 人工审核门禁不可跳过** | 不涉及审核流程 | ✅ PASS |
| **III. 契约优先与跨端一致性** | 纯前端改动，无需 API 契约 | ✅ PASS |
| **IV. 异步媒体流水线可靠性** | 不涉及媒体处理 | ✅ PASS |
| **V. 可观测性、版本化与简洁实现** | 使用 sessionStorage，实现简洁 | ✅ PASS |

**结论**: 无宪章违规，可以继续实施。

## Project Structure

### Documentation (this feature)

```
specs/20260505-frontend-layout-sidebar/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出（N/A - 无数据模型）
├── quickstart.md        # Phase 1 输出
└── tasks.md             # Phase 2 输出 (/adk:tasks)
```

### Source Code (repository root)

```
frontend/
├── src/
│   ├── modules/
│   │   └── layout/
│   │       └── AppLayout.tsx    # 主要改动文件
│   ├── styles/
│   │   └── app.css              # CSS 样式改动
│   └── pages/
│       └── projects/
│           └── [projectId]/
│               └── *.tsx        # 各页面（状态初始化）
└── tests/
    └── (无新增测试)
```

**Structure Decision**: 纯前端项目，仅修改 `frontend/src/` 目录下的文件。主要改动集中在 `AppLayout.tsx` 和 `app.css`。

## Complexity Tracking

*无宪章违规，本节不适用*

---

## Phase 0: Research

### 研究问题

1. **CSS 固定定位最佳实践**
   - `position: fixed` 与 flex 布局的配合
   - 避免内容被遮挡的方案

2. **sessionStorage 状态管理**
   - 状态初始化时机
   - 跨页面状态一致性

3. **响应式布局处理**
   - 小屏幕设备的适配方案
   - 断点选择

### 研究结论

见 [research.md](./research.md)

---

## Phase 1: Design

### 数据模型

本功能无后端数据模型。前端状态存储于 sessionStorage：

- Key: `sidebar-collapsed`
- Value: `"true"` | `"false"`

见 [data-model.md](./data-model.md)

### 快速开始

见 [quickstart.md](./quickstart.md)

---

## Risks & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 固定定位导致内容遮挡 | 中 | 使用 margin-left 为主内容区域预留空间 |
| 小屏幕显示异常 | 低 | 设置断点，小屏幕自动收起 |
| 状态初始化闪烁 | 低 | 在 DOMContentLoaded 前应用状态 |

## Next Steps

1. 用户确认本计划
2. 执行 `/adk:tasks` 生成详细任务分解
