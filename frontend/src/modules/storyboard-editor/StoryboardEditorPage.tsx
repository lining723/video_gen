import { escapeAttribute, escapeHtml } from '../../utils/html.ts';
import { shotDetailForm, shotListItem } from './ShotCard.tsx';

const STYLE_PRESETS = [
  '电影感写实',
  '高级广告片',
  '温暖生活方式',
  '未来科技感',
  '纪录片纪实',
  '国潮质感',
];

export function storyboardEditorContent(project, shots) {
  const currentStyle = project?.storyboard_style || '';
  const presetButtons = STYLE_PRESETS.map((style) => (
    `<button class="ghost storyboard-style-preset" data-style-preset="${escapeAttribute(style)}">${escapeHtml(style)}</button>`
  )).join('');

  if (!shots || shots.length === 0) {
    return `
      <section class="surface strong">
        <div class="section-head">
          <div>
            <h3>统一镜头风格</h3>
            <p>先确定整支片子的风格，再生成分镜。后续单镜头重生和开始渲染也会沿用这里的统一风格。</p>
          </div>
          <div class="pill-row">
            <span class="pill"><strong>当前风格</strong>${escapeHtml(currentStyle || '未设置')}</span>
          </div>
        </div>
        <div id="storyboard-feedback" hidden></div>
        <div class="storyboard-style-panel">
          <div class="field">
            <label>分镜统一风格</label>
            <input id="storyboard-style-input" value="${escapeAttribute(currentStyle)}" placeholder="如：电影感写实、高级广告片、未来科技感" />
          </div>
          <div class="action-row">
            ${presetButtons}
            <button id="save-storyboard-style" class="secondary">一键设置风格</button>
          </div>
          <p class="muted">设置完成后，再生成分镜，所有镜头会按同一风格输出。</p>
        </div>
      </section>
      <section class="surface strong">
        <div class="empty-state">
          <h3>还没有分镜</h3>
          <p>场景审核通过后，再生成镜头级内容。这里会按镜头顺序展开所有可编辑字段。</p>
          <button id="generate-storyboard">生成分镜</button>
        </div>
      </section>
    `;
  }
  return `
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>分镜审核</h3>
          <p>列表模式更适合审核和排序，详细编辑收进弹窗处理，避免页面被长表单淹没。</p>
        </div>
        <div class="pill-row">
          <span class="pill"><strong>镜头数</strong>${shots.length}</span>
          <span class="pill"><strong>交互</strong>拖拽排序 + 弹窗编辑</span>
          <span class="pill"><strong>统一风格</strong>${escapeHtml(currentStyle || '未设置')}</span>
        </div>
      </div>
      <div id="storyboard-feedback" hidden></div>
      <div class="storyboard-style-panel">
        <div class="field">
          <label>分镜统一风格</label>
          <input id="storyboard-style-input" value="${escapeAttribute(currentStyle)}" placeholder="如：电影感写实、高级广告片、未来科技感" />
        </div>
        <div class="action-row">
          ${presetButtons}
          <button id="save-storyboard-style" class="secondary">一键设置风格</button>
        </div>
        <p class="muted">新生成的分镜、单镜头重新生成和后续渲染都会自动带上这条统一风格。</p>
      </div>
      <div class="action-row">
        <button id="approve-storyboard">通过分镜并开始渲染</button>
        <button id="reject-storyboard" class="warn">驳回分镜</button>
      </div>
    </section>
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>镜头列表</h3>
          <p>拖动列表可以直接调整顺序；每一项提供查看详情和重新生成两个快捷操作。</p>
        </div>
      </div>
      <div class="plain-list storyboard-review-list" data-shot-review-list>
        ${shots.map((shot) => shotListItem(shot)).join('')}
      </div>
    </section>
    <div class="modal-shell" id="shot-detail-modal" hidden>
      <div class="modal-backdrop" data-action="close-shot-modal"></div>
      <div class="modal-panel">
        <div class="section-head">
          <div>
            <h3>分镜详情</h3>
            <p>可在弹窗内直接编辑并重新生成当前镜头。</p>
          </div>
          <button class="ghost" data-action="close-shot-modal">关闭</button>
        </div>
        <div id="shot-detail-modal-body">${shotDetailForm(shots[0])}</div>
      </div>
    </div>
  `;
}
