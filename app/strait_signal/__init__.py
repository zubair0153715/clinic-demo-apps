"""Strait Signal — Hormuz dark-fleet / STS-candidate collector.

Runs inside the clinic-demo FastAPI app as background tasks. The AISStream
API key is read ONLY from the AISSTREAM_API_KEY environment variable (a
platform secret set in the FastAPI Cloud dashboard). The key is NEVER
printed, logged, or written to any file. If the key is unset, the collector
stays idle and retries every 5 minutes; the app keeps serving normally.

Detected events are candidates only — never sanctions findings.
"""
