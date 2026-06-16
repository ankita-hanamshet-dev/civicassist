import React from 'react'
import ReactMarkdown from 'react-markdown'

const LANG_LABEL = { es: '🇺🇾 ES', en: '🇬🇧 EN' }

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function Message({ message }) {
  const { role, content, meta = {}, ts } = message
  const isUser = role === 'user'

  return (
    <div className={`message-row ${role}`}>
      <div className={`avatar ${role}`}>
        {isUser ? '👤' : '⚖️'}
      </div>
      <div>
        <div className={`bubble ${role} ${meta.isError ? 'error' : ''}`}>
          {isUser ? (
            <span>{content}</span>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}

          {/* Metadata tags for assistant messages */}
          {!isUser && !meta.isError && (meta.category || meta.subcategory) && (
            <div className="meta-tags">
              {meta.category && (
                <span className="meta-tag cat">📁 {meta.category}</span>
              )}
              {meta.subcategory && (
                <span className="meta-tag sub">🏷️ {meta.subcategory}</span>
              )}
              {meta.language && (
                <span className="meta-tag lang">{LANG_LABEL[meta.language] || meta.language}</span>
              )}
              {meta.sources && meta.sources.slice(0, 2).map((src, i) => (
                <span key={i} className="meta-tag src" title={src}>
                  📎 {src.length > 40 ? src.slice(0, 40) + '…' : src}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="timestamp">{formatTime(ts)}</div>
      </div>
    </div>
  )
}
