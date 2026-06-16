import React from 'react'
import { starters } from '../i18n'

export default function WelcomeScreen({ onStart, t, language }) {
  const items = starters[language]

  return (
    <div className="welcome-screen">
      <div className="welcome-icon">⚖️</div>
      <h2 className="welcome-title">{t.welcomeTitle}</h2>
      <p className="welcome-sub">
        {t.welcomeSubtitle}
      </p>
      <div className="welcome-cards">
        {items.map((s, i) => (
          <div key={i} className="welcome-card" onClick={() => onStart(s.q)}>
            <div className="welcome-card-icon">{s.icon}</div>
            <div className="welcome-card-title">{s.title}</div>
            <div className="welcome-card-desc">{s.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
