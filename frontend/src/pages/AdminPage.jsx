import React, { useState, useEffect } from 'react'
import { triggerIngest, getStats, getConfig, reindex, updateLlmConfig, updatePathsConfig } from '../utils/api'

export default function AdminPage({ t }) {
  const [stats, setStats] = useState(null)
  const [config, setConfig] = useState(null)
  const [ingestResult, setIngestResult] = useState(null)
  const [reindexResult, setReindexResult] = useState(null)
  const [loading, setLoading] = useState({ stats: false, ingest: false, reindex: false, config: false, configSave: false })
  const [errors, setErrors] = useState({})

  // Configuration card state
  const [configEditing, setConfigEditing] = useState(false)
  const [configForm, setConfigForm] = useState(null)
  const [configSaveResult, setConfigSaveResult] = useState(null)
  const [showApiKey, setShowApiKey] = useState(false)

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

  useEffect(() => { fetchStats(); fetchConfig() }, [])

  const fetchConfig = async () => {
    setLoading(p => ({ ...p, config: true }))
    try {
      const cfg = await getConfig()
      setConfig(cfg)
      setConfigForm(cfgToForm(cfg))
      setErrors(p => ({ ...p, config: null }))
    } catch (e) {
      setErrors(p => ({ ...p, config: e.message }))
    } finally {
      setLoading(p => ({ ...p, config: false }))
    }
  }

  const cfgToForm = (cfg) => ({
    // paths
    raw_pdfs: cfg.paths?.raw_pdfs ?? '',
    markdown_output: cfg.paths?.markdown_output ?? '',
    vectorstore: cfg.paths?.vectorstore ?? '',
    index_file: cfg.paths?.index_file ?? '',
    // llm
    api_endpoint: cfg.llm.api_endpoint,
    api_key: '',
    model_name: cfg.llm.model_name,
    temperature: cfg.llm.temperature,
    max_tokens: cfg.llm.max_tokens,
    chat_endpoint: cfg.llm.chat_endpoint,
    embedding_endpoint: cfg.llm.embedding_endpoint,
  })

  const handleConfigEdit = () => {
    setConfigForm(cfgToForm(config))
    setConfigSaveResult(null)
    setConfigEditing(true)
  }

  const handleConfigCancel = () => {
    setConfigEditing(false)
    setConfigSaveResult(null)
  }

  const handleConfigSave = async () => {
    setLoading(p => ({ ...p, configSave: true }))
    setConfigSaveResult(null)
    try {
      const llmPayload = {
        api_endpoint: configForm.api_endpoint,
        model_name: configForm.model_name,
        temperature: configForm.temperature,
        max_tokens: configForm.max_tokens,
        chat_endpoint: configForm.chat_endpoint,
        embedding_endpoint: configForm.embedding_endpoint,
      }
      if (configForm.api_key) llmPayload.api_key = configForm.api_key

      const pathsPayload = {
        raw_pdfs: configForm.raw_pdfs,
        markdown_output: configForm.markdown_output,
        vectorstore: configForm.vectorstore,
        index_file: configForm.index_file,
      }

      await updateLlmConfig(llmPayload)
      const result = await updatePathsConfig(pathsPayload)
      setConfig(result)
      setConfigForm(cfgToForm(result))
      setConfigSaveResult({ ok: true })
      setConfigEditing(false)
    } catch (e) {
      setConfigSaveResult({ ok: false, message: e.message })
    } finally {
      setLoading(p => ({ ...p, configSave: false }))
    }
  }

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

        {/* Configuration card — editable */}
        <div className="admin-card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
            <h2 style={{ margin: 0 }}>📁 {t.configuration}</h2>
            {!configEditing && config && (
              <button className="btn-secondary" onClick={handleConfigEdit} style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                ✏️ Edit
              </button>
            )}
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 16 }}>
            {t.configurationDesc}
          </p>

          {loading.config ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{t.loading}</div>
          ) : errors.config ? (
            <div className="status-banner error">❌ {errors.config}</div>
          ) : configEditing && configForm ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>

                <div style={sectionStyle}>
                  <div style={sectionHeadStyle}>Paths</div>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>{t.pdfSource}</span>
                    <input style={inputStyle} value={configForm.raw_pdfs}
                      onChange={e => setConfigForm(f => ({ ...f, raw_pdfs: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>{t.markdownOutput}</span>
                    <input style={inputStyle} value={configForm.markdown_output}
                      onChange={e => setConfigForm(f => ({ ...f, markdown_output: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>{t.vectorStore}</span>
                    <input style={inputStyle} value={configForm.vectorstore}
                      onChange={e => setConfigForm(f => ({ ...f, vectorstore: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Index file</span>
                    <input style={inputStyle} value={configForm.index_file}
                      onChange={e => setConfigForm(f => ({ ...f, index_file: e.target.value }))} />
                  </label>
                </div>

                <div style={sectionStyle}>
                  <div style={sectionHeadStyle}>LLM</div>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>API Endpoint</span>
                    <input style={inputStyle} value={configForm.api_endpoint}
                      onChange={e => setConfigForm(f => ({ ...f, api_endpoint: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>API Key</span>
                    <div style={{ position: 'relative' }}>
                      <input
                        style={{ ...inputStyle, paddingRight: 36 }}
                        type={showApiKey ? 'text' : 'password'}
                        placeholder="Leave blank to keep existing key"
                        value={configForm.api_key}
                        onChange={e => setConfigForm(f => ({ ...f, api_key: e.target.value }))}
                      />
                      <button type="button" onClick={() => setShowApiKey(v => !v)}
                        style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        {showApiKey ? '🙈' : '👁'}
                      </button>
                    </div>
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Model Name</span>
                    <input style={inputStyle} value={configForm.model_name}
                      onChange={e => setConfigForm(f => ({ ...f, model_name: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Temperature ({configForm.temperature})</span>
                    <input style={inputStyle} type="range" min="0" max="1" step="0.05"
                      value={configForm.temperature}
                      onChange={e => setConfigForm(f => ({ ...f, temperature: parseFloat(e.target.value) }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Max Tokens</span>
                    <input style={inputStyle} type="number" min="256" max="32768" step="256"
                      value={configForm.max_tokens}
                      onChange={e => setConfigForm(f => ({ ...f, max_tokens: parseInt(e.target.value, 10) }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Chat Endpoint</span>
                    <input style={inputStyle} value={configForm.chat_endpoint}
                      onChange={e => setConfigForm(f => ({ ...f, chat_endpoint: e.target.value }))} />
                  </label>

                  <label style={labelStyle}>
                    <span style={labelTextStyle}>Embedding Endpoint</span>
                    <input style={inputStyle} value={configForm.embedding_endpoint}
                      onChange={e => setConfigForm(f => ({ ...f, embedding_endpoint: e.target.value }))} />
                  </label>
                </div>

              </div>

              <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
                <button className="btn-primary" onClick={handleConfigSave} disabled={loading.configSave}>
                  {loading.configSave ? <span className="spinner" /> : '💾'} Save
                </button>
                <button className="btn-secondary" onClick={handleConfigCancel} disabled={loading.configSave}>
                  Cancel
                </button>
                {configSaveResult && !configSaveResult.ok && (
                  <span style={{ fontSize: '0.85rem', color: 'var(--error)' }}>
                    ❌ {configSaveResult.message}
                  </span>
                )}
              </div>
            </>
          ) : config ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24 }}>
              <div>
                <div style={sectionHeadStyle}>Paths</div>
                <StatRow label={t.pdfSource} value={config.paths?.raw_pdfs} mono />
                <StatRow label={t.markdownOutput} value={config.paths?.markdown_output} mono />
                <StatRow label={t.vectorStore} value={config.paths?.vectorstore} mono />
                <StatRow label="Index file" value={config.paths?.index_file} mono />
              </div>
              <div>
                <div style={sectionHeadStyle}>LLM</div>
                <StatRow label="API endpoint" value={config.llm.api_endpoint} mono />
                <StatRow label="Chat endpoint" value={config.llm.chat_endpoint} mono />
                <StatRow label="Embedding endpoint" value={config.llm.embedding_endpoint} mono />
                <StatRow label={t.llmModel} value={config.llm.model_name} />
                <StatRow label="Temperature" value={config.llm.temperature} />
                <StatRow label="Max tokens" value={config.llm.max_tokens} />
              </div>
            </div>
          ) : null}
        </div>

      </div>
    </div>
  )
}

function StatRow({ label, value, mono }) {
  return (
    <div className="stat-row">
      <span className="stat-label">{label}</span>
      <span className="stat-value" style={mono ? { fontSize: '0.75rem', fontFamily: 'monospace' } : undefined}>
        {value}
      </span>
    </div>
  )
}

const labelStyle = { display: 'flex', flexDirection: 'column', gap: 5 }
const labelTextStyle = { fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }
const inputStyle = { padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', fontSize: '0.85rem', background: 'var(--surface)', color: 'var(--text)', width: '100%', boxSizing: 'border-box' }
const sectionStyle = { display: 'flex', flexDirection: 'column', gap: 14 }
const sectionHeadStyle = { fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, borderBottom: '1px solid var(--border)', paddingBottom: 6 }
