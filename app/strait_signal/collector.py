"""AISStream collector + periodic detection, as FastAPI lifespan tasks.

Key handling: the API key is read ONLY from os.environ.get
("AISSTREAM_API_KEY") each retry cycle. It is NEVER printed, logged, or
written to any file. If unset, the collector stays idle and retries
every 5 minutes; the app keeps serving normally.

Resilience: every failure backs off (5s doubling to 300s cap) and the
task never raises out of its loop, so a bad key, a network outage, or an
AISStream-side close can never crash the app. On container restart the
lifespan simply starts the task again — the key comes from the platform
secret env var, not from any file.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from . import detector
from .state import STATE, MAX_EVENTS_PER_KIND

log = logging.getLogger("strait_signal.collector")

STREAM_URL = "wss://stream.aisstream.io/v0/stream"
# Strait of Hormuz + Gulf of Oman approach. Same corridor as the local client.
BBOX = [[27.5, 55.0], [25.0, 59.5]]
MESSAGE_TYPES = [
    "PositionReport",
    "ShipStaticData",
    "StaticDataReport",
    "StandardClassBPositionReport",
    "ExtendedClassBPositionReport",
]

KEY_MISSING_RETRY_S = 300        # 5 min
DETECT_INTERVAL_S = 900          # 15 min
MAX_JSONL_BYTES = 50 * 1024 * 1024

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "strait_signal"
JSONL_PATH = DATA_DIR / "ais_raw.jsonl"


def _sanitize_error(exc):
    """Short error string guaranteed free of any secret material."""
    text = str(exc)[:200]
    return text or exc.__class__.__name__


def _rotate_jsonl_if_needed():
    try:
        if JSONL_PATH.exists() and JSONL_PATH.stat().st_size > MAX_JSONL_BYTES:
            backup = JSONL_PATH.with_suffix(".jsonl.1")
            if backup.exists():
                backup.unlink()
            JSONL_PATH.rename(backup)
            log.info("strait_signal: rotated ais_raw.jsonl (over 50MB)")
    except Exception as exc:  # noqa: BLE001 - rotation is best-effort
        log.warning("strait_signal: jsonl rotation failed: %s", _sanitize_error(exc))


def _append_jsonl(envelope):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_jsonl_if_needed()
        with open(JSONL_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(envelope) + "\n")
    except Exception as exc:  # noqa: BLE001 - persistence is best-effort
        log.warning("strait_signal: jsonl append failed: %s", _sanitize_error(exc))


def _record(envelope):
    meta = envelope.get("MetaData") or {}
    mmsi = str(meta.get("MMSI", ""))
    STATE.buffer.append(envelope)
    STATE.messages_seen += 1
    if mmsi:
        STATE.vessel_mmsis.add(mmsi)
    STATE.last_message_at = datetime.now(timezone.utc).isoformat()
    _append_jsonl(envelope)


async def _stream_once(api_key):
    """One connection attempt. Returns on close/error; never raises."""
    import websockets  # imported here so the app boots without the dep
    async with websockets.connect(STREAM_URL, max_size=4 * 1024 * 1024) as ws:
        # Subscribe within 3 seconds of connecting. The key travels only
        # inside this message; it is never logged.
        await ws.send(json.dumps({
            "APIKey": api_key,
            "BoundingBoxes": [BBOX],
            "FilterMessageTypes": MESSAGE_TYPES,
        }))
        log.info("strait_signal: subscribed to AISStream (Hormuz bbox)")
        STATE.status = "streaming"
        STATE.consecutive_failures = 0
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
            except asyncio.TimeoutError:
                continue
            envelope = json.loads(raw)
            _record(envelope)


async def run_forever():
    """Lifespan task: collect forever, idle without a key, never crash."""
    backoff = 5
    while True:
        try:
            api_key = os.environ.get("AISSTREAM_API_KEY") or ""
            STATE.key_set = bool(api_key)
            if not api_key:
                STATE.status = "idle"
                log.info("strait_signal: AISSTREAM_API_KEY not set — "
                         "collector idle, retry in 5 min")
                await asyncio.sleep(KEY_MISSING_RETRY_S)
                continue
            STATE.status = "streaming"
            await _stream_once(api_key)
            # _stream_once returned = connection closed; treat as a failure.
            raise ConnectionError("AISStream connection closed")
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - collector must never die
            STATE.status = "backoff"
            STATE.consecutive_failures += 1
            STATE.reconnect_count += 1
            STATE.last_error = _sanitize_error(exc)
            log.warning("strait_signal: collector error (%s); reconnecting in %ss",
                        STATE.last_error, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 300)


async def detect_forever():
    """Lifespan task: re-run detection over the buffer every 15 minutes."""
    while True:
        try:
            await asyncio.sleep(DETECT_INTERVAL_S)
            payload = detector.detect_from_envelopes(list(STATE.buffer))
            STATE.events = {
                "gap_events": payload["gap_events"][-MAX_EVENTS_PER_KIND:],
                "sts_candidates": payload["sts_candidates"][-MAX_EVENTS_PER_KIND:],
                "generated_at_utc": payload["generated_at_utc"],
                "messages_read": payload["messages_read"],
                "position_reports_kept": payload["position_reports_kept"],
                "vessels_seen": payload["vessels_seen"],
            }
            if payload["gap_events"] or payload["sts_candidates"]:
                STATE.last_event_at = datetime.now(timezone.utc).isoformat()
                log.info("strait_signal: detection found %d gap + %d STS candidates",
                         len(payload["gap_events"]), len(payload["sts_candidates"]))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - detection must never die
            log.warning("strait_signal: detection failed: %s", _sanitize_error(exc))
