import { request } from './http.ts';

export const updateStoryboardSettings = (projectId, body) => request(`/api/projects/${projectId}/storyboard:settings`, { method: 'PUT', body });
export const generateStoryboard = (projectId) => request(`/api/projects/${projectId}/storyboard:generate`, { method: 'POST' });
export const updateShot = (projectId, shotId, body) => request(`/api/projects/${projectId}/storyboard/shots/${shotId}`, { method: 'PUT', body });
export const regenerateShot = (projectId, shotId) => request(`/api/projects/${projectId}/storyboard/shots/${shotId}:regenerate`, { method: 'POST' });
export const reviewStoryboard = (projectId, body) => request(`/api/projects/${projectId}/storyboard:review`, { method: 'POST', body });
