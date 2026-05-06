import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { projectDashboardContent } from '../../../modules/project-dashboard/ProjectDashboardPage.tsx';
import { getTimeline, updateProjectSettings } from '../../../services/projects.ts';
import { formatProjectLabel } from '../../../utils/project.ts';

function setProjectSettingsFeedback(root, kind, message) {
  const target = root.querySelector('#project-settings-feedback');
  if (!target) return;
  if (!message) {
    target.hidden = true;
    target.innerHTML = '';
    return;
  }
  target.hidden = false;
  target.className = `notice ${kind}`;
  target.textContent = message;
}

export async function renderProjectDashboard(root, projectId) {
  const data = (await getTimeline(projectId)).item;
  root.innerHTML = appShell({
    eyebrow: 'Project Overview',
    title: '项目总览',
    description: '把项目状态、当前阶段和各流程入口压缩到同一视图里，进入任何步骤前都能快速完成判断。',
    metrics: `
      <div class="metric-chip">
        <span class="metric-label">项目状态</span>
        <span class="metric-value">${formatProjectLabel(data.project.status)}</span>
      </div>
      <div class="metric-chip">
        <span class="metric-label">当前阶段</span>
        <span class="metric-value">${formatProjectLabel(data.project.current_stage)}</span>
      </div>
    `,
    actions: `
      <div class="hero-note">总览页不再承担复杂编辑，只负责回答三个问题：项目在哪一步、内容生成到哪一步、下一步该进哪里。</div>
      <a class="button-link" href="#/projects/${projectId}/scene">进入场景审核</a>
    `,
    content: projectDashboardContent(data),
    projectId,
    currentView: 'overview',
    projectName: data.project.name,
    projectStatus: data.project.status,
    projectStage: data.project.current_stage,
  });

  const saveButton = root.querySelector('#save-project-model-settings');
  if (saveButton) {
    saveButton.onclick = async () => {
      await updateProjectSettings(projectId, {
        text_model: root.querySelector('#project-text-model')?.value || '',
        image_model: root.querySelector('#project-image-model')?.value || '',
        video_model: root.querySelector('#project-video-model')?.value || '',
      });
      await renderProjectDashboard(root, projectId);
      setProjectSettingsFeedback(root, 'success', '项目模型设置已保存。');
    };
  }

  // Initialize sidebar state
  initSidebarState();
  const sidebarToggle = root.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.onclick = () => toggleSidebar();
  }
}
