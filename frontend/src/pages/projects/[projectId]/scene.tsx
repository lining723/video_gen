import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { sceneReviewContent } from '../../../modules/scene-review/SceneReviewPage.tsx';
import { getTimeline } from '../../../services/projects.ts';
import { generateScene, reviewScene, updateSceneSettings } from '../../../services/sceneDesign.ts';

function setSceneSettingsFeedback(root, kind, message) {
  const target = root.querySelector('#scene-settings-feedback');
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

function getSceneCount(root) {
  const value = Number(root.querySelector('#scene-count-input')?.value || 3);
  return Math.max(1, Math.min(12, value));
}

export async function renderScenePage(root, projectId) {
  const data = (await getTimeline(projectId)).item;
  root.innerHTML = appShell({
    eyebrow: 'Scene Review',
    title: '场景设计审核',
    description: '先把整体叙事框架定住，再进入分镜和渲染，这一页只处理结构与方向。',
    metrics: `
      <div class="metric-chip">
        <span class="metric-label">当前版本</span>
        <span class="metric-value">${data.scene ? `V${data.scene.version}` : '未生成'}</span>
      </div>
      <div class="metric-chip">
        <span class="metric-label">配置场景数</span>
        <span class="metric-value">${data.project.scene_count || 3}</span>
      </div>
    `,
    actions: `
      <div class="hero-note">场景页改成“场景数量 + 摘要 + 场景列表 + 审核面板”的结构，先把拆分段落定住，再判断内容方向。</div>
      <a class="button-link secondary" href="#/projects/${projectId}">回到项目总览</a>
    `,
    content: sceneReviewContent(data.project, data.scene),
    projectId,
    currentView: 'scene',
    projectName: data.project.name,
    projectStatus: data.project.status,
    projectStage: data.project.current_stage,
  });
  const gen = root.querySelector('#generate-scene');
  if (gen) gen.onclick = async () => { await generateScene(projectId, { scene_count: getSceneCount(root) }); await renderScenePage(root, projectId); };
  const approve = root.querySelector('#scene-approve');
  const reject = root.querySelector('#scene-reject');
  const regenerate = root.querySelector('#scene-regenerate');
  const saveSceneCount = root.querySelector('#save-scene-count');
  const comment = () => root.querySelector('#scene-comment')?.value || '';
  if (saveSceneCount) {
    saveSceneCount.onclick = async () => {
      const sceneCount = getSceneCount(root);
      await updateSceneSettings(projectId, { scene_count: sceneCount });
      await renderScenePage(root, projectId);
      setSceneSettingsFeedback(root, 'success', `场景数量已更新为 ${sceneCount}。`);
    };
  }
  if (approve) approve.onclick = async () => { await reviewScene(projectId, { action: 'approve', comment: comment() }); location.hash = `#/projects/${projectId}/storyboard`; };
  if (reject) reject.onclick = async () => { await reviewScene(projectId, { action: 'reject', comment: comment() }); await renderScenePage(root, projectId); };
  if (regenerate) regenerate.onclick = async () => { await reviewScene(projectId, { action: 'regenerate', comment: comment() }); await renderScenePage(root, projectId); };

  // Initialize sidebar state
  initSidebarState();
  const sidebarToggle = root.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.onclick = () => toggleSidebar();
  }
}
