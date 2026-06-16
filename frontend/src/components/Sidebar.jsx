import React from 'react'
import { categories, quickQuestions } from '../i18n'

export default function Sidebar({ onQuickQuestion, language, t }) {
  const items = categories[language]
  const questions = quickQuestions[language]

  return (
    <aside className="chat-sidebar">
      <div className="sidebar-card">
        <h3>{t.categories}</h3>
        <div>
          {items.map(c => (
            <span key={c.id} className={`category-pill ${c.id}`}>
              {c.icon} {c.label}
            </span>
          ))}
        </div>
      </div>

      <div className="sidebar-card">
        <h3>{t.quickQuestions}</h3>
        <ul className="quick-questions">
          {questions.map((q, i) => (
            <li key={i}>
              <button
                className="quick-q-btn"
                onClick={() => onQuickQuestion(q.text)}
              >
                {q.text}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="sidebar-card">
        <h3>{t.officialResources}</h3>
        <ul style={{ listStyle: 'none', fontSize: '0.82rem', lineHeight: 2 }}>
          {t.resourceLinks.map((link, index) => (
            <li key={index}>
              <a href={link.href} target="_blank" rel="noreferrer">
                🔗 {link.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}
