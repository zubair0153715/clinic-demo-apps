"""Tukra transcription — optional faster-whisper path.

Transcription only runs when faster-whisper is importable (VM/dev machines).
On hosts without it (e.g. the free-tier container), this returns an honest
error and the UI asks for a transcript/SRT instead — the rest of Tukra
(highlight detection, captions, clip pack) works fully without it.
"""
import os


def available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def transcribe(audio_path, model_size="tiny", language=None):
    """Transcribe audio/video to [(start, end, text)] word-agnostic segments.

    Returns (segments, error). Segments are line-level; word timing for
    karaoke captions is derived proportionally in captions.py.
    """
    if not available():
        return None, ("Auto-transcript is server par available nahi hai "
                       "(faster-whisper installed nahi). Transcript ya SRT "
                       "paste karo — baqi sab kaam karega.")
    if not os.path.isfile(audio_path):
        return None, "Audio file nahi mili."
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(audio_path, language=language,
                                           vad_filter=True)
        out = [(round(s.start, 2), round(s.end, 2), s.text.strip())
               for s in segments if s.text.strip()]
    except Exception as e:
        return None, f"Transcription fail hui: {type(e).__name__}."
    if not out:
        return None, "Audio mein koi speech nahi mili."
    return out, None
