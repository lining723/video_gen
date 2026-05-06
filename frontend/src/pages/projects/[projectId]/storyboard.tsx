import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { storyboardEditorContent } from '../../../modules/storyboard-editor/StoryboardEditorPage.tsx';
import { shotDetailForm } from '../../../modules/storyboard-editor/ShotCard.tsx';
import { collectShotPayload } from '../../../modules/storyboard-editor/shotUtils.ts';
import { getTimeline } from '../../../services/projects.ts';
import { generateStoryboard, regenerateShot, reviewStoryboard, updateShot, updateStoryboardSettings } from '../../../services/storyboard.ts';
import { formatProjectLabel } from '../../../utils/project.ts';

function setFeedback(root, kind, message) {
  const target = root.querySelector('#storyboard-feedback');
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

function getShotById(data, shotId) {
  return (data.storyboard || []).find((item) => item.id === shotId) || null;
}

function openShotModal(root, shot) {
  const modal = root.querySelector('#shot-detail-modal');
  const body = root.querySelector('#shot-detail-modal-body');
  if (!modal || !body || !shot) return;
  body.innerHTML = shotDetailForm(shot);
  modal.hidden = false;
}

function closeShotModal(root) {
  const modal = root.querySelector('#shot-detail-modal');
  if (modal) modal.hidden = true;
}

function getDragAfterElement(container, y, draggingId) {
  const items = [...container.querySelectorAll('.shot-list-item:not(.dragging)')].filter((item) => item.dataset.shotId !== draggingId);
  let closest = null;
  let closestOffset = Number.NEGATIVE_INFINITY;
  for (const item of items) {
    const box = item.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closestOffset) {
      closestOffset = offset;
      closest = item;
    }
  }
  return closest;
}

async function persistShotOrder(root, projectId) {
  const items = [...root.querySelectorAll('.shot-list-item')];
  await Promise.all(items.map((item, index) => updateShot(projectId, item.dataset.shotId, { sequence: index + 1 })));
}

function bindModalActions(root, projectId) {
  root.querySelectorAll('[data-action="close-shot-modal"]').forEach((button) => {
    button.onclick = () => closeShotModal(root);
  });

  const modalBody = root.querySelector('#shot-detail-modal-body');
  if (!modalBody) return;
  const shotId = modalBody.querySelector('.shot-detail-form')?.dataset.shotId;
  if (!shotId) return;

  const saveButton = modalBody.querySelector('[data-action="save-shot"]');
  if (saveButton) {
    saveButton.onclick = async () => {
      await updateShot(projectId, shotId, collectShotPayload(modalBody));
      await renderStoryboardPage(root, projectId, { openShotId: shotId, feedback: { kind: 'success', message: '分镜已保存。' } });
    };
  }

  const regenerateButton = modalBody.querySelector('[data-action="regenerate-shot"]');
  if (regenerateButton) {
    regenerateButton.onclick = async () => {
      await regenerateShot(projectId, shotId);
      await renderStoryboardPage(root, projectId, { openShotId: shotId, feedback: { kind: 'success', message: '镜头已重新生成。' } });
    };
  }
}

function bindShotList(root, projectId, data) {
  root.querySelectorAll('[data-action="view-shot"]').forEach((button) => {
    button.onclick = () => {
      const shotId = button.closest('.shot-list-item')?.dataset.shotId;
      const shot = getShotById(data, shotId);
      if (!shot) return;
      openShotModal(root, shot);
      bindModalActions(root, projectId);
    };
  });

  root.querySelectorAll('.shot-list-item [data-action="regenerate-shot"]').forEach((button) => {
    button.onclick = async () => {
      const shotId = button.closest('.shot-list-item')?.dataset.shotId;
      if (!shotId) return;
      const shot = getShotById(data, shotId);
      await regenerateShot(projectId, shotId);
      await renderStoryboardPage(root, projectId, { feedback: { kind: 'success', message: `镜头 ${shot?.sequence || ''} 已重新生成。` } });
    };
  });

  const list = root.querySelector('[data-shot-review-list]');
  if (!list) return;
  let dragging = null;
  let orderChanged = false;

  list.querySelectorAll('.shot-list-item').forEach((item) => {
    item.addEventListener('dragstart', () => {
      dragging = item;
      orderChanged = false;
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', async () => {
      item.classList.remove('dragging');
      if (orderChanged) {
        await persistShotOrder(root, projectId);
        await renderStoryboardPage(root, projectId, { feedback: { kind: 'success', message: '镜头顺序已更新。' } });
      }
      dragging = null;
    });
  });

  list.addEventListener('dragover', (event) => {
    event.preventDefault();
    if (!dragging) return;
    const afterElement = getDragAfterElement(list, event.clientY, dragging.dataset.shotId);
    orderChanged = true;
    if (!afterElement) {
      list.appendChild(dragging);
    } else {
      list.insertBefore(dragging, afterElement);
    }
  });
}

function bindStoryboardStyle(root, projectId, currentStyle) {
  const input = root.querySelector('#storyboard-style-input');
  const saveButton = root.querySelector('#save-storyboard-style');
  if (!(input instanceof HTMLInputElement) || !(saveButton instanceof HTMLButtonElement)) return;

  root.querySelectorAll('[data-style-preset]').forEach((button) => {
    button.onclick = async () => {
      const nextStyle = button.dataset.stylePreset || '';
      input.value = nextStyle;
      await updateStoryboardSettings(projectId, { storyboard_style: nextStyle });
      await renderStoryboardPage(root, projectId, {
        feedback: { kind: 'success', message: `统一风格已切换为“${nextStyle}”。` },
      });
    };
  });

  saveButton.onclick = async () => {
    const nextStyle = input.value.trim();
    if (nextStyle === currentStyle) {
      setFeedback(root, 'info', nextStyle ? '当前统一风格未发生变化。' : '当前未设置统一风格。');
      return;
    }
    await updateStoryboardSettings(projectId, { storyboard_style: nextStyle });
    await renderStoryboardPage(root, projectId, {
      feedback: {
        kind: 'success',
        message: nextStyle
          ? `统一风格已保存为“${nextStyle}”，后续生成会保持一致。`
          : '统一风格已清空，后续生成将按场景内容自由生成。',
      },
    });
  };
}

export async function renderStoryboardPage(root, projectId, options = {}) {
  const data = (await getTimeline(projectId)).item;
  root.innerHTML = appShell({
    eyebrow: 'Storyboard',
    title: '分镜审核',
    description: '列表页负责审核、排序和操作分发；详情编辑进入弹窗完成，镜头信息不会再把主页面撑成长表单。',
    metrics: `
      <div class="metric-chip">
        <span class="metric-label">镜头数</span>
        <span class="metric-value">${(data.storyboard || []).length}</span>
      </div>
      <div class="metric-chip">
        <span class="metric-label">当前阶段</span>
        <span class="metric-value">${formatProjectLabel(data.project.current_stage)}</span>
      </div>
    `,
    actions: `
      <div class="hero-note">分镜审核页现在支持统一风格设定、列表拖拽排序、详情弹窗编辑和单镜头重生，审核动作更集中。</div>
      <a class="button-link secondary" href="#/projects/${projectId}/scene">回看场景设计</a>
    `,
    content: storyboardEditorContent(data.project, data.storyboard),
    projectId,
    currentView: 'storyboard',
    projectName: data.project.name,
    projectStatus: data.project.status,
    projectStage: data.project.current_stage,
  });

  const gen = root.querySelector('#generate-storyboard');
  if (gen) {
    gen.onclick = async () => {
      await generateStoryboard(projectId);
      await renderStoryboardPage(root, projectId, { feedback: { kind: 'success', message: '分镜已重新生成。' } });
    };
  }

  const approve = root.querySelector('#approve-storyboard');
  const reject = root.querySelector('#reject-storyboard');
  if (approve) approve.onclick = async () => { await reviewStoryboard(projectId, { action: 'approve' }); location.hash = `#/projects/${projectId}/renders`; };
  if (reject) reject.onclick = async () => { await reviewStoryboard(projectId, { action: 'reject', comment: '请调整分镜' }); await renderStoryboardPage(root, projectId, { feedback: { kind: 'warn', message: '分镜已驳回，请继续调整。' } }); };

  bindStoryboardStyle(root, projectId, (data.project.storyboard_style || '').trim());
  bindShotList(root, projectId, data);
  if (options.feedback) {
    setFeedback(root, options.feedback.kind, options.feedback.message);
  }
  if (options.openShotId) {
    const shot = getShotById(data, options.openShotId);
    if (shot) {
      openShotModal(root, shot);
      bindModalActions(root, projectId);
    }
  }

  // Initialize sidebar state
  initSidebarState();
  const sidebarToggle = root.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.onclick = () => toggleSidebar();
  }
}
