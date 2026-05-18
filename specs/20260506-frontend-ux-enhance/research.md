# Research: 前端页面重构与用户体验增强

**Feature**: `20260506-frontend-ux-enhance`
**Date**: 2026-05-06

## 1. 暗黑模式 CSS 变量策略

**Decision**: 使用 `[data-theme="dark"]` 选择器覆盖 CSS 变量，在 `<html>` 元素上切换属性。

**Rationale**:
- 现有 `app.css` 已在 `:root` 中定义 24 个 CSS 变量（`--bg`、`--text`、`--accent` 等），只需新增一个 `[data-theme="dark"]` 块覆盖这些变量即可
- 所有现有样式选择器已引用 CSS 变量，不需要修改选择器
- `data-theme` 属性方案比 class 切换更明确，不会与现有 class 冲突

**Alternatives considered**:
- `prefers-color-scheme` 媒体查询：仅支持系统主题跟随，无法实现手动切换覆盖
- CSS class `.dark`：与现有 BEM-like class 命名可能冲突，语义不如 `data-theme` 清晰
- 独立 CSS 文件（`dark.css`）：增加 HTTP 请求，切换时有加载延迟

**Dark theme color mapping** (key decisions):
| Variable | Light | Dark |
|----------|-------|------|
| `--bg` | `#f4efe7` | `#1a1a1a` |
| `--bg-deep` | `#e8dfd2` | `#0d0d0d` |
| `--surface` | `rgba(255,252,247,0.82)` | `rgba(30,30,30,0.82)` |
| `--text` | `#1d1a17` | `#e8e4df` |
| `--text-muted` | `#6c6258` | `#9d958b` |
| `--accent` | `#b85c38` | `#d4754e` (higher lightness for dark bg) |
| Body gradient | warm cream tones | dark neutral tones |

## 2. FOUC（Flash of Unstyled Content）防护

**Decision**: 在 `index.html` 的 `<head>` 中内联同步阻塞脚本，在首帧渲染前设置 `data-theme`。

**Rationale**:
- 当前 `server.js` 只做静态文件服务，无服务端渲染
- 内联 `<script>` 不依赖外部 JS 加载，在 HTML 解析阶段同步执行
- 脚本仅读取 `localStorage` 和 `matchMedia`，< 1ms 执行时间

**Implementation**:
```html
<script>
(function(){var t=localStorage.getItem('theme-preference');
if(!t) t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
document.documentElement.setAttribute('data-theme',t);})();
</script>
```

**Alternatives considered**:
- CSS `prefers-color-scheme` 回退：无法覆盖用户手动偏好，FOUC 无法避免
- 服务端读取 cookie：当前无 cookie 机制，引入会增加复杂度

## 3. 搜索实现：前端过滤 vs 后端搜索

**Decision**: 统一使用后端搜索（`GET /api/projects?search=keyword`），无论项目数量多少。

**Rationale**:
- 搜索天然与分页耦合，前端过滤无法正确处理跨页搜索
- 项目名称搜索在 SQLite `LIKE` 查询中性能足够（< 1000 条时 < 10ms）
- 单一实现路径简化了前后端逻辑，避免"前端过滤/后端搜索"两套代码
- SQLite `LIKE` 默认不区分大小写（对于 ASCII 字符），符合需求

**Alternatives considered**:
- 纯前端过滤：无法与分页协同（需要先拉全量数据再前端分页），数据量大时性能差
- FTS5 全文搜索：过度设计，项目名称搜索不需要全文索引

## 4. URL Hash 查询参数解析

**Decision**: 在 `_app.tsx` 的 `parseRoute()` 中新增 hash 查询参数解析，将 `?key=value` 部分提取为 `URLSearchParams`。

**Rationale**:
- 当前 `parseRoute()` 只解析路径段（`#/projects/123/scene` → `['projects', '123', 'scene']`），不处理查询参数
- hash 路由天然支持 `?` 查询字符串（`#/projects?page=2&search=test`），浏览器不会发送到服务器
- `URLSearchParams` 是标准 API，无兼容问题

**Implementation**:
```typescript
function parseRoute() {
  const hash = location.hash.replace(/^#/, '') || '/projects';
  const [path, query] = hash.split('?');
  const parts = path.split('/').filter(Boolean);
  const params = new URLSearchParams(query || '');
  return { parts, params };
}
```

**Alternatives considered**:
- 自定义分隔符（如 `#/projects/page/2`）：非标准，与现有路由格式冲突，不支持可选参数
- History API (`pushState`)：需要改造整个路由系统，改动范围过大

## 5. 分页后端实现

**Decision**: 在 `ProjectRepository.list()` 增加 `page`、`page_size`、`search` 可选参数，SQL 层做 `LIMIT/OFFSET` 和 `WHERE name LIKE`。

**Rationale**:
- SQLite 的 `LIMIT ? OFFSET ?` 是标准分页方式
- 需要额外 `SELECT COUNT(*)` 获取总数以计算 `total_pages`
- 保持 `page`、`page_size` 默认值与原 `list()` 行为兼容（不传参时返回全部数据）

**Implementation**:
```python
def list(self, page=None, page_size=None, search=None):
    where = ''
    params = []
    if search:
        where = ' WHERE name LIKE ?'
        params.append(f'%{search}%')
    
    if page and page_size:
        count = self.db.fetchone(f'SELECT COUNT(*) as cnt FROM projects{where}', params)
        total = count['cnt'] if count else 0
        offset = (page - 1) * page_size
        rows = self.db.fetchall(
            f'SELECT * FROM projects{where} ORDER BY created_at DESC LIMIT ? OFFSET ?',
            params + [page_size, offset]
        )
        return {
            'items': [dict(row) for row in rows],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': max(1, (total + page_size - 1) // page_size) if total > 0 else 0,
        }
    
    rows = self.db.fetchall(f'SELECT * FROM projects{where} ORDER BY created_at DESC', params)
    return {'items': [dict(row) for row in rows]}
```

**Alternatives considered**:
- 游标分页（`keyset pagination`）：对 `created_at` 排序场景更高效，但实现复杂，不支持跳页，不适合通用列表
- 全量查询 + 前端分页：数据量大时浪费带宽和内存

## 6. 请求取消（AbortController）

**Decision**: 在 `request()` 函数中支持 `AbortController` 信号，分页/搜索切换时取消前一个未完成的请求。

**Rationale**:
- 快速切换页码或连续输入搜索词时，前一个请求的响应可能覆盖后一个请求的结果（竞态条件）
- `AbortController` 是现代浏览器标准 API，`fetch` 原生支持
- 改动集中在 `http.ts` 的 `request()` 函数，对调用方透明

**Implementation**: 在 `request()` 函数中接受可选的 `signal` 参数，分页/搜索调用方创建 `AbortController` 并在新请求前 `abort()` 上一个。

## 7. 现有 KeyframeGrid React Island 兼容性

**Decision**: `KeyframeGrid.tsx` 使用 Ant Design，自带样式体系。暗黑模式下不对其内部做深度适配，仅确保外层容器背景与主题一致。

**Rationale**:
- Ant Design 组件有自己的 `ConfigProvider` 主题机制，深色模式适配需要单独处理
- 该组件是独立的 React island，不在本次核心重构范围内
- 通过在 `.keyframe-grid-container` 上设置 `background: var(--bg)` 确保容器与整体风格一致

**Alternative considered**: 
- 全面适配 Ant Design dark theme：工作量过大，且该组件本身在独立页面中，视觉差异可接受
