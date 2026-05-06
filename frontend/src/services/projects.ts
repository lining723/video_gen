import { request } from './http.ts';

export const listProjects = () => request('/api/projects');
export const createProject = (body) => request('/api/projects', { method: 'POST', body });
export const getProject = (projectId) => request(`/api/projects/${projectId}`);
export const getTimeline = (projectId) => request(`/api/projects/${projectId}/timeline`);
export const updateProjectSettings = (projectId, body) => request(`/api/projects/${projectId}:settings`, { method: 'PUT', body });
