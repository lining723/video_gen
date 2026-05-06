import { mediaUrl } from '../../services/http.ts';
import { renderMediaPreview } from '../media/MediaPreview.tsx';
import { escapeHtml } from '../../utils/html.ts';

function featureLabel(key) {
  return {
    subtitles: '字幕烧录',
    background_music: '背景音乐',
    voiceover_mix: '旁白音轨',
    fade_transition: '简单转场',
  }[key] || key;
}

function bgmSourceLabel(source) {
  return {
    custom: '自定义 BGM',
    generated: '系统内置 BGM',
    disabled: '未启用 BGM',
  }[source || ''] || '未知来源';
}

export function finalVideoContent(item, options = {}) {
  const { pending = false } = options;
  if (!item && pending) {
    return `
      <section class="surface strong">
        <div class="empty-state">
          <h3>正在合成最终成片</h3>
          <p>成片页会自动刷新，当前会依次完成字幕烧录、旁白混入、背景音乐混音和简单转场，再输出最终视频。</p>
        </div>
      </section>
    `;
  }

  if (!item) {
    return `
      <section class="surface strong">
        <div class="empty-state">
          <h3>成片还没有生成</h3>
          <p>先在渲染控制页完成镜头渲染，再触发成片合成，这里会直接展示最终版本。</p>
        </div>
      </section>
    `;
  }
  const features = (item.features || []).map((feature) => `<span class="pill">${escapeHtml(featureLabel(feature))}</span>`).join('');
  return `
    <section class="surface strong video-stage">
      <div class="section-head">
        <div>
          <h2 class="headline">最终成片 V${escapeHtml(item.version)}</h2>
          <p class="subheadline">成片页现在会展示本次实际启用的合成功能，以及背景音乐的来源。</p>
        </div>
        <div class="pill-row">
          <span class="pill"><strong>时长</strong>${escapeHtml(item.duration)}s</span>
          <span class="pill"><strong>分辨率</strong>${escapeHtml(item.resolution || 'unknown')}</span>
          <span class="pill"><strong>BGM</strong>${escapeHtml(bgmSourceLabel(item.bgm_source))}</span>
        </div>
      </div>
      <div class="feature-summary">
        <strong>本次启用</strong>
        <div class="pill-row" style="margin-top:10px;">
          ${features || '<span class="pill">未启用额外处理</span>'}
        </div>
      </div>
      <div class="action-row" style="margin-bottom:14px;">
        <a class="button-link" href="${mediaUrl(item.storage_path)}" target="_blank" rel="noreferrer">下载 / 查看成片</a>
      </div>
      ${renderMediaPreview(item.storage_path, `最终成片 V${item.version}`)}
    </section>
  `;
}
