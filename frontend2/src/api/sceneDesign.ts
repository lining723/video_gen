import api from './http'

export const updateSceneSettings = (projectId: string, body: { scene_count: number }) =>
  api.put(`/projects/${projectId}/scene-design:settings`, body).then((r) => r.data)
export const generateScene = (projectId: string, body: { scene_count?: number } = {}) =>
  api.post(`/projects/${projectId}/scene-design:generate`, body).then((r) => r.data)
export const reviewScene = (projectId: string, body: { action: string; comment?: string }) =>
  api.post(`/projects/${projectId}/scene-design:review`, body).then((r) => r.data)
