import api from './http'
import type { ApiResponse, ListResponse, Project, Timeline } from '@/types'

export const listProjects = () => api.get<ListResponse<Project>>('/projects').then((r) => r.data)
export const createProject = (body: { name: string; prompt: string; scene_count: number }) =>
  api.post<ApiResponse<Project>>('/projects', body).then((r) => r.data)
export const getProject = (projectId: string) =>
  api.get<ApiResponse<Project>>(`/projects/${projectId}`).then((r) => r.data)
export const getTimeline = (projectId: string) =>
  api.get<ApiResponse<Timeline>>(`/projects/${projectId}/timeline`).then((r) => r.data)
export const updateProjectSettings = (projectId: string, body: Record<string, string>) =>
  api.put(`/projects/${projectId}:settings`, body).then((r) => r.data)
