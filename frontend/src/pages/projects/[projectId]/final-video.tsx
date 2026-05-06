import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { finalVideoContent } from '../../../modules/final-video/FinalVideoPage.tsx';
import { getFinalVideo } from '../../../services/render.ts';
import { getTimeline } from '../../../services/projects.ts';
import { formatProjectLabel } from '../../../utils/project.ts';

const finalVideoPendingKey = (projectId) => `final-video-pending:${projectId}`;
const finalVideoRoute = (projectId) => `#/projects/${projectId}/final-video`;

export async function renderFinalVideoPage(root, projectId) {
  const timeline = (await getTimeline(projectId)).item;
  let item = null;
  let pending = false;

  try {
    const response = await getFinalVideo(projectId);
    item = response.item;
    sessionStorage.removeItem(finalVideoPendingKey(projectId));
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }
    pending = timeline.project.current_stage === 'video_rendering' || sessionStorage.getItem(finalVideoPendingKey(projectId)) === '1';
  }

  const data = timeline;
  root.innerHTML = appShell({
    eyebrow: 'Final Video',
    title: '最终成片',
    description: '这一页只保留最终输出结果，不再混入流程操作。到这里，重点是确认版本质量并取走成片。',
    metrics: `
      <div class="metric-chip">
        <span class="metric-label">项目阶段</span>
        <span class="metric-value">${formatProjectLabel(data.project.current_stage)}</span>
      </div>
      <div class="metric-chip">
        <span class="metric-label">项目状态</span>
        <span class="metric-value">${formatProjectLabel(data.project.status)}</span>
      </div>
    `,
    actions: `
      <div class="hero-note">成片页改成单一结果页，避免再让用户在这里做流程控制，只保留预览与下载。合成中会自动轮询。</div>
      <a class="button-link secondary" href="#/projects/${projectId}/renders">回到渲染控制</a>
    `,
    content: finalVideoContent(item, { pending }),
    projectId,
    currentView: 'final-video',
    projectName: data.project.name,
    projectStatus: data.project.status,
    projectStage: data.project.current_stage,
  });

  if (pending && !item) {
    setTimeout(() => {
      if (location.hash === finalVideoRoute(projectId)) {
        renderFinalVideoPage(root, projectId);
      }
    }, 1500);
  }

  // Initialize sidebar state
  initSidebarState();
  const sidebarToggle = root.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.onclick = () => toggleSidebar();
  }
}
