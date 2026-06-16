# CivicAssist — User Guide

## Overview

CivicAssist answers questions about Uruguayan **residency** and **identity card (Cédula de Identidad)** procedures. It retrieves answers from official government documents and web pages — it does not guess or invent information.

The app has two sections:
- **Chat** — ask questions in Spanish or English
- **Admin** — manage the knowledge base and configuration (requires login)

---

## Chat

### Asking a question

1. Open the app at `http://localhost:3000`
2. Select your language (ES / EN) in the top-right corner
3. Type your question in the input box and press **Enter** or click **Send**

The assistant will:
- Classify your question (residency or cédula, and which subcategory)
- Search the knowledge base for relevant source documents
- Generate a grounded answer with source citations

### Conversation history

CivicAssist remembers the last few exchanges in your session, so you can ask follow-up questions without repeating context:

> "What documents do I need for temporary residency?"
> "And how long does it take?"

### Language

Switch the language selector at the top of the page to get responses in Spanish or English. The language you set overrides any auto-detection — if you write in English with the selector set to English, the response will be in English even though the underlying documents are in Spanish.

### Quick questions

The sidebar contains pre-written questions grouped by category. Click any of them to send it instantly.

### What the assistant can and cannot answer

**Can answer:**
- Requirements, steps, and timelines for residency types
- Documents needed for a Cédula
- Which government agency handles what
- Differences between residency categories

**Cannot answer:**
- The status of your specific application
- Questions outside residency and Cédula topics
- Legal advice (consult a lawyer for that)

When the answer is not in the knowledge base, the assistant will say so and direct you to the relevant agency.

---

## Admin Panel

Access the Admin panel by clicking **Admin** and logging in. Default credentials are set in `config/config.yaml` under `admin.username` and `admin.password`.

### System Status

Shows:
- ChromaDB collection name
- Number of indexed chunks
- Whether the vector store is reachable

### Full Ingest

Runs the complete data pipeline:

1. Converts all PDFs in `backend/data/rawPDF/` to Markdown
2. Scrapes `gub.uy/tramites` for relevant pages (keyword-filtered)
3. Builds `INDEX.md` — a structured decision tree of categories and sources
4. Embeds all Markdown into ChromaDB

**When to use:** First run, or when you add new PDFs.

This process can take several minutes depending on the number of documents and your LLM's speed (the indexer makes an LLM call to build `INDEX.md`).

### Reindex

Skips PDF conversion and scraping. Rebuilds `INDEX.md` and re-embeds from the existing Markdown files.

**When to use:** When you've edited Markdown files directly, or want to refresh embeddings without re-scraping.

### Configuration Editor

Displays all current settings and allows live editing of:

| Section | Fields |
|---------|--------|
| **LLM** | API endpoint, API key (masked), model name, temperature, max tokens, chat endpoint, embedding endpoint |
| **Paths** | Raw PDFs directory, Markdown output, vector store, index file |

Click **Edit** to switch to form mode. Click **Save** to write changes to `config.yaml` and reload the backend settings — no server restart needed.

---

## Adding New Documents

1. Place PDF files in `backend/data/rawPDF/` (or the directory configured under `paths.raw_pdfs`)
2. Open the Admin panel
3. Click **Full Ingest**

PDFs are automatically categorized by keyword matching:
- Files mentioning "residencia permanente", "permanent residency" etc. → `residencia / Residencia Permanente`
- Files mentioning "cédula", "DNIC" etc. → `cedula / Cédula de Identidad`

If a PDF doesn't match any keyword, it is stored under `unknown` and still indexed.

---

## Switching LLM Providers

Edit `config/config.yaml` (or use the Admin config editor) and set:

**Claude (Anthropic):**
```yaml
llm:
  api_endpoint: "https://api.anthropic.com"
  api_key: "${LLM_API_KEY}"
  model_name: "claude-sonnet-4-6"
  chat_endpoint: "/v1/chat/completions"
```

**OpenAI:**
```yaml
llm:
  api_endpoint: "https://api.openai.com"
  api_key: "${LLM_API_KEY}"
  model_name: "gpt-4o-mini"
  chat_endpoint: "/v1/chat/completions"
```

**Ollama (local):**
```yaml
llm:
  api_endpoint: "http://localhost:11434"
  api_key: ""
  model_name: "llama3"
  chat_endpoint: "/v1/chat/completions"
```

Store your API key in `backend/.env` as `LLM_API_KEY=...` rather than directly in `config.yaml`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "No relevant context found" | Knowledge base is empty | Run Full Ingest from Admin |
| Responses in wrong language | Language selector set incorrectly | Switch the language toggle in the top-right |
| Admin login fails | Wrong credentials | Check `admin.username` / `admin.password` in `config.yaml` |
| LLM call fails (500 error) | Wrong API key or endpoint | Check LLM settings in Admin → Configuration |
| Slow responses | Large PDF set or slow LLM | Try a faster model or reduce `max_tokens` in config |
| Embeddings fail | Embedding endpoint misconfigured | Verify `llm.embedding_endpoint` in config |

---

## Legal Disclaimer

CivicAssist provides legal **information** for orientation purposes only. It is not legal advice. For official guidance, consult:

- [DNIC (Dirección Nacional de Identificación Civil)](https://www.dnic.gub.uy)
- [Dirección Nacional de Migración](https://www.migracion.gub.uy)
- [gub.uy — Trámites y servicios](https://www.gub.uy/tramites)
