"""MedExplain Studio: upload PDFs, queue chapter video jobs, serve finished MP4s."""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from .pages import STUDIO_HTML

import hmac

log = logging.getLogger("study.routes")
router = APIRouter(prefix="/study")

BASE = os.path.expanduser("~/workspace/medexplain")
UPLOADS = os.path.join(BASE, "uploads")
QUEUE = os.path.join(BASE, "queue")
DONE = os.path.join(BASE, "done")

WORKER_KEY = os.environ.get("MEDEXPLAIN_WORKER_KEY", "")


def _check_worker(x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    # Fail closed: no key configured => no worker access.
    if not WORKER_KEY or not hmac.compare_digest(x_worker_key or "", WORKER_KEY):
        raise HTTPException(status_code=403, detail="forbidden")

for d in (UPLOADS, QUEUE, DONE):
    os.makedirs(d, exist_ok=True)


def _safe_name(name: str) -> str:
    name = os.path.basename(name or "upload.pdf")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name[:120] or "upload.pdf"


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "chapter").lower()).strip("-")
    return s[:60] or "chapter"


# ---------- pages ----------

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def studio():
    return HTMLResponse(STUDIO_HTML)


# ---------- API ----------

@router.get("/api/books")
def list_books():
    books = sorted(f for f in os.listdir(UPLOADS) if f.lower().endswith(".pdf"))
    return {"books": books}


@router.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only_pdf")
    fname = _safe_name(file.filename)
    # avoid collisions
    dest = os.path.join(UPLOADS, fname)
    if os.path.exists(dest):
        stem = fname[:-4]
        fname = f"{stem}_{uuid.uuid4().hex[:6]}.pdf"
        dest = os.path.join(UPLOADS, fname)
    data = await file.read()
    if len(data) > 200 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file_too_large")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="not_a_pdf")
    with open(dest, "wb") as f:
        f.write(data)
    log.info("uploaded %s (%d bytes)", fname, len(data))
    return {"ok": True, "filename": fname}


class JobIn(BaseModel):
    pdf: str
    chapter: str
    pages: str  # e.g. "45-62" or "45"


def _parse_pages(pages: str):
    m = re.match(r"^\s*(\d+)\s*(?:-\s*(\d+))?\s*$", pages or "")
    if not m:
        raise HTTPException(status_code=400, detail="bad_pages_format")
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    if a < 1 or b < a or (b - a) > 40:
        raise HTTPException(status_code=400, detail="pages_out_of_range")
    return a, b


@router.post("/api/jobs")
def create_job(job: JobIn):
    pdf = _safe_name(job.pdf)
    if not os.path.exists(os.path.join(UPLOADS, pdf)):
        raise HTTPException(status_code=404, detail="pdf_not_found")
    chapter = (job.chapter or "").strip()[:120]
    if not chapter:
        raise HTTPException(status_code=400, detail="chapter_required")
    a, b = _parse_pages(job.pages)
    jid = uuid.uuid4().hex[:12]
    rec = {
        "id": jid,
        "pdf": pdf,
        "chapter": chapter,
        "pages": f"{a}-{b}",
        "slug": _slug(chapter),
        "status": "queued",
        "error": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(QUEUE, f"{jid}.json"), "w") as f:
        json.dump(rec, f)
    log.info("job queued %s (%s %s)", jid, chapter, rec["pages"])
    return {"ok": True, "id": jid}


@router.get("/api/jobs")
def list_jobs():
    jobs = []
    for f in sorted(os.listdir(QUEUE), reverse=True):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(QUEUE, f)) as fh:
                jobs.append(json.load(fh))
        except Exception:
            continue
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return {"jobs": jobs}


@router.get("/api/videos")
def list_videos():
    vids = []
    for f in sorted(os.listdir(DONE), reverse=True):
        if not f.lower().endswith(".mp4"):
            continue
        p = os.path.join(DONE, f)
        title = f[:-4].replace("-", " ").replace("_", " ").title()
        vids.append({
            "filename": f,
            "title": title,
            "size_mb": round(os.path.getsize(p) / 1048576, 1),
        })
    return {"videos": vids}


@router.get("/video/{filename}")
def serve_video(filename: str):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    p = os.path.join(DONE, safe)
    if not os.path.isfile(p) or not safe.lower().endswith(".mp4"):
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(p, media_type="video/mp4", filename=safe)


# ---------- VM render-worker bridge (not linked in UI) ----------

@router.get("/api/worker/next")
def worker_next(x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    best = None
    for f in os.listdir(QUEUE):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(QUEUE, f)) as fh:
                j = json.load(fh)
        except Exception:
            continue
        if j.get("status") in ("queued", "failed") and j.get("retries", 0) < 3 and \
                (best is None or j.get("created_at", "") < best.get("created_at", "")):
            best = j
    return {"job": best}


@router.get("/api/worker/pdf/{filename}")
def worker_pdf(filename: str, x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    safe = _safe_name(filename)
    p = os.path.join(UPLOADS, safe)
    if not os.path.isfile(p):
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(p, media_type="application/pdf", filename=safe)


class WorkerStatusIn(BaseModel):
    status: str
    error: str = ""
    video: str = ""
    duration_s: float = 0


@router.post("/api/worker/jobs/{jobid}/status")
def worker_job_status(jobid: str, s: WorkerStatusIn, x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    jid = re.sub(r"[^a-z0-9]", "", jobid)[:16]
    p = os.path.join(QUEUE, f"{jid}.json")
    if not os.path.isfile(p):
        raise HTTPException(status_code=404, detail="not_found")
    if s.status not in ("working", "done", "failed"):
        raise HTTPException(status_code=400, detail="bad_status")
    with open(p) as fh:
        j = json.load(fh)
    if j.get("status") == "failed" and s.status == "working":
        j["retries"] = j.get("retries", 0) + 1
    j["status"] = s.status
    j["error"] = s.error[:500]
    if s.video:
        j["video"] = re.sub(r"[^A-Za-z0-9._-]", "_", s.video)
    if s.duration_s:
        j["duration_s"] = s.duration_s
    with open(p, "w") as fh:
        json.dump(j, fh)
    return {"ok": True}


@router.post("/api/worker/videos")
async def worker_video_upload(file: UploadFile = File(...), x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(file.filename or "video.mp4"))
    if not name.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="only_mp4")
    data = await file.read()
    if len(data) > 500 * 1024 * 1024 or len(data) < 1024:
        raise HTTPException(status_code=400, detail="bad_size")
    if data[4:8] != b"ftyp":
        raise HTTPException(status_code=400, detail="not_mp4")
    with open(os.path.join(DONE, name), "wb") as f:
        f.write(data)
    log.info("worker uploaded video %s (%d bytes)", name, len(data))
    return {"ok": True, "filename": name}
