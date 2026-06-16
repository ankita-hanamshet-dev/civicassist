import React, { useEffect, useRef } from 'react'
import { useChat } from '../hooks/useChat'
import Message from '../components/Message'
import ChatInput from '../components/ChatInput'
import Sidebar from '../components/Sidebar'
import WelcomeScreen from '../components/WelcomeScreen'

export default function ChatPage({ t, language }) {
  const { messages, loading, ask, clear } = useChat()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="chat-layout">
      <Sidebar onQuickQuestion={ask} language={language} t={t} />

      <div className="chat-window-wrap">
        <div className="chat-toolbar">
          <span className="chat-toolbar-title">
            💬 {messages.length > 0
              ? `${Math.ceil(messages.length / 2)} ${t.consultations}`
              : t.newConversation}
          </span>
          {messages.length > 0 && (
            <button className="btn-clear" onClick={clear}>
              🗑️ {t.clear}
            </button>
          )}
        </div>

        <div className="messages-area">
          {messages.length === 0 ? (
            <WelcomeScreen onStart={ask} t={t} language={language} />
          ) : (
            messages.map(msg => <Message key={msg.id} message={msg} />)
          )}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar assistant">⚖️</div>
              <div className="typing-indicator">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <ChatInput onSend={ask} disabled={loading} t={t} />
      </div>
    </div>
  )
}
