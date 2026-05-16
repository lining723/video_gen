import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'dev-secret-key-change-me',
  },
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const payload = error.response?.data
    const msg = payload?.error || `Request failed with status ${error.response?.status}`
    const err = new Error(msg) as any
    err.status = error.response?.status
    err.payload = payload
    return Promise.reject(err)
  }
)

export default api

export function mediaUrl(path: string): string {
  return `/media/${encodeURIComponent(path)}`
}
