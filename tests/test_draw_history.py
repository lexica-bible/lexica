"""V11.2 DRAW-CACHE HISTORY controls (DESIGN_v11_acceptance.md V11.2 ruling 5, RULED
2026-07-12; rides in the quote-repair build session). A repair mechanism that rewrites
raws makes preserved draw history load-bearing — the ELEVATED evidence-cost record
(V11.1 paid for its absence twice: the d1 raws were unrecoverable) travels with this
ticket.

Controls (db-free, model-free; DRAWS_DIR is pointed at a temp dir for the run):
  1. SUPERSEDE: saving a draw over an existing one with different prose MOVES the old
     file into draws/history/ byte-intact — never overwrites.
  2. IDENTICAL REFRESH: same sig AND same prose_sha is not a supersession — no archive
     (history is evidence, not duplicates).
  3. UNREADABLE old file: archived anyway — evidence is never discarded on a parse
     error.
  4. TWO supersessions → two history files (nothing clobbers inside history/ either).

Red-first: this file was run BEFORE archive_draw existed and failed loudly
(AttributeError) — the controls provably fire before any green is trusted.
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_lexica_def as B

# Minimal but real save_draw inputs (the test_repair_pass ctx shape).
SID = "G9999"
GSET = [("gift", 3)]
CTX = [("Pro", 18, 16, "gift", "", "A gift of a man widens him; and sits him by monarchs.", "", "")]


def hist_files():
    hdir = os.path.join(B.DRAWS_DIR, "history")
    return sorted(os.listdir(hdir)) if os.path.isdir(hdir) else []


def main():
    tmp = tempfile.mkdtemp(prefix="draws_test_")
    old_dir = B.DRAWS_DIR
    B.DRAWS_DIR = tmp
    try:
        # ── 1. SUPERSEDE: a second save with different prose archives the first.
        B.save_draw(SID, "lemma", "translit", GSET, CTX, "first prose")
        with open(B.draw_path(SID), encoding="utf-8") as f:
            first = json.load(f)
        B.save_draw(SID, "lemma", "translit", GSET, CTX, "second prose")
        h = hist_files()
        assert len(h) == 1, f"supersession did not archive: {h}"
        with open(os.path.join(tmp, "history", h[0]), encoding="utf-8") as f:
            archived = json.load(f)
        assert archived == first, "archived draw is not byte-faithful to the superseded one"
        assert archived["raw"] == "first prose"
        with open(B.draw_path(SID), encoding="utf-8") as f:
            assert json.load(f)["raw"] == "second prose"

        # ── 2. IDENTICAL REFRESH: same input + same prose → no new archive.
        B.save_draw(SID, "lemma", "translit", GSET, CTX, "second prose")
        assert len(hist_files()) == 1, "a byte-identical refresh was archived (duplicate salt)"

        # ── 3. TWO supersessions → two history files, both intact.
        B.save_draw(SID, "lemma", "translit", GSET, CTX, "third prose")
        h = hist_files()
        assert len(h) == 2, h
        raws = set()
        for name in h:
            with open(os.path.join(tmp, "history", name), encoding="utf-8") as f:
                raws.add(json.load(f)["raw"])
        assert raws == {"first prose", "second prose"}, raws

        # ── 4. UNREADABLE old file: archived, never clobbered or discarded.
        with open(B.draw_path(SID), "w", encoding="utf-8") as f:
            f.write("{not json")
        B.save_draw(SID, "lemma", "translit", GSET, CTX, "fourth prose")
        h = hist_files()
        assert len(h) == 3, h
        unreadable = [n for n in h if "unreadab" in n]   # the sig slot is sig[:8]
        assert len(unreadable) == 1, h
        with open(os.path.join(tmp, "history", unreadable[0]), encoding="utf-8") as f:
            assert f.read() == "{not json", "unreadable bytes were not preserved intact"
    finally:
        B.DRAWS_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)

    print("test_draw_history: ok")


if __name__ == "__main__":
    main()
