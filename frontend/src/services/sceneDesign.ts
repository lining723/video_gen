import { request } from './http.ts';

export const updateSceneSettings = (projectId, body) => request(`/api/projects/${projectId}/scene-design:settings`, { method: 'PUT', body });
export const generateScene = (projectId, body = {}) => request(`/api/projects/${projectId}/scene-design:generate`, { method: 'POST', body });
export const reviewScene = (projectId, body) => request(`/api/projects/${projectId}/scene-design:review`, { method: 'POST', body });
