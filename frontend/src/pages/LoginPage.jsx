import React, { useState } from 'react'
import { loginAdmin } from '../utils/api'

export default function LoginPage({ t, onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async event => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      await loginAdmin(username, password)
      const authToken = btoa(`${username}:${password}`)
      onLogin(authToken)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-auth-card">
      <h1>{t.loginTitle}</h1>
      <p>{t.loginSubtitle}</p>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          {t.usernameLabel}
          <input
            type="text"
            value={username}
            onChange={event => setUsername(event.target.value)}
            placeholder={t.usernameLabel}
            autoComplete="username"
            required
          />
        </label>

        <label>
          {t.passwordLabel}
          <input
            type="password"
            value={password}
            onChange={event => setPassword(event.target.value)}
            placeholder={t.passwordLabel}
            autoComplete="current-password"
            required
          />
        </label>

        {error && <div className="status-banner error">❌ {error}</div>}

        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? '🔒' : '🔑'} {t.loginAction}
        </button>
      </form>
    </div>
  )
}
