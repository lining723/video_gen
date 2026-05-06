import { escapeHtml } from '../../utils/html.ts';
import { formatProjectLabel } from '../../utils/project.ts';

const SIDEBAR_STATE_KEY = 'sidebar-collapsed';

const stageItems = [
  { key: 'overview', label: '项目总览', icon: '📊', href: (projectId) => `#/projects/${projectId}`, code: '00' },
  { key: 'scene', label: '场景审核', icon: '🎬', href: (projectId) => `#/projects/${projectId}/scene`, code: '01' },
  { key: 'storyboard', label: '分镜编辑', icon: '📝', href: (projectId) => `#/projects/${projectId}/storyboard`, code: '02' },
  { key: 'renders', label: '渲染控制', icon: '⚙️', href: (projectId) => `#/projects/${projectId}/renders`, code: '03' },
  { key: 'final-video', label: '最终成片', icon: '🎞️', href: (projectId) => `#/projects/${projectId}/final-video`, code: '04' },
];

function renderStageNavigation(projectId, currentView) {
  if (!projectId) return '';

  return `
    <div class="surface strong">
      <div class="section-head">
        <div>
          <h3>制作流程</h3>
          <p>按场景、分镜、渲染、成片的顺序推进。</p>
        </div>
      </div>
      <ul class="nav-list">
        ${stageItems.map((item) => `
          <li>
            <a class="nav-link ${item.key === currentView ? 'active' : ''}" href="${item.href(projectId)}" title="${item.label}">
              <span class="nav-icon">${item.icon}</span>
              <span class="nav-label">${item.label}</span>
              <span class="nav-code">${item.code}</span>
            </a>
          </li>
        `).join('')}
      </ul>
    </div>
  `;
}

function renderProjectMeta(projectName, status, stage) {
  if (!projectName && !status && !stage) return '';
  return `
    <div class="surface">
      <div class="section-head">
        <div>
          <h3>当前项目</h3>
          <p>用统一的页面结构承接整个视频生产流程。</p>
        </div>
      </div>
      <div class="content-stack">
        <div>
          <strong>${escapeHtml(projectName || '未命名项目')}</strong>
        </div>
        <div class="pill-row">
          ${status ? `<span class="pill status-pill"><strong>状态</strong>${escapeHtml(formatProjectLabel(status))}</span>` : ''}
          ${stage ? `<span class="pill"><strong>阶段</strong>${escapeHtml(formatProjectLabel(stage))}</span>` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderSidebarToggle() {
  return `
    <button class="sidebar-toggle" title="收起/展开菜单栏">
      <span class="toggle-icon">◀</span>
    </button>
  `;
}

export function initSidebarState() {
  const isCollapsed = sessionStorage.getItem(SIDEBAR_STATE_KEY) === 'true';
  const sidebar = document.querySelector('.sidebar');
  if (sidebar && isCollapsed) {
    sidebar.classList.add('collapsed');
  }
}

export function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  const isCollapsed = sidebar.classList.toggle('collapsed');
  sessionStorage.setItem(SIDEBAR_STATE_KEY, String(isCollapsed));

  // Update toggle icon
  const toggleIcon = sidebar.querySelector('.toggle-icon');
  if (toggleIcon) {
    toggleIcon.textContent = isCollapsed ? '▶' : '◀';
  }
}

export function appShell(options) {
  const {
    eyebrow = 'AI Video Studio',
    title = '',
    description = '',
    metrics = '',
    actions = '',
    content = '',
    projectId = '',
    currentView = '',
    projectName = '',
    projectStatus = '',
    projectStage = '',
    aside = '',
  } = options;

  const sidebar = projectId
    ? `
      <aside class="sidebar">
        ${renderProjectMeta(projectName, projectStatus, projectStage)}
        ${renderStageNavigation(projectId, currentView)}
        ${aside}
        ${renderSidebarToggle()}
      </aside>
    `
    : '';

  return `
    <div class="app-shell">
      <div class="ambient-orb one"></div>
      <div class="ambient-orb two"></div>
      ${sidebar}
      <header class="topbar">
        <a class="brand-mark" href="#/projects">
          <div class="brand-copy">
            <strong>Frame Flow</strong>
            <span>AI video direction console</span>
          </div>
        </a>
        <a class="topbar-link" href="#/projects">项目首页</a>
      </header>
      <main class="page-shell">
        <section class="hero-panel">
          <div class="hero-grid">
            <div>
              <span class="eyebrow">${escapeHtml(eyebrow)}</span>
              <h1 class="hero-title">${escapeHtml(title)}</h1>
              <p class="hero-description">${escapeHtml(description)}</p>
              ${metrics ? `<div class="hero-metrics">${metrics}</div>` : ''}
            </div>
            ${actions ? `<div class="hero-actions">${actions}</div>` : '<div class="hero-actions"></div>'}
          </div>
        </section>
        <section class="content-grid single">
          <div class="content-stack">${content}</div>
        </section>
      </main>
    </div>
  `;
}
