import api from './http'

export interface KeyframeFrame {
  position: number
  time_ratio: number
  image_url?: string
  thumbnail_url?: string
  status: string
  error_message?: string
}

export interface KeyframeGrid {
  grid_type: string
  frame_count: number
  frames: KeyframeFrame[]
}

export const getKeyframes = (projectId: string, shotId: string) =>
  api.get<KeyframeGrid>(`/projects/${projectId}/shots/${shotId}/keyframes`).then((r) => r.data)

export const getProjectKeyframesStatus = (projectId: string) =>
  api.get(`/projects/${projectId}/keyframes/status`).then((r) => r.data)

export const retryKeyframe = (projectId: string, shotId: string, position: number) =>
  api.post(`/projects/${projectId}/shots/${shotId}/keyframes/${position}/retry`).then((r) => r.data)

export const generateKeyframes = (projectId: string, shotId: string) =>
  api.post(`/projects/${projectId}/shots/${shotId}/keyframes:generate`).then((r) => r.data)

export interface CompositeGrid {
  grid_type: string
  frame_count: number
  image_url: string
}

export const generateCompositeGrid = (projectId: string, shotId: string) =>
  api.post<CompositeGrid>(`/projects/${projectId}/shots/${shotId}/keyframes:generate-composite`).then((r) => r.data)
