"""AIS-gap + STS-candidate detection (adapted from the standalone
maritime-intel pipeline/detect.py — same params, same labels, same
provenance wording). Pure stdlib. Works on in-memory envelopes instead
of a JSONL file so the deployed collector needs no local log.

Every output is labelled "candidate — requires human review" and no
vessel is ever labelled "sanctioned".
"""

import math
from datetime import datetime, timezone

CORRIDOR = {"lat_min": 25.0, "lat_max": 27.5, "lon_min": 55.0, "lon_max": 59.5}

DEFAULTS = {
    "gap_min_hours": 6.0,
    "sts_max_dist_nm": 0.5,
    "sts_max_sog_kt": 2.0,
    "sts_min_duration_min": 30.0,
    "sts_pair_window_min": 15.0,
}


def haversine_nm(lat1, lon1, lat2, lon2):
    r = math.radians
    dlat = r(lat2 - lat1)
    dlon = r(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(dlon / 2) ** 2
    return 3440.065 * 2 * math.asin(min(1.0, math.sqrt(a)))


def in_corridor(lat, lon):
    return (CORRIDOR["lat_min"] <= lat <= CORRIDOR["lat_max"]
            and CORRIDOR["lon_min"] <= lon <= CORRIDOR["lon_max"])


def parse_time(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_report(envelope):
    """Normalise one AISStream envelope to a position report dict or None."""
    meta = envelope.get("MetaData") or {}
    msg = envelope.get("Message") or {}
    pr = None
    for key in ("PositionReport", "StandardClassBPositionReport",
                "ExtendedClassBPositionReport"):
        if key in msg and isinstance(msg[key], dict):
            pr = msg[key]
            break
    if pr is None:
        return None
    try:
        lat, lon = float(pr["Latitude"]), float(pr["Longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    ts = parse_time(meta.get("time_utc")) or parse_time(pr.get("Timestamp"))
    if ts is None:
        return None
    try:
        sog = float(pr.get("Sog")) if pr.get("Sog") is not None else None
    except (TypeError, ValueError):
        sog = None
    return {"mmsi": str(meta.get("MMSI", "")),
            "ship_name": meta.get("ShipName"),
            "time": ts, "lat": lat, "lon": lon, "sog": sog}


def build_tracks(envelopes):
    """Return {mmsi: [sorted reports]}, plus counters."""
    tracks = {}
    kept = 0
    for envelope in envelopes:
        try:
            rep = extract_report(envelope)
        except Exception:
            continue
        if rep is None or not rep["mmsi"]:
            continue
        kept += 1
        tracks.setdefault(rep["mmsi"], []).append(rep)
    for mmsi in tracks:
        tracks[mmsi].sort(key=lambda r: r["time"])
    return tracks, kept


def find_gaps(tracks, gap_min_hours):
    events = []
    for mmsi, reps in tracks.items():
        for a, b in zip(reps, reps[1:]):
            gap_h = (b["time"] - a["time"]).total_seconds() / 3600.0
            if gap_h >= gap_min_hours and in_corridor(a["lat"], a["lon"]):
                events.append({
                    "event_type": "ais_gap_event",
                    "classification": "AIS-gap event — requires human review. "
                                      "Consistent with AIS off, receiver gap, or spoofing. "
                                      "NOT proof of wrongdoing.",
                    "mmsi": mmsi,
                    "ship_name": a.get("ship_name"),
                    "gap_start_utc": a["time"].isoformat(),
                    "gap_end_utc": b["time"].isoformat(),
                    "gap_hours": round(gap_h, 2),
                    "last_lat": a["lat"], "last_lon": a["lon"],
                    "reappearance_lat": b["lat"], "reappearance_lon": b["lon"],
                    "confidence": "candidate",
                })
    return sorted(events, key=lambda e: e["gap_start_utc"])


def _close_pairs(rep_a, rep_b, max_dist_nm, max_sog, window_min):
    """Yield (time, dist_nm) samples where two tracks are close, slow, and
    near-simultaneous. Two-pointer merge over sorted tracks."""
    i = j = 0
    a, b = rep_a, rep_b
    while i < len(a) and j < len(b):
        dt_min = abs((a[i]["time"] - b[j]["time"]).total_seconds()) / 60.0
        if dt_min <= window_min:
            dist = haversine_nm(a[i]["lat"], a[i]["lon"], b[j]["lat"], b[j]["lon"])
            sog_a = a[i]["sog"] if a[i]["sog"] is not None else 999.0
            sog_b = b[j]["sog"] if b[j]["sog"] is not None else 999.0
            if dist <= max_dist_nm and sog_a <= max_sog and sog_b <= max_sog:
                yield (max(a[i]["time"], b[j]["time"]), dist,
                       (a[i]["lat"] + b[j]["lat"]) / 2.0,
                       (a[i]["lon"] + b[j]["lon"]) / 2.0)
            if a[i]["time"] <= b[j]["time"]:
                i += 1
            else:
                j += 1
        elif a[i]["time"] < b[j]["time"]:
            i += 1
        else:
            j += 1


def find_sts_candidates(tracks, params):
    events = []
    mmsis = sorted(tracks)
    for x in range(len(mmsis)):
        for y in range(x + 1, len(mmsis)):
            m1, m2 = mmsis[x], mmsis[y]
            run_start = run_end = None
            run_min_dist = None
            run_mid = (None, None)
            last_t = None
            samples = list(_close_pairs(
                tracks[m1], tracks[m2],
                params["sts_max_dist_nm"], params["sts_max_sog_kt"],
                params["sts_pair_window_min"]))
            for t, dist, mlat, mlon in samples:
                if run_start is None:
                    run_start = run_end = t
                    run_min_dist = dist
                    run_mid = (mlat, mlon)
                elif (t - last_t).total_seconds() / 60.0 <= params["sts_pair_window_min"] * 2:
                    run_end = t
                    run_min_dist = min(run_min_dist, dist)
                    run_mid = (mlat, mlon)
                else:
                    if (run_end - run_start).total_seconds() / 60.0 >= params["sts_min_duration_min"]:
                        events.append(_sts_event(m1, m2, tracks, run_start, run_end, run_min_dist, run_mid))
                    run_start = run_end = t
                    run_min_dist = dist
                    run_mid = (mlat, mlon)
                last_t = t
            if run_start is not None and (run_end - run_start).total_seconds() / 60.0 >= params["sts_min_duration_min"]:
                events.append(_sts_event(m1, m2, tracks, run_start, run_end, run_min_dist, run_mid))
    return sorted(events, key=lambda e: e["window_start_utc"])


def _sts_event(m1, m2, tracks, start, end, min_dist, mid):
    names = []
    for m in (m1, m2):
        nm = next((r.get("ship_name") for r in tracks[m] if r.get("ship_name")), None)
        names.append(nm)
    return {
        "event_type": "sts_candidate",
        "classification": "STS candidate — matches pattern: two vessels close together, "
                          "both near-stationary, for an extended window. Also consistent "
                          "with joint anchorage / bunkering / coincidence. NOT proof of a "
                          "transfer and NOT a sanctions finding.",
        "mmsi_a": m1, "ship_name_a": names[0],
        "mmsi_b": m2, "ship_name_b": names[1],
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "duration_min": round((end - start).total_seconds() / 60.0, 1),
        "min_distance_nm": round(min_dist, 3),
        "approx_lat": mid[0], "approx_lon": mid[1],
        "confidence": "candidate",
    }


def detect_from_envelopes(envelopes, params=None):
    """Run full detection over in-memory envelopes. Returns the same
    payload shape as the standalone detector (minus source_file)."""
    params = dict(DEFAULTS, **(params or {}))
    tracks, kept = build_tracks(envelopes)
    gaps = find_gaps(tracks, params["gap_min_hours"])
    sts = find_sts_candidates(tracks, params)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "messages_read": len(envelopes),
        "position_reports_kept": kept,
        "vessels_seen": len(tracks),
        "detector_params": params,
        "corridor": dict(CORRIDOR),
        "provenance": "Candidate events only. Each event is derived from the "
                      "collected AIS messages; no vessel is labelled sanctioned.",
        "gap_events": gaps,
        "sts_candidates": sts,
    }
