import api from './http'
import type { ApiResponse, FinalVideo } from '@/types'

export const generateSubjects = (projectId: string) =>
  api.post(`/projects/${projectId}/subjects:generate`).then((r) => r.data)
export const generateShotSubject = (projectId: string, shotId: string, body: Record<string, string>) =>
  api.post(`/projects/${projectId}/subjects/shots/${shotId}:generate`, body).then((r) => r.data)
export const uploadShotSubject = (projectId: string, shotId: string, body: any) =>
  api.post(`/projects/${projectId}/subjects/shots/${shotId}:upload`, body).then((r) => r.data)
export const updateFinalVideoSettings = (projectId: string, body: Record<string, boolean>) =>
  api.put(`/projects/${projectId}/final-video:settings`, body).then((r) => r.data)
export const uploadFinalVideoBgm = (projectId: string, body: any) =>
  api.post(`/projects/${projectId}/final-video/bgm:upload`, body).then((r) => r.data)
export const clearFinalVideoBgm = (projectId: string) =>
  api.post(`/projects/${projectId}/final-video/bgm:clear`).then((r) => r.data)
export const startRenders = (projectId: string, body: { force?: boolean } = {}) =>
  api.post(`/projects/${projectId}/renders:start`, body).then((r) => r.data)
export const retryRender = (projectId: string, shotId: string, body: { force?: boolean } = {}) =>
  api.post(`/projects/${projectId}/renders/shots/${shotId}:retry`, body).then((r) => r.data)
export const getRenderStatus = (projectId: string, shotId: string) =>
  api.get(`/projects/${projectId}/renders/shots/${shotId}`).then((r) => r.data)
export const composeVideo = (projectId: string) =>
  api.post(`/projects/${projectId}/final-video:compose`).then((r) => r.data)
export const getFinalVideo = (projectId: string) =>
  api.get<ApiResponse<FinalVideo>>(`/projects/${projectId}/final-video`).then((r) => r.data)

// Subject operations
export const lockSubject = (projectId: string, subjectId: string) =>
  api.post(`/projects/${projectId}/subjects/${subjectId}:lock`).then((r) => r.data)
export const unlockSubject = (projectId: string, subjectId: string) =>
  api.post(`/projects/${projectId}/subjects/${subjectId}:unlock`).then((r) => r.data)
export const updateSubjectFeature = (projectId: string, subjectId: string, body: { feature_description: string }) =>
  api.put(`/projects/${projectId}/subjects/${subjectId}`, body).then((r) => r.data)
export const regenerateSubject = (projectId: string, subjectId: string, body: { cascade_render?: boolean } = {}) =>
  api.post(`/projects/${projectId}/subjects/${subjectId}:regenerate`, body).then((r) => r.data)
export const getSubjectVersions = (projectId: string, subjectId: string) =>
  api.get(`/projects/${projectId}/subjects/${subjectId}/versions`).then((r) => r.data)
export const rollbackSubjectVersion = (projectId: string, subjectId: string, body: { target_version: number }) =>
  api.post(`/projects/${projectId}/subjects/${subjectId}:rollback`, body).then((r) => r.data)
