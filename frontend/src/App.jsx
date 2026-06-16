import React, { useState, useEffect } from 'react'
import ChatPage from './pages/ChatPage'
import AdminPage from './pages/AdminPage'
import LoginPage from './pages/LoginPage'
import './styles/globals.css'
import { DEFAULT_LANGUAGE, translations, languageLabels } from './i18n'

export default function App() {
  const [page, setPage] = useState('chat')
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE)
  const [authToken, setAuthToken] = useState(null)
  const t = translations[language]

  useEffect(() => {
    const savedToken = window.localStorage.getItem('adminAuthToken')
    if (savedToken) {
      setAuthToken(savedToken)
    }
  }, [])

  const handleLogin = token => {
    window.localStorage.setItem('adminAuthToken', token)
    setAuthToken(token)
    setPage('admin')
  }

  const handleLogout = () => {
    window.localStorage.removeItem('adminAuthToken')
    setAuthToken(null)
    setPage('chat')
  }

  const showAdmin = page === 'admin' && authToken
  const showLogin = page === 'login' || (page === 'admin' && !authToken)

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-flag">🇺🇾</span>
            <div>
              <h1 className="brand-name">CivicAssist</h1>
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
                onClick={() => setPage(authToken ? 'admin' : 'login')}
              >
                <span className="nav-icon">⚙️</span>
                {t.navAdmin}
              </button>
            </nav>

            {authToken && (
              <button className="nav-btn logout-btn" onClick={handleLogout}>
                🔓 {t.logout}
              </button>
            )}

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
        {showAdmin ? (
          <AdminPage t={t} />
        ) : showLogin ? (
          <LoginPage t={t} onLogin={handleLogin} />
        ) : (
          <ChatPage t={t} language={language} />
        )}
      </main>

      <footer className="app-footer">
        <p>{t.footer}</p>
      </footer>
    </div>
  )
}
