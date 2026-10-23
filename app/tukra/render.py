"""Tukra MP4 rendering via ffmpeg (when available).

Renders one vertical 1080x1920 clip: cuts the segment, center-crops to 9:16,
burns the karaoke ASS captions. Pure function over files; the route checks
capabilities() first and returns an honest error where ffmpeg is missing.
"""
import os
import shutil
import subprocess


def available():
    return shutil.which("ffmpeg") is not None


def render_clip(input_video, start, end, ass_path, out_path,
                width=1080, height=1920, timeout=300):
    """Render a vertical captioned clip. Returns (out_path, error)."""
    if not available():
        return None, "ffmpeg is server par available nahi — ASS/SRT download karo."
    for p, name in ((input_video, "video"), (ass_path, "ASS file")):
        if not os.path.isfile(p):
            return None, f"{name} nahi mili: {p}"
    dur = float(end) - float(start)
    if dur <= 0:
        return None, "Clip ka duration invalid hai."
    vf = (
        f"crop=ih*9/16:ih,"
        f"scale={width}:{height},"
        f"subtitles='{ass_path}'"
    )
    cmd = ["ffmpeg", "-y",
           "-ss", str(start), "-t", str(round(dur, 2)),
           "-i", input_video,
           "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-c:a", "aac", "-movflags", "+faststart",
           out_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "Render timeout — lambi clip hai, chhoti karke try karo."
    if proc.returncode != 0 or not os.path.isfile(out_path):
        tail = (proc.stderr or "")[-400:]
        return None, f"ffmpeg fail hua: {tail}"
    return out_path, None
