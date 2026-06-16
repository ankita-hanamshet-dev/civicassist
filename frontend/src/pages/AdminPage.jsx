import React, { useState, useEffect } from 'react'
import { triggerIngest, getStats, reindex } from '../utils/api'

export default function AdminPage({ t }) {
  const [stats, setStats] = useState(null)
  const [ingestResult, setIngestResult] = useState(null)
  const [reindexResult, setReindexResult] = useState(null)
  const [loading, setLoading] = useState({ stats: false, ingest: false, reindex: false })
  const [errors, setErrors] = useState({})

  const fetchStats = async () => {
    setLoading(p => ({ ...p, stats: true }))
    try {
      const s = await getStats()
      setStats(s)
      setErrors(p => ({ ...p, stats: null }))
    } catch (e) {
      setErrors(p => ({ ...p, stats: e.message }))
    } finally {
      setLoading(p => ({ ...p, stats: false }))
    }
  }

  useEffect(() => { fetchStats() }, [])

  const handleIngest = async () => {
    setLoading(p => ({ ...p, ingest: true }))
    setIngestResult(null)
    try {
      const r = await triggerIngest()
      setIngestResult({ ok: true, data: r })
      fetchStats()
    } catch (e) {
      setIngestResult({ ok: false, message: e.message })
    } finally {
      setLoading(p => ({ ...p, ingest: false }))
    }
  }

  const handleReindex = async () => {
    setLoading(p => ({ ...p, reindex: true }))
    setReindexResult(null)
    try {
      const r = await reindex()
      setReindexResult({ ok: true, data: r })
      fetchStats()
    } catch (e) {
      setReindexResult({ ok: false, message: e.message })
    } finally {
      setLoading(p => ({ ...p, reindex: false }))
    }
  }

  return (
    <div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', color: 'var(--navy)', marginBottom: 20 }}>
        ⚙️ {t.adminTitle}
      </h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: '0.9rem' }}>
        {t.adminSubtitle}
      </p>

      <div className="admin-grid">

        {/* Stats card */}
        <div className="admin-card">
          <h2>📊 {t.systemStatus}</h2>
          <p>{t.vectorStats}</p>

          {loading.stats ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{t.loading}</div>
          ) : errors.stats ? (
            <div className="status-banner error">❌ {errors.stats}</div>
          ) : stats ? (
            <div>
              <div className="stat-row">
                <span className="stat-label">Colección</span>
                <span className="stat-value">{stats.collection_name}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Chunks indexados</span>
                <span className="stat-value">{stats.total_chunks.toLocaleString()}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Estado</span>
                <span className="stat-value" style={{ color: 'var(--success)' }}>✅ {stats.status}</span>
              </div>
            </div>
          ) : null}

          <button className="btn-secondary" onClick={fetchStats} style={{ marginTop: 14 }}>
            {loading.stats ? <span className="spinner" style={{ borderTopColor: 'var(--navy)' }} /> : '🔄'} {t.refresh}
          </button>
        </div>

        {/* Ingest card */}
        <div className="admin-card">
          <h2>📥 {t.fullIngest}</h2>
          <p>{t.fullIngestDesc}</p>
          <button className="btn-primary" onClick={handleIngest} disabled={loading.ingest}>
            {loading.ingest ? <span className="spinner" /> : '▶️'} {t.startIngest}
          </button>

          {ingestResult && (
            <div className={`status-banner ${ingestResult.ok ? 'success' : 'error'}`}>
              {ingestResult.ok ? (
                <>
                  ✅ {t.loading}<br />
                  📄 PDFs: {ingestResult.data.pdf_documents}<br />
                  🌐 Páginas web: {ingestResult.data.web_pages}<br />
                  🔢 Chunks embebidos: {ingestResult.data.total_chunks_embedded}
                </>
              ) : (
                `❌ ${ingestResult.message}`
              )}
            </div>
          )}
        </div>

        {/* Reindex card */}
        <div className="admin-card">
          <h2>🔄 {t.reindex}</h2>
          <p>{t.reindexDesc}</p>
          <button className="btn-secondary" onClick={handleReindex} disabled={loading.reindex}>
            {loading.reindex ? <span className="spinner" style={{ borderTopColor: 'var(--navy)' }} /> : '⚡'} {t.reindexAction}
          </button>

          {reindexResult && (
            <div className={`status-banner ${reindexResult.ok ? 'success' : 'error'}`}>
              {reindexResult.ok
                ? `✅ Re-indexado. Chunks: ${reindexResult.data.chunks}`
                : `❌ ${reindexResult.message}`}
            </div>
          )}
        </div>

        {/* Info card */}
        <div className="admin-card">
          <h2>📁 {t.configuration}</h2>
          <p>{t.configurationDesc}</p>
          <div>
            <div className="stat-row">
              <span className="stat-label">{t.pdfSource}</span>
              <span className="stat-value" style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                C:\Users\abirs\…\raw_pdfs
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">{t.markdownOutput}</span>
              <span className="stat-value" style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                ./backend/data/markdown
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">{t.vectorStore}</span>
              <span className="stat-value" style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                ./backend/data/vectorstore
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">{t.llmModel}</span>
              <span className="stat-value">claude-sonnet-4-6</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
