"""Plain-language explanation layer for SecureAPK findings.

v1: curated static explanations per finding type (honest, no fake AI).
Optional: if GEMINI_API_KEY is set, a single batched Gemini pass rewrites the
plain explanations; any failure falls back silently to the static text.
"""
import json
import os
import urllib.request

# title-keyword -> (plain_what, plain_why)
EXPLAIN = [
    (("debuggable",),
     "The app was built in debug mode — like leaving your house key under the doormat.",
     "Anyone with a USB cable can attach a debugger, read the app's memory, and steal secrets or bypass checks."),
    (("allowbackup", "backup enabled"),
     "The app lets Android back up its private data.",
     "On older devices (or with user consent) someone can pull the app's stored data — including login tokens — off the phone."),
    (("cleartext",),
     "The app is allowed to send data without encryption (plain HTTP).",
     "Unencrypted traffic can be read or modified by anyone on the same network — logins, tokens and personal data leak."),
    (("targetsdk", "outdated"),
     "The app targets an old Android version.",
     "Old targets miss years of built-in security hardening; newer Android versions protect users by default."),
    (("permission",),
     "The app requests a powerful permission.",
     "Each dangerous permission widens what the app *could* do with your data. If the feature doesn't truly need it, it's unnecessary risk."),
    (("exported",),
     "A part of the app is visible to other apps on the phone.",
     "Exported components can be triggered by malicious apps. They should be locked down unless they genuinely need to be public."),
    (("secret", "api key", "token", "hardcoded"),
     "A secret (API key, token or password) is baked into the app.",
     "Anyone who downloads the app can extract it and abuse the paid service behind it — on your bill."),
    (("http://", "cleartext url"),
     "The app talks to an unencrypted web address.",
     "Same risk as cleartext traffic: readable and tamperable on the network."),
    (("ip address", "public ip"),
     "The app contains a hard-coded server address.",
     "Hard-coded infrastructure is brittle and can reveal your backend to attackers."),
    (("advertising sdk", "tracker", "sdk"),
     "The app bundles third-party advertising/tracking SDKs.",
     "Each SDK shares user data with another company — a privacy and compliance surface you own."),
    (("signed", "signature", "certificate"),
     "Something is off with the app's signature.",
     "The signature proves who built the app. Problems here mean the app can't be trusted as genuine."),
    (("obfuscat",),
     "The code shows signs of obfuscation.",
     "Obfuscation slows down analysis but is not real protection — and it can also hide malicious behavior."),
]

FALLBACK = (
    "Something in the app deserves a closer look.",
    "Review the technical detail and apply the recommended fix.",
)


def explain_finding(title: str, detail: str):
    t = (title + " " + detail).lower()
    for keywords, what, why in EXPLAIN:
        if any(k in t for k in keywords):
            return what, why
    return FALLBACK


def enrich(findings):
    """Add plain-language 'plain_what' / 'plain_why' to each finding dict."""
    out = []
    for f in findings:
        what, why = explain_finding(f.get("title", ""), f.get("detail", ""))
        g = dict(f)
        g["plain_what"] = what
        g["plain_why"] = why
        out.append(g)
    return out


def gemini_rewrite(findings):
    """Optional batched Gemini pass. Returns findings unchanged on any failure."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or not findings:
        return findings
    try:
        items = [{"title": f.get("title", ""), "detail": f.get("detail", "")[:300]}
                 for f in findings[:25]]
        prompt = (
            "You are a mobile-security explainer. For each finding below, write ONE short "
            "plain-English sentence a non-technical app owner understands: what it means for "
            "their users. No jargon, no markdown, max 25 words each. "
            "Return ONLY a JSON array of strings, same order.\n\n"
            + json.dumps(items))
        body = json.dumps(
            {"contents": [{"parts": [{"text": prompt}]}],
             "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}}).encode()
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + key,
            data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # extract JSON array from response
        start, end = text.find("["), text.rfind("]")
        if start < 0 or end < 0:
            return findings
        rewrites = json.loads(text[start:end + 1])
        out = []
        for f, rw in zip(findings, rewrites):
            g = dict(f)
            if isinstance(rw, str) and rw.strip():
                g["plain_what"] = rw.strip()
            out.append(g)
        # findings beyond the rewrite list keep static text
        out.extend(findings[len(rewrites):])
        return out
    except Exception:
        return findings


SEV_COLOR = {"High": "#c0392b", "Medium": "#d68910", "Low": "#1e8449"}
SEV_BG = {"High": "#fdedec", "Medium": "#fef9e7", "Low": "#eafaf1"}
