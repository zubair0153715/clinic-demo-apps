"""One-shot KB builder. Run on the VM BEFORE deploy so kb.json ships
inside the app package (survives deploy wipes).

Usage:
    ~/workspace/.venv-fc/bin/python -m app.pharma_ai.build_kb
Run from ~/workspace/clinic-demo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.pharma_ai import kb as kbmod  # noqa: E402

SEED_DOCS = [
    {
        "doc_id": "katzung-bcp-2018",
        "title": "Basic & Clinical Pharmacology (2018)",
        "source": "seed",
        "path": Path.home() / "workspace/user/files/Basic-Clinical-Pharmacology-2018_0_8zzt.pdf",
    },
]


def main():
    kbmod.KB.load()
    for doc in SEED_DOCS:
        p = doc["path"]
        if not p.exists():
            print(f"SKIP (missing): {p}")
            continue
        print(f"Ingesting {doc['title']} ...")
        pages = kbmod.extract_pages(p)
        n = kbmod.KB.add_document(doc["doc_id"], doc["title"], doc["source"], pages)
        print(f"  {len(pages)} pages -> {n} chunks")
    kbmod.KB.save()
    print(f"Saved {kbmod.KB_PATH} ({kbmod.KB_PATH.stat().st_size/1e6:.1f} MB)")
    # smoke test
    hits = kbmod.KB.search("aminoglycosides nephrotoxicity mechanism", top_k=3)
    print(f"Smoke search: {len(hits)} hits")
    for h in hits:
        print(f"  [{h['score']}] {h['doc_title']} — {h['section']} (p.{h['page_start']})")


if __name__ == "__main__":
    main()
