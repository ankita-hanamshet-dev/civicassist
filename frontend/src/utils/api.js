const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const PREFIX = import.meta.env.VITE_API_PREFIX || '/api/v1'

const getAdminAuthHeaders = () => {
  const authToken = window.localStorage.getItem('adminAuthToken')
  return authToken ? { Authorization: `Basic ${authToken}` } : {}
}

const api = async (path, options = {}) => {
  const url = `${BASE_URL}${PREFIX}${path}`
  const { headers: extraHeaders, ...rest } = options
  const res = await fetch(url, {
    ...rest,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  return res.json()
}

export const sendChat = (question, conversation_history = [], session_id = null, language = null) =>
  api('/chat', {
    method: 'POST',
    body: JSON.stringify({ question, conversation_history, session_id, language }),
  })

export const loginAdmin = (username, password) =>
  api('/admin/auth', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })

export const triggerIngest = () =>
  api('/admin/ingest', { method: 'POST', headers: getAdminAuthHeaders() })

export const getStats = () =>
  api('/admin/stats', { headers: getAdminAuthHeaders() })

export const getConfig = () =>
  api('/admin/config', { headers: getAdminAuthHeaders() })

export const reindex = () =>
  api('/admin/reindex', { method: 'POST', headers: getAdminAuthHeaders() })

export const updateLlmConfig = (llmData) =>
  api('/admin/config/llm', {
    method: 'PUT',
    headers: getAdminAuthHeaders(),
    body: JSON.stringify(llmData),
  })

export const updatePathsConfig = (pathsData) =>
  api('/admin/config/paths', {
    method: 'PUT',
    headers: getAdminAuthHeaders(),
    body: JSON.stringify(pathsData),
  })
