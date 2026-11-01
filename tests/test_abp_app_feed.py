"""Locked tests for scripts/abp_app_feed.py — the frozen ABP app-feed reader
(DESIGN_q2_build.md §3, §4; rulings §9.1, §9.2, §9.9, §9.10-§9.16).

Synthetic feed + synthetic manifest only (§9.15: no committed slice of the third-party
feed). The real-TSV case runs only when abp_app_html/abp_app_slots_italic.tsv is present
(PA, or the local second copy) and is skipped otherwise. No database anywhere.

Cases:
  pins      feed sha + size match → rows; one changed byte → STOP; wrong size → STOP;
            no manifest entry → STOP; count-differs file vs its .sha256 (ok / changed).
  shape     header must be the nine columns; unknown app book name → STOP; italic 0/1;
            italic 0 with italic_words → STOP; slot_index 0..n-1; verse not contiguous → STOP.
  keying    Psalm-title shift (our v0 ↔ feed v1); feed-only inside the versification class
            = allowed and attributed; a planted feed-only verse outside it → STOP.
  cli       --check-style report on synthetic keys exits 0 / 1.
  real      the committed manifest pins the local TSV; 31,238 verses; feed-only 10, all
            inside the frozen class (skips when the TSV is absent).

Run:  python tests/test_abp_app_feed.py
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import abp_app_feed as feed  # noqa: E402

HEADER = "\t".join(feed.COLUMNS)
ROWS = [
    # book, chapter, verse, slot_index, strongs, greek, english, italic, italic_words
    ("Genesis", 1, 1, 0, "1722", "εν", "In", 0, ""),
    ("Genesis", 1, 1, 1, "746", "αρχή", "the beginning", 1, "the"),
    ("Psalms", 3, 1, 0, "5568", "ψαλμός", "A psalm", 0, ""),       # app title = verse 1
    ("Psalms", 3, 2, 0, "2962", "κύριε", "O LORD", 0, ""),
    ("Habakkuk", 3, 20, 0, "1473", "εγώ", "I", 0, ""),            # app-only verse, class 3
    ("1 Peter", 3, 12, 0, "3754", "ότι", "For", 0, ""),
]
OURS = {("Gen", 1, 1), ("Psa", 3, 0), ("Psa", 3, 1), ("Hab", 3, 19), ("1Pe", 3, 12)}
VCLASS = {("Pro", 16), ("Pro", 24), ("Jer", 10), ("Hab", 3)}


def _line(r):
    return "\t".join(str(x) for x in r)


class Synthetic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rows=ROWS, header=HEADER, pin=True, pin_bytes=None):
        p = self.d / "feed.tsv"
        p.write_bytes((header + "\n" + "".join(_line(r) + "\n" for r in rows)).encode("utf-8"))
        m = self.d / "manifest.json"
        files = {}
        if pin:
            data = p.read_bytes()
            files[feed.FEED_LABEL] = {"sha256": hashlib.sha256(data).hexdigest(),
                                      "bytes": pin_bytes if pin_bytes is not None else len(data)}
        m.write_text(json.dumps({"created": "test", "files": files}), encoding="utf-8")
        return p, m

    # ── pins ────────────────────────────────────────────────────────────────
    def test_pin_ok_returns_rows_verbatim(self):
        p, m = self.write()
        slots = feed.read_slots(p, m)
        self.assertEqual(len(slots), len(ROWS))
        self.assertEqual(slots[1]["english"], "the beginning")
        self.assertEqual(slots[1]["italic_words"], "the")
        self.assertEqual(slots[1]["abbrev"], "Gen")

    def test_one_changed_byte_stops(self):
        p, m = self.write()
        b = bytearray(p.read_bytes())
        i = b.index(b"In")
        b[i] = ord("A")                        # same size, different hash
        p.write_bytes(bytes(b))
        with self.assertRaisesRegex(feed.FeedError, "SHA"):
            feed.read_slots(p, m)

    def test_wrong_size_stops(self):
        p, m = self.write(pin_bytes=1)
        with self.assertRaisesRegex(feed.FeedError, "SIZE"):
            feed.verify_feed(p, m)

    def test_no_manifest_entry_stops(self):
        p, m = self.write(pin=False)
        with self.assertRaisesRegex(feed.FeedError, "no entry"):
            feed.verify_feed(p, m)

    def test_count_differs_sidecar(self):
        cd = self.d / "count_differs.tsv"
        cd.write_text("book\tchapter\tverse\tapp_verse\n1Pe\t3\t12\t12\n", encoding="utf-8", newline="\n")
        side = Path(str(cd) + ".sha256")
        side.write_text(hashlib.sha256(cd.read_bytes()).hexdigest() + "  count_differs.tsv\n",
                        encoding="utf-8")
        self.assertIn(("1Pe", 3, 12), feed.load_count_differs(cd))
        cd.write_text("book\tchapter\tverse\tapp_verse\n1Pe\t3\t13\t13\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(feed.FeedError, "SHA"):
            feed.load_count_differs(cd)
        side.unlink()
        with self.assertRaisesRegex(feed.FeedError, "no .sha256"):
            feed.load_count_differs(cd)

    # ── shape ───────────────────────────────────────────────────────────────
    def test_header_must_match(self):
        p, m = self.write(header="\t".join(feed.COLUMNS[:7]))
        with self.assertRaisesRegex(feed.FeedError, "header"):
            feed.read_slots(p, m)

    def test_unknown_book_stops(self):
        p, m = self.write(rows=ROWS + [("Hezekiah", 1, 1, 0, "1", "x", "y", 0, "")])
        with self.assertRaisesRegex(feed.FeedError, "no mapping"):
            feed.read_slots(p, m)

    def test_italic_shape(self):
        p, m = self.write(rows=[("Genesis", 1, 1, 0, "1722", "εν", "In", 2, "")])
        with self.assertRaisesRegex(feed.FeedError, "not 0/1"):
            feed.read_slots(p, m)
        p, m = self.write(rows=[("Genesis", 1, 1, 0, "1722", "εν", "In", 0, "In")])
        with self.assertRaisesRegex(feed.FeedError, "italic 0 with"):
            feed.read_slots(p, m)

    def test_grouping_keeps_slot_order(self):
        p, m = self.write()
        v = feed.group_verses(feed.read_slots(p, m))
        self.assertEqual([s["english"] for s in v[("Gen", 1, 1)]], ["In", "the beginning"])
        self.assertEqual(len(v), 5)

    def test_slot_gap_stops(self):
        rows = [ROWS[0], ("Genesis", 1, 1, 2, "746", "αρχή", "the beginning", 0, "")]
        p, m = self.write(rows=rows)
        with self.assertRaisesRegex(feed.FeedError, "slot_index"):
            feed.group_verses(feed.read_slots(p, m))

    def test_verse_not_contiguous_stops(self):
        rows = [ROWS[0], ROWS[2], ("Genesis", 1, 1, 1, "746", "αρχή", "the beginning", 0, "")]
        p, m = self.write(rows=rows)
        with self.assertRaisesRegex(feed.FeedError, "contiguous"):
            feed.group_verses(feed.read_slots(p, m))

    # ── keying ──────────────────────────────────────────────────────────────
    def feed_keys(self):
        p, m = self.write()
        return feed.group_verses(feed.read_slots(p, m)).keys()

    def test_psalm_title_shift(self):
        res = feed.pair_keys(OURS, self.feed_keys(), VCLASS)
        self.assertEqual(res["pairs"][("Psa", 3, 0)], ("Psa", 3, 1))
        self.assertEqual(res["pairs"][("Psa", 3, 1)], ("Psa", 3, 2))
        self.assertEqual(res["psalm_shift"], {("Psa", 3)})

    def test_feed_only_inside_class_is_attributed(self):
        res = feed.pair_keys(OURS, self.feed_keys(), VCLASS)
        self.assertEqual(res["feed_only"], [("Hab", 3, 20)])
        self.assertEqual(res["ours_only"], [("Hab", 3, 19)])
        self.assertEqual(res["feed_only_outside"], [])

    def test_planted_feed_only_outside_class_stops(self):
        keys = list(self.feed_keys()) + [("Gen", 1, 99)]
        res = feed.pair_keys(OURS, keys, VCLASS)
        self.assertEqual(res["feed_only_outside"], [("Gen", 1, 99)])

    def test_report_exit_codes(self):
        p, m = self.write()
        verses = feed.group_verses(feed.read_slots(p, m))
        self.assertEqual(feed._report("t", OURS, verses, VCLASS, None), 0)
        self.assertEqual(feed._report("t", OURS - {("Gen", 1, 1)}, verses, VCLASS, None), 1)

    def test_committed_versification_class(self):
        self.assertEqual(feed.load_versification_class(), VCLASS)


@unittest.skipUnless(feed.FEED_PATH.is_file(), "real feed TSV not present (gitignored)")
class RealFeed(unittest.TestCase):
    def test_real_feed_pin_and_keying(self):
        slots = feed.read_slots()
        verses = feed.group_verses(slots)
        self.assertEqual(len(slots), 577994)
        self.assertEqual(len(verses), 31238)
        res = feed.pair_keys(feed.abp_texts_keys(), verses.keys(), feed.load_versification_class())
        self.assertEqual(len(res["psalm_shift"]), 147)
        self.assertEqual(len(res["feed_only"]), 10)
        self.assertEqual(len(res["ours_only"]), 9)
        self.assertEqual(res["feed_only_outside"], [])


if __name__ == "__main__":
    unittest.main()
