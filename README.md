# 🇺🇾 UruguayLex — Asistente Legal / Legal Assistant

**UruguayLex** is a RAG-powered bilingual legal assistant specialising in Uruguayan law for:
- **Residencia** (Permanent, Temporary, Refugio, Prórroga, Category Change)
- **Cédula de Identidad** (Uruguayans, Foreigners, Renewal, First-time, Duplicates)

Users may ask questions in **Spanish or English**.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  ChatPage · AdminPage · Sidebar · MessageBubbles     │
└──────────────────────────┬──────────────────────────┘
                           │ HTTP / REST
┌──────────────────────────▼──────────────────────────┐
│              Backend (FastAPI / Python)              │
│                                                      │
│  POST /api/v1/chat        → query.py                 │
│  POST /api/v1/admin/ingest → ingestion + scraper     │
│  POST /api/v1/admin/reindex → indexer + vectorstore  │
│  GET  /api/v1/admin/stats  → vectorstore stats       │
│                                                      │
│  Services:                                           │
│  ├─ ingestion.py   PDF → Markdown                    │
│  ├─ scraper.py     gub.uy → Markdown                 │
│  ├─ indexer.py     → INDEX.md (decision tree)        │
│  ├─ vectorstore.py → ChromaDB embed / retrieve       │
│  └─ query.py       classify → retrieve → Claude      │
└──────────────────────────────────────────────────────┘
                 │              │
         ChromaDB         Claude API
       (local vectors)   (claude-sonnet-4-6)
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API key

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and set:  ANTHROPIC_API_KEY=your_key_here

# Start server
python main.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 3. Quick start (Windows)
```
scripts\start_backend.bat     # Terminal 1
scripts\start_frontend.bat    # Terminal 2
```

---

## First Run — Ingesting Data

1. Place your PDF files in:
   `C:\Users\abirs\Documents\Cursor\LAWassist\data\raw_pdfs`
   (or update `paths.raw_pdfs` in `config/config.yaml`)

2. Open the app → **Admin** tab → click **Iniciar Ingestión**

   This will:
   - Convert PDFs to categorised Markdown files
   - Scrape relevant pages from `gub.uy/tramites`
   - Build `INDEX.md` (the decision-tree index)
   - Embed everything into ChromaDB

3. Switch to **Consultas** and start asking questions!

---

## Configuration (`config/config.yaml`)

| Key | Purpose |
|-----|---------|
| `anthropic.api_key` | Resolved from `$ANTHROPIC_API_KEY` env var |
| `anthropic.model` | LLM model (`claude-sonnet-4-6`) |
| `paths.raw_pdfs` | Source folder for PDF files |
| `paths.markdown_output` | Where Markdown files are generated |
| `paths.vectorstore` | ChromaDB persistence directory |
| `paths.index_file` | Path to INDEX.md |
| `chromadb.embedding_model` | Sentence-transformer model for embeddings |
| `scraping.base_url` | Root URL for web crawl |
| `scraping.target_keywords` | Keywords that determine relevance |
| `api.cors_origins` | Allowed frontend origins |

---

## INDEX.md — Decision Tree

The auto-generated `INDEX.md` acts as the master index.
Every Markdown file has YAML front-matter:

```yaml
---
title: "Residencia Permanente en Uruguay"
category: "residencia"
subcategory: "Residencia Permanente"
source: "PDF: decreto_residencia.pdf"
index_creation_date: "2026-06-15"
---
```

The query pipeline:
1. **Classify** → Claude reads the question and returns `{category, subcategory}`
2. **Filter** → ChromaDB query is scoped to those metadata fields
3. **Generate** → Claude answers grounded in the retrieved chunks

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Send a question, get an answer |
| POST | `/api/v1/admin/ingest` | Full ingest (PDF + scrape + embed) |
| POST | `/api/v1/admin/reindex` | Rebuild index + re-embed |
| GET | `/api/v1/admin/stats` | ChromaDB stats |

### Chat request body
```json
{
  "question": "¿Cómo obtengo la residencia permanente?",
  "conversation_history": [],
  "session_id": "optional-uuid"
}
```

---

## Project Structure

```
lawassist/
├── config/
│   └── config.yaml              # ← All configuration
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt
│   ├── app/
│   │   ├── core/config.py       # Config loader
│   │   ├── api/
│   │   │   ├── chat.py          # Chat endpoint
│   │   │   └── admin.py         # Admin endpoints
│   │   ├── models/schemas.py    # Pydantic models
│   │   └── services/
│   │       ├── ingestion.py     # PDF → Markdown
│   │       ├── scraper.py       # gub.uy crawler
│   │       ├── indexer.py       # INDEX.md builder
│   │       ├── vectorstore.py   # ChromaDB
│   │       └── query.py         # Classify + RAG + LLM
│   └── data/
│       ├── markdown/            # Generated .md files + INDEX.md
│       └── vectorstore/         # ChromaDB persistence
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx
│   │   │   └── AdminPage.jsx
│   │   ├── components/
│   │   │   ├── Message.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── WelcomeScreen.jsx
│   │   ├── hooks/useChat.js
│   │   ├── utils/api.js
│   │   └── styles/globals.css
│   └── package.json
└── scripts/
    ├── start_backend.bat
    └── start_frontend.bat
```

---

## Disclaimer

> This application provides legal information for **orientation purposes only**.
> It is not legal advice. Always consult the competent Uruguayan authorities:
> [DNIC](https://www.dnic.gub.uy) · [Migraciones](https://www.migracion.gub.uy) · [gub.uy](https://www.gub.uy/tramites)
