import api from './http'
import type { TextModel, ImageModel, VideoModelsResponse } from '@/types'

export const listVideoModels = () =>
  api.get<VideoModelsResponse>('/models/video').then((r) => r.data)
export const listTextModels = () =>
  api.get<{ ok: boolean; models: TextModel[]; default_model: string }>('/models/text').then((r) => r.data)
export const listImageModels = () =>
  api.get<{ ok: boolean; models: ImageModel[]; default_model: string }>('/models/image').then((r) => r.data)
