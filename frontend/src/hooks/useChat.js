import { useState, useCallback, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { sendChat } from '../utils/api'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const sessionId = useRef(uuidv4())

  const addMessage = (role, content, meta = {}) => {
    setMessages(prev => [...prev, { id: uuidv4(), role, content, meta, ts: Date.now() }])
  }

  const ask = useCallback(async (question) => {
    if (!question.trim()) return
    setError(null)
    addMessage('user', question)
    setLoading(true)

    // Build history for API (last 6 messages)
    const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }))

    try {
      const result = await sendChat(question, history, sessionId.current)
      addMessage('assistant', result.answer, {
        category: result.category,
        subcategory: result.subcategory,
        language: result.language,
        sources: result.sources,
        chunks_used: result.chunks_used,
      })
    } catch (e) {
      setError(e.message)
      addMessage('assistant', `❌ Error: ${e.message}`, { isError: true })
    } finally {
      setLoading(false)
    }
  }, [messages])

  const clear = useCallback(() => {
    setMessages([])
    setError(null)
    sessionId.current = uuidv4()
  }, [])

  return { messages, loading, error, ask, clear }
}
