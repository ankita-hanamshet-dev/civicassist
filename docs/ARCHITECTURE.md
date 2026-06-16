# CivicAssist — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (React + Vite)                   │
│                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌───────────────┐  │
│   │  ChatPage    │   │  AdminPage   │   │  LoginPage    │  │
│   │  + Sidebar   │   │  (auth req.) │   │               │  │
│   └──────┬───────┘   └──────┬───────┘   └───────────────┘  │
│          │  useChat hook     │  fetch                        │
│          │  utils/api.js     │  utils/api.js                 │
└──────────┼───────────────────┼─────────────────────────────┘
           │ POST /api/v1/chat │ /api/v1/admin/*
           ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python)                     │
│                                                             │
│  Routers                                                    │
│  ├── chat.py          → answer_question()                   │
│  └── admin.py         → ingest / reindex / stats / config   │
│                                                             │
│  Services                                                   │
│  ├── query.py         classify → retrieve → LLM             │
│  ├── llm.py           provider-agnostic HTTP client         │
│  ├── vectorstore.py   ChromaDB embed + retrieve             │
│  ├── indexer.py       build INDEX.md decision tree          │
│  ├── ingestion.py     PDF → categorised Markdown            │
│  └── scraper.py       gub.uy → Markdown                     │
│                                                             │
│  Core                                                       │
│  └── config.py        settings loader (YAML + env vars)     │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
    ┌──────▼──────┐          ┌────────▼────────┐
    │  ChromaDB   │          │  LLM Provider   │
    │  (local     │          │  Claude / OpenAI│
    │   vectors)  │          │  / Ollama       │
    └─────────────┘          └─────────────────┘
```

## Query Pipeline (Chat Request)

Every user question goes through three stages:

```
User question
      │
      ▼
1. CLASSIFY
   LLM call with CLASSIFICATION_PROMPT
   → { category, subcategory, language }
      │
      ▼
2. RETRIEVE
   ChromaDB semantic search
   filtered by category + subcategory
   → top-8 chunks
   (fallback: unfiltered search if < 3 chunks found)
      │
      ▼
3. GENERATE
   System prompt (EN or ES) + context + question → LLM
   → grounded answer + source citations
```

### Key design choices

- **Two LLM calls per query.** The first (classification) is cheap — 256 tokens max, no context. The second (generation) gets the full retrieved context.
- **Category filter at retrieval time.** ChromaDB is queried with a `where` filter on `category` metadata. This keeps results focused without needing a separate re-ranker.
- **Fallback broadening.** If the filtered search returns fewer than 3 chunks, the query retries without a filter so the user always gets an answer.
- **Language override.** The UI sends an explicit `language` field. This takes precedence over LLM-detected language — critical for English users whose questions get mis-classified.

## Ingestion Pipeline (Admin Trigger)

```
PDF files (backend/data/rawPDF/)
      │
      ▼
ingestion.py
  PyMuPDF extracts text page-by-page
  Keyword matching assigns category + subcategory
  → Markdown files (backend/data/markdown/)
      │
      ▼ (parallel)
scraper.py
  Crawls gub.uy/tramites/ depth-first
  Filters pages matching target_keywords from config
  → Markdown files (backend/data/markdown/)
      │
      ▼
indexer.py
  Reads all Markdown files
  LLM call to build structured INDEX.md
  (category → subcategory → source mapping)
      │
      ▼
vectorstore.py
  Chunks Markdown (overlap-aware)
  Embeds with sentence-transformers (all-MiniLM-L6-v2)
  Stores in ChromaDB with metadata:
    { source, title, category, subcategory, filename }
```

## Component Map

### Backend

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app setup, CORS, router mounting |
| `app/core/config.py` | Loads `config/config.yaml`, applies env var overrides, exposes `get_settings()` singleton |
| `app/api/chat.py` | `POST /api/v1/chat` — validates request, calls `answer_question()` |
| `app/api/admin.py` | All `/api/v1/admin/*` routes with Basic auth |
| `app/services/query.py` | Full classify → retrieve → generate pipeline |
| `app/services/llm.py` | Provider-agnostic `create_chat_completion()` and `create_embedding()` — detects Anthropic vs OpenAI vs Ollama from endpoint URL |
| `app/services/vectorstore.py` | ChromaDB wrapper: `embed_documents()`, `retrieve()`, `get_stats()` |
| `app/services/ingestion.py` | PDF → Markdown using PyMuPDF, keyword-based category tagging |
| `app/services/scraper.py` | Async gub.uy crawler → Markdown |
| `app/services/indexer.py` | Builds `INDEX.md` decision tree via LLM |
| `app/models/schemas.py` | Pydantic request/response models |

### Frontend

| File | Responsibility |
|------|---------------|
| `App.jsx` | Root: language state, routing between Chat and Admin |
| `i18n.js` | All UI strings in ES + EN, `DEFAULT_LANGUAGE` |
| `utils/api.js` | `sendChat()`, admin API calls — wraps `fetch` |
| `hooks/useChat.js` | Chat state: message list, session ID, loading, `ask()` |
| `pages/ChatPage.jsx` | Chat UI layout: Sidebar + message thread + input |
| `pages/AdminPage.jsx` | Admin dashboard: status, ingest, reindex, config editor |
| `pages/LoginPage.jsx` | Admin login form |
| `components/Message.jsx` | Renders a single message bubble with metadata tags |
| `components/Sidebar.jsx` | Category browser + quick question buttons |
| `components/ChatInput.jsx` | Text input with submit |
| `components/WelcomeScreen.jsx` | Shown before the first message |

## Data Storage

```
backend/data/
├── rawPDF/          ← Input: drop PDFs here before ingestion
├── markdown/
│   ├── INDEX.md     ← LLM-generated category/subcategory index
│   └── *.md         ← Converted from PDF and scraped pages
└── vectorstore/     ← ChromaDB on-disk persistence
    └── <collection-uuid>/
```

All paths are configurable in `config/config.yaml` under `paths.*`.

## Configuration & Secrets

`config/config.yaml` is the single source of truth. It supports `${ENV_VAR}` substitution for secrets.

**Never commit real API keys to `config.yaml`.** Use `backend/.env` instead:

```
LLM_API_KEY=sk-ant-...
```

The settings loader reads `.env` automatically via `python-dotenv`.

## LLM Provider Detection

`llm.py` detects the provider from the `api_endpoint` URL:

| Endpoint contains | Provider | Auth header | System prompt placement |
|---|---|---|---|
| `anthropic.com` or `claude` | Anthropic | `x-api-key` | `payload["system"]` |
| `openai.com` | OpenAI | `Authorization: Bearer` | prepended as `system` message |
| `ollama` | Ollama | `Authorization: Bearer` | prepended as `system` message |
| anything else | Generic | `Authorization: Bearer` | prepended as `system` message |
