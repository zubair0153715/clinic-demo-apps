"""PharmaAI routes: chat UI, ask API, document upload, KB listing."""
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import gen
from . import kb as kbmod
from .pages import CHAT_HTML

log = logging.getLogger("pharma_ai.routes")
router = APIRouter(prefix="/pharma-ai")

DISCLAIMER = ("Study aid only — not medical advice. Verify with your textbooks "
              "and a qualified pharmacist/doctor.")

# Load the shipped knowledge base once at import.
kbmod.KB.load()


class AskIn(BaseModel):
    question: str


def _safe_filename(name):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:80] or "upload.pdf"


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def chat_page():
    return HTMLResponse(CHAT_HTML)


@router.get("/api/docs")
def list_docs():
    return {"docs": kbmod.KB.doc_list(),
            "generated_by": "BM25 RAG v1 (no fine-tuning)",
            "disclaimer": DISCLAIMER}


@router.post("/api/ask")
def ask(inp: AskIn):
    q = (inp.question or "").strip()
    if not q:
        return JSONResponse({"error": "Empty question."}, status_code=400)
    if len(q) > 1000:
        return JSONResponse({"error": "Question too long (max 1000 chars)."},
                            status_code=400)
    passages = kbmod.KB.search(q, top_k=5)
    if not passages:
        return {"question": q, "answer": None, "generated": False,
                "notice": ("Your books don't seem to cover this — "
                           "try different wording, or upload the relevant document."),
                "citations": [], "passages": [], "disclaimer": DISCLAIMER}
    citations = [f"{p['doc_title']} — {p['section']}" for p in passages]
    answer, err = gen.generate(q, passages)
    if answer:
        return {"question": q, "answer": answer, "generated": True,
                "notice": None, "citations": citations,
                "passages": passages, "disclaimer": DISCLAIMER}
    # graceful fallback: passages only
    return {"question": q, "answer": None, "generated": False,
            "notice": err, "citations": citations,
            "passages": passages, "disclaimer": DISCLAIMER}


@router.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    name = _safe_filename(file.filename or "upload.pdf")
    if not name.lower().endswith(".pdf"):
        return JSONResponse({"ok": False, "error": "Only PDF files."},
                            status_code=400)
    data = await file.read()
    if len(data) > 60 * 1024 * 1024:
        return JSONResponse({"ok": False, "error": "Max 60 MB."},
                            status_code=400)
    kbmod.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = kbmod.UPLOADS_DIR / f"{uuid.uuid4().hex[:8]}_{name}"
    dest.write_bytes(data)
    title = name[:-4].replace("_", " ").replace("-", " ").strip() or "Uploaded document"
    try:
        n = kbmod.KB.ingest_pdf(dest, doc_id=f"upload-{uuid.uuid4().hex[:8]}",
                                title=title, source="user upload")
    except Exception as e:
        log.warning("upload ingest failed: %s", e)
        return JSONResponse({"ok": False,
                             "error": f"Could not read that PDF: {e}"},
                            status_code=400)
    return {"ok": True, "title": title, "chunks": n,
            "note": "Indexed for this session. Rebuild the KB to keep it across deploys."}
