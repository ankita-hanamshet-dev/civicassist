# CivicAssist — Project Vision

## Problem

Navigating Uruguayan immigration and identity procedures is difficult, especially for foreigners. Official information is scattered across multiple government websites (gub.uy, DNIC, Migraciones), often in Spanish only, and frequently incomplete or outdated. People end up making expensive mistakes — wrong forms, missing documents, expired timelines — because they couldn't find a clear, trustworthy answer.

## Vision

CivicAssist is a bilingual (Spanish / English) legal information assistant that gives people fast, grounded answers about Uruguayan residency and identity card procedures — sourced directly from official PDFs and government web pages, not from general LLM training data.

It is not a replacement for a lawyer or an official government office. It is a first stop: a way to understand the process, know the steps, and identify the right agency before investing time and money.

## Who It Is For

| User | Need |
|------|------|
| **Foreigners living in or moving to Uruguay** | Understand residency types, timelines, document requirements |
| **Uruguayan residents** | Cédula renewal, duplicates, first-time issuance |
| **NGOs and social workers** | Quick reference tool when helping clients with paperwork |
| **Developers / researchers** | Template for RAG-based civic information assistants |

## Guiding Principles

1. **Grounded, not hallucinated.** Every answer is built from retrieved source documents. The LLM does not invent legal facts.
2. **Bilingual by design.** The UI, the assistant, and all configuration support both Spanish and English equally.
3. **Provider-agnostic.** Works with Claude, OpenAI, or any self-hosted Ollama model — swap via config with no code changes.
4. **Admin-first data management.** PDFs and scraped pages are ingested, chunked, and indexed through an in-app admin panel — no CLI required.
5. **Transparent sourcing.** Responses cite the source documents used, so users can verify and read further.

## Scope (Current Version)

- **Residencia:** Permanente, Temporaria, Refugio, Prórroga, Cambio de Categoría, Legal
- **Cédula de Identidad:** For Uruguayans and foreigners, renewal, first-time, duplicates

## Out of Scope

- General legal advice beyond the above categories
- Real-time status tracking of individual applications
- Direct integration with government APIs
- Document generation or form filling
