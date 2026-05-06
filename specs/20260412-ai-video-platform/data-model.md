# Data Model: 智能视频生成平台

## 1. Project
- 主键：`id`
- 字段：`name`、`creator_id`、`status`、`current_stage`、`scene_design_version`、`storyboard_version`、`final_video_version`、`created_at`、`updated_at`
- 关系：1:N SceneDesign、1:N StoryboardShot、1:N SubjectAsset、1:N ShotRenderTask、1:N FinalVideo
- 规则：项目删除前必须清理关联任务与媒资引用

## 2. SceneDesign
- 主键：`id`
- 字段：`project_id`、`version`、`input_prompt`、`scene_summary`、`scene_payload`、`review_status`、`review_comment`、`created_at`
- 关系：N:1 Project
- 规则：仅 `scene_approved` 版本可进入分镜生成阶段

## 3. StoryboardShot
- 主键：`id`
- 字段：`project_id`、`version`、`sequence`、`duration`、`description`、`subtitle_text`、`voiceover_text`、`subject_refs`、`status`
- 关系：N:1 Project
- 规则：`duration` 不得超过配置上限；`subtitle_text` 与 `voiceover_text` 必填

## 4. SubjectAsset
- 主键：`id`
- 字段：`project_id`、`name`、`profile`、`image_path`、`image_version`、`created_at`
- 关系：N:1 Project；可被多个 StoryboardShot 引用
- 规则：相同主体需去重，生成统一版本参考图

## 5. ShotRenderTask
- 主键：`id`
- 字段：`project_id`、`shot_id`、`status`、`cache_key`、`cache_hit`、`render_path`、`retry_count`、`error_message`、`started_at`、`finished_at`
- 关系：N:1 Project；N:1 StoryboardShot
- 规则：失败重试不超过 3 次；缓存命中时跳过重复渲染

## 6. FinalVideo
- 主键：`id`
- 字段：`project_id`、`version`、`storage_path`、`duration`、`resolution`、`created_at`
- 关系：N:1 Project
- 规则：仅在全部必要镜头完成后允许创建最终成片记录

## 7. State Machines

### Project
`idea_submitted` → `scene_generated` → `scene_reviewing` → `scene_approved` → `storyboard_generated` → `storyboard_reviewing` → `storyboard_approved` → `subject_generating` → `subject_ready` → `video_rendering` → `compositing` → `completed`

异常分支：任一关键阶段可进入 `failed`；镜头局部失败时项目可进入 `video_render_partial_failed`。

### ShotRenderTask
`queued` → `running` → `succeeded`

异常分支：`running` → `failed` → `queued`（重试）
