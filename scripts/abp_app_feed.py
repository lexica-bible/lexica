#!/usr/bin/env python3
"""
abp_app_feed.py — the ONE reader of the frozen ABP app-edition feed (edition-upgrade lane,
docs/handoffs/DESIGN_q2_build.md §3, §4; rulings §9.1, §9.2, §9.9, §9.10-§9.16).

A shared LIBRARY: derivation A (English rows) and derivation B (prose) each import it and each
read the frozen bytes themselves, in their own process (§9.7). Nothing here writes a file that
either side reads. The reader only VERIFIES, READS and GROUPS — every cell is passed through
verbatim; it never joins, flattens or reorders English (charter §4.3: "if both come from one
flattening step the gate measures nothing").

The library opens no database (§9.10). It never re-derives the count-differs set — that is the
separate gated census step on the copy (census_count_differs.py vs the frozen file); the reader
only checks the frozen file against its .sha256 and loads it.

Pins (stop on any mismatch, before a single row is handed out):
  * feed sha256 AND byte size == cert_manifest.json["files"][FEED_LABEL]   (DESIGN §3)
    — the literal hash lives only in the manifest, never here.
  * frozen count-differs file == its .sha256 sidecar                        (§9.2 / §9.10)

Verse keying (§4): (abbrev, chapter, verse) after APP_TO_ABBREV (imported from the audit, never
copied). Psalm-title rule: where OUR side has verse 0 in a Psalm chapter, our v pairs with the
feed's v+1. A feed-only verse = STOP unless its chapter is in the frozen versification class
(tests/fixtures/edition_upgrade/versification_class.json, §9.11).

CLI (read-only):
  python3 scripts/abp_app_feed.py --check [--count-differs FILE]
      pins + header + per-cell shape + grouping, then keys the feed against abp_texts/ (repo files).
  python3 scripts/abp_app_feed.py --attribute <copy.db> [--count-differs FILE]
      the §9.9 dry run: keys the feed against the COPY's verses rows (opened mode=ro, read only
      for its verse keys) and attributes 31,237 vs 31,238. Run on PA is a later gated step.
Exit 0 = every check passed; exit 1 = STOP, the reason printed.
"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter, OrderedDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_abp_app_vs_surface import APP_TO_ABBREV  # noqa: E402  (one book map, never a copy)

FEED_LABEL = "abp_app_html/abp_app_slots_italic.tsv"
FEED_PATH = BASE_DIR / FEED_LABEL
MANIFEST_PATH = BASE_DIR / "cert_manifest.json"
VCLASS_PATH = BASE_DIR / "tests" / "fixtures" / "edition_upgrade" / "versification_class.json"
COLUMNS = ["book", "chapter", "verse", "slot_index", "strongs", "greek", "english",
           "italic", "italic_words"]


class FeedError(Exception):
    """Any pin, shape or keying failure. Callers stop on it; nothing is skipped."""


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── pins ─────────────────────────────────────────────────────────────────────
def verify_feed(feed_path=FEED_PATH, manifest_path=MANIFEST_PATH, label=FEED_LABEL):
    """Feed sha256 and byte size must equal the manifest's entry. Returns the sha."""
    feed_path, manifest_path = Path(feed_path), Path(manifest_path)
    if not manifest_path.is_file():
        raise FeedError(f"manifest not found: {manifest_path}")
    pinned = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {}).get(label)
    if not pinned:
        raise FeedError(f"manifest {manifest_path.name} has no entry for {label}")
    if not feed_path.is_file():
        raise FeedError(f"feed not found: {feed_path}")
    size = feed_path.stat().st_size
    if size != pinned["bytes"]:
        raise FeedError(f"feed SIZE {size:,} != pinned {pinned['bytes']:,} ({label})")
    sha = _sha256(feed_path)
    if sha != pinned["sha256"]:
        raise FeedError(f"feed SHA {sha} != pinned {pinned['sha256']} ({label})")
    return sha


def verify_sidecar(path):
    """`<file>.sha256` (sha256sum format: '<hex>  name' or '<hex> *name') must match the file."""
    path = Path(path)
    side = Path(str(path) + ".sha256")
    if not path.is_file():
        raise FeedError(f"file not found: {path}")
    if not side.is_file():
        raise FeedError(f"no .sha256 beside {path}")
    want = side.read_text(encoding="utf-8").split()[0].lower()
    got = _sha256(path)
    if got != want:
        raise FeedError(f"SHA {got} != {side.name} {want} ({path.name})")
    return got


# ── feed rows ────────────────────────────────────────────────────────────────
def read_slots(feed_path=FEED_PATH, manifest_path=MANIFEST_PATH, label=FEED_LABEL):
    """Verify the pin, then return every slot in file order as a dict with the key fields
    `abbrev`, `chapter`, `verse`, `slot_index` (ints) and the cells verbatim."""
    verify_feed(feed_path, manifest_path, label)
    slots = []
    with open(feed_path, encoding="utf-8", newline="") as f:
        rd = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(rd, None)
        if header != COLUMNS:
            raise FeedError(f"feed header {header} != {COLUMNS}")
        unknown = Counter()
        for n, row in enumerate(rd, start=2):
            if len(row) != len(COLUMNS):
                raise FeedError(f"line {n}: {len(row)} cells, expected {len(COLUMNS)}")
            r = dict(zip(COLUMNS, row))
            ab = APP_TO_ABBREV.get(r["book"])
            if ab is None:
                unknown[r["book"]] += 1
                continue
            if r["italic"] not in ("0", "1"):
                raise FeedError(f"line {n}: italic {r['italic']!r} not 0/1")
            if r["italic"] == "0" and r["italic_words"] != "":
                raise FeedError(f"line {n}: italic 0 with italic_words {r['italic_words']!r}")
            try:
                ch, v, si = int(r["chapter"]), int(r["verse"]), int(r["slot_index"])
            except ValueError:
                raise FeedError(f"line {n}: chapter/verse/slot_index not numbers")
            r.update(abbrev=ab, chapter=ch, verse=v, slot_index=si, italic=int(r["italic"]))
            slots.append(r)
    if unknown:
        raise FeedError(f"app book names with no mapping: {dict(unknown)}")
    return slots


def group_verses(slots):
    """(abbrev, chapter, verse) -> ordered slot list. Each verse's slot_index must run
    0..n-1 with no gap or repeat, and a verse's slots must be contiguous in the file."""
    out, last = OrderedDict(), None
    for s in slots:
        k = (s["abbrev"], s["chapter"], s["verse"])
        if k in out and k != last:
            raise FeedError(f"verse {k} is not contiguous in the feed")
        out.setdefault(k, []).append(s)
        last = k
    for k, lst in out.items():
        idx = [s["slot_index"] for s in lst]
        if idx != list(range(len(lst))):
            raise FeedError(f"verse {k}: slot_index {idx[:8]}... is not 0..{len(lst) - 1}")
    return out


# ── frozen side files ────────────────────────────────────────────────────────
def load_versification_class(path=VCLASS_PATH):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return {(b, int(c)) for b, c in doc["chapters"]}


def load_count_differs(path):
    """The frozen census member list (census_count_differs.py --out format). Checked against
    its .sha256 first. Returns {(abbrev, chapter, verse): row dict} keyed on OUR verse."""
    verify_sidecar(path)
    out = {}
    with open(path, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for r in rd:
            k = (r["book"], int(r["chapter"]), int(r["verse"]))
            if k in out:
                raise FeedError(f"count-differs file repeats {k}")
            out[k] = r
    return out


# ── keying (§4, §9.9) ────────────────────────────────────────────────────────
def pair_keys(our_keys, feed_keys, vclass):
    """Pair our verse keys with feed verse keys. Returns a dict:
       pairs {our: feed}, psalm_shift {(b, ch)}, ours_only [..], feed_only [..],
       feed_only_outside [..] (non-empty = STOP)."""
    our_keys, feed_keys = set(our_keys), set(feed_keys)
    shift = {(b, ch) for (b, ch, v) in our_keys if b == "Psa" and v == 0}
    pairs, ours_only = {}, []
    for k in sorted(our_keys):
        b, ch, v = k
        ka = (b, ch, v + 1) if (b, ch) in shift else k
        if ka in feed_keys:
            pairs[k] = ka
        else:
            ours_only.append(k)
    used = set(pairs.values())
    feed_only = sorted(k for k in feed_keys if k not in used)
    outside = [k for k in feed_only if (k[0], k[1]) not in vclass]
    return {"pairs": pairs, "psalm_shift": shift, "ours_only": ours_only,
            "feed_only": feed_only, "feed_only_outside": outside}


def abp_texts_keys():
    """Our verse keys from the committed abp_texts/ files (the build's own parser)."""
    from build_words_from_abp import iter_verses, _abp_sources
    return {(b, c, v) for b, c, v, _w in iter_verses(*_abp_sources())}


def copy_verse_keys(db_path):
    """Our verse keys from a db COPY's verses rows — opened read-only (mode=ro)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return {(b, c, v) for b, c, v in con.execute("SELECT book, chapter, verse FROM verses")}
    finally:
        con.close()


# ── CLI ──────────────────────────────────────────────────────────────────────
def _report(label, our_keys, verses, vclass, count_differs):
    res = pair_keys(our_keys, verses.keys(), vclass)
    print(f"ours ({label}) verses {len(our_keys):,} · feed verses {len(verses):,} · "
          f"difference {len(verses) - len(our_keys):+d}")
    print(f"Psalm-title shift chapters {len(res['psalm_shift'])} · paired {len(res['pairs']):,}")
    print(f"ours-only {len(res['ours_only'])}: " + ", ".join(f"{b} {c}:{v}" for b, c, v in res["ours_only"]))
    print(f"feed-only {len(res['feed_only'])}: " + ", ".join(f"{b} {c}:{v}" for b, c, v in res["feed_only"]))
    print(f"   feed-only by chapter: " + ", ".join(
        f"{b} {c} ×{n}" for (b, c), n in sorted(Counter((b, c) for b, c, _ in res["feed_only"]).items())))
    print(f"   attribution: feed - ours = {len(res['feed_only'])} feed-only - {len(res['ours_only'])} ours-only"
          f" = {len(res['feed_only']) - len(res['ours_only']):+d}")
    if count_differs is not None:
        missing = sorted(k for k in count_differs if k not in our_keys)
        print(f"count-differs frozen members {len(count_differs):,} · not among our verses {len(missing)}")
        if missing:
            print("STOP: count-differs members with no verse on our side: " + ", ".join(map(str, missing[:20])))
            return 1
    if res["feed_only_outside"]:
        print("STOP: feed-only verse(s) outside the versification class: " +
              ", ".join(f"{b} {c}:{v}" for b, c, v in res["feed_only_outside"]))
        return 1
    print("feed-only outside versification class: 0")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only checks on the frozen ABP app feed.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="pins + shape, keyed against abp_texts/")
    g.add_argument("--attribute", metavar="COPY_DB", help="§9.9 dry run, keyed against the copy's verses")
    ap.add_argument("--feed", default=str(FEED_PATH))
    ap.add_argument("--manifest", default=str(MANIFEST_PATH))
    ap.add_argument("--vclass", default=str(VCLASS_PATH))
    ap.add_argument("--count-differs", metavar="FILE", help="frozen census member list (+ .sha256)")
    a = ap.parse_args(argv)
    try:
        sha = verify_feed(a.feed, a.manifest)
        print(f"feed pin OK: {FEED_LABEL} sha256 {sha} · {Path(a.feed).stat().st_size:,} bytes")
        slots = read_slots(a.feed, a.manifest)
        verses = group_verses(slots)
        books = {s["abbrev"] for s in slots}
        it = sum(s["italic"] for s in slots)
        print(f"slots {len(slots):,} · verses {len(verses):,} · books {len(books)} · "
              f"italic slots {it:,}")
        vclass = load_versification_class(a.vclass)
        print(f"versification class: {len(vclass)} chapters " +
              ", ".join(f"{b} {c}" for b, c in sorted(vclass)))
        cd = None
        if a.count_differs:
            cd = load_count_differs(a.count_differs)
            print(f"count-differs pin OK: {Path(a.count_differs).name}")
        if a.check:
            ours, label = abp_texts_keys(), "abp_texts/"
        else:
            # <copy> is mandatory with no default — it must never fall through to live.
            if not a.attribute or not Path(a.attribute).is_file():
                raise FeedError(f"--attribute needs an existing copy db path, got {a.attribute!r}")
            ours, label = copy_verse_keys(a.attribute), f"copy {a.attribute}"
        rc = _report(label, ours, verses, vclass, cd)
    except FeedError as e:
        print(f"STOP: {e}")
        return 1
    print("RESULT: " + ("PASS" if rc == 0 else "STOP"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
