export interface Project {
  id: string
  name: string
  prompt: string
  status: string
  current_stage: string
  scene_count?: number
  storyboard_style?: string
  text_model?: string
  image_model?: string
  video_model?: string
  compose_enable_subtitles?: boolean
  compose_enable_bgm?: boolean
  compose_enable_voiceover?: boolean
  compose_enable_transitions?: boolean
  final_bgm_path?: string
}

export interface Scene {
  id: string
  version: number
  scene_summary: string
  scene_list: SceneItem[]
}

export interface SceneItem {
  title: string
  description: string
}

export interface Shot {
  id: string
  sequence: number
  duration: number
  shot_type: string
  camera_movement: string
  scene_time: string
  background: string
  description: string
  subtitle_text: string
  dubbing_text: string
  voiceover_text: string
  voiceover_tone: string
  action_direction: string
  sound_effects: string
  subject_refs: string[]
}

export interface Subject {
  id: string
  name: string
  image_path: string
  source_url?: string
  is_locked: boolean
  feature_description: string
  image_version: number
  generation_warning?: { message: string }
  variant_type?: string
  shot_id?: string
  profile?: string
}

export interface RenderTask {
  shot_id: string
  status: string
  render_path: string
  force_refresh: boolean
  error_message: string
  progress_message: string
  cache_hit: boolean
  sequence?: number
  last_polled_at?: string
}

export interface FinalVideo {
  version: number
  storage_path: string
  duration: string
  resolution: string
  bgm_source: string
  features: string[]
}

export interface Timeline {
  project: Project
  scene: Scene | null
  storyboard: Shot[]
  subjects: Subject[]
  render_tasks: RenderTask[]
}

export interface TextModel {
  id: string
  name: string
  provider_id: string
  provider_name: string
}

export interface ImageModel {
  id: string
  name: string
  provider_id: string
  provider_name: string
}

export interface VideoModel {
  id: string
  provider_id: string
  provider_name: string
  model_type: string
  name: string
  capabilities: string[]
  requires_first_frame: boolean
  max_duration: number
  default_resolution: string
  default_ratio: string
}

export interface VideoProvider {
  id: string
  name: string
  enabled: boolean
  models: VideoModel[]
}

export interface VideoModelsResponse {
  ok: boolean
  providers: VideoProvider[]
  models: VideoModel[]
  default_model: string
}

export interface ListResponse<T> {
  items: T[]
}

export interface ApiResponse<T> {
  ok?: boolean
  item: T
}
