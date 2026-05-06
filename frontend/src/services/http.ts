const config = window.APP_CONFIG || {};
const API_BASE = config.apiBase || 'http://127.0.0.1:8100';
const API_KEY = config.apiKey || '';

export async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload?.error || `Request failed with status ${response.status}`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

export function mediaUrl(path) {
  return `${API_BASE}/media/${encodeURIComponent(path)}`;
}
