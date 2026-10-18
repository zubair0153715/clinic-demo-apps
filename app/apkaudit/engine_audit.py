#!/usr/bin/env python3
"""
apk-audit-demo / audit.py
=========================
Automated STATIC security audit of an Android APK -> Markdown report.

Pipeline: androguard (manifest, permissions, dex strings, certs)
          + optional apktool  (--deep: smali-level secret scan)
          + jadx available in tools/ for manual deep-dives.

LEGAL USE ONLY: audit your own apps, apps you have written permission to
test, or open-source sample APKs. No cracking, no piracy, no license bypass.

Usage:
    python audit.py app.apk [-o report.md] [--deep]
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

# --- quieten androguard's very chatty debug logging ---------------------------
try:
    from loguru import logger as _lg
    _lg.remove()
    _lg.add(sys.stderr, level="ERROR")
except Exception:
    pass

from androguard.core.apk import APK
from androguard.core.dex import DEX

NS = "{http://schemas.android.com/apk/res/android}"
TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")

SEVERITY_WEIGHT = {"High": 25, "Medium": 10, "Low": 2}

# http:// URLs that are just XML namespace identifiers, never fetched
URL_NAMESPACE_DENY = (
    "http://schemas.android.com", "http://www.w3.org/", "http://apache.org/xml",
    "http://xml.org/sax", "http://schemas.xmlsoap.org", "http://purl.org",
    "http://java.sun.com", "http://xmlpull.org",
)

# permission -> (severity, why it matters)
DANGEROUS_PERMS = {
    # --- High ---
    "android.permission.READ_SMS": ("High", "can read all SMS incl. OTPs/2FA codes"),
    "android.permission.RECEIVE_SMS": ("High", "can intercept incoming SMS (OTP theft)"),
    "android.permission.SEND_SMS": ("High", "can send SMS (premium-rate fraud)"),
    "android.permission.RECEIVE_WAP_PUSH": ("High", "can intercept WAP push / MMS"),
    "android.permission.RECEIVE_MMS": ("High", "can read MMS messages"),
    "android.permission.READ_CALL_LOG": ("High", "call history is sensitive metadata"),
    "android.permission.WRITE_CALL_LOG": ("High", "can modify call history"),
    "android.permission.PROCESS_OUTGOING_CALLS": ("High", "can see/redirect outgoing calls"),
    "android.permission.BIND_ACCESSIBILITY_SERVICE": ("High", "accessibility = full UI control, classic banker-trojan vector"),
    "android.permission.BIND_DEVICE_ADMIN": ("High", "device-admin can lock/wipe, hard to remove"),
    # --- Medium ---
    "android.permission.ACCESS_FINE_LOCATION": ("Medium", "precise GPS tracking"),
    "android.permission.ACCESS_COARSE_LOCATION": ("Medium", "approximate location tracking"),
    "android.permission.ACCESS_BACKGROUND_LOCATION": ("Medium", "location tracking even when app closed"),
    "android.permission.CAMERA": ("Medium", "can capture photos/video"),
    "android.permission.RECORD_AUDIO": ("Medium", "can record microphone"),
    "android.permission.READ_CONTACTS": ("Medium", "address book harvesting"),
    "android.permission.WRITE_CONTACTS": ("Medium", "can modify address book"),
    "android.permission.READ_PHONE_STATE": ("Medium", "device identifiers / call state"),
    "android.permission.READ_PHONE_NUMBERS": ("Medium", "user's phone number(s)"),
    "android.permission.READ_CALENDAR": ("Medium", "calendar contents"),
    "android.permission.WRITE_CALENDAR": ("Medium", "can alter calendar"),
    "android.permission.BODY_SENSORS": ("Medium", "health sensor data"),
    "android.permission.ACTIVITY_RECOGNITION": ("Medium", "physical activity profiling"),
    "android.permission.REQUEST_INSTALL_PACKAGES": ("Medium", "can install other APKs (dropper risk)"),
    "android.permission.SYSTEM_ALERT_WINDOW": ("Medium", "overlay windows (tapjacking / overlay attacks)"),
    "android.permission.MANAGE_EXTERNAL_STORAGE": ("Medium", "all-files access on shared storage"),
    "android.permission.READ_CALL_LOG": ("High", "call history is sensitive metadata"),
    # --- Low ---
    "android.permission.READ_EXTERNAL_STORAGE": ("Low", "broad read of shared storage"),
    "android.permission.WRITE_EXTERNAL_STORAGE": ("Low", "broad write of shared storage"),
}

# (name, regex, severity, recommendation) — scanned over dex strings (+ smali in --deep)
SECRET_PATTERNS = [
    ("AWS Access Key ID", r"AKIA[0-9A-Z]{16}", "High",
     "Rotate the key immediately; move to server-side or signed short-lived credentials."),
    ("Google API key", r"AIza[0-9A-Za-z\-_]{35}", "High",
     "Restrict the key (Android app + API restrictions) or proxy it server-side."),
    ("Slack token", r"xox[baprs]-[0-9A-Za-z\-]{10,}", "High",
     "Revoke the token; never ship chat-ops tokens in the client."),
    ("GitHub token", r"gh[pousr]_[A-Za-z0-9]{36}", "High",
     "Revoke the token; it may grant repo/org access."),
    ("Private key material", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----", "High",
     "A private key inside the app is compromised by definition — rotate it."),
    ("AWS secret access key", r"(?i)aws.{0,30}['\"][0-9a-zA-Z/+]{40}['\"]", "High",
     "Rotate the key immediately; AWS secret keys must never ship in a client."),
    ("Slack webhook URL", r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}", "High",
     "Revoke the webhook; it lets anyone post into your Slack workspace."),
    ("GitHub fine-grained token", r"github_pat_[A-Za-z0-9_]{22}", "High",
     "Revoke the token; fine-grained PATs can carry broad repo/org scopes."),
    ("Google OAuth client ID", r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com", "High",
     "Client IDs are semi-public, but paired with a leaked secret they enable OAuth abuse — audit usage."),
    ("Stripe live key", r"(?:sk|pk|rk)_live_[0-9a-zA-Z]{16,}", "High",
     "Rotate the key in the Stripe dashboard; a leaked sk_live can move real money."),
    ("Twilio credential", r"(?:AC|SK)[0-9a-fA-F]{32}", "High",
     "Rotate in the Twilio console; leaked SIDs can send SMS/calls on your bill."),
    ("Mailgun API key", r"key-[0-9a-z]{32}", "Medium",
     "Rotate the key; it can send email as your domain."),
    ("Firebase hosting/storage URL", r"[a-z0-9-]+\.(?:firebaseapp\.com|firebasestorage\.googleapis\.com)", "Medium",
     "Check Firebase security rules and storage access controls."),
    ("JWT token", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "High",
     "A signed token in the binary can be replayed — use short expiry and server-side issuance."),
    ("Bearer token", r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}", "Medium",
     "Bearer tokens in the client are extractable — prefer short-lived, scoped tokens."),
    ("Firebase Realtime DB URL", r"https?://[a-z0-9\-]+\.firebaseio\.com", "Medium",
     "Check Firebase security rules — open rules + known URL = readable DB."),
    ("Hardcoded API key / token", r"(?i)(?:api[_-]?key|client[_-]?secret|auth[_-]?token|access[_-]?token)\s*[:=]\s*[\"']([A-Za-z0-9_\-]{12,})[\"']", "Medium",
     "Move secrets server-side; the client is not a safe place for them."),
    ("Hardcoded password", r"(?i)\bpassword\s*[:=]\s*[\"']([^\s\"']{6,})[\"']", "Medium",
     "Remove embedded credentials; use proper auth flows."),
]
PLACEHOLDER_DENY = re.compile(r"^(your|xxx+|test|example|sample|demo|null|none|undefined|123+|abcdef|placeholder|changeme|key[_-]?here)", re.I)

# dex class prefix -> (tracker name, category)
TRACKERS = {
    "Lcom/google/android/gms/ads/": ("Google AdMob", "Advertising"),
    "Lcom/google/android/gms/measurement/": ("Google Analytics/Measurement", "Analytics"),
    "Lcom/google/firebase/": ("Firebase", "Analytics/Crash"),
    "Lcom/facebook/": ("Facebook SDK", "Social/Ads"),
    "Lcom/appsflyer/": ("AppsFlyer", "Attribution"),
    "Lcom/amplitude/": ("Amplitude", "Analytics"),
    "Lcom/mixpanel/": ("Mixpanel", "Analytics"),
    "Lcom/segment/analytics/": ("Segment", "Analytics"),
    "Lio/sentry/": ("Sentry", "Crash reporting"),
    "Lcom/crashlytics/": ("Crashlytics", "Crash reporting"),
    "Lcom/flurry/": ("Flurry", "Analytics"),
    "Lcom/onesignal/": ("OneSignal", "Push"),
    "Lcom/airship/": ("Airship", "Push"),
    "Lcom/branch/": ("Branch", "Deep linking"),
    "Lcom/mopub/": ("MoPub", "Advertising"),
    "Lcom/unity3d/ads/": ("Unity Ads", "Advertising"),
    "Lcom/applovin/": ("AppLovin", "Advertising"),
    "Lcom/chartboost/": ("Chartboost", "Advertising"),
    "Lcom/tapjoy/": ("Tapjoy", "Advertising"),
    "Lcom/ironsource/": ("ironSource", "Advertising"),
    "Lcom/vungle/": ("Vungle/Liftoff", "Advertising"),
    "Lcom/inmobi/": ("InMobi", "Advertising"),
}

URL_RE = re.compile(r"https?://[^\s\"'<>\\]+")
IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b")


def redact(s, keep=4):
    s = str(s)
    return (s[:keep] + "***REDACTED***") if len(s) > keep + 4 else "***REDACTED***"


ENTROPY_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-/+=.]{24,}")
ENTROPY_KW_RE = re.compile(r"(?i)(secret|api[_-]?key|[^a-z]token|password|passwd|credential|auth[_-]?key|private[_-]?key)")


def shannon(s):
    """Shannon entropy in bits/char; random-looking secrets score ~4.5+."""
    if not s:
        return 0.0
    n = len(s)
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def is_private_ip(ip):
    p = [int(x) for x in ip.split(".")]
    return (p[0] == 10 or p[0] == 127 or (p[0] == 192 and p[1] == 168)
            or (p[0] == 172 and 16 <= p[1] <= 31) or ip == "0.0.0.0")

# ---------------------------------------------------------------- analysis ---

def get_dex_list(apk):
    """Return list of raw dex byte-blobs (handles multidex)."""
    try:
        dexes = apk.get_all_dex()
        if dexes:
            return list(dexes)
    except AttributeError:
        pass
    raw = apk.get_dex()
    return [raw] if raw else []


def exported_components(manifest):
    """(tag, name) for components reachable by other apps."""
    out = []
    app = manifest.find("application")
    if app is None:
        return out
    for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
        for el in app.findall(tag):
            name = el.get(NS + "name") or "?"
            exp = el.get(NS + "exported")
            has_if = el.find("intent-filter") is not None
            # targetSdk<31: intent-filter implies exported=true
            if exp == "true" or (exp is None and has_if):
                out.append((tag, name))
    return out


def deep_smali_scan(apk_path):
    """Optional --deep: decode with apktool and grep smali for secrets."""
    apktool = os.path.join(TOOLS_DIR, "apktool.jar")
    if not (os.path.exists(apktool) and shutil.which("java")):
        return {"skipped": "apktool or java not available"}
    tmp = tempfile.mkdtemp(prefix="apk_audit_")
    try:
        r = subprocess.run(
            ["java", "-jar", apktool, "d", "-f", "-o", tmp, apk_path],
            capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return {"skipped": "apktool decode failed: " + (r.stderr or "")[-200:]}
        hits = {}
        for root, _, files in os.walk(tmp):
            for f in files:
                if not f.endswith(".smali"):
                    continue
                try:
                    with open(os.path.join(root, f), errors="ignore") as fh:
                        text = fh.read()
                except OSError:
                    continue
                for name, pat, sev, _rec in SECRET_PATTERNS:
                    for m in re.finditer(pat, text):
                        val = (m.group(1) if m.lastindex else m.group(0)).strip()
                        if len(val) < 6 or not re.search(r"[A-Za-z0-9]{3}", val):
                            continue
                        if PLACEHOLDER_DENY.match(val):
                            continue
                        hits.setdefault(name, set()).add(redact(val))
        return {"hits": {k: sorted(v)[:5] for k, v in hits.items()}}
    except subprocess.TimeoutExpired:
        return {"skipped": "apktool decode timed out"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def analyze(apk_path):
    findings = []
    notes = []

    def add(sev, title, detail, rec):
        findings.append({"severity": sev, "title": title,
                         "detail": detail, "recommendation": rec})

    # ---- file basics ----
    size = os.path.getsize(apk_path)
    sha256 = hashlib.sha256()
    with open(apk_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha256.update(chunk)

    apk = APK(apk_path)
    manifest = apk.get_android_manifest_xml()
    app_el = manifest.find("application")

    info = {
        "file": os.path.basename(apk_path),
        "sha256": sha256.hexdigest(),
        "size_mb": round(size / 1e6, 2),
        "package": apk.get_package(),
        "app_name": apk.get_app_name(),
        "version": f"{apk.get_androidversion_name()} (code {apk.get_androidversion_code()})",
        "min_sdk": apk.get_min_sdk_version(),
        "target_sdk": apk.get_target_sdk_version(),
        "signed": apk.is_signed(),
    }

    # ---- signing cert ----
    try:
        certs = apk.get_certificates() or []
        if certs:
            c = certs[0]
            subj = getattr(getattr(c, "subject", None), "human_friendly", None) or str(getattr(c, "subject", "?"))
            info["cert_subject"] = subj
            for attr in ("not_valid_before", "not_valid_after",
                         "not_valid_before_utc", "not_valid_after_utc"):
                if hasattr(c, attr):
                    info.setdefault("cert_validity", {})[attr.replace("_utc", "")] = str(getattr(c, attr))
        else:
            info["cert_subject"] = "none found"
    except Exception as e:  # never let cert parsing kill the audit
        info["cert_subject"] = f"unreadable ({type(e).__name__})"

    # ---- manifest flags ----
    if app_el is not None:
        if app_el.get(NS + "debuggable") == "true":
            add("High", "App is debuggable",
                "android:debuggable=\"true\" — anyone with adb can attach a debugger and dump memory.",
                "Set debuggable=false for release builds.")
        if app_el.get(NS + "allowBackup") == "true":
            add("Low", "Backup enabled (allowBackup=true)",
                "App data can be pulled via adb backup on older devices / with user consent.",
                "Set allowBackup=false if the app holds sensitive data, or use scoped backup rules.")
        if app_el.get(NS + "usesCleartextTraffic") == "true":
            add("Medium", "Cleartext HTTP traffic allowed",
                "android:usesCleartextTraffic=\"true\" — the app may send data over unencrypted HTTP.",
                "Enforce HTTPS-only via a Network Security Config.")

    # ---- SDK levels ----
    try:
        if info["target_sdk"] and int(info["target_sdk"]) < 30:
            add("Medium", f"Outdated targetSdk ({info['target_sdk']})",
                "Old target SDKs miss years of platform security hardening.",
                "Target a recent SDK (33+).")
        elif info["target_sdk"] and int(info["target_sdk"]) < 33:
            add("Low", f"targetSdk {info['target_sdk']} is aging",
                "Not ancient, but newer targets get stronger defaults.",
                "Consider bumping the target SDK.")
    except (TypeError, ValueError):
        pass

    # ---- permissions ----
    perms = apk.get_permissions() or []
    perm_rows = []
    for p in sorted(set(perms)):
        if p in DANGEROUS_PERMS:
            sev, why = DANGEROUS_PERMS[p]
            perm_rows.append((p, sev))
            add(sev, f"Permission: {p}",
                f"This permission allows: {why}.",
                "Confirm the feature genuinely needs it; drop it otherwise (least privilege).")
        else:
            perm_rows.append((p, "Info"))
    info["permissions"] = perm_rows

    # ---- exported components ----
    exported = exported_components(manifest)
    info["exported"] = exported
    shown = 0
    for tag, name in exported:
        if name.startswith("androidx.") or name.startswith("com.google.android.gms"):
            continue  # support-library noise
        if shown < 12:
            add("Low", f"Exported {tag}: {name}",
                "Other apps can invoke this component. Normal for launcher/share "
                "targets, but each exported entry widens the attack surface.",
                "Set exported=false unless it must be reachable; guard with permissions.")
            shown += 1
    if len(exported) - shown > 0:
        notes.append(f"...and {len(exported) - shown} more exported components (support-library).")

    # ---- dex strings: secrets / urls / ips ----
    secret_hits = {}
    entropy_hits = set()
    urls, clear_urls, ips = set(), set(), set()
    class_names = set()
    for raw in get_dex_list(apk):
        try:
            d = DEX(raw)
        except Exception:
            continue
        for s in d.get_strings():
            if not s or len(s) > 400:
                continue
            for name, pat, _sev, _rec in SECRET_PATTERNS:
                m = re.search(pat, s)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    # skip UI labels / whitespace-only captures ("Password:\n  ")
                    if len(val) < 6 or not re.search(r"[A-Za-z0-9]{3}", val):
                        continue
                    if PLACEHOLDER_DENY.match(val):
                        continue
                    secret_hits.setdefault(name, set()).add(redact(val))
            for u in URL_RE.findall(s):
                u = u.rstrip(").,;")
                urls.add(u[:120])
                if u.startswith(URL_NAMESPACE_DENY):
                    continue  # XML namespace identifier, never fetched over network
                if u.startswith("http://"):
                    host = u[7:].split("/")[0].split(":")[0]
                    if not (host in ("localhost", "127.0.0.1") or host.startswith(("10.", "192.168."))):
                        clear_urls.add(u[:120])
            for ip in IP_RE.findall(s):
                if not is_private_ip(ip):
                    ips.add(ip)
            if ENTROPY_KW_RE.search(s):
                for tok in ENTROPY_TOKEN_RE.findall(s):
                    if len(tok) < 24 or "://" in tok or "." in tok or PLACEHOLDER_DENY.match(tok):
                        continue
                    if re.fullmatch(r"[0-9a-fA-F]+", tok):
                        continue  # hex hash, not a secret
                    if shannon(tok) >= 4.5:
                        entropy_hits.add(redact(tok))
        try:
            for cls in d.get_classes():
                class_names.add(cls.get_name())
        except Exception:
            pass

    for name, pat, sev, rec in SECRET_PATTERNS:
        vals = secret_hits.get(name)
        if vals:
            shown_vals = ", ".join(sorted(vals)[:5])
            extra = f" (+{len(vals) - 5} more)" if len(vals) > 5 else ""
            add(sev, f"Hardcoded secret: {name} ({len(vals)} found)",
                f"Examples (redacted): {shown_vals}{extra}",
                rec)

    if entropy_hits:
        shown_e = ", ".join(sorted(entropy_hits)[:5])
        extra_e = f" (+{len(entropy_hits) - 5} more)" if len(entropy_hits) > 5 else ""
        add("Medium", f"Possible secrets near key-words ({len(entropy_hits)})",
            f"Random-looking strings next to secret-like keywords (redacted): {shown_e}{extra_e}.",
            "Verify none is a live credential; move real secrets server-side or into secure storage.")
    if clear_urls:
        sample = "\n".join(f"    - {u}" for u in sorted(clear_urls)[:8])
        extra = f"\n    (+{len(clear_urls) - 8} more)" if len(clear_urls) > 8 else ""
        add("Medium", f"Cleartext http:// URLs in code ({len(clear_urls)})",
            f"Unencrypted endpoints found:\n{sample}{extra}",
            "Migrate these endpoints to HTTPS.")
    if ips:
        add("Low", f"Hardcoded public IP addresses ({len(ips)})",
            "IPs: " + ", ".join(sorted(ips)[:8]),
            "Prefer DNS names; hardcoded IPs hinder rotation and incident response.")
    notes.append(f"{len(urls)} total URLs and {len(class_names)} classes scanned.")

    # ---- tracker / SDK detection ----
    found = {}
    for prefix, (tname, cat) in TRACKERS.items():
        if any(cn.startswith(prefix) for cn in class_names):
            found[tname] = cat
    info["trackers"] = found
    ad_trackers = [t for t, c in found.items() if c == "Advertising"]
    if ad_trackers:
        add("Low", f"Advertising SDKs bundled ({len(ad_trackers)})",
            "Found: " + ", ".join(ad_trackers),
            "Ad SDKs expand the data-sharing surface; disclose them in the privacy policy.")

    # ---- risk score ----
    score = min(100, sum(SEVERITY_WEIGHT[f["severity"]] for f in findings))
    band = "Low" if score < 25 else ("Medium" if score < 60 else "High")
    info["risk_score"] = score
    info["risk_band"] = band

    return {"info": info, "findings": findings, "notes": notes}

# ------------------------------------------------------------------ report ---

def render_markdown(result, apk_path, deep_info=None):
    info, findings, notes = result["info"], result["findings"], result["notes"]
    L = []
    A = L.append
    A(f"# APK Security Audit Report")
    A("")
    A(f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · static analysis only · "
      f"tool: apk-audit-demo (androguard)_")
    A("")
    sev_count = {s: sum(1 for f in findings if f["severity"] == s) for s in ("High", "Medium", "Low")}
    A(f"## Verdict — Risk score: **{info['risk_score']}/100 ({info['risk_band']} risk)**")
    A("")
    A(f"High: **{sev_count['High']}** · Medium: **{sev_count['Medium']}** · Low: **{sev_count['Low']}**")
    A("")
    A("## App information")
    A("")
    A("| Field | Value |")
    A("|---|---|")
    A(f"| File | `{info['file']}` ({info['size_mb']} MB) |")
    A(f"| SHA-256 | `{info['sha256'][:32]}…` |")
    A(f"| Package | `{info['package']}` |")
    A(f"| App name | {info['app_name']} |")
    A(f"| Version | {info['version']} |")
    A(f"| minSdk / targetSdk | {info['min_sdk']} / {info['target_sdk']} |")
    A(f"| Signed | {info['signed']} |")
    A(f"| Signing cert | {info['cert_subject']} |")
    A("")
    A("## Findings")
    A("")
    if not findings:
        A("_No findings — clean static profile._")
    for i, f in enumerate(sorted(findings, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x["severity"]]), 1):
        A(f"### {i}. [{f['severity']}] {f['title']}")
        A("")
        A(f"{f['detail']}")
        A("")
        A(f"**Recommendation:** {f['recommendation']}")
        A("")
    A("## Permissions")
    A("")
    A("| Permission | Rating |")
    A("|---|---|")
    for p, sev in info["permissions"]:
        A(f"| `{p}` | {sev} |")
    A("")
    A("## Exported components (reachable by other apps)")
    A("")
    if info["exported"]:
        for tag, name in info["exported"]:
            A(f"- `{tag}` — `{name}`")
    else:
        A("_None exported._")
    A("")
    A("## Third-party SDKs / trackers detected")
    A("")
    if info["trackers"]:
        for t, c in sorted(info["trackers"].items()):
            A(f"- **{t}** ({c})")
    else:
        A("_None of the known tracker signatures found._")
    A("")
    if deep_info:
        A("## Deep scan (apktool smali)")
        A("")
        if "hits" in deep_info:
            if deep_info["hits"]:
                for name, vals in deep_info["hits"].items():
                    A(f"- **{name}**: " + ", ".join(vals))
            else:
                A("_No additional secrets in smali._")
        else:
            A(f"_Skipped: {deep_info.get('skipped')}_")
        A("")
    if notes:
        A("## Notes")
        A("")
        for n in notes:
            A(f"- {n}")
        A("")
    A("---")
    A("_Scope: static analysis only (manifest, permissions, dex strings, certificates). "
      "No dynamic execution was performed. Findings are candidates for manual review, "
      "not confirmed vulnerabilities._")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Static APK security audit -> Markdown report")
    ap.add_argument("apk", help="path to the APK file")
    ap.add_argument("-o", "--output", default=None, help="output .md path (default: <apk>-audit.md)")
    ap.add_argument("--deep", action="store_true",
                    help="also decode with apktool and scan smali (slower)")
    ap.add_argument("--json", action="store_true",
                    help="also write structured findings JSON next to the report "
                         "(for pipeline use, e.g. fix.py)")
    args = ap.parse_args()

    if not os.path.isfile(args.apk):
        print(f"error: file not found: {args.apk}", file=sys.stderr)
        sys.exit(2)

    print(f"[*] Analyzing {args.apk} ...", file=sys.stderr)
    result = analyze(args.apk)

    deep_info = None
    if args.deep:
        print("[*] Deep scan: decoding with apktool ...", file=sys.stderr)
        deep_info = deep_smali_scan(args.apk)

    md = render_markdown(result, args.apk, deep_info)
    out = args.output or (os.path.splitext(args.apk)[0] + "-audit.md")
    with open(out, "w") as fh:
        fh.write(md)
    n = len(result["findings"])
    print(f"[+] Done: {n} findings, risk {result['info']['risk_score']}/100 "
          f"({result['info']['risk_band']}) -> {out}", file=sys.stderr)
    if args.json:
        jout = os.path.splitext(out)[0] + ".json"
        with open(jout, "w") as fh:
            json.dump(result, fh, indent=2, default=str)
        print(f"[+] JSON findings -> {jout}", file=sys.stderr)


if __name__ == "__main__":
    main()
