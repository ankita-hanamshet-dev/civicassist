import React, { useState, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, disabled, t }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = ref.current.scrollHeight + 'px'
    }
  }, [value])

  const submit = () => {
    const q = value.trim()
    if (!q || disabled) return
    onSend(q)
    setValue('')
  }

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="chat-input-area">
      <div className="input-row">
        <textarea
          ref={ref}
          className="chat-textarea"
          placeholder={t.placeholder}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          disabled={disabled}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={submit}
          disabled={disabled || !value.trim()}
          title={t.sendTitle}
        >
          {disabled ? <span className="spinner" /> : '➤'}
        </button>
      </div>
      <p className="input-hint">{t.inputHint}</p>
    </div>
  )
}
