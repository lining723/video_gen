import api from './http'

export const updateStoryboardSettings = (projectId: string, body: { storyboard_style: string }) =>
  api.put(`/projects/${projectId}/storyboard:settings`, body).then((r) => r.data)
export const generateStoryboard = (projectId: string) =>
  api.post(`/projects/${projectId}/storyboard:generate`).then((r) => r.data)
export const updateShot = (projectId: string, shotId: string, body: Record<string, any>) =>
  api.put(`/projects/${projectId}/storyboard/shots/${shotId}`, body).then((r) => r.data)
export const regenerateShot = (projectId: string, shotId: string) =>
  api.post(`/projects/${projectId}/storyboard/shots/${shotId}:regenerate`).then((r) => r.data)
export const reviewStoryboard = (projectId: string, body: { action: string; comment?: string }) =>
  api.post(`/projects/${projectId}/storyboard:review`, body).then((r) => r.data)
