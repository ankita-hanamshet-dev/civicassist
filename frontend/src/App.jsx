import React, { useState } from 'react'
import ChatPage from './pages/ChatPage'
import AdminPage from './pages/AdminPage'
import './styles/globals.css'
import { DEFAULT_LANGUAGE, translations, languageLabels } from './i18n'

export default function App() {
  const [page, setPage] = useState('chat')
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE)
  const t = translations[language]

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-flag">🇺🇾</span>
            <div>
              <h1 className="brand-name">UruguayLex</h1>
              <p className="brand-tagline">{t.tagline}</p>
            </div>
          </div>

          <div className="header-right">
            <nav className="header-nav">
              <button
                className={`nav-btn ${page === 'chat' ? 'active' : ''}`}
                onClick={() => setPage('chat')}
              >
                <span className="nav-icon">💬</span>
                {t.navChat}
              </button>
              <button
                className={`nav-btn ${page === 'admin' ? 'active' : ''}`}
                onClick={() => setPage('admin')}
              >
                <span className="nav-icon">⚙️</span>
                {t.navAdmin}
              </button>
            </nav>

            <div className="lang-select">
              <label htmlFor="language-select" className="visually-hidden">
                Language
              </label>
              <select
                id="language-select"
                value={language}
                onChange={e => setLanguage(e.target.value)}
              >
                {Object.entries(languageLabels).map(([code, label]) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        {page === 'chat' ? (
          <ChatPage t={t} language={language} />
        ) : (
          <AdminPage t={t} />
        )}
      </main>

      <footer className="app-footer">
        <p>{t.footer}</p>
      </footer>
    </div>
  )
}
