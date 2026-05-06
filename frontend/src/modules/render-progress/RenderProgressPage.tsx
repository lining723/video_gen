import { renderMediaPreview } from '../media/MediaPreview.tsx';
import { escapeAttribute, escapeHtml } from '../../utils/html.ts';

function pickLatestBy(items, getKey) {
  const map = new Map();
  for (const item of items || []) {
    map.set(getKey(item), item);
  }
  return Array.from(map.values());
}

function renderStatusText(item) {
  if (item.progress_message) return item.progress_message;
  if (item.status === 'missing') return '未创建任务';
  if (item.status === 'running' && item.force_refresh) return '强制重生成中';
  if (item.status === 'running') return '渲染中';
  if (item.status === 'succeeded' && item.force_refresh) return '已替换旧产物';
  if (item.status === 'succeeded' && item.cache_hit) return '已完成（缓存命中）';
  if (item.status === 'succeeded') return '已完成';
  return item.status || '未知状态';
}

function buildComposeReadiness(data, latestTasks) {
  const blockers = [];

  for (const shot of data.storyboard || []) {
    const task = latestTasks.find((item) => item.shot_id === shot.id);
    if (!task) {
      blockers.push(`镜头 ${shot.sequence} 尚未创建渲染任务`);
      continue;
    }
    if (task.status !== 'succeeded') {
      blockers.push(`镜头 ${shot.sequence} 仍处于${renderStatusText(task)}`);
      continue;
    }
    if (!String(task.render_path || '').toLowerCase().endsWith('.mp4')) {
      blockers.push(`镜头 ${shot.sequence} 还没有可播放的视频产物`);
    }
  }

  return {
    ready: (data.storyboard || []).length > 0 && blockers.length === 0,
    blockers,
  };
}

function pickLatestShotSubjects(items) {
  const map = new Map();
  for (const item of items || []) {
    if (!item.shot_id) continue;
    map.set(item.shot_id, item);
  }
  return map;
}

function findFallbackSubject(shot, latestGlobalByName, latestGlobalSubjects) {
  for (const subjectName of shot.subject_refs || []) {
    const matched = latestGlobalByName.get(subjectName);
    if (matched) return matched;
  }
  return latestGlobalSubjects[0] || null;
}

export function renderProgressContent(data, options = {}) {
  const { composeError = '', manualProgressByShotId = {} } = options;
  const sequenceByShotId = Object.fromEntries((data.storyboard || []).map((item) => [item.id, item.sequence]));
  const orderedShots = [...(data.storyboard || [])].sort((a, b) => Number(a.sequence || 0) - Number(b.sequence || 0));
  const latestGlobalSubjects = pickLatestBy((data.subjects || []).filter((item) => !item.shot_id), (item) => item.name);
  const latestGlobalByName = new Map(latestGlobalSubjects.map((item) => [item.name, item]));
  const latestShotSubjectsByShotId = pickLatestShotSubjects(data.subjects || []);
  const latestTasks = pickLatestBy(data.render_tasks || [], (item) => item.shot_id);
  const latestTaskByShotId = Object.fromEntries(
    latestTasks.map((item, index) => [item.shot_id, { ...item, sequence: sequenceByShotId[item.shot_id] || item.sequence || index + 1 }])
  );
  const composeReadiness = buildComposeReadiness(data, latestTasks);
  const composeSettings = {
    subtitles: !!data.project.compose_enable_subtitles,
    bgm: !!data.project.compose_enable_bgm,
    voiceover: !!data.project.compose_enable_voiceover,
    transitions: !!data.project.compose_enable_transitions,
    bgmPath: data.project.final_bgm_path || '',
  };

  const subjectCards = orderedShots.map((shot, index) => {
    const previousShot = index > 0 ? orderedShots[index - 1] : null;
    const previousTask = previousShot ? latestTaskByShotId[previousShot.id] : null;
    const canUsePreviousFrame = !!(
      previousShot &&
      previousTask &&
      previousTask.status === 'succeeded' &&
      String(previousTask.render_path || '').toLowerCase().endsWith('.mp4')
    );
    const uploadedAsset = latestShotSubjectsByShotId.get(shot.id) || null;
    const fallbackAsset = findFallbackSubject(shot, latestGlobalByName, latestGlobalSubjects);
    const activeAsset = uploadedAsset || fallbackAsset;
    const assetLabel = uploadedAsset
      ? (uploadedAsset.profile || '镜头主体图')
      : fallbackAsset
        ? '全局主体图'
        : '暂无图片';
    const subjectRefs = (shot.subject_refs || []).join('、') || '主角';
    const title = `镜头 ${shot.sequence}`;

    return `
      <article class="meta-panel subject-shot-card">
        <div class="subject-head">
          <div>
            <h4>${escapeHtml(title)}</h4>
            <p>关联主体：${escapeHtml(subjectRefs)}</p>
          </div>
          <span class="pill status-pill ${uploadedAsset ? 'success' : ''}">
            ${escapeHtml(assetLabel)}
          </span>
        </div>
        <div class="action-row" style="margin-top:12px;">
          <button class="generate-shot-subject secondary" data-shot-id="${escapeAttribute(shot.id)}">直接生成</button>
          <button class="generate-variant-btn secondary" data-shot-id="${escapeAttribute(shot.id)}" ${fallbackAsset ? '' : 'disabled'}>生成变体</button>
          <button class="derive-shot-subject ghost" data-shot-id="${escapeAttribute(shot.id)}" ${canUsePreviousFrame ? '' : 'disabled'}>
            使用上一镜头尾帧
          </button>
          <button class="upload-shot-subject secondary" data-shot-id="${escapeAttribute(shot.id)}">上传图片</button>
          <input class="shot-subject-input" type="file" accept="image/*" data-shot-id="${escapeAttribute(shot.id)}" hidden />
        </div>
        ${previousShot
          ? canUsePreviousFrame
            ? `<div class="notice info subject-upload-note">可直接沿用镜头 ${escapeHtml(previousShot.sequence)} 的尾帧生成主体图。</div>`
            : `<div class="notice info subject-upload-note">镜头 ${escapeHtml(previousShot.sequence)} 需要先产出可播放视频，才能复用尾帧。</div>`
          : '<div class="notice info subject-upload-note">首个镜头没有上一镜头尾帧，可直接生成或上传图片。</div>'}
        ${uploadedAsset
          ? '<div class="notice info subject-upload-note">该镜头已绑定独立主体图，渲染时会优先使用这张图片。</div>'
          : fallbackAsset
            ? '<div class="notice info subject-upload-note">当前未上传镜头专属图片，渲染时会继续使用全局主体图。</div>'
            : '<div class="notice warn subject-upload-note">当前没有可用主体图，请先生成主体图或为该镜头上传图片。</div>'}
        ${activeAsset ? renderMediaPreview(activeAsset.image_path, `${title} 主体图`, activeAsset.source_url || '') : '<div class="muted">暂无可预览文件</div>'}
      </article>
    `;
  }).join('') || '<div class="muted">暂无镜头，暂时无法上传主体图片。</div>';

  const globalSubjectLibrary = latestGlobalSubjects.map((item) => {
    const isLocked = !!item.is_locked;
    const featureDescription = item.feature_description || '';
    const imageVersion = item.image_version || 1;
    return `
    <li class="subject-item" data-subject-id="${escapeAttribute(item.id)}">
      <div class="subject-head">
        <div>
          <h4>${escapeHtml(item.name)} <span class="version-badge">v${imageVersion}</span></h4>
          <p>${escapeHtml(item.image_path || '暂无路径')}</p>
        </div>
        <div class="subject-badges">
          ${isLocked ? '<span class="pill status-pill">已锁定</span>' : ''}
          ${item.generation_warning ? '<span class="pill status-pill warn">生成告警</span>' : ''}
          ${item.variant_type === 'variant' ? '<span class="pill status-pill info">变体</span>' : ''}
        </div>
      </div>
      ${featureDescription ? `
        <div class="feature-description-section" style="margin-top:12px;">
          <div class="feature-header">
            <strong>特征描述</strong>
            ${!isLocked ? `<button class="edit-feature-btn ghost" data-subject-id="${escapeAttribute(item.id)}">编辑</button>` : ''}
          </div>
          <p class="feature-text ${isLocked ? 'locked' : ''}">${escapeHtml(featureDescription)}</p>
        </div>
      ` : ''}
      <div class="action-row" style="margin-top:12px;">
        ${!isLocked ? `<button class="lock-subject-btn secondary" data-subject-id="${escapeAttribute(item.id)}">锁定特征</button>` : `<button class="unlock-subject-btn ghost" data-subject-id="${escapeAttribute(item.id)}">解锁</button>`}
        <button class="regenerate-subject-btn secondary" data-subject-id="${escapeAttribute(item.id)}" ${isLocked ? '' : 'disabled'}>重新生成</button>
        <button class="subject-versions-btn ghost" data-subject-id="${escapeAttribute(item.id)}">历史版本</button>
      </div>
      ${item.generation_warning ? `<div class="notice warn" style="margin-top:12px;">${escapeHtml(item.generation_warning.message || '模型已回退')}</div>` : ''}
      ${renderMediaPreview(item.image_path, `${item.name} 主体图`, item.source_url || '')}
    </li>
  `}).join('') || '<li>暂无全局主体图</li>';

  const orderedTaskItems = (data.storyboard || []).length
    ? (data.storyboard || []).map((shot) => latestTaskByShotId[shot.id] || {
      shot_id: shot.id,
      sequence: shot.sequence,
      status: 'missing',
      render_path: '',
      force_refresh: false,
      error_message: '',
    })
    : latestTasks;

  const tasks = orderedTaskItems.map((item, index) => {
    const sequence = item.sequence || sequenceByShotId[item.shot_id] || index + 1;
    const manualProgress = manualProgressByShotId[item.shot_id];
    return `
      <li class="task-item">
        <div class="task-head">
          <div>
            <h4>镜头 ${escapeHtml(sequence)}</h4>
            <p>${escapeHtml(item.render_path || '尚未产出渲染文件')}</p>
          </div>
          <span class="pill status-pill ${item.status === 'succeeded' ? 'success' : item.status === 'failed' ? 'warn' : ''}">
            ${escapeHtml(renderStatusText(item))}
          </span>
        </div>
        <div class="action-row" style="margin-top:12px;">
          <button class="query-render-status ghost" data-shot-id="${escapeAttribute(item.shot_id)}">查询进度</button>
          <button class="retry-render secondary" data-shot-id="${escapeAttribute(item.shot_id)}">重新生成</button>
          <button class="retry-render-force" data-shot-id="${escapeAttribute(item.shot_id)}">跳过缓存重渲染</button>
        </div>
        ${manualProgress ? `<div class="notice info" style="margin-top:12px;">${escapeHtml(manualProgress)}</div>` : ''}
        ${item.last_polled_at ? `<div class="notice info" style="margin-top:12px;">最近查询时间：${escapeHtml(item.last_polled_at)}</div>` : ''}
        ${item.force_refresh ? '<div class="notice info" style="margin-top:12px;">本次任务已启用跳过缓存。</div>' : ''}
        ${item.error_message ? `<div class="notice warn" style="margin-top:12px;"><pre>渲染诊断：${escapeHtml(item.error_message)}</pre></div>` : ''}
        ${item.render_path ? renderMediaPreview(item.render_path, `镜头 ${sequence} 预览`) : ''}
      </li>
    `;
  }).join('') || '<li>暂无渲染任务</li>';

  const succeeded = latestTasks.filter((item) => item.status === 'succeeded').length;
  const running = latestTasks.filter((item) => item.status === 'running').length;
  const uploadedShots = Array.from(latestShotSubjectsByShotId.keys()).length;

  return `
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>渲染控制台</h3>
          <p>把高频动作放在一处，减少在资产列表和任务列表之间来回找按钮。</p>
        </div>
      </div>
      ${composeError ? `<div class="notice warn" style="margin-bottom:16px;">${escapeHtml(composeError)}</div>` : ''}
      ${!composeReadiness.ready ? `<div class="notice info" style="margin-bottom:16px;">${escapeHtml(`当前还不能合成成片：${composeReadiness.blockers.join('；')}`)}</div>` : ''}
      <div class="action-row">
        <button id="generate-subjects" class="secondary">生成主体图</button>
        <button id="start-renders">开始渲染</button>
        <button id="start-renders-force" class="warn">全部跳过缓存重渲染</button>
        <button id="compose-video" class="ghost" ${composeReadiness.ready ? '' : 'disabled'}>合成成片</button>
      </div>
      <div class="compose-settings-panel">
        <div class="section-head">
          <div>
            <h3>成片设置</h3>
            <p>这些设置会保存到项目里，后续再次合成会沿用当前配置。</p>
          </div>
        </div>
        <div class="compose-toggle-grid">
          <label class="checkbox-card">
            <input type="checkbox" class="compose-setting-toggle" data-setting="compose_enable_subtitles" ${composeSettings.subtitles ? 'checked' : ''} />
            <span>字幕烧录</span>
          </label>
          <label class="checkbox-card">
            <input type="checkbox" class="compose-setting-toggle" data-setting="compose_enable_voiceover" ${composeSettings.voiceover ? 'checked' : ''} />
            <span>旁白音轨</span>
          </label>
          <label class="checkbox-card">
            <input type="checkbox" class="compose-setting-toggle" data-setting="compose_enable_bgm" ${composeSettings.bgm ? 'checked' : ''} />
            <span>背景音乐</span>
          </label>
          <label class="checkbox-card">
            <input type="checkbox" class="compose-setting-toggle" data-setting="compose_enable_transitions" ${composeSettings.transitions ? 'checked' : ''} />
            <span>简单转场</span>
          </label>
        </div>
        <div class="compose-bgm-row">
          <div>
            <strong>自定义 BGM</strong>
            <p>${escapeHtml(composeSettings.bgmPath || '当前未上传，默认使用系统内置音乐床')}</p>
          </div>
          <div class="action-row">
            <button class="secondary" id="upload-final-bgm">上传 BGM</button>
            <button class="ghost" id="clear-final-bgm" ${composeSettings.bgmPath ? '' : 'disabled'}>清除 BGM</button>
            <input id="final-bgm-input" type="file" accept="audio/*" hidden />
          </div>
        </div>
      </div>
      <div class="stats-grid" style="margin-top:18px;">
        <div class="stat-block">
          <strong>${uploadedShots}</strong>
          <span>镜头已上传图片</span>
        </div>
        <div class="stat-block">
          <strong>${latestGlobalSubjects.length}</strong>
          <span>全局主体资产</span>
        </div>
        <div class="stat-block">
          <strong>${latestTasks.length}</strong>
          <span>最新渲染任务</span>
        </div>
        <div class="stat-block">
          <strong>${running}</strong>
          <span>渲染中</span>
        </div>
        <div class="stat-block">
          <strong>${succeeded}</strong>
          <span>已完成</span>
        </div>
      </div>
    </section>
    <section class="two-column">
      <div class="surface">
        <div class="section-head">
          <div>
            <h3>主体资产</h3>
            <p>每个镜头都能上传自己的主体图；未上传时，渲染会继续沿用全局主体资产。</p>
          </div>
        </div>
        <div class="grid-list subject-shot-grid">${subjectCards}</div>
        <div class="subject-library">
          <div class="section-head">
            <div>
              <h3>全局主体库</h3>
              <p>这里保留自动生成的主体图，未上传镜头专属图片时会作为默认首帧来源。</p>
            </div>
          </div>
          <ul class="plain-list">${globalSubjectLibrary}</ul>
        </div>
      </div>
      <div class="surface">
        <div class="section-head">
          <div>
            <h3>渲染任务</h3>
            <p>每个镜头只保留最新状态，重试与预览直接贴近结果。</p>
          </div>
        </div>
        <ul class="plain-list">${tasks}</ul>
      </div>
    </section>
  `;
}
