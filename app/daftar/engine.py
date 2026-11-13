# -*- coding: utf-8 -*-
"""Daftar engine — free AI study notebook (NotebookLM / Gemini Notebook
gap build).

Pure, deterministic logic. No network, no storage, no key needed.

What this engine does (all testable exactly):

* Source validation — a source is text the USER pasted or uploaded.
  Max 50,000 words per source, min 20 words, max 50 sources per
  notebook. Empty, too-short and too-long sources are refused with
  an honest error, never silently truncated.
* Chunking — word-based chunks (200 words, 40-word overlap) with
  stable ids like "S1-C3". Chunk ids never change for the same
  source text, so citations stay valid.
* Retrieval — BM25 ranking over chunks (rank-bm25, already a
  clinic-demo dependency). Deterministic: the same query over the
  same chunks always returns the same order.
* Citation checking — every AI citation quote must appear
  WORD-FOR-WORD inside the cited chunk. An answer whose quotes are
  invented is refused. This is the checkable-grounding gap
  NotebookLM leaves open (its audio product carries no citations
  at all, and a 300-document study found it hallucinated in 13%
  of outputs — Hagar et al., 2025).
* PDF extraction — pypdf text extraction. Scanned/image PDFs with
  no text layer return the honest "no text found" error.
* AI-output validators — chat answers, flashcards, quizzes, audio
  scripts and study guides must carry every field, cite only
  chunks that exist, and (for quizzes) exactly one correct option
  out of four unique options.
* Export — flashcards to CSV with correct quoting; notebook
  export/import as JSON with the same limits re-checked on import.
* Demo source — a short, standard-textbook passage on
  photosynthesis, so chat, audio and the study kit can be tried
  immediately. Every fact in it is standard textbook material
  (see the gap report 2026-11-13-daftar.md).

Nothing here is NotebookLM's property: chunking, BM25, CSV export
and photosynthesis facts are public knowledge, and every line of
code is original.
"""

import csv
import io
import json
import re

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - rank-bm25 is a declared dep
    BM25Okapi = None

LANGUAGES = ["en", "roman", "ur"]

MAX_SOURCE_WORDS = 50000
MIN_SOURCE_WORDS = 20
MAX_SOURCES_PER_NOTEBOOK = 50
CHUNK_WORDS = 200
CHUNK_OVERLAP = 40
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
RETRIEVE_TOP_K = 5

LANGUAGE_NAMES = {
    "en": "English",
    "roman": "Roman-Urdu",
    "ur": "Urdu",
}


def _norm_ws(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def word_count(text):
    """Word count of a text (whitespace split)."""
    return len((text or "").split())


def tokenize(text):
    """Lowercase word tokens for BM25. Deterministic."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def reading_time_minutes(words, wpm=200):
    """Whole minutes to read `words` at `wpm` (default 200 wpm)."""
    if not isinstance(words, int) or words <= 0:
        return 0
    return max(1, -(-words // wpm))


# --- sources ----------------------------------------------------------------

def validate_source(title, text):
    """Validate one user source. Returns (clean, error) where clean is
    {"title": str, "text": str, "words": int}."""
    title = _norm_ws(title)
    if not title:
        return None, "Source ka naam dein."
    if len(title) > 120:
        return None, "Source ka naam 120 harf se chhota rakhein."
    text = (text or "").strip()
    if not text:
        return None, "Source khaali hai — kuch text dein."
    if len(text.encode("utf-8", "ignore")) > MAX_TEXT_BYTES:
        return None, "Source 2 MB se bara hai — chhota text dein."
    words = word_count(text)
    if words < MIN_SOURCE_WORDS:
        return None, (f"Source bohat chhota hai ({words} lafz) — "
                      f"kam se kam {MIN_SOURCE_WORDS} lafz dein.")
    if words > MAX_SOURCE_WORDS:
        return None, (f"Source bohat bara hai ({words:,} lafz) — "
                      f"zyada se zyada {MAX_SOURCE_WORDS:,} lafz.")
    return {"title": title, "text": text, "words": words}, None


def validate_sources(sources):
    """Validate a list of raw source dicts. Returns
    (clean_list, error)."""
    if not isinstance(sources, list) or not sources:
        return None, "Kam se kam ek source dein."
    if len(sources) > MAX_SOURCES_PER_NOTEBOOK:
        return None, (f"Zyada se zyada {MAX_SOURCES_PER_NOTEBOOK} "
                      "sources — NotebookLM free bhi 50 deta hai.")
    clean = []
    seen_titles = set()
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            return None, f"Source {i + 1} samajh nahi aaya."
        one, err = validate_source(src.get("title", ""),
                                   src.get("text", ""))
        if err:
            return None, f"Source {i + 1}: {err}"
        key = one["title"].lower()
        if key in seen_titles:
            return None, f"Do sources ka naam aik jaisa hai: {one['title']}"
        seen_titles.add(key)
        one["id"] = f"S{i + 1}"
        clean.append(one)
    return clean, None


# --- chunking ----------------------------------------------------------------

def chunk_text(text, source_id, chunk_words=CHUNK_WORDS,
               overlap=CHUNK_OVERLAP):
    """Split text into overlapping word chunks. Returns a list of
    {"id", "source_id", "index", "text", "start_word", "end_word"}.
    Chunk ids are stable: S<source>-C<index>."""
    words = (text or "").split()
    if not words:
        return []
    step = max(1, chunk_words - overlap)
    chunks = []
    idx = 1
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_words)
        chunks.append({
            "id": f"{source_id}-C{idx}",
            "source_id": source_id,
            "index": idx,
            "text": " ".join(words[start:end]),
            "start_word": start + 1,
            "end_word": end,
        })
        idx += 1
        if end >= len(words):
            break
        start += step
    return chunks


def chunk_sources(sources):
    """Chunk every validated source. `sources` is the clean list from
    validate_sources. Returns (chunks, error)."""
    chunks = []
    for src in sources:
        chunks.extend(chunk_text(src["text"], src["id"]))
    if not chunks:
        return None, "Chunk banane ke liye text nahi mila."
    return chunks, None


def find_chunk(chunks, chunk_id):
    for ch in chunks or []:
        if ch.get("id") == chunk_id:
            return ch
    return None


def sample_chunks(chunks, max_chunks=12):
    """Evenly sample at most `max_chunks` from a long chunk list, so
    a study kit / audio script stays inside a bounded AI context
    while still covering the whole source. Returns the sampled list
    (in original order)."""
    if not isinstance(chunks, list) or not chunks:
        return []
    if not isinstance(max_chunks, int) or max_chunks < 1:
        return []
    if len(chunks) <= max_chunks:
        return list(chunks)
    # Even sampling that always includes the first AND the last
    # chunk, so the whole source stays covered.
    picked = []
    for i in range(max_chunks):
        idx = round(i * (len(chunks) - 1) / (max_chunks - 1))
        if not picked or picked[-1] is not chunks[idx]:
            picked.append(chunks[idx])
    return picked


# --- retrieval ----------------------------------------------------------------

def retrieve(query, chunks, top_k=RETRIEVE_TOP_K):
    """BM25-rank the chunks for `query`. Returns
    (ranked_chunks, error). Ranked chunks carry a "score" (float).
    Deterministic for the same inputs."""
    if BM25Okapi is None:
        return None, "Retrieval engine mojood nahi (rank-bm25)."
    query = _norm_ws(query)
    if not query:
        return None, "Sawal khaali hai."
    if not chunks:
        return None, "Pehle sources dein."
    if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
        return None, "top_k 1–20 ke darmiyan hona chahiye."
    tokens = [tokenize(ch["text"]) for ch in chunks]
    bm25 = BM25Okapi(tokens)
    scores = bm25.get_scores(tokenize(query))
    if max(scores) <= 0:
        # Tiny-corpus quirk: with very few chunks, BM25 IDF can be
        # zero for every term (a term in half the docs has IDF
        # log(1) = 0). Fall back to plain token-overlap ranking so
        # retrieval still works on a 1-2 source notebook. Same
        # determinism: overlap desc, then chunk order.
        qtokens = set(tokenize(query))
        overlap = [len(qtokens & set(t)) for t in tokens]
        order = sorted(range(len(chunks)),
                       key=lambda i: (-overlap[i], i))
        ranked = []
        for i in order[:top_k]:
            if overlap[i] <= 0:
                continue
            ch = dict(chunks[i])
            ch["score"] = float(overlap[i])
            ranked.append(ch)
        return ranked, None
    order = sorted(range(len(chunks)), key=lambda i: (-scores[i], i))
    ranked = []
    for i in order[:top_k]:
        if scores[i] <= 0:
            continue
        ch = dict(chunks[i])
        ch["score"] = round(float(scores[i]), 4)
        ranked.append(ch)
    if not ranked:
        return [], None
    return ranked, None


def search_chunks(query, chunks, top_k=RETRIEVE_TOP_K):
    """Keyword search across chunks (no key, no AI). Same BM25 as
    retrieve, plus a plain substring fallback so a query that
    matches no token still finds an exact phrase."""
    ranked, err = retrieve(query, chunks, top_k=top_k)
    if err:
        return None, err
    if ranked:
        return ranked, None
    q = _norm_ws(query).lower()
    hits = [ch for ch in chunks if q in ch["text"].lower()]
    return hits[:top_k], None


# --- citation checking ---------------------------------------------------------

def quote_in_chunk(quote, chunk_text):
    """True when the quote appears word-for-word (whitespace
    normalised) inside the chunk text."""
    q = _norm_ws(quote)
    if not q or len(q) < 8:
        return False
    return q in _norm_ws(chunk_text)


def check_citations(citations, chunks):
    """Validate a list of {"chunk_id", "quote"}. Returns
    (clean, error). Every quote must be verbatim in its chunk."""
    if not isinstance(citations, list):
        return None, "Citations list nahi hain."
    clean = []
    for i, cit in enumerate(citations):
        if not isinstance(cit, dict):
            return None, f"Citation {i + 1} samajh nahi aaya."
        cid = cit.get("chunk_id", "")
        quote = cit.get("quote", "")
        ch = find_chunk(chunks, cid)
        if ch is None:
            return None, (f"Citation {i + 1}: chunk {cid!r} mojood "
                          "nahi — AI ne ghalat chunk likha.")
        if not quote_in_chunk(quote, ch["text"]):
            return None, (f"Citation {i + 1}: ye jumla chunk {cid} "
                          "mein lafz-ba-lafz mojood nahi — AI ne "
                          "jumla banaya ho sakta hai.")
        clean.append({"chunk_id": cid, "quote": _norm_ws(quote)})
    return clean, None


# --- PDF extraction --------------------------------------------------------------

def extract_pdf_text(data):
    """Extract text from PDF bytes with pypdf. Returns
    (text, pages, error). Scanned/image PDFs return the honest
    no-text error instead of an empty string."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        return None, 0, "PDF khaali hai."
    if len(data) > MAX_PDF_BYTES:
        return None, 0, "PDF 10 MB se bari hai — chhoti PDF dein."
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, 0, "PDF reader mojood nahi."
    try:
        reader = PdfReader(io.BytesIO(bytes(data)))
        pages = len(reader.pages)
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        text = "\n".join(p for p in parts if p.strip())
    except Exception as exc:
        return None, 0, f"PDF parh nahi sake ({exc})."
    if not _norm_ws(text):
        return None, pages, ("Is PDF mein text nahi mila — shayad ye "
                             "scanned/image PDF hai. Text wali PDF ya "
                             "paste kiya hua text istemal karein.")
    return text, pages, None


# --- AI-output validators ---------------------------------------------------------

def _bad_str(value, field, max_len=5000):
    return (not isinstance(value, str) or not _norm_ws(value)
            or len(value) > max_len)


def validate_ai_chat(data, chunks):
    """Validate a grounded chat answer. `data` must be
    {"answer": str, "not_found": bool, "citations": [...]}.
    not_found=true allows empty citations; otherwise at least one
    verbatim citation is required."""
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    answer = data.get("answer", "")
    if _bad_str(answer, "answer", 8000):
        return None, "AI ka jawab khaali ya bohat lamba hai."
    not_found = data.get("not_found", False)
    if not isinstance(not_found, bool):
        return None, "'not_found' true ya false hona chahiye."
    citations, err = check_citations(data.get("citations", []), chunks)
    if err:
        return None, err
    if not_found and citations:
        return None, ("AI ne kaha jawab sources mein nahi, phir bhi "
                      "citations diye — mutazaad jawab.")
    if not not_found and not citations:
        return None, ("Jawab mein kam se kam ek citation hona chahiye "
                      "— warna ye AI ki apni baat hai, source ki nahi.")
    return {"answer": _norm_ws(answer), "not_found": not_found,
            "citations": citations, "ai": True}, None


def validate_ai_flashcards(data, chunks):
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    cards = data.get("cards")
    if not isinstance(cards, list) or not 3 <= len(cards) <= 30:
        return None, "Flashcards 3–30 ke darmiyan hone chahiye."
    clean = []
    for i, card in enumerate(cards):
        if not isinstance(card, dict):
            return None, f"Card {i + 1} samajh nahi aaya."
        q = card.get("question", "")
        a = card.get("answer", "")
        if _bad_str(q, "question", 600) or _bad_str(a, "answer", 1200):
            return None, f"Card {i + 1}: sawal ya jawab khaali hai."
        cid = card.get("chunk_id", "")
        if find_chunk(chunks, cid) is None:
            return None, f"Card {i + 1}: chunk {cid!r} mojood nahi."
        clean.append({"question": _norm_ws(q), "answer": _norm_ws(a),
                      "chunk_id": cid})
    return {"cards": clean, "ai": True}, None


def validate_ai_quiz(data, chunks):
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    questions = data.get("questions")
    if not isinstance(questions, list) or not 3 <= len(questions) <= 20:
        return None, "Quiz mein 3–20 sawal hone chahiye."
    clean = []
    for i, item in enumerate(questions):
        if not isinstance(item, dict):
            return None, f"Sawal {i + 1} samajh nahi aaya."
        q = item.get("question", "")
        options = item.get("options")
        correct = item.get("correct")
        explanation = item.get("explanation", "")
        if _bad_str(q, "question", 600):
            return None, f"Sawal {i + 1}: sawal khaali hai."
        if (not isinstance(options, list) or len(options) != 4
                or any(_bad_str(o, "option", 400) for o in options)):
            return None, (f"Sawal {i + 1}: chaar mukhtalif options "
                          "hone chahiye.")
        opts = [_norm_ws(o) for o in options]
        if len(set(o.lower() for o in opts)) != 4:
            return None, (f"Sawal {i + 1}: options aik jaise nahi "
                          "hone chahiye.")
        if not isinstance(correct, int) or not 0 <= correct <= 3:
            return None, (f"Sawal {i + 1}: exactly ek sahi option "
                          "(0–3) batana zaroori hai.")
        if _bad_str(explanation, "explanation", 800):
            return None, f"Sawal {i + 1}: wazahat khaali hai."
        cid = item.get("chunk_id", "")
        if find_chunk(chunks, cid) is None:
            return None, f"Sawal {i + 1}: chunk {cid!r} mojood nahi."
        clean.append({"question": _norm_ws(q), "options": opts,
                      "correct": correct,
                      "explanation": _norm_ws(explanation),
                      "chunk_id": cid})
    return {"questions": clean, "ai": True}, None


def validate_ai_audio(data, chunks):
    """Validate a two-host audio-overview script. `data` must be
    {"style": "brief"|"deep"|"revision", "turns": [{speaker, text,
    chunk_ids}]}. Total words must be 150–3000."""
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    style = data.get("style", "")
    if style not in ("brief", "deep", "revision"):
        return None, "Audio style brief, deep ya revision hona chahiye."
    turns = data.get("turns")
    if not isinstance(turns, list) or not 4 <= len(turns) <= 60:
        return None, "Audio script mein 4–60 turns hone chahiye."
    clean = []
    total_words = 0
    prev = None
    for i, turn in enumerate(turns):
        if not isinstance(turn, dict):
            return None, f"Turn {i + 1} samajh nahi aaya."
        speaker = turn.get("speaker", "")
        text = turn.get("text", "")
        if speaker not in ("A", "B"):
            return None, f"Turn {i + 1}: speaker A ya B hona chahiye."
        if prev is not None and speaker == prev:
            return None, (f"Turn {i + 1}: aik hi host lagatar nahi "
                          "bol sakta — hosts badalte rehne chahiye.")
        prev = speaker
        if _bad_str(text, "text", 2500):
            return None, f"Turn {i + 1}: text khaali hai."
        cids = turn.get("chunk_ids", [])
        if (not isinstance(cids, list) or not cids
                or any(find_chunk(chunks, c) is None for c in cids)):
            return None, (f"Turn {i + 1}: har turn mein kam se kam "
                          "ek mojood chunk ki citation honi chahiye.")
        total_words += word_count(text)
        clean.append({"speaker": speaker, "text": _norm_ws(text),
                      "chunk_ids": list(cids)})
    if not 150 <= total_words <= 3000:
        return None, (f"Audio script {total_words} lafz ki hai — "
                      "150–3000 lafz ke darmiyan honi chahiye.")
    return {"style": style, "turns": clean,
            "total_words": total_words,
            "est_minutes": reading_time_minutes(total_words, wpm=150),
            "ai": True}, None


def validate_ai_guide(data, chunks):
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    points = data.get("key_points")
    if (not isinstance(points, list) or not 3 <= len(points) <= 15
            or any(_bad_str(p, "point", 500) for p in points)):
        return None, "Study guide mein 3–15 key points hone chahiye."
    terms = data.get("terms")
    if (not isinstance(terms, list) or not 3 <= len(terms) <= 20):
        return None, "Study guide mein 3–20 terms hone chahiye."
    clean_terms = []
    for i, term in enumerate(terms):
        if not isinstance(term, dict):
            return None, f"Term {i + 1} samajh nahi aaya."
        name = term.get("term", "")
        definition = term.get("definition", "")
        if _bad_str(name, "term", 200) or _bad_str(definition,
                                                   "definition", 800):
            return None, f"Term {i + 1}: naam ya tareef khaali hai."
        cid = term.get("chunk_id", "")
        if find_chunk(chunks, cid) is None:
            return None, f"Term {i + 1}: chunk {cid!r} mojood nahi."
        clean_terms.append({"term": _norm_ws(name),
                            "definition": _norm_ws(definition),
                            "chunk_id": cid})
    timeline = data.get("timeline", [])
    clean_timeline = []
    if not isinstance(timeline, list):
        return None, "Timeline list honi chahiye."
    for i, item in enumerate(timeline):
        if not isinstance(item, dict):
            return None, f"Timeline {i + 1} samajh nahi aaya."
        if (_bad_str(item.get("event", ""), "event", 300)
                or _bad_str(item.get("when", ""), "when", 200)):
            return None, f"Timeline {i + 1}: event ya waqt khaali hai."
        clean_timeline.append({"event": _norm_ws(item["event"]),
                               "when": _norm_ws(item["when"])})
    return {"key_points": [_norm_ws(p) for p in points],
            "terms": clean_terms, "timeline": clean_timeline,
            "ai": True}, None


# --- export -------------------------------------------------------------------

def flashcards_to_csv(cards):
    """Flashcards list -> CSV text (question, answer, source_chunk).
    Proper quoting via the csv module. Returns (csv_text, error)."""
    if not isinstance(cards, list) or not cards:
        return None, "CSV ke liye kam se kam ek card dein."
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["question", "answer", "source_chunk"])
    for card in cards:
        if not isinstance(card, dict):
            return None, "Card samajh nahi aaya."
        q = card.get("question", "")
        a = card.get("answer", "")
        if not _norm_ws(q) or not _norm_ws(a):
            return None, "Har card mein sawal aur jawab zaroori hai."
        writer.writerow([_norm_ws(q), _norm_ws(a),
                         card.get("chunk_id", "")])
    return buf.getvalue(), None


def export_notebook(notebook):
    """Notebook dict -> JSON text for backup. Re-validates sources."""
    if not isinstance(notebook, dict):
        return None, "Notebook samajh nahi aaya."
    title = _norm_ws(notebook.get("title", ""))
    if not title:
        return None, "Notebook ka naam dein."
    sources, err = validate_sources(notebook.get("sources", []))
    if err:
        return None, err
    payload = {"app": "daftar", "version": 1, "title": title,
               "sources": [{"title": s["title"], "text": s["text"]}
                           for s in sources]}
    return json.dumps(payload, ensure_ascii=False, indent=2), None


def import_notebook(raw):
    """Parse an exported notebook JSON. Returns (notebook, error)."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None, "Ye Daftar backup file nahi lagti."
    if not isinstance(data, dict) or data.get("app") != "daftar":
        return None, "Ye Daftar backup file nahi lagti."
    title = _norm_ws(data.get("title", ""))
    if not title:
        return None, "Backup mein notebook ka naam nahi hai."
    sources, err = validate_sources(data.get("sources", []))
    if err:
        return None, f"Backup mein masla: {err}"
    return {"title": title, "sources": sources}, None


# --- demo source ----------------------------------------------------------------

DEMO_SOURCE = {
    "title": "Photosynthesis — demo source",
    "text": (
        "Photosynthesis is the process by which green plants, algae and "
        "some bacteria convert light energy into chemical energy stored "
        "in sugars. The overall equation is 6CO2 + 6H2O + light energy "
        "-> C6H12O6 + 6O2. Carbon dioxide enters the leaf through "
        "stomata, tiny pores mostly on the underside of the leaf, while "
        "water is absorbed by the roots and carried up through the xylem. "
        "Oxygen is released as a by-product.\n\n"
        "Photosynthesis has two stages. The light-dependent reactions "
        "take place in the thylakoid membrane of the chloroplast. "
        "Chlorophyll and other pigments absorb light, water is split, "
        "oxygen is released, and the energy is stored as ATP and NADPH. "
        "The light-independent reactions, the Calvin cycle, take place "
        "in the stroma of the chloroplast. There, the enzyme Rubisco "
        "fixes carbon dioxide onto a five-carbon molecule called RuBP, "
        "and the resulting molecules are converted into sugar using the "
        "ATP and NADPH made in the first stage.\n\n"
        "Chlorophyll a is the main pigment. It absorbs red light around "
        "680 nanometres and blue light around 430 nanometres, and it "
        "reflects green light, which is why leaves look green. "
        "Chlorophyll b and carotenoids are accessory pigments that "
        "broaden the range of light the plant can use and protect it "
        "from damage by excess light.\n\n"
        "Rubisco, short for ribulose-1,5-bisphosphate carboxylase/"
        "oxygenase, is the most abundant protein on Earth. It is also "
        "a slow enzyme, so plants make very large amounts of it. "
        "Rubisco can also bind oxygen instead of carbon dioxide, a "
        "wasteful side reaction called photorespiration. When stomata "
        "close on hot, dry days to save water, carbon dioxide inside "
        "the leaf falls, oxygen rises, and photorespiration increases, "
        "which lowers the efficiency of photosynthesis.\n\n"
        "The rate of photosynthesis depends on light intensity, carbon "
        "dioxide concentration and temperature. At low light the rate "
        "rises with light intensity, then levels off when another "
        "factor becomes limiting. This is the principle of limiting "
        "factors: the slowest factor sets the pace of the whole process."
    ),
}


def demo_chunks():
    """Chunk the demo source. Returns the chunk list."""
    clean, _ = validate_sources([DEMO_SOURCE])
    chunks, _ = chunk_sources(clean)
    return chunks
