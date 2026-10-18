#!/usr/bin/env python3
"""
apk-audit-demo / fix.py  (v2 — auto-fix layer)
==============================================
Takes an APK + its audit report and generates a SOURCE-LEVEL fix bundle:

    fixes/
        AndroidManifest.fixed.xml          decoded manifest with safe fixes applied
        AndroidManifest.diff               unified diff vs the decoded original
        res/xml/network_security_config.xml  HTTPS-only network security config
        FIXES.md                           per-finding: what was wrong, the exact
                                           fix, and where to change it in YOUR source

Usage:
    python fix.py report.md app.apk [-o fixes/]

WHAT THIS IS:
  A patch generator for the APP OWNER's own source code. You copy the files
  into your Android Studio project, review them, rebuild and re-sign the APK
  yourself with your own keystore.

WHAT THIS IS NOT:
  It NEVER repackages, re-signs, or modifies anyone's APK binary. There is no
  `apktool b`, no signing step, nothing that touches the original APK file.
  Rebuilding someone else's APK (modding / cracking / "premium unlock") is
  piracy — this tool cannot do that and never will.

LEGAL USE ONLY: your own apps, or apps you have written permission to test.
"""
import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(HERE, "tools")
APKTOOL = os.path.join(TOOLS_DIR, "apktool.jar")

# androguard/audit live in the same folder
from app.apkaudit import engine_audit as audit_mod  # noqa: E402  (gives us analyze() + NS)

NS = audit_mod.NS
ANDROID_NS_URI = "http://schemas.android.com/apk/res/android"

# ---------------------------------------------------------------- helpers ---

def log(msg):
    print(msg, file=sys.stderr)


def decode_manifest(apk_path):
    """Decode APK with apktool, return (manifest_text, tmpdir).

    Falls back to re-serializing androguard's parsed manifest if apktool/java
    is unavailable. The APK itself is only ever READ, never modified.
    """
    if os.path.exists(APKTOOL) and shutil.which("java"):
        tmp = tempfile.mkdtemp(prefix="apk_fix_")
        try:
            r = subprocess.run(
                ["java", "-jar", APKTOOL, "d", "-f", "-o", tmp, apk_path],
                capture_output=True, text=True, timeout=300)
            man = os.path.join(tmp, "AndroidManifest.xml")
            if r.returncode == 0 and os.path.isfile(man):
                with open(man, encoding="utf-8") as fh:
                    return fh.read(), tmp, False
            log("[!] apktool decode failed, falling back to androguard manifest")
        except subprocess.TimeoutExpired:
            log("[!] apktool decode timed out, falling back to androguard manifest")
        shutil.rmtree(tmp, ignore_errors=True)

    # fast path: parse ONLY the manifest via AXMLPrinter (no DEX parsing,
    # tiny memory footprint — safe for small containers)
    try:
        from androguard.core.axml import AXMLPrinter
        with zipfile.ZipFile(apk_path) as _z:
            _raw = _z.read("AndroidManifest.xml")
        manifest = AXMLPrinter(_raw).get_xml_obj()
        register_namespaces_from_tree(manifest)
        text = ET.tostring(manifest, encoding="unicode")
        tmp = tempfile.mkdtemp(prefix="apk_fix_")
        log("[*] Using manifest-only parse as the fix base")
        return text, tmp, True
    except Exception as _e:
        log(f"[!] manifest-only parse failed ({type(_e).__name__}), trying full APK parse")
    # last resort: serialize androguard's parsed manifest (formatting differs
    # from the developer's source, but the semantic content is identical)
    apk = audit_mod.APK(apk_path)
    manifest = apk.get_android_manifest_xml()
    register_namespaces_from_tree(manifest)
    text = ET.tostring(manifest, encoding="unicode")
    tmp = tempfile.mkdtemp(prefix="apk_fix_")
    return text, tmp, True


def register_namespaces_from_tree(root):
    """Keep original xmlns prefixes (android:, tools:, ...) on serialization."""
    seen = {}

    def walk(el):
        for attr in list(el.attrib) + ([el.tag] if "}" in el.tag else []):
            if attr.startswith("{"):
                uri = attr[1:].split("}")[0]
                seen.setdefault(uri, None)
        for child in el:
            walk(child)

    walk(root)
    # 'android' is the one we know for sure; register any others generically
    ET.register_namespace("android", ANDROID_NS_URI)
    n = 0
    for uri in seen:
        if uri != ANDROID_NS_URI:
            try:
                ET.register_namespace(f"ns{n}", uri)
                n += 1
            except ValueError:
                pass


def register_namespaces_from_text(text):
    """Register xmlns prefixes found in the raw manifest text (apktool path)."""
    for prefix, uri in re.findall(r'xmlns:([A-Za-z0-9_]+)="([^"]+)"', text):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass

# ------------------------------------------------------- manifest fixing ---

EXPORTED_TAGS = ("activity", "activity-alias", "service", "receiver", "provider")


def is_effectively_exported(el):
    exp = el.get(NS + "exported")
    if exp == "true":
        return True
    if exp is None and el.find("intent-filter") is not None:
        return True  # targetSdk<31 semantics: intent-filter => exported
    return False


def apply_manifest_fixes(manifest_text):
    """Apply CONSERVATIVE auto-fixes via surgical text edits on the ORIGINAL
    manifest text (keeps formatting intact -> minimal, reviewable diff).

    Returns (fixed_text, changes, guided).
    changes: human-readable strings describing what was auto-changed.
    guided:  list of (component_tag, name, reason) left for manual review.
    """
    # --- detect with ElementTree, patch with text edits ---
    register_namespaces_from_text(manifest_text)
    root = ET.fromstring(manifest_text)
    app = root.find("application")
    changes, guided = [], []
    if app is None:
        return manifest_text, ["(no <application> element found — no manifest fixes applied)"], guided

    text = manifest_text

    def patch_application_tag(old, new, desc):
        """Replace an attribute string inside the <application ...> opening tag."""
        nonlocal text
        m = re.search(r"<application\b.*?>", text, re.DOTALL)
        if not m:
            return False
        tag = m.group(0)
        if old not in tag:
            return False
        text = text[:m.start()] + tag.replace(old, new, 1) + text[m.end():]
        changes.append(desc)
        return True

    # 1. cleartext traffic -> false (safe: only ever tightens transport security)
    if app.get(NS + "usesCleartextTraffic") == "true":
        patch_application_tag('android:usesCleartextTraffic="true"',
                              'android:usesCleartextTraffic="false"',
                              'android:usesCleartextTraffic "true" -> "false" on <application>')

    # 2. allowBackup -> false. Security-safe; note the UX tradeoff in FIXES.md.
    if app.get(NS + "allowBackup") == "true":
        patch_application_tag('android:allowBackup="true"',
                              'android:allowBackup="false"',
                              'android:allowBackup "true" -> "false" on <application> '
                              "(note: users lose automatic backup/restore — see FIXES.md)")

    # 3. debuggable -> false, but ONLY if it was explicitly true (never invent it)
    if app.get(NS + "debuggable") == "true":
        patch_application_tag('android:debuggable="true"',
                              'android:debuggable="false"',
                              'android:debuggable "true" -> "false" on <application>')

    # 4. network security config reference — only if the app has none already
    if app.get(NS + "networkSecurityConfig") is None:
        m = re.search(r"<application\b.*?>", text, re.DOTALL)
        if m:
            tag = m.group(0)
            # insert before the closing '>' of the opening tag
            new_tag = tag[:-1].rstrip() + ' android:networkSecurityConfig="@xml/network_security_config">'
            text = text[:m.start()] + new_tag + text[m.end():]
            changes.append('added android:networkSecurityConfig="@xml/network_security_config" '
                           'on <application> (pairs with res/xml/network_security_config.xml in this bundle)')

    # 5. exported=false ONLY on components with NO intent-filter.
    #    Components WITH an intent-filter are left alone: flipping those can
    #    break launchers, share targets and widgets (guided instead).
    for tagname in EXPORTED_TAGS:
        for el in app.findall(tagname):
            name = el.get(NS + "name") or "?"
            if not is_effectively_exported(el):
                continue
            if el.find("intent-filter") is None:
                # surgical: within THIS component's opening tag only
                pat = re.compile(r"<%s\b[^>]*?android:name=\"%s\"[^>]*?>" % (tagname, re.escape(name)))
                def _fix_opening(m):
                    opening = m.group(0)
                    if 'android:exported="true"' in opening:
                        return opening.replace('android:exported="true"',
                                               'android:exported="false"', 1)
                    return opening
                new_text, n = pat.subn(_fix_opening, text, count=1)
                if n:
                    text = new_text
                    changes.append(f'{tagname} "{name}": android:exported -> "false" (no intent-filter)')
                else:
                    guided.append((tagname, name, "opening tag not matched for safe patching — review manually"))
            else:
                guided.append((tagname, name,
                               "has an intent-filter — verify it truly needs to be "
                               "reachable by other apps before setting exported=false"))

    # validate the result is still well-formed XML
    ET.fromstring(text)
    if not text.lstrip().startswith("<?xml"):
        text = '<?xml version="1.0" encoding="utf-8"?>\n' + text
    return text, changes, guided


NETWORK_SECURITY_CONFIG = """<?xml version="1.0" encoding="utf-8"?>
<!-- Enforces HTTPS-only traffic. Copy to app/src/main/res/xml/network_security_config.xml
     and reference it from <application android:networkSecurityConfig="@xml/network_security_config" .../> -->
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <!-- If you MUST allow cleartext to specific legacy hosts during migration,
         add a <domain-config> here instead of re-enabling it globally:
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">legacy.example.com</domain>
    </domain-config>
    -->
</network-security-config>
"""

# ------------------------------------------------------------------ FIXES.md ---

GUIDED_PERMISSION_HELP = {
    "android.permission.MANAGE_EXTERNAL_STORAGE": (
        "Verify need: can the feature use MediaStore / Storage Access Framework instead? "
        "Google Play heavily restricts this permission — most apps are rejected."),
    "android.permission.REQUEST_INSTALL_PACKAGES": (
        "Verify need: is in-app APK installation truly a feature (self-updater, plugin "
        "system)? If not, remove it — it is a classic dropper/malware flag."),
    "android.permission.SYSTEM_ALERT_WINDOW": (
        "Verify need: overlays are a tapjacking vector; prefer in-app UI."),
    "android.permission.READ_SMS": (
        "Verify need: prefer the SMS Retriever API / SMS User Consent API instead of "
        "reading all SMS."),
    "android.permission.ACCESS_FINE_LOCATION": (
        "Verify need: could coarse location suffice? Request in-use only, never background "
        "unless justified."),
    "android.permission.CAMERA": (
        "Verify need: could an ACTION_IMAGE_CAPTURE intent delegate to the camera app?"),
    "android.permission.RECORD_AUDIO": (
        "Verify need: microphone access must be clearly tied to a user-visible feature."),
    "android.permission.READ_CONTACTS": (
        "Verify need: could a contact-picker intent replace broad read access?"),
}

SECRETS_SNIPPET = """```gradle
// 1) Put the real value in local.properties (NEVER commit this file):
//    local.properties:
//        MY_API_KEY=the_real_key_here

// 2) app/build.gradle — expose it as a BuildConfig field:
android {
    defaultConfig {
        def localProps = new Properties()
        file(rootProject.file("local.properties")).withInputStream { localProps.load(it) }
        buildConfigField "String", "MY_API_KEY",
            "\\"${localProps.getProperty('MY_API_KEY', '')}\\""
    }
    buildFeatures { buildConfig = true }
}

// 3) In code, read BuildConfig.MY_API_KEY instead of a hardcoded literal.
```

```gitignore
# .gitignore — make sure secrets never reach git:
local.properties
*.jks
*.keystore
```

> Better still: don't ship the secret at all. Put it behind YOUR server —
> the app calls your API, your server calls the third party with the key.
> Anything inside the APK is public by definition (this audit proves it)."""

CRYPTO_SNIPPET = """```kotlin
// AndroidX Security — encrypted key-value storage
// build.gradle: implementation("androidx.security:security-crypto:1.1.0-alpha06")
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val prefs = EncryptedSharedPreferences.create(
    context,
    "secret_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
prefs.edit().putString("token", token).apply()
```"""

def render_fixes_md(info, findings, changes, guided_exported):
    L = []
    A = L.append
    A("# Source-Level Fixes")
    A("")
    A(f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · "
      f"for `{info['package']}` ({info['app_name']}) · based on the static audit report_")
    A("")
    A("## ⛔ Read this first — what this bundle is and is NOT")
    A("")
    A("- These are **source patches for YOUR OWN app's source code**. Copy the files into "
      "your Android Studio project, review every change, then **rebuild and re-sign the "
      "APK yourself** with your own keystore (`./gradlew assembleRelease`).")
    A("- This tool **never repackages, re-signs, or modifies any APK binary**. There is no "
      "`apktool b` step here, no signing step, nothing that writes to the original APK.")
    A("- Rebuilding *someone else's* APK (modding, cracking, \"premium unlock\", ad removal) "
      "is piracy. This tool cannot do that and never will. "
      "**Personal use does not make it legal** — and cracked APKs are the #1 malware "
      "vector (banking trojans love \"premium cracked\" downloads).")
    A("- Every finding below is marked **AUTO-APPLIED** (safe, done for you in this bundle) "
      "or **GUIDED** (needs your judgment — exact copy-paste snippet provided, with the "
      "reason it wasn't auto-applied).")
    A("")
    A("## How to apply")
    A("")
    A("1. Review `AndroidManifest.diff` — every auto-change, line by line.")
    A("2. Copy `AndroidManifest.fixed.xml` → `app/src/main/AndroidManifest.xml` in YOUR source.")
    A("3. Copy `res/xml/network_security_config.xml` → `app/src/main/res/xml/network_security_config.xml`.")
    A("4. Work through the GUIDED items below (copy-paste snippets included).")
    A("5. Rebuild + sign with YOUR keystore, then re-run `audit.py` on the new APK to verify.")
    A("")
    A("## Auto-applied manifest changes")
    A("")
    if changes:
        for c in changes:
            A(f"- {c}")
    else:
        A("_No safe auto-fixes applied — nothing in the manifest met the conservative bar._")
    A("")

    A("## Per-finding fixes")
    A("")
    src_manifest = "`app/src/main/AndroidManifest.xml` (adjust if your module path differs)"
    ordered = sorted(findings, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}[x["severity"]])
    for i, f in enumerate(ordered, 1):
        title, sev = f["title"], f["severity"]
        A(f"### {i}. [{sev}] {title}")
        A("")
        A(f"**What was wrong:** {f['detail'].splitlines()[0] if f['detail'] else ''}")
        A("")

        if title == "Cleartext HTTP traffic allowed":
            A("**Fix: AUTO-APPLIED** ✅")
            A(f"- {src_manifest} → `<application>`: `android:usesCleartextTraffic=\"false\"` (in `AndroidManifest.fixed.xml`).")
            A("- `res/xml/network_security_config.xml` (in this bundle) enforces HTTPS-only via "
              "`cleartextTrafficPermitted=\"false\"`, referenced from the manifest.")
        elif title == "App is debuggable":
            A("**Fix: AUTO-APPLIED** ✅")
            A(f"- {src_manifest} → `<application>`: `android:debuggable=\"false\"` (in `AndroidManifest.fixed.xml`). "
              "Also confirm your `build.gradle` release type doesn't set `debuggable true`.")
        elif title.startswith("Backup enabled"):
            A("**Fix: AUTO-APPLIED** ✅ (with a tradeoff — read this)")
            A(f"- {src_manifest} → `<application>`: `android:allowBackup=\"false\"` (in `AndroidManifest.fixed.xml`).")
            A("- Tradeoff: users lose automatic backup/restore of app data. If your app benefits "
              "from backup, keep `\"true\"` but add `android:fullBackupContent=\"@xml/backup_rules\"` "
              "with scoped `<include>`/`<exclude>` rules instead of reverting blindly.")
        elif title.startswith("Exported "):
            comp = title.split("Exported ", 1)[1]
            # This component was auto-fixed iff it had no intent-filter; components
            # with intent-filters were recorded in guided_exported instead.
            was_guided = any(g[1] in comp for g in guided_exported)
            if was_guided:
                reason = next(g[2] for g in guided_exported if g[1] in comp)
                A("**Fix: GUIDED** 🛠️ (not auto-applied — flipping this could break the app)")
                A(f"- Reason: {reason}.")
                A(f"- If you confirm nothing outside your app needs it, set in {src_manifest}:")
                A("  ```xml")
                A(f"  <!-- inside the <{comp.split(':')[0].strip()}> element for {comp.split(':')[-1].strip()} -->")
                A('  android:exported="false"')
                A("  ```")
            else:
                A("**Fix: AUTO-APPLIED** ✅")
                A(f"- `{comp}` had no intent-filter, so `android:exported=\"false\"` was set "
                  f"in `AndroidManifest.fixed.xml`. Nothing outside your app could have been "
                  f"relying on it without an intent-filter.")
        elif title.startswith("Permission:"):
            perm = title.split("Permission:", 1)[1].strip()
            A("**Fix: GUIDED** 🛠️ (permissions are NEVER auto-removed — deleting one your "
              "feature needs crashes the app)")
            A("- **Step 1 —** " + GUIDED_PERMISSION_HELP.get(
                perm, "Audit every call site: is this permission tied to a feature users asked for? "
                      "Prefer narrow alternatives (pickers, intents, MediaStore)."))
            A("- **Step 2 — if NOT needed, delete exactly this line** from "
              f"{src_manifest}:")
            A("  ```xml")
            A(f'  <uses-permission android:name="{perm}" />')
            A("  ```")
            A("- **Step 3 —** remove the now-dead code paths that requested it, rebuild, and "
              "retest the feature.")
        elif title.startswith("Hardcoded secret:"):
            A("**Fix: GUIDED** 🛠️ (a scanner can't know where in your source the literal lives, "
              "and values are redacted in the report — search your source for the pattern)")
            A("- Search your source for the flagged pattern (e.g. `AIza`, `AKIA`, `xoxb-`) and "
              "replace every literal with the pattern below.")
            A("- " + SECRETS_SNIPPET.replace("\n", "\n  "))
        elif title.startswith("Cleartext http:// URLs in code"):
            A("**Fix: GUIDED** 🛠️ (only you know which endpoints have HTTPS equivalents)")
            A("- Migrate each `http://` endpoint to `https://`. The network security config in "
              "this bundle will then *enforce* it at runtime — any missed URL fails loudly "
              "instead of leaking silently.")
            A("- After migrating, re-run the audit: this finding should disappear.")
        elif title.startswith("Hardcoded public IP"):
            A("**Fix: GUIDED** 🛠️")
            A("- Replace hardcoded IPs with DNS names so you can rotate infrastructure without "
              "shipping a new APK.")
        elif title.startswith("Outdated targetSdk") or title.startswith("targetSdk"):
            A("**Fix: GUIDED** 🛠️ (a build-system change — test thoroughly)")
            A("- In `app/build.gradle`: `targetSdk 34` (or current). Then fix any behavior "
              "changes the new target introduces (permissions, background limits, etc.).")
        elif title.startswith("Advertising SDKs"):
            A("**Fix: GUIDED** 🛠️")
            A("- No code change required — but disclose every ad SDK in your Play Store "
              "Data Safety form and privacy policy, or remove SDKs you don't use.")
        else:
            A("**Fix: GUIDED** 🛠️")
            A(f"- Follow the audit recommendation: {f['recommendation']}")
        A("")

    # crypto section only if relevant findings exist
    if any("crypto" in t.lower() or "keystore" in t.lower() or "sharedpreferences" in t.lower()
           for t in [f["title"] for f in findings]):
        A("## Insecure storage / crypto — recommended pattern")
        A("")
        A(CRYPTO_SNIPPET)
        A("")
    else:
        A("_No insecure crypto/storage patterns were detected by the static scan, so no "
          "crypto migration snippet is included. If you store tokens, use "
          "AndroidX Security's EncryptedSharedPreferences._")
        A("")

    A("---")
    A("_Scope reminder: static analysis only. Re-run `audit.py` on your rebuilt APK to "
      "confirm each finding is gone. Findings are candidates for manual review, not "
      "confirmed vulnerabilities._")
    return "\n".join(L) + "\n"


# -------------------------------------------------------------------- main ---

def main():
    ap = argparse.ArgumentParser(
        description="Generate a source-level fix bundle from an APK + its audit report. "
                    "Never repackages or re-signs the APK.")
    ap.add_argument("report", help="audit report .md (from audit.py)")
    ap.add_argument("apk", help="path to the APK file (read-only)")
    ap.add_argument("-o", "--outdir", default="fixes",
                    help="output directory for the fix bundle (default: fixes/)")
    args = ap.parse_args()

    if not os.path.isfile(args.report):
        print(f"error: report not found: {args.report}", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.apk):
        print(f"error: APK not found: {args.apk}", file=sys.stderr)
        sys.exit(2)

    log(f"[*] Re-analyzing {args.apk} for structured findings ...")
    result = audit_mod.analyze(args.apk)
    info, findings = result["info"], result["findings"]
    log(f"[*] {len(findings)} findings loaded")

    # package sanity check against the report
    with open(args.report, encoding="utf-8") as fh:
        report_text = fh.read()
    if info["package"] not in report_text:
        log(f"[!] warning: report doesn't mention package {info['package']} — "
            f"continuing anyway (fixes derive from the APK)")

    log("[*] Decoding manifest (read-only) ...")
    manifest_text, tmpdir, used_fallback = decode_manifest(args.apk)
    try:
        fixed_text, changes, guided_exported = apply_manifest_fixes(manifest_text)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    outdir = args.outdir
    res_xml = os.path.join(outdir, "res", "xml")
    os.makedirs(res_xml, exist_ok=True)

    # 1. fixed manifest
    fixed_path = os.path.join(outdir, "AndroidManifest.fixed.xml")
    with open(fixed_path, "w", encoding="utf-8") as fh:
        fh.write(fixed_text)

    # 2. unified diff vs original
    diff = difflib.unified_diff(
        manifest_text.splitlines(), fixed_text.splitlines(),
        fromfile="AndroidManifest.xml (decoded original)",
        tofile="AndroidManifest.fixed.xml",
        lineterm="")
    diff_text = "\n".join(diff) + "\n"
    diff_path = os.path.join(outdir, "AndroidManifest.diff")
    with open(diff_path, "w", encoding="utf-8") as fh:
        fh.write(diff_text)

    # 3. network security config
    nsc_path = os.path.join(res_xml, "network_security_config.xml")
    with open(nsc_path, "w", encoding="utf-8") as fh:
        fh.write(NETWORK_SECURITY_CONFIG)

    # 4. FIXES.md
    fixes_md = render_fixes_md(info, findings, changes, guided_exported)
    fixes_path = os.path.join(outdir, "FIXES.md")
    with open(fixes_path, "w", encoding="utf-8") as fh:
        fh.write(fixes_md)

    n_auto = len(changes)
    print(f"[+] Fix bundle written to {outdir}/", file=sys.stderr)
    print(f"    - AndroidManifest.fixed.xml ({n_auto} auto-applied manifest changes)", file=sys.stderr)
    print(f"    - AndroidManifest.diff", file=sys.stderr)
    print(f"    - res/xml/network_security_config.xml", file=sys.stderr)
    print(f"    - FIXES.md ({len(findings)} per-finding entries)", file=sys.stderr)
    if used_fallback:
        print("    (!) manifest was reconstructed via androguard (apktool unavailable) — "
              "formatting differs from source but semantics are identical", file=sys.stderr)


if __name__ == "__main__":
    main()


def build_fix_bundle(apk_path, outdir, result=None):
    """Library entry point: generate the source-level fix bundle for an APK.

    Returns dict with paths + counts. Never repackages or re-signs the APK.
    Pass a pre-computed analyze() result to avoid a second full scan.
    """
    if result is None:
        result = audit_mod.analyze(apk_path)
    info, findings = result["info"], result["findings"]

    manifest_text, tmpdir, used_fallback = decode_manifest(apk_path)
    try:
        fixed_text, changes, guided_exported = apply_manifest_fixes(manifest_text)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    res_xml = os.path.join(outdir, "res", "xml")
    os.makedirs(res_xml, exist_ok=True)

    fixed_path = os.path.join(outdir, "AndroidManifest.fixed.xml")
    with open(fixed_path, "w", encoding="utf-8") as fh:
        fh.write(fixed_text)

    diff = difflib.unified_diff(
        manifest_text.splitlines(), fixed_text.splitlines(),
        fromfile="AndroidManifest.xml (decoded original)",
        tofile="AndroidManifest.fixed.xml",
        lineterm="")
    diff_path = os.path.join(outdir, "AndroidManifest.diff")
    with open(diff_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(diff) + "\n")

    nsc_path = os.path.join(res_xml, "network_security_config.xml")
    with open(nsc_path, "w", encoding="utf-8") as fh:
        fh.write(NETWORK_SECURITY_CONFIG)

    fixes_md = render_fixes_md(info, findings, changes, guided_exported)
    fixes_path = os.path.join(outdir, "FIXES.md")
    with open(fixes_path, "w", encoding="utf-8") as fh:
        fh.write(fixes_md)

    return {
        "outdir": outdir,
        "auto_changes": len(changes),
        "findings": len(findings),
        "used_fallback": used_fallback,
        "files": [fixed_path, diff_path, nsc_path, fixes_path],
    }
