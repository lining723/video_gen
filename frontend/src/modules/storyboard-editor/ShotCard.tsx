import { escapeAttribute, escapeHtml } from '../../utils/html.ts';

function snippet(value, fallback = '暂无内容') {
  const text = String(value || '').trim();
  if (!text) return fallback;
  return text.length > 72 ? `${text.slice(0, 72)}...` : text;
}

export function shotListItem(shot) {
  return `
    <article class="surface strong shot-list-item" data-shot-id="${escapeAttribute(shot.id)}" draggable="true">
      <div class="shot-list-layout">
        <div class="drag-handle" aria-hidden="true">⋮⋮</div>
        <div class="shot-list-copy">
          <div class="shot-list-head">
            <div>
              <span class="shot-order">${escapeHtml(shot.sequence)}</span>
              <h4>镜头 ${escapeHtml(shot.sequence)}</h4>
            </div>
            <div class="pill-row">
              <span class="pill"><strong>类型</strong>${escapeHtml(shot.shot_type || '未填写')}</span>
              <span class="pill"><strong>运镜</strong>${escapeHtml(shot.camera_movement || '未填写')}</span>
              <span class="pill"><strong>时长</strong>${escapeHtml(shot.duration)}s</span>
            </div>
          </div>
          <div class="summary-grid shot-list-summary">
            <div class="meta-panel">
              <h4>场景</h4>
              <p>${escapeHtml(snippet(shot.background || shot.description))}</p>
            </div>
            <div class="meta-panel">
              <h4>字幕</h4>
              <p>${escapeHtml(snippet(shot.subtitle_text))}</p>
            </div>
            <div class="meta-panel">
              <h4>配音</h4>
              <p>${escapeHtml(snippet(shot.dubbing_text))}</p>
            </div>
          </div>
        </div>
        <div class="shot-list-actions">
          <button class="ghost" data-action="view-shot">查看详情</button>
          <button class="secondary" data-action="regenerate-shot">重新生成</button>
        </div>
      </div>
    </article>
  `;
}

export function shotDetailForm(shot) {
  return `
    <div class="shot-detail-form" data-shot-id="${escapeAttribute(shot.id)}">
      <div class="shot-head">
        <div>
          <span class="shot-order">${escapeHtml(shot.sequence)}</span>
          <h4>镜头 ${escapeHtml(shot.sequence)} 详情</h4>
          <p>在弹窗中直接编辑分镜信息，保存后立即写回当前版本。</p>
        </div>
        <div class="pill-row">
          <span class="pill"><strong>当前时间</strong>${escapeHtml(shot.scene_time || '未填写')}</span>
          <span class="pill"><strong>音色</strong>${escapeHtml(shot.voiceover_tone || '未填写')}</span>
        </div>
      </div>
      <div class="compact-grid shot-grid-top">
        <div class="field">
          <label>顺序</label>
          <input data-field="sequence" type="number" value="${escapeAttribute(shot.sequence)}" />
        </div>
        <div class="field">
          <label>时长</label>
          <input data-field="duration" type="number" value="${escapeAttribute(shot.duration)}" />
        </div>
        <div class="field">
          <label>镜头类型</label>
          <input data-field="shot_type" value="${escapeAttribute(shot.shot_type || '')}" placeholder="如：全景 / 中景 / 特写" />
        </div>
        <div class="field">
          <label>运镜方式</label>
          <input data-field="camera_movement" value="${escapeAttribute(shot.camera_movement || '')}" placeholder="如：推进 / 摇镜 / 跟拍" />
        </div>
      </div>
      <div class="stacked-fields" style="margin-top:14px;">
        <div class="compact-grid shot-grid-middle">
          <div class="field">
            <label>时间</label>
            <input data-field="scene_time" value="${escapeAttribute(shot.scene_time || '')}" placeholder="如：清晨 / 黄昏 / 深夜" />
          </div>
          <div class="field">
            <label>配音音色</label>
            <input data-field="voiceover_tone" value="${escapeAttribute(shot.voiceover_tone || '')}" placeholder="如：温暖女声 / 沉稳男声" />
          </div>
        </div>
        <div class="field">
          <label>背景</label>
          <textarea data-field="background" rows="3">${escapeHtml(shot.background || '')}</textarea>
        </div>
        <div class="field">
          <label>动作指导</label>
          <textarea data-field="action_direction" rows="3">${escapeHtml(shot.action_direction || '')}</textarea>
        </div>
        <div class="field">
          <label>音效</label>
          <textarea data-field="sound_effects" rows="3">${escapeHtml(shot.sound_effects || '')}</textarea>
        </div>
        <div class="field">
          <label>镜头描述</label>
          <textarea data-field="description" rows="3">${escapeHtml(shot.description || '')}</textarea>
        </div>
        <div class="field">
          <label>字幕</label>
          <textarea data-field="subtitle_text" rows="3">${escapeHtml(shot.subtitle_text || '')}</textarea>
        </div>
        <div class="field">
          <label>配音</label>
          <textarea data-field="dubbing_text" rows="3">${escapeHtml(shot.dubbing_text || '')}</textarea>
        </div>
        <div class="field">
          <label>旁白</label>
          <textarea data-field="voiceover_text" rows="3" placeholder="可选填写">${escapeHtml(shot.voiceover_text || '')}</textarea>
        </div>
      </div>
      <div class="action-row" style="margin-top:18px;">
        <button class="secondary" data-action="regenerate-shot">重新生成</button>
        <button data-action="save-shot">保存</button>
        <button class="ghost" data-action="close-shot-modal">关闭</button>
      </div>
    </div>
  `;
}
