import { appShell } from '../../modules/layout/AppLayout.tsx';
import { projectCreateForm } from '../../modules/project-create/ProjectCreateForm.tsx';
import { createProject, listProjects } from '../../services/projects.ts';
import { escapeHtml, preserveLineBreaks } from '../../utils/html.ts';
import { formatProjectLabel } from '../../utils/project.ts';

export async function renderProjectsPage(root) {
  const projects = (await listProjects()).items || [];
  const total = projects.length;
  const active = projects.filter((item) => item.status !== 'completed').length;
  const completed = projects.filter((item) => item.status === 'completed').length;

  const list = projects.map((item) => `
    <li class="project-list-item">
      <div class="project-title-row">
        <div>
          <h3>${escapeHtml(item.name || '未命名项目')}</h3>
          <p>${preserveLineBreaks(item.prompt || '暂无项目描述')}</p>
        </div>
        <div class="pill-row">
          <span class="pill status-pill ${item.status === 'completed' ? 'success' : ''}">
            <strong>状态</strong>${escapeHtml(formatProjectLabel(item.status))}
          </span>
          <span class="pill"><strong>阶段</strong>${escapeHtml(formatProjectLabel(item.current_stage || 'draft'))}</span>
        </div>
      </div>
      <div class="action-row" style="margin-top:14px;">
        <a class="button-link secondary" href="#/projects/${item.id}">查看项目流转</a>
      </div>
    </li>
  `).join('') || `
    <li>
      <div class="empty-state">
        <h3>还没有项目</h3>
        <p>先从左侧创建一个视频需求，后面的场景设计、分镜和渲染都会按同一条流程展开。</p>
      </div>
    </li>
  `;

  const metrics = `
    <div class="metric-chip">
      <span class="metric-label">项目总数</span>
      <span class="metric-value">${total}</span>
    </div>
    <div class="metric-chip">
      <span class="metric-label">进行中</span>
      <span class="metric-value">${active}</span>
    </div>
    <div class="metric-chip">
      <span class="metric-label">已完成</span>
      <span class="metric-value">${completed}</span>
    </div>
  `;

  const actions = `
    <div class="hero-note">
      这一页不再只是入口表单，而是整个视频项目的中控台。新项目创建、现有项目回看和流程切换都收敛到同一层级。
    </div>
    <a class="button-link ghost" href="#/projects">回到项目清单</a>
  `;

  const content = `
    <div class="project-landing">
      ${projectCreateForm()}
      <section class="surface">
        <div class="section-head">
          <div>
            <h2 class="headline">最近项目</h2>
            <p class="subheadline">所有项目统一展示名称、当前阶段和创意说明，便于快速继续推进。</p>
          </div>
        </div>
        <ul class="plain-list">${list}</ul>
      </section>
    </div>
  `;

  root.innerHTML = appShell({
    title: '智能视频生成平台',
    description: '用更清晰的页面结构承接项目创建、流程推进和结果回看，让操作路径更短，内容层级更稳。',
    metrics,
    actions,
    content,
  });
  root.querySelector('#create-project').onclick = async () => {
    const name = root.querySelector('#project-name').value;
    const prompt = root.querySelector('#project-prompt').value;
    const sceneCount = Number(root.querySelector('#project-scene-count').value || 3);
    const result = await createProject({ name, prompt, scene_count: sceneCount });
    location.hash = `#/projects/${result.item.id}/scene`;
  };
}
