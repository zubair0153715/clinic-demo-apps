# PharmaAI Assistant v1 — RAG study assistant

**Live:** https://clinic-demo.fastapicloud.dev/pharma-ai

Zubair's own pharma knowledge assistant. Ask a question → it searches his
pharma books (BM25 retrieval) → an AI model writes a grounded answer with
citations (book title + chapter + page).

## Why RAG, not fine-tuning — stated plainly

Fine-tuning a model needs a GPU. This VM has no GPU, and neither does the
free hosting tier. So v1 is **retrieval-augmented generation**:

1. Book PDFs are extracted to text, split into ~500-word chunks.
2. A BM25 keyword index (pure Python, `rank-bm25`) finds the most relevant chunks.
3. The owner's free Gemini key (`GEMINI_API_KEY`) generates an answer
   **only from those passages**, with citations.

No weights are trained. The knowledge lives in the books, not in a model.

## Knowledge base

- **Seeded:** "Basic & Clinical Pharmacology (2018)" — 1264 pages → 2199 chunks.
- **Index file:** `app/pharma_ai/kbdata/kb.json` (~7 MB). Built on the VM with
  `python -m app.pharma_ai.build_kb` (run from `~/workspace/clinic-demo`)
  **before** deploy, so it ships inside the app package and survives deploys.
- **IMPORTANT packaging gotcha:** the repo `.gitignore` excludes any directory
  named `data/`, and the FastAPI Cloud deploy respects it. The index must live
  under `kbdata/` (or any non-`data/` name), never `data/`.
- **Uploads:** `POST /pharma-ai/api/upload` (PDF, ≤60 MB) — text is extracted,
  chunked and indexed at runtime. Runtime uploads are lost on the next deploy
  unless the KB is rebuilt with them (re-run `build_kb.py` with the PDFs added
  to `SEED_DOCS`, or keep a persistent upload workflow for v2).

## Endpoints

| Route | What |
|---|---|
| `GET /pharma-ai` | Chat UI (with study-aid banner) |
| `POST /pharma-ai/api/ask` | `{question}` → grounded answer + citations + passages |
| `GET /pharma-ai/api/docs` | Indexed documents |
| `POST /pharma-ai/api/upload` | Add a PDF to the index |

## Graceful degradation

- No `GEMINI_API_KEY` → the API returns the retrieved passages with a clear
  notice instead of breaking.
- Gemini quota exhausted (HTTP 429) → same fallback, retry message included.
- No relevant passages → honest "your books don't cover this" instead of guessing.

## Honest framing (standing rule)

Every surface carries it: **study & research aid only — NOT medical advice.**
The page banner, every API response (`disclaimer` field), and every generated
answer end with it. Same rule as the MedExplain tool.

## Limits of v1

- Keyword search (BM25), not semantic — odd phrasing can miss; try synonyms.
- Generation quality depends on the Gemini free-tier quota.
- Answers are only as good as the indexed books; one textbook seeded so far.
- No user accounts, no per-user history (v2 scope).
- Uploads don't survive deploys yet (see above).
