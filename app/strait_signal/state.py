"""Shared in-memory state for Strait Signal.

Single event loop, so plain structures are safe (no threads). Events live in
memory with a cap; container restarts lose them (documented — container
SQLite is wiped on deploy, so nothing durable is assumed).
"""

import threading
from collections import deque
from datetime import datetime, timezone

MAX_BUFFER = 20000          # raw envelopes kept in memory
MAX_EVENTS_PER_KIND = 200   # cap per event list


def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


class StraitSignalState:
    def __init__(self):
        self.status = "idle"          # idle | streaming | backoff
        self.key_set = False          # True only if env var is non-empty
        self.started_at = utcnow_iso()
        self.messages_seen = 0
        self.vessel_mmsis = set()
        self.last_message_at = None
        self.last_event_at = None
        self.reconnect_count = 0
        self.consecutive_failures = 0
        self.last_error = None        # sanitized, never contains the key
        self.buffer = deque(maxlen=MAX_BUFFER)
        self.events = {
            "gap_events": [],
            "sts_candidates": [],
            "generated_at_utc": None,
            "messages_read": 0,
            "position_reports_kept": 0,
            "vessels_seen": 0,
        }
        self._lock = threading.Lock()

    def status_payload(self):
        return {
            "collector": "strait_signal",
            "status": self.status,
            "key_set": self.key_set,
            "started_at_utc": self.started_at,
            "messages_seen": self.messages_seen,
            "vessels_seen": len(self.vessel_mmsis),
            "last_message_at_utc": self.last_message_at,
            "last_event_at_utc": self.last_event_at,
            "reconnect_count": self.reconnect_count,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "buffer_size": len(self.buffer),
            "events_count": len(self.events["gap_events"])
            + len(self.events["sts_candidates"]),
            "events_generated_at_utc": self.events["generated_at_utc"],
        }


STATE = StraitSignalState()
