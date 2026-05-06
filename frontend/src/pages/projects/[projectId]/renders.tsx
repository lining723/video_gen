import { appShell, initSidebarState, toggleSidebar } from '../../../modules/layout/AppLayout.tsx';
import { renderProgressContent } from '../../../modules/render-progress/RenderProgressPage.tsx';
import { fetchTimeline } from '../../../hooks/useProjectTimeline.ts';
import { clearFinalVideoBgm, composeVideo, generateShotSubject, generateSubjects, getRenderStatus, retryRender, startRenders, updateFinalVideoSettings, uploadFinalVideoBgm, uploadShotSubject, lockSubject, unlockSubject, updateSubjectFeature, regenerateSubject, getSubjectVersions, rollbackSubjectVersion } from '../../../services/render.ts';

const noticeKey = (projectId) => `render-force-notice:${projectId}`;
const finalVideoPendingKey = (projectId) => `final-video-pending:${projectId}`;
const composeErrorKey = (projectId) => `compose-error:${projectId}`;
const manualProgressKey = (projectId) => `render-progress-query:${projectId}`;
const previewExpandedKey = (projectId) => `render-preview-expanded:${projectId}`;
const rendersRoute = (projectId) => `#/projects/${projectId}/renders`;

function rerenderRendersPageLater(root, projectId, delay) {
  setTimeout(() => {
    if (location.hash === rendersRoute(projectId)) {
      renderRendersPage(root, projectId);
    }
  }, delay);
}

function latestByShot(items) {
  const map = new Map();
  (items || []).forEach((item) => map.set(item.shot_id, item));
  return Array.from(map.values());
}

function buildNotice(projectId, data) {
  const latestTasks = latestByShot(data.render_tasks || []);
  const sequenceByShotId = Object.fromEntries((data.storyboard || []).map((item) => [item.id, item.sequence]));
  const raw = sessionStorage.getItem(noticeKey(projectId));
  if (!raw) return '';

  try {
    const pending = JSON.parse(raw);
    if (pending.scope === 'shot') {
      const task = latestTasks.find((item) => item.shot_id === pending.shotId);
      if (!task) return '';
      const sequence = sequenceByShotId[pending.shotId] || '-';
      if (task.status === 'running' && task.force_refresh) {
        return `<div class="notice info"><strong>镜头 ${sequence}</strong> 正在跳过缓存重新生成，请稍候。</div>`;
      }
      if (task.status === 'succeeded' && task.force_refresh) {
        sessionStorage.removeItem(noticeKey(projectId));
        return `<div class="notice success"><strong>镜头 ${sequence}</strong> 已替换旧缓存产物。</div>`;
      }
      return '';
    }

    if (pending.scope === 'all') {
      const forceTasks = latestTasks.filter((item) => item.force_refresh);
      if (forceTasks.some((item) => item.status === 'running')) {
        return '<div class="notice info">整批镜头正在跳过缓存重新生成，请稍候。</div>';
      }
      if (forceTasks.length && forceTasks.every((item) => item.status === 'succeeded')) {
        sessionStorage.removeItem(noticeKey(projectId));
        return '<div class="notice success">整批镜头已完成重新生成，旧缓存产物已替换。</div>';
      }
    }
  } catch {
    sessionStorage.removeItem(noticeKey(projectId));
  }
  return '';
}

function readManualProgress(projectId) {
  try {
    return JSON.parse(sessionStorage.getItem(manualProgressKey(projectId)) || '{}');
  } catch {
    sessionStorage.removeItem(manualProgressKey(projectId));
    return {};
  }
}

function writeManualProgress(projectId, value) {
  sessionStorage.setItem(manualProgressKey(projectId), JSON.stringify(value));
}

function readExpandedPreviewKeys(projectId) {
  try {
    const parsed = JSON.parse(sessionStorage.getItem(previewExpandedKey(projectId)) || '[]');
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.map((item) => String(item)));
  } catch {
    sessionStorage.removeItem(previewExpandedKey(projectId));
    return new Set();
  }
}

function writeExpandedPreviewKeys(projectId, value) {
  sessionStorage.setItem(previewExpandedKey(projectId), JSON.stringify(Array.from(value)));
}

function collectExpandedPreviewKeys(root) {
  const keys = new Set();
  root.querySelectorAll('details.details[data-preview-key][open]').forEach((element) => {
    const key = element.dataset.previewKey;
    if (key) keys.add(key);
  });
  return keys;
}

function persistExpandedPreviewKeysFromDom(root, projectId) {
  const detailNodes = root.querySelectorAll('details.details[data-preview-key]');
  if (!detailNodes.length) return;
  writeExpandedPreviewKeys(projectId, collectExpandedPreviewKeys(root));
}

function restoreExpandedPreviewKeys(root, projectId) {
  const expanded = readExpandedPreviewKeys(projectId);
  if (!expanded.size) return;
  root.querySelectorAll('details.details[data-preview-key]').forEach((element) => {
    const key = element.dataset.previewKey;
    element.open = !!(key && expanded.has(key));
  });
}

function bindPreviewTogglePersistence(root, projectId) {
  root.querySelectorAll('details.details[data-preview-key]').forEach((element) => {
    element.ontoggle = () => {
      writeExpandedPreviewKeys(projectId, collectExpandedPreviewKeys(root));
    };
  });
}

function formatManualProgress(item) {
  const parts = [item.progress_label || '已收到最新进度'];
  if (item.started_at) parts.push(`开始于 ${item.started_at}`);
  if (item.finished_at) parts.push(`结束于 ${item.finished_at}`);
  if (item.updated_at) parts.push(`记录更新时间 ${item.updated_at}`);
  return parts.join('，');
}

async function fileToUploadBody(file) {
  const dataUrl = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Failed to read image file'));
    reader.onload = () => resolve(String(reader.result || ''));
    reader.readAsDataURL(file);
  });
  const parts = String(dataUrl).split(',', 2);
  return {
    filename: file.name,
    content_type: file.type || 'application/octet-stream',
    data_base64: parts[1] || '',
  };
}

export async function renderRendersPage(root, projectId) {
  persistExpandedPreviewKeysFromDom(root, projectId);
  const data = await fetchTimeline(projectId);
  const notice = buildNotice(projectId, data);
  const composeError = sessionStorage.getItem(composeErrorKey(projectId)) || '';
  const manualProgressByShotId = readManualProgress(projectId);
  root.innerHTML = appShell({
    eyebrow: 'Render Progress',
    title: '渲染控制',
    description: '把主体生成、渲染状态、缓存重试和成片合成收进一个操作面上，让整个后半程更顺手。',
    metrics: `
      <div class="metric-chip">
        <span class="metric-label">主体资产</span>
        <span class="metric-value">${(data.subjects || []).length}</span>
      </div>
      <div class="metric-chip">
        <span class="metric-label">渲染记录</span>
        <span class="metric-value">${(data.render_tasks || []).length}</span>
      </div>
    `,
    actions: `
      <div class="hero-note">渲染页从原来的信息长串改成三块：控制台、主体资产、镜头任务。高频按钮都集中在顶部。</div>
      <a class="button-link secondary" href="#/projects/${projectId}/storyboard">返回分镜编辑</a>
    `,
    content: `${notice ? `<section>${notice}</section>` : ''}${renderProgressContent(data, { composeError, manualProgressByShotId })}`,
    projectId,
    currentView: 'renders',
    projectName: data.project.name,
    projectStatus: data.project.status,
    projectStage: data.project.current_stage,
  });
  restoreExpandedPreviewKeys(root, projectId);
  bindPreviewTogglePersistence(root, projectId);

  // Initialize sidebar state and bind toggle
  initSidebarState();
  const sidebarToggle = root.querySelector('.sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.onclick = () => toggleSidebar();
  }

  root.querySelector('#generate-subjects').onclick = async () => {
    await generateSubjects(projectId);
    await renderRendersPage(root, projectId);
  };

  root.querySelector('#start-renders').onclick = async () => {
    await startRenders(projectId);
    rerenderRendersPageLater(root, projectId, 1200);
  };

  root.querySelector('#start-renders-force').onclick = async () => {
    sessionStorage.setItem(noticeKey(projectId), JSON.stringify({ scope: 'all', at: Date.now() }));
    await startRenders(projectId, { force: true });
    rerenderRendersPageLater(root, projectId, 1200);
  };

  root.querySelector('#compose-video').onclick = async () => {
    try {
      await composeVideo(projectId);
      sessionStorage.removeItem(composeErrorKey(projectId));
      sessionStorage.setItem(finalVideoPendingKey(projectId), '1');
      setTimeout(() => { location.hash = `#/projects/${projectId}/final-video`; }, 400);
    } catch (error) {
      sessionStorage.removeItem(finalVideoPendingKey(projectId));
      sessionStorage.setItem(composeErrorKey(projectId), error.payload?.details?.blockers?.map((item) => `镜头 ${item.sequence} ${item.reason}`).join('；') || error.message);
      await renderRendersPage(root, projectId);
    }
  };

  root.querySelectorAll('.retry-render').forEach((button) => {
    button.onclick = async () => {
      await retryRender(projectId, button.dataset.shotId);
      rerenderRendersPageLater(root, projectId, 1200);
    };
  });

  root.querySelectorAll('.retry-render-force').forEach((button) => {
    button.onclick = async () => {
      sessionStorage.setItem(noticeKey(projectId), JSON.stringify({ scope: 'shot', shotId: button.dataset.shotId, at: Date.now() }));
      await retryRender(projectId, button.dataset.shotId, { force: true });
      rerenderRendersPageLater(root, projectId, 1200);
    };
  });

  root.querySelectorAll('.query-render-status').forEach((button) => {
    button.onclick = async () => {
      const result = await getRenderStatus(projectId, button.dataset.shotId);
      writeManualProgress(projectId, {
        ...readManualProgress(projectId),
        [button.dataset.shotId]: formatManualProgress(result.item),
      });
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.upload-shot-subject').forEach((button) => {
    button.onclick = () => {
      const input = root.querySelector(`.shot-subject-input[data-shot-id="${button.dataset.shotId}"]`);
      if (input) input.click();
    };
  });

  root.querySelectorAll('.generate-shot-subject').forEach((button) => {
    button.onclick = async () => {
      await generateShotSubject(projectId, button.dataset.shotId, { mode: 'generate' });
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.derive-shot-subject').forEach((button) => {
    button.onclick = async () => {
      if (button.disabled) return;
      await generateShotSubject(projectId, button.dataset.shotId, { mode: 'previous_tail_frame' });
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.generate-variant-btn').forEach((button) => {
    button.onclick = async () => {
      if (button.disabled) return;
      const variantHints = ['微笑表情', '严肃表情', '侧面角度', '运动装束', '休闲服装', '正装打扮'];
      const hint = prompt(`请输入变体方向：\n\n预设选项：\n${variantHints.join('、')}\n\n或输入自定义描述：`);
      if (hint && hint.trim()) {
        await generateShotSubject(projectId, button.dataset.shotId, { mode: 'variant', variant_hint: hint.trim() });
        await renderRendersPage(root, projectId);
      }
    };
  });

  root.querySelectorAll('.shot-subject-input').forEach((input) => {
    input.onchange = async () => {
      const [file] = Array.from(input.files || []);
      if (!file) return;
      await uploadShotSubject(projectId, input.dataset.shotId, await fileToUploadBody(file));
      input.value = '';
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.compose-setting-toggle').forEach((input) => {
    input.onchange = async () => {
      await updateFinalVideoSettings(projectId, {
        [input.dataset.setting]: !!input.checked,
      });
      await renderRendersPage(root, projectId);
    };
  });

  const bgmUploadButton = root.querySelector('#upload-final-bgm');
  const clearBgmButton = root.querySelector('#clear-final-bgm');
  const bgmInput = root.querySelector('#final-bgm-input');
  if (bgmUploadButton && bgmInput) {
    bgmUploadButton.onclick = () => bgmInput.click();
    bgmInput.onchange = async () => {
      const [file] = Array.from(bgmInput.files || []);
      if (!file) return;
      await uploadFinalVideoBgm(projectId, await fileToUploadBody(file));
      bgmInput.value = '';
      await renderRendersPage(root, projectId);
    };
  }
  if (clearBgmButton) {
    clearBgmButton.onclick = async () => {
      await clearFinalVideoBgm(projectId);
      await renderRendersPage(root, projectId);
    };
  }

  const latestTasks = latestByShot(data.render_tasks || []);

  // Subject operations event handlers
  root.querySelectorAll('.lock-subject-btn').forEach((button) => {
    button.onclick = async () => {
      await lockSubject(projectId, button.dataset.subjectId);
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.unlock-subject-btn').forEach((button) => {
    button.onclick = async () => {
      await unlockSubject(projectId, button.dataset.subjectId);
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.edit-feature-btn').forEach((button) => {
    button.onclick = async () => {
      const subjectId = button.dataset.subjectId;
      const featureText = root.querySelector(`.feature-text[data-subject-id="${subjectId}"]`);
      const currentDescription = featureText?.textContent || '';
      const newDescription = prompt('编辑特征描述：', currentDescription);
      if (newDescription !== null && newDescription !== currentDescription) {
        await updateSubjectFeature(projectId, subjectId, { feature_description: newDescription });
        await renderRendersPage(root, projectId);
      }
    };
  });

  root.querySelectorAll('.regenerate-subject-btn').forEach((button) => {
    button.onclick = async () => {
      if (button.disabled) return;
      const subjectId = button.dataset.subjectId;
      const subject = (data.subjects || []).find((item) => item.id === subjectId);
      const currentVersion = subject?.image_version || 1;
      const confirmed = confirm(`确定要重新生成主体图吗？\n\n当前版本：v${currentVersion}\n新版本：v${currentVersion + 1}`);
      if (!confirmed) return;
      await regenerateSubject(projectId, subjectId, { cascade_render: false });
      await renderRendersPage(root, projectId);
    };
  });

  root.querySelectorAll('.subject-versions-btn').forEach((button) => {
    button.onclick = async () => {
      const subjectId = button.dataset.subjectId;
      const result = await getSubjectVersions(projectId, subjectId);
      const versions = result.items || [];
      if (versions.length === 0) {
        alert('暂无历史版本');
        return;
      }
      const versionList = versions.map((v) => `v${v.version} - ${v.created_at || '未知时间'}`).join('\n');
      const targetVersion = prompt(`历史版本列表：\n${versionList}\n\n输入要回退的版本号：`);
      if (targetVersion) {
        const version = parseInt(targetVersion, 10);
        if (!isNaN(version)) {
          await rollbackSubjectVersion(projectId, subjectId, { target_version: version });
          await renderRendersPage(root, projectId);
        }
      }
    };
  });

  if (latestTasks.some((item) => item.status === 'running')) {
    rerenderRendersPageLater(root, projectId, 3000);
  }

  if (composeError) {
    sessionStorage.removeItem(composeErrorKey(projectId));
  }
}
