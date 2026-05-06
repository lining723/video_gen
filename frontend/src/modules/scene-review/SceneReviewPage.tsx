import { escapeAttribute, escapeHtml, preserveLineBreaks } from '../../utils/html.ts';

export function sceneReviewContent(project, scene) {
  const sceneCount = Math.max(1, Math.min(12, Number(project?.scene_count || (scene?.scene_list || []).length || 3)));
  const settingsPanel = `
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>场景数量</h3>
          <p>先确定这一版要拆成几段场景，重新生成时也会沿用这个数量。</p>
        </div>
        <div class="pill-row">
          <span class="pill"><strong>当前配置</strong>${sceneCount}</span>
        </div>
      </div>
      <div id="scene-settings-feedback" hidden></div>
      <div class="stacked-fields">
        <div class="field">
          <label for="scene-count-input">场景数量</label>
          <input id="scene-count-input" type="number" min="1" max="12" value="${escapeAttribute(sceneCount)}" />
          <div class="field-help">建议控制在 3-8 段，便于后续分镜与渲染节奏保持稳定。</div>
        </div>
        <div class="action-row">
          <button id="save-scene-count" class="secondary">保存数量</button>
        </div>
      </div>
    </section>
  `;

  if (!scene) {
    return `
      ${settingsPanel}
      <section class="surface strong">
        <div class="empty-state">
          <h3>还没有场景设计</h3>
          <p>先生成一版整体场景，页面会在这里按段落列出每个场景的标题、说明和审核操作。</p>
          <button id="generate-scene">生成场景设计</button>
        </div>
      </section>
    `;
  }
  const items = (scene.scene_list || []).map((item, index) => `
    <article class="scene-card">
      <h4>${escapeHtml(item.title || `场景 ${index + 1}`)}</h4>
      <p>${preserveLineBreaks(item.description || '暂无描述')}</p>
    </article>
  `).join('');
  return `
    ${settingsPanel}
    <section class="surface strong">
      <div class="section-head">
        <div>
          <h2 class="headline">场景设计 V${escapeHtml(scene.version)}</h2>
          <p class="subheadline">${preserveLineBreaks(scene.scene_summary || '暂无场景摘要')}</p>
        </div>
        <div class="pill-row">
          <span class="pill"><strong>场景数</strong>${(scene.scene_list || []).length}</span>
        </div>
      </div>
      <div class="scene-grid">${items}</div>
    </section>
    <section class="split-layout">
      <div class="surface">
        <div class="section-head">
          <div>
            <h3>审核意见</h3>
            <p>只保留一个输入区和三个关键动作，让审核流更干净。</p>
          </div>
        </div>
        <div class="stacked-fields">
          <div class="field">
            <label for="scene-comment">反馈备注</label>
            <textarea id="scene-comment" rows="4" placeholder="例如：第二段场景节奏偏慢，通勤场景需要更明确。"></textarea>
          </div>
          <div class="action-row">
            <button id="scene-approve">通过并进入分镜</button>
            <button id="scene-reject" class="warn">驳回</button>
            <button id="scene-regenerate" class="secondary">重新生成</button>
          </div>
        </div>
      </div>
      <div class="surface">
        <div class="section-head">
          <div>
            <h3>审核原则</h3>
            <p>这个侧栏只负责提醒决策标准，不参与编辑。</p>
          </div>
        </div>
        <ul class="mini-list content-stack muted">
          <li>确认每一段场景都对创意需求有回应。</li>
          <li>检查场景顺序是否有明显断裂或重复。</li>
          <li>通过后会直接进入分镜页，不建议在这里做过细文案修改。</li>
        </ul>
      </div>
    </section>
  `;
}
