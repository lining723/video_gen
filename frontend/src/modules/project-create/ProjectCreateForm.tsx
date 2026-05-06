export function projectCreateForm() {
  return `
    <section class="surface strong">
      <div class="section-head">
        <div>
          <h2 class="headline">新建视频项目</h2>
          <p class="subheadline">先定义片名与创意指令，系统会从场景设计开始逐步推进后续流程。</p>
        </div>
      </div>
      <div class="stacked-fields">
        <div class="field">
          <label for="project-name">项目名称</label>
          <input id="project-name" placeholder="例如：新品发布视频" value="新品发布视频" />
          <div class="field-help">名称会出现在总览、阶段导航和成片页中。</div>
        </div>
        <div class="field">
          <label for="project-prompt">创意需求</label>
          <textarea id="project-prompt" rows="6" placeholder="输入创意需求">为一款智能耳机生成 30 秒宣传视频，突出降噪、通勤、轻量感。</textarea>
          <div class="field-help">建议直接写清楚产品、氛围、卖点和时长，这样前面的场景与后面的分镜更稳定。</div>
        </div>
        <div class="field">
          <label for="project-scene-count">场景数量</label>
          <input id="project-scene-count" type="number" min="1" max="12" value="3" />
          <div class="field-help">用于控制场景设计输出的段落数量，后续在场景页也可以继续调整。</div>
        </div>
        <div class="action-row">
          <button id="create-project">创建并进入场景审核</button>
        </div>
      </div>
    </section>
  `;
}
