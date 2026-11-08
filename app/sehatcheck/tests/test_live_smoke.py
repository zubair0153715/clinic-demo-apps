"""SehatCheck LIVE smoke test — hits the real openFDA API.

Only runs with SEHATCHECK_LIVE=1 (network + live data). Skipped in
normal CI runs; the fixture-based suite in test_engine.py covers logic.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("SEHATCHECK_LIVE") != "1",
    reason="live openFDA smoke test — set SEHATCHECK_LIVE=1 to run")


def test_live_acetaminophen_totals():
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    try:
        from sehatcheck import engine
    except ImportError:
        from app.sehatcheck import engine
    engine._CACHE.clear()
    res = engine.lookup("acetaminophen")
    assert res["ok"] is True
    assert res["total_reports"] > 400000
    assert res["serious_reports"] > 300000
    assert res["outcomes"]["death"] > 50000
    assert res["top_reactions"][0][0] == "DRUG DEPENDENCE"
    assert res["label"]["warnings"]
