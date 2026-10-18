"""Knowledge-base engine: PDF -> text -> chunks -> BM25 index.

Pure-Python, no GPU, no embeddings. The index JSON is built on the VM
(build_kb.py) and ships inside the app package so it survives deploys.
Runtime uploads are indexed in memory + saved to data/ (lost on redeploy
unless rebuilt — documented in README).
"""
import json
import logging
import re
import threading
from pathlib import Path

log = logging.getLogger("pharma_ai.kb")

# NOTE: must NOT live under a directory named "data/" — the repo .gitignore
# excludes "data/" and the FastAPI Cloud deploy packaging respects it,
# so kb.json would silently never ship. "kbdata/" is not ignored.
DATA_DIR = Path(__file__).parent / "kbdata"
UPLOADS_DIR = DATA_DIR / "uploads"
KB_PATH = DATA_DIR / "kb.json"

CHUNK_WORDS = 500
CHUNK_OVERLAP = 60
CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+(\d+)\s*[.\-]?\s*(.+?)\s*$", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1]


def extract_pages(pdf_path):
    """Return list of (page_no_1based, text)."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    out = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        out.append((i + 1, txt))
    return out


def chunk_document(doc_id, doc_title, pages):
    """Split pages into ~500-word overlapping chunks with chapter labels."""
    chunks = []
    section = "Front matter"
    buf_words = []       # (word, page_no)
    buf_section = section
    buf_page_start = None

    def flush():
        nonlocal buf_words, buf_section, buf_page_start
        if not buf_words:
            return
        text = " ".join(w for w, _ in buf_words)
        chunks.append({
            "doc_id": doc_id,
            "doc_title": doc_title,
            "section": buf_section,
            "page_start": buf_page_start,
            "page_end": buf_words[-1][1],
            "text": text,
        })
        # overlap: keep last CHUNK_OVERLAP words for next chunk
        keep = buf_words[-CHUNK_OVERLAP:] if len(buf_words) > CHUNK_OVERLAP else []
        buf_words = keep
        buf_page_start = keep[0][1] if keep else None

    for page_no, text in pages:
        for line in text.splitlines():
            m = CHAPTER_RE.match(line.strip())
            if m and len(line.strip()) < 120:
                # new chapter -> flush current buffer under old section
                if buf_words:
                    flush()
                    buf_words, buf_page_start = [], None
                section = f"Chapter {m.group(1)}: {m.group(2).strip()}"
                buf_section = section
                continue
            words = line.split()
            if not words:
                continue
            if buf_page_start is None:
                buf_page_start = page_no
                buf_section = section
            buf_words.extend((w, page_no) for w in words)
            while len(buf_words) >= CHUNK_WORDS:
                # flush a full chunk, keep overlap
                text = " ".join(w for w, _ in buf_words[:CHUNK_WORDS])
                chunks.append({
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "section": buf_section,
                    "page_start": buf_page_start,
                    "page_end": buf_words[CHUNK_WORDS - 1][1],
                    "text": text,
                })
                buf_words = buf_words[CHUNK_WORDS - CHUNK_OVERLAP:]
                buf_page_start = buf_words[0][1] if buf_words else None
                buf_section = section
    flush()
    return chunks


class KnowledgeBase:
    def __init__(self):
        self._lock = threading.RLock()
        self.docs = []     # [{doc_id, title, source, pages, chunks}]
        self.chunks = []   # flat list
        self._bm25 = None
        self._tokenized = []

    # ---------- persistence ----------
    def load(self):
        with self._lock:
            if KB_PATH.exists():
                try:
                    data = json.loads(KB_PATH.read_text(encoding="utf-8"))
                    self.docs = data.get("docs", [])
                    self.chunks = data.get("chunks", [])
                    log.info("pharma_ai KB loaded: %d docs, %d chunks",
                             len(self.docs), len(self.chunks))
                except Exception as e:
                    log.warning("pharma_ai KB load failed: %s", e)
            self._rebuild_index()

    def save(self):
        with self._lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            KB_PATH.write_text(json.dumps(
                {"docs": self.docs, "chunks": self.chunks},
                ensure_ascii=False), encoding="utf-8")

    # ---------- indexing ----------
    def _rebuild_index(self):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            log.error("rank_bm25 not installed — search disabled")
            self._bm25 = None
            return
        self._tokenized = [_tokenize(c["text"]) for c in self.chunks]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    def add_document(self, doc_id, title, source, pages):
        """Chunk + index one document's extracted pages. Returns chunk count."""
        with self._lock:
            self.docs = [d for d in self.docs if d["doc_id"] != doc_id]
            self.chunks = [c for c in self.chunks if c["doc_id"] != doc_id]
            chunks = chunk_document(doc_id, title, pages)
            self.docs.append({"doc_id": doc_id, "title": title,
                              "source": source,
                              "pages": pages[-1][0] if pages else 0,
                              "chunks": len(chunks)})
            self.chunks.extend(chunks)
            self._rebuild_index()
            return len(chunks)

    def ingest_pdf(self, pdf_path, doc_id, title, source="upload"):
        pages = extract_pages(Path(pdf_path))
        n = self.add_document(doc_id, title, source, pages)
        self.save()
        return n

    # ---------- retrieval ----------
    def search(self, query, top_k=5):
        with self._lock:
            if not self._bm25 or not self.chunks:
                return []
            scores = self._bm25.get_scores(_tokenize(query))
            ranked = sorted(range(len(scores)), key=lambda i: scores[i],
                            reverse=True)[:top_k]
            out = []
            for i in ranked:
                if scores[i] <= 0:
                    continue
                c = dict(self.chunks[i])
                c["score"] = round(float(scores[i]), 3)
                out.append(c)
            return out

    def doc_list(self):
        with self._lock:
            return [dict(d) for d in self.docs]


KB = KnowledgeBase()
