import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { projectDashboardContent } from '../../../modules/project-dashboard/ProjectDashboardPage.tsx';
import { getTimeline, updateProjectSettings } from '../../../services/projects.ts';
import { listVideoModels, listTextModels, listImageModels } from '../../../services/models.ts';
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

async function populateModelSelectors(root, project) {
  // 填充视频模型选择器
  try {
    const videoData = await listVideoModels();
    const videoSelect = root.querySelector('#project-video-model') as HTMLSelectElement;
    if (videoSelect && videoData.ok) {
      // 清空现有选项
      videoSelect.innerHTML = '<option value="">使用默认模型</option>';
      // 按提供商分组
      for (const provider of videoData.providers || []) {
        const group = document.createElement('optgroup');
        group.label = provider.name;
        for (const model of provider.models || []) {
          const option = document.createElement('option');
          option.value = model.id;
          option.textContent = model.name;
          if (model.id === project.video_model) {
            option.selected = true;
          }
          group.appendChild(option);
        }
        videoSelect.appendChild(group);
      }
    }
  } catch (error) {
    console.error('Failed to load video models:', error);
  }

  // 填充文本模型选择器
  try {
    const textData = await listTextModels();
    const textSelect = root.querySelector('#project-text-model') as HTMLSelectElement;
    if (textSelect && textData.ok) {
      textSelect.innerHTML = '<option value="">使用默认模型</option>';
      for (const model of textData.models || []) {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.provider_name})`;
        if (model.id === project.text_model) {
          option.selected = true;
        }
        textSelect.appendChild(option);
      }
    }
  } catch (error) {
    console.error('Failed to load text models:', error);
  }

  // 填充图片模型选择器
  try {
    const imageData = await listImageModels();
    const imageSelect = root.querySelector('#project-image-model') as HTMLSelectElement;
    if (imageSelect && imageData.ok) {
      imageSelect.innerHTML = '<option value="">使用默认模型</option>';
      for (const model of imageData.models || []) {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.provider_name})`;
        if (model.id === project.image_model) {
          option.selected = true;
        }
        imageSelect.appendChild(option);
      }
    }
  } catch (error) {
    console.error('Failed to load image models:', error);
  }
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

  // 填充模型选择器
  await populateModelSelectors(root, data.project);

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
