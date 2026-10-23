"""Tukra routes — free AI clip maker: transcript/SRT in, clip pack out.

Original clean-room build. Not affiliated with OpusClip or any other
clip-making tool. Stateless: no server storage, uploads deleted after
processing, nothing trains on your content.
"""
import logging
import os
import re
import tempfile

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from . import captions as capmod
from . import gemini
from . import highlights as hlmod
from . import render as rendermod
from . import transcribe as transmod
from .pages import TUKRA_HTML

log = logging.getLogger("tukra.routes")
router = APIRouter(prefix="/tukra")

MAX_INPUT = 500_000
MAX_UPLOAD_MB = 100


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def page():
    return HTMLResponse(TUKRA_HTML)


@router.get("/api/ai-status")
def api_ai_status():
    return JSONResponse({
        "ai_available": gemini.key_available(),
        "ffmpeg_available": rendermod.available(),
        "transcribe_available": transmod.available(),
    })


def _sentences_with_timing(segments):
    """Split timed segments into sentence-level segments (proportional)."""
    out = []
    for s, e, text in segments:
        sents = hlmod.split_sentences(text)
        if not sents:
            continue
        total = sum(len(x) for x in sents) or 1
        cursor = s
        for i, sent in enumerate(sents):
            share = len(sent) / total
            wend = s + (e - s) * sum(len(x) for x in sents[:i + 1]) / total
            if i == len(sents) - 1:
                wend = e
            out.append((round(cursor, 2), round(wend, 2), sent))
            cursor = wend
    return out


class AnalyzeIn(BaseModel):
    content: str = ""
    lang: str = "en"          # en | ur | roman
    use_ai: bool = True
    max_clips: int = 8


@router.post("/api/analyze")
def api_analyze(body: AnalyzeIn):
    content = (body.content or "").strip()
    if not content:
        return JSONResponse(
            {"error": "Transcript khaali hai — text paste karo ya SRT/VTT file do."},
            status_code=400)
    if len(content) > MAX_INPUT:
        return JSONResponse(
            {"error": f"Input bohat lamba hai ({len(content)} chars)."},
            status_code=400)
    lang = body.lang if body.lang in ("en", "ur", "roman") else "en"
    max_clips = max(1, min(int(body.max_clips or 8), 12))
    warnings = []

    timed = capmod.detect_input_format(content) == "timed"
    clips = []
    sentences = []
    segments = []
    if timed:
        try:
            segments = capmod.parse_timed(content)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        sent_segs = _sentences_with_timing(segments)
        sentences = [t for _, _, t in sent_segs]
        clips = hlmod.detect_highlights_timed(sent_segs, max_clips=max_clips)
    else:
        sentences = hlmod.split_sentences(content)
        clips = hlmod.detect_highlights_text(content, max_clips=max_clips)

    if not clips:
        return JSONResponse(
            {"error": "Koi strong moment nahi mila — lamba transcript do ya AI try karo.",
             "warnings": warnings}, status_code=200)

    ai_used = False
    if body.use_ai and gemini.key_available() and sentences:
        moments, err = gemini.pick_moments(" ".join(sentences), lang=lang)
        if err:
            warnings.append(f"AI moments unavailable ({err}) — rule-based results.")
        else:
            clips = hlmod.apply_ai_picks(clips, moments)
            ai_used = True
            warnings.append("AI ne moments pick kiye — titles/why AI-generated hain.")
    elif body.use_ai:
        warnings.append("AI key nahi hai — rule-based detection use hui (hamesha free).")

    # Attach per-clip word timings (relative to clip start) for caption files.
    for c in clips:
        if c["timed"] and segments:
            c["words"] = [[w, ws, we] for w, ws, we in
                          capmod.clip_words(segments, c["start"], c["end"])]
        else:
            c["words"] = []
        if not c["title"]:
            hook = c["hook"] or ""
            c["title"] = hook[:60] + ("…" if len(hook) > 60 else "")
        c["social"] = capmod.social_caption(c["hook"], lang)

    return JSONResponse({
        "clips": clips, "warnings": warnings, "ai": ai_used,
        "timed": timed, "lang": lang,
        "stats": {"sentences": len(sentences),
                  "segments": len(segments) if timed else 0},
    })


class CaptionsIn(BaseModel):
    clip: dict = {}
    format: str = "ass"   # ass | srt | vtt


@router.post("/api/captions")
def api_captions(body: CaptionsIn):
    clip = body.clip or {}
    words = [tuple(w) for w in (clip.get("words") or [])]
    if not words:
        return JSONResponse(
            {"error": "Is clip ke liye word timing nahi hai — timed SRT/VTT upload karo."},
            status_code=400)
    fmt = (body.format or "ass").lower()
    try:
        if fmt == "srt":
            text, ctype, ext = capmod.to_srt(words), "text/plain", "srt"
        elif fmt == "vtt":
            text, ctype, ext = capmod.to_vtt(words), "text/vtt", "vtt"
        else:
            text, ctype, ext = capmod.to_ass_karaoke(words), "text/plain", "ass"
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    cid = re.sub(r"[^A-Za-z0-9_-]+", "-", clip.get("id", "clip")).strip("-") or "clip"
    return Response(
        content=text.encode("utf-8"),
        media_type=f"{ctype}; charset=utf-8",
        headers={"Content-Disposition":
                 f'attachment; filename="tukra-{cid}.{ext}"'},
    )


@router.post("/api/render")
async def api_render(clip_json: str = Form(""), video: UploadFile = File(None)):
    """Render a vertical MP4 with burned karaoke captions (needs ffmpeg)."""
    import json as jsonlib
    if not rendermod.available():
        return JSONResponse(
            {"error": "MP4 render is server par available nahi (ffmpeg missing). "
                      "ASS/SRT download karke CapCut/VN mein lagao — 2 minute ka kaam."},
            status_code=200)
    if video is None:
        return JSONResponse({"error": "Video file upload karo."}, status_code=400)
    try:
        clip = jsonlib.loads(clip_json or "{}")
    except Exception:
        return JSONResponse({"error": "Clip data invalid hai."}, status_code=400)
    words = [tuple(w) for w in (clip.get("words") or [])]
    if not words or clip.get("start") is None:
        return JSONResponse(
            {"error": "Render ke liye timed clip chahiye (SRT/VTT wala)."},
            status_code=400)
    data = await video.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return JSONResponse(
            {"error": f"Video {MAX_UPLOAD_MB}MB se chhoti honi chahiye."},
            status_code=400)
    tmpdir = tempfile.mkdtemp(prefix="tukra-")
    try:
        in_path = os.path.join(tmpdir, "in" + os.path.splitext(video.filename or "")[1])
        with open(in_path, "wb") as f:
            f.write(data)
        ass_path = os.path.join(tmpdir, "caps.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(capmod.to_ass_karaoke(words))
        out_path = os.path.join(tmpdir, "clip.mp4")
        _ok, err = rendermod.render_clip(in_path, clip["start"], clip["end"],
                                         ass_path, out_path)
        if err:
            return JSONResponse({"error": err}, status_code=200)
        with open(out_path, "rb") as f:
            mp4 = f.read()
        cid = re.sub(r"[^A-Za-z0-9_-]+", "-", clip.get("id", "clip")).strip("-")
        return Response(content=mp4, media_type="video/mp4",
                        headers={"Content-Disposition":
                                 f'attachment; filename="tukra-{cid or "clip"}.mp4"'})
    finally:
        for p in (os.path.join(tmpdir, "in" + os.path.splitext(video.filename or "")[1]),
                  os.path.join(tmpdir, "caps.ass"),
                  os.path.join(tmpdir, "clip.mp4")):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


@router.post("/api/transcribe")
async def api_transcribe(video: UploadFile = File(None)):
    """Optional server transcription (only where faster-whisper exists)."""
    if not transmod.available():
        ok, err = transmod.transcribe("/nonexistent")
        return JSONResponse({"error": err}, status_code=200)
    if video is None:
        return JSONResponse({"error": "Audio/video file upload karo."},
                            status_code=400)
    data = await video.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return JSONResponse({"error": f"File {MAX_UPLOAD_MB}MB se chhoti ho."},
                            status_code=400)
    tmpdir = tempfile.mkdtemp(prefix="tukra-tr-")
    in_path = os.path.join(tmpdir, "in" + os.path.splitext(video.filename or "")[1])
    try:
        with open(in_path, "wb") as f:
            f.write(data)
        segments, err = transmod.transcribe(in_path)
        if err:
            return JSONResponse({"error": err}, status_code=200)
        srt = ""
        for n, (s, e, t) in enumerate(segments, 1):
            srt += f"{n}\n{capmod.srt_time(s)} --> {capmod.srt_time(e)}\n{t}\n\n"
        return JSONResponse({"srt": srt, "segments": len(segments)})
    finally:
        try:
            os.remove(in_path)
            os.rmdir(tmpdir)
        except OSError:
            pass
