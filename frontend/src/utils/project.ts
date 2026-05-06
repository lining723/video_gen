const PROJECT_LABELS = {
  draft: '草稿',
  created: '已创建',
  scene_design_pending: '待生成场景',
  scene_design_review: '场景待审核',
  scene_approved: '场景已通过',
  storyboard_pending: '待生成分镜',
  storyboard_review: '分镜待审核',
  storyboard_approved: '分镜已通过',
  render_pending: '待渲染',
  renders_running: '渲染中',
  video_rendering: '成片合成中',
  completed: '已完成',
  failed: '失败',
};

export function formatProjectLabel(value) {
  if (!value) return '未开始';
  return PROJECT_LABELS[value] || String(value).replace(/_/g, ' ');
}
