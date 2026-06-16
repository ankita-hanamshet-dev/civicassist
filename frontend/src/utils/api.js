const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const PREFIX = import.meta.env.VITE_API_PREFIX || '/api/v1'

const api = async (path, options = {}) => {
  const url = `${BASE_URL}${PREFIX}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  return res.json()
}

export const sendChat = (question, conversation_history = [], session_id = null) =>
  api('/chat', {
    method: 'POST',
    body: JSON.stringify({ question, conversation_history, session_id }),
  })

export const triggerIngest = () =>
  api('/admin/ingest', { method: 'POST' })

export const getStats = () =>
  api('/admin/stats')

export const reindex = () =>
  api('/admin/reindex', { method: 'POST' })
