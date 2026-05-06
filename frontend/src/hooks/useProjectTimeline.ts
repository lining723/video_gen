import { getTimeline } from '../services/projects.ts';

export async function fetchTimeline(projectId) {
  const result = await getTimeline(projectId);
  return result.item;
}
