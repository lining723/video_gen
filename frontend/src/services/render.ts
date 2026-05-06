import { request } from './http.ts';

export const generateSubjects = (projectId) => request(`/api/projects/${projectId}/subjects:generate`, { method: 'POST' });
export const generateShotSubject = (projectId, shotId, body) => request(`/api/projects/${projectId}/subjects/shots/${shotId}:generate`, { method: 'POST', body });
export const uploadShotSubject = (projectId, shotId, body) => request(`/api/projects/${projectId}/subjects/shots/${shotId}:upload`, { method: 'POST', body });
export const updateFinalVideoSettings = (projectId, body) => request(`/api/projects/${projectId}/final-video:settings`, { method: 'PUT', body });
export const uploadFinalVideoBgm = (projectId, body) => request(`/api/projects/${projectId}/final-video/bgm:upload`, { method: 'POST', body });
export const clearFinalVideoBgm = (projectId) => request(`/api/projects/${projectId}/final-video/bgm:clear`, { method: 'POST' });
export const startRenders = (projectId, body = {}) => request(`/api/projects/${projectId}/renders:start`, { method: 'POST', body });
export const retryRender = (projectId, shotId, body = {}) => request(`/api/projects/${projectId}/renders/shots/${shotId}:retry`, { method: 'POST', body });
export const getRenderStatus = (projectId, shotId) => request(`/api/projects/${projectId}/renders/shots/${shotId}`);
export const composeVideo = (projectId) => request(`/api/projects/${projectId}/final-video:compose`, { method: 'POST' });
export const getFinalVideo = (projectId) => request(`/api/projects/${projectId}/final-video`);

// Subject operations for consistency control
export const lockSubject = (projectId, subjectId) => request(`/api/projects/${projectId}/subjects/${subjectId}:lock`, { method: 'POST' });
export const unlockSubject = (projectId, subjectId) => request(`/api/projects/${projectId}/subjects/${subjectId}:unlock`, { method: 'POST' });
export const updateSubjectFeature = (projectId, subjectId, body) => request(`/api/projects/${projectId}/subjects/${subjectId}`, { method: 'PUT', body });
export const regenerateSubject = (projectId, subjectId, body = {}) => request(`/api/projects/${projectId}/subjects/${subjectId}:regenerate`, { method: 'POST', body });
export const getSubjectVersions = (projectId, subjectId) => request(`/api/projects/${projectId}/subjects/${subjectId}/versions`);
export const rollbackSubjectVersion = (projectId, subjectId, body) => request(`/api/projects/${projectId}/subjects/${subjectId}:rollback`, { method: 'POST', body });
