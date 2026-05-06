import { escapeAttribute, escapeHtml, preserveLineBreaks } from '../../utils/html.ts';
import { formatProjectLabel } from '../../utils/project.ts';

export function projectDashboardContent(data) {
  const project = data.project;
  const shotCount = (data.storyboard || []).length;
  const renderCount = (data.render_tasks || []).length;
  const subjectCount = (data.subjects || []).length;

  return `
    <section class="surface strong">
      <div class="section-head">
        <div>
          <h2 class="headline">${escapeHtml(project.name)}</h2>
          <p class="subheadline">${preserveLineBreaks(project.prompt || '暂无项目描述')}</p>
        </div>
        <div class="pill-row">
          <span class="pill status-pill"><strong>状态</strong>${escapeHtml(formatProjectLabel(project.status))}</span>
          <span class="pill"><strong>阶段</strong>${escapeHtml(formatProjectLabel(project.current_stage))}</span>
        </div>
      </div>
      <div class="summary-grid">
        <div class="stat-block">
          <strong>${data.scene ? `V${escapeHtml(data.scene.version)}` : '--'}</strong>
          <span>场景版本</span>
        </div>
        <div class="stat-block">
          <strong>${shotCount}</strong>
          <span>已生成镜头</span>
        </div>
        <div class="stat-block">
          <strong>${subjectCount}</strong>
          <span>主体资产</span>
        </div>
        <div class="stat-block">
          <strong>${renderCount}</strong>
          <span>渲染任务记录</span>
        </div>
      </div>
    </section>
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>模型设置</h3>
          <p>项目级分别配置文本、图片、视频模型。后续场景、分镜、主体图和渲染都会按这里的配置执行。</p>
        </div>
      </div>
      <div id="project-settings-feedback" hidden></div>
      <div class="compact-grid">
        <div class="field">
          <label for="project-text-model">文本模型</label>
          <select id="project-text-model">
            <option value="">使用默认模型</option>
          </select>
        </div>
        <div class="field">
          <label for="project-image-model">图片模型</label>
          <select id="project-image-model">
            <option value="">使用默认模型</option>
          </select>
        </div>
        <div class="field">
          <label for="project-video-model">视频模型</label>
          <select id="project-video-model">
            <option value="">使用默认模型</option>
          </select>
        </div>
      </div>
      <div class="action-row" style="margin-top:18px;">
        <button id="save-project-model-settings">保存模型设置</button>
      </div>
    </section>
    <section class="surface">
      <div class="section-head">
        <div>
          <h3>流程入口</h3>
          <p>把四个关键阶段放到一层，减少跳转认知成本。</p>
        </div>
      </div>
      <div class="two-column">
        <a class="surface strong" href="#/projects/${project.id}/scene">
          <h3>场景审核</h3>
          <p class="subheadline">确认画面结构、段落安排与整体叙事气质。</p>
        </a>
        <a class="surface strong" href="#/projects/${project.id}/storyboard">
          <h3>分镜编辑</h3>
          <p class="subheadline">逐条细化镜头描述、字幕和配音文案。</p>
        </a>
        <a class="surface strong" href="#/projects/${project.id}/renders">
          <h3>渲染控制</h3>
          <p class="subheadline">查看主体资产、发起渲染并处理缓存重试。</p>
        </a>
        <a class="surface strong" href="#/projects/${project.id}/final-video">
          <h3>最终成片</h3>
          <p class="subheadline">查看最终视频版本与下载入口。</p>
        </a>
      </div>
    </section>
  `;
}
