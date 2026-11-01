"""Locked tests for derivation A — the app-feed English transplant in
scripts/build_words_from_abp.py (DESIGN_q2_build.md §9.17-§9.47).

Part 1 — DEFAULT PATH IS BYTE-IDENTICAL (§9.43). `default_path_digest()` runs
build_verse_words over EVERY committed abp_texts/ verse three ways (bare; with the
ruling-10 attestation map + name roster; with synthetic BibleHub rows so bh_lookup
really matches) and hashes the outputs. BASELINE_DIGEST was computed with the build
as committed at 4737662e, BEFORE the bh_match_english keyword existed. No database.

Run:  python tests/test_app_transplant.py
"""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_words_from_abp as B  # noqa: E402

# Computed twice (same value) on the unmodified build at 4737662e, 2026-10-31.
BASELINE_DIGEST = "f6f7f58ba3370eecb704c513e883d5125de9416bf4e643a4409286c9479805e3"


def _synthetic_bh(words):
    """BibleHub-shaped rows built from the verse itself, reversed so the base-only
    fallback in bh_lookup matters: (base, norm_english, gpos, italic_words, smcap)."""
    rows = []
    for i, w in enumerate(words):
        raw = w[1]
        if not raw or raw == "G*":
            continue
        base = raw[1:].split(".")[0]
        rows.append((base, B.normalize(w[0]), i + 1, w[0].split()[0].lower() if w[0] else "", ""))
    return list(reversed(rows))


def default_path_digest():
    ren = B.build_attestation_map()
    names = B.load_name_roster()
    h = hashlib.sha256()
    n = 0
    for abbrev, ch, v, words in B.iter_verses(*B._abp_sources()):
        a = B.build_verse_words(words, [], None)
        b = B.build_verse_words(words, [], None, ren=ren, article_refusals=[],
                                names=names, pn_star_refusals=[])
        c = B.build_verse_words(words, _synthetic_bh(words), None)
        h.update(repr((abbrev, ch, v, a, b, c)).encode("utf-8"))
        n += 1
    return n, h.hexdigest()


class DefaultPath(unittest.TestCase):
    def test_default_path_byte_identical(self):
        n, d = default_path_digest()
        self.assertEqual(n, 31237)
        self.assertEqual(d, BASELINE_DIGEST)

    def test_keyword_with_own_english_is_identity(self):
        words = B.parse_abp_line("(Gen 1:1)  InG1722 the beginningG746 God madeG4160 G3588 G2316")[3]
        bh = _synthetic_bh(words)
        self.assertEqual(B.build_verse_words(words, bh, None),
                         B.build_verse_words(words, bh, None, bh_match_english=[w[0] for w in words]))

    def test_keyword_matches_bibilehub_on_given_english(self):
        words = [("alpha", "G100", None, False, False), ("beta", "G100", None, False, False)]
        bh = [("100", "beta", 7, "", ""), ("100", "alpha", 3, "", "")]
        self.assertEqual([r[5] for r in B.build_verse_words(words, bh, None)], [3, 7])
        swapped = B.build_verse_words(words, bh, None, bh_match_english=["beta", "alpha"])
        self.assertEqual([r[5] for r in swapped], [7, 3])
        with self.assertRaises(ValueError):
            B.build_verse_words(words, bh, None, bh_match_english=["only one"])


# ── Part 2 — the transplant on synthetic feed + synthetic abp_texts lines ─────────
import csv as _csv          # noqa: E402
import json as _json        # noqa: E402
import os as _os            # noqa: E402
import sqlite3 as _sqlite3  # noqa: E402
import tempfile as _tempfile  # noqa: E402
import abp_app_feed as F    # noqa: E402

APP_NAME = {"Gen": "Genesis", "Pro": "Proverbs", "Mat": "Matthew", "Exo": "Exodus"}


class Env:
    """A temp directory holding a synthetic feed, manifest, censuses and frozen files."""

    def __init__(self, src, feed, cd=(), dash=(), markup=(), glue=(), vclass=(("Pro", 16),),
                 dash_pin=None, fold_pin=None, bracket=(), correction=()):
        self.tmp = _tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        fp = d / "feed.tsv"
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(F.COLUMNS) + "\n")
            for (ab, ch, v), slots in feed.items():
                for i, (strongs, eng) in enumerate(slots):
                    f.write(f"{APP_NAME[ab]}\t{ch}\t{v}\t{i}\t{strongs}\tx\t{eng}\t0\t\n")
        mp = d / "manifest.json"
        data = fp.read_bytes()
        mp.write_text(_json.dumps({"files": {F.FEED_LABEL: {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}}}), encoding="utf-8")
        vp = d / "vclass.json"
        vp.write_text(_json.dumps({"chapters": [list(c) for c in vclass]}), encoding="utf-8")

        def frozen(name, header, rows):
            p = d / name
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\t".join(header) + "\n")
                for r in rows:
                    f.write("\t".join(str(x) for x in r) + "\n")
            Path(str(p) + ".sha256").write_text(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + name + "\n")
            return p
        self.cd = frozen("cd.tsv", ["book", "chapter", "verse"], cd)
        dp = frozen("dash.tsv", ["book", "chapter", "verse", "slot_index", "shape"], dash)
        kp = frozen("markup.tsv", ["book", "chapter", "verse", "slot_index", "class"], markup)
        gp = frozen("glue.tsv", ["book", "chapter", "verse", "slot_index", "feed_word", "verdict"], glue)
        bp = frozen("bracket.tsv", ["book", "chapter", "verse", "class"], bracket)
        cp = frozen("correction.tsv", ["book", "chapter", "verse"], correction)
        self.src = src
        self.kw = dict(feed_path=fp, manifest_path=mp, vclass_path=vp, dash_path=dp,
                       markup_path=kp, glue_path=gp, bracket_path=bp, correction_path=cp,
                       dash_pin=dash_pin, fold_pin=fold_pin)

    def app(self, count_differs="frozen"):
        return B.AppTransplant(self.src, count_differs=self.cd if count_differs == "frozen" else count_differs,
                               **self.kw)

    def close(self):
        self.tmp.cleanup()


def run_verse(app, src, key, lex=None):
    raw = B.parse_abp_line(f"({key[0]} {key[1]}:{key[2]}) {src[key]}")[3]
    old = B.build_verse_words(raw, [], lex)
    return app.apply(key, raw, None, old, [], lex), old


GEN = ("Gen", 1, 1)
GEN_SRC = "InG1722 the beginningG746 God madeG4160 G3588 G2316 theG3588 heavenG3772"
GEN_FEED = [("1722", "In"), ("746", "the beginning"), ("4160-3588-2316", "God created"),
            ("3588", "the"), ("3772", "sky")]


class Transplant(unittest.TestCase):
    def env(self, **kw):
        e = Env(**kw)
        self.addCleanup(e.close)
        return e

    def test_strict_pass_english_from_feed_greek_from_old(self):
        e = self.env(src={GEN: GEN_SRC}, feed={GEN: GEN_FEED})
        app = e.app()
        rows, old = run_verse(app, e.src, GEN)
        self.assertEqual(app.tally["transplanted"], 1)
        self.assertEqual([r[1] for r in rows], ["In", "the beginning", "God created", None, None, "the", "sky"])
        for o, r in zip(old, rows):     # Greek side + italics identical to the OLD set
            self.assertEqual((o[0], o[3], o[4], o[7], o[8], o[9], o[10], o[11]),
                             (r[0], r[3], r[4], r[7], r[8], r[9], r[10], r[11]))

    def test_frozen_member_kept(self):
        k = ("Gen", 1, 2)
        src = {GEN: GEN_SRC, k: "AndG2532 itG1473"}
        feed = {GEN: GEN_FEED, k: [("2532", "And"), ("1473-1510", "it was")]}
        e = self.env(src=src, feed=feed, cd=[k])
        app = e.app()
        rows, old = run_verse(app, src, k)
        self.assertIs(rows, old)
        self.assertEqual(app.tally["count_differs"], 1)

    def test_frozen_drift_stops(self):
        k = ("Gen", 1, 2)
        src = {GEN: GEN_SRC, k: "AndG2532 itG1473"}
        feed = {GEN: GEN_FEED, k: [("2532", "And"), ("1473-1510", "it was")]}
        e = self.env(src=src, feed=feed, cd=[])
        with self.assertRaisesRegex(F.FeedError, "drifted"):
            e.app()

    def strict_fail(self, src_text, feed_slots, lex=None, **kw):
        e = self.env(src={GEN: src_text}, feed={GEN: feed_slots}, **kw)
        app = e.app()
        rows, old = run_verse(app, e.src, GEN, lex)
        self.assertIs(rows, old)
        self.assertEqual(app.tally["strict_fail"], 1)
        return app.strict_fail[0]

    def test_dotted(self):
        r = self.strict_fail("[2wingedG4071 1feathered]G4420", [("4071", "[2winged"), ("4420.2", "1feathered]")])
        self.assertEqual(r[3:], (1, "4420", "4420.2", "dotted"))

    def test_swap(self):
        r = self.strict_fail("AndG2532 thatG3754", [("3754", "that"), ("2532", "and")])
        self.assertEqual(r[3:], (0, "2532", "3754", "swap"))

    def test_other(self):
        r = self.strict_fail("AndG2532 thatG3754", [("2532", "And"), ("3739", "which")])
        self.assertEqual(r[3:], (1, "3754", "3739", "other"))

    def test_rows(self):
        r = self.strict_fail("soG3779 let walkG4043", [("3779", "so"), ("4043", "1let 2walk")])
        self.assertEqual(r[-1], "rows")

    def test_passdiff_lump(self):
        # OLD "Jesus the" on the article + empty star: _split_pn_article_lump fires in the OLD
        # set only; the FEED set has no lump -> the sets disagree on Strong's -> passdiff.
        r = self.strict_fail("Jesus theG3588 G* saidG2036",
                             [("3588", "the"), ("*", "Jesus"), ("2036", "said")])
        self.assertEqual(r[-1], "passdiff")

    def test_passdiff_split(self):
        # _split_compounds (lexicon on) moves "God" in the OLD set and reorders positions;
        # the FEED's one-word gloss gives it nothing to move -> passdiff.
        r = self.strict_fail("God madeG4160 G3588 G2316", [("4160-3588-2316", "created")],
                             lex={"2316": {"god"}, "4160": {"make", "made"}, "3588": {"the"}})
        self.assertEqual(r[-1], "passdiff")

    def test_untagged(self):
        r = self.strict_fail("AndG2532 thatG3754 G", [("2532", "And"), ("3754", "that")])
        self.assertEqual(r[-1], "untagged")

    def test_dash_reason(self):
        r = self.strict_fail(GEN_SRC, GEN_FEED, dash=[("Gen", 1, 1, 4, "mid_space_hyphen")])
        # first_diff_pos is the position on OUR Strong's spine (slot 2 expands to 3 parts)
        self.assertEqual(r[3:], (6, "3772", "3772", "dash"))

    def test_markup_reason_marker_and_glue(self):
        r = self.strict_fail(GEN_SRC, GEN_FEED, markup=[("Gen", 1, 1, 1, "camel_glue")])
        self.assertEqual(r[3:], (1, "746", "746", "markup"))
        r = self.strict_fail(GEN_SRC, GEN_FEED, glue=[("Gen", 1, 1, 3, "x", "glued")])
        self.assertEqual(r[-1], "markup")

    def test_bracket_reason(self):
        r = self.strict_fail(GEN_SRC, GEN_FEED, bracket=[("Gen", 1, 1, "unclosed")])
        self.assertEqual(r[3:], ("", "", "", "bracket"))

    def test_correction_reason_wins_over_feed_shape_checks(self):
        r = self.strict_fail(GEN_SRC, GEN_FEED, correction=[GEN], bracket=[("Gen", 1, 1, "unclosed")],
                             markup=[("Gen", 1, 1, 1, "camel_glue")])
        self.assertEqual(r[-1], "correction")

    def test_eligible_artifact(self):
        k2 = ("Gen", 1, 2)
        src = {GEN: GEN_SRC, k2: "AndG2532 thatG3754"}
        e = self.env(src=src, feed={GEN: GEN_FEED, k2: [("3754", "that"), ("2532", "and")]})
        app = e.app()
        run_verse(app, src, GEN)
        run_verse(app, src, k2)
        import io
        from contextlib import redirect_stdout
        with _tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
            app.report(d, stamp="T")
            with open(Path(d) / "eligible_T.tsv", encoding="utf-8", newline="") as f:
                rows = list(_csv.DictReader(f, delimiter="\t"))
        self.assertEqual([(r["verse"], r["eligible"], r["reason"]) for r in rows],
                         [("1", "1", ""), ("2", "0", "swap")])

    def test_glue_wording_passes(self):
        e = self.env(src={GEN: GEN_SRC}, feed={GEN: GEN_FEED}, glue=[("Gen", 1, 1, 4, "sky", "wording")])
        app = e.app()
        run_verse(app, e.src, GEN)
        self.assertEqual(app.tally["transplanted"], 1)

    def test_versification_in_class_kept_and_outside_stops(self):
        k = ("Pro", 16, 2)
        src = {GEN: GEN_SRC, k: "AndG2532"}
        e = self.env(src=src, feed={GEN: GEN_FEED, k: [("2532", "But")], ("Pro", 16, 40): [("1", "x")]})
        app = e.app()
        rows, old = run_verse(app, src, k)
        self.assertIs(rows, old)
        self.assertEqual(app.tally["versification"], 1)
        e2 = self.env(src={GEN: GEN_SRC}, feed={GEN: GEN_FEED, ("Gen", 1, 40): [("1", "x")]})
        with self.assertRaisesRegex(F.FeedError, "outside the versification class"):
            e2.app()

    def test_dash_normalization_and_pin(self):
        feed = [("1722", "In"), ("746", "the beginning -"), ("4160-3588-2316", "God made"),
                ("3588", "the"), ("3772", "heaven")]
        e = self.env(src={GEN: GEN_SRC}, feed={GEN: feed}, dash_pin=1, fold_pin=0)
        rows, _ = run_verse(e.app(), e.src, GEN)
        self.assertEqual(rows[1][1], "the beginning --")
        e2 = self.env(src={GEN: GEN_SRC}, feed={GEN: feed}, dash_pin=2)
        with self.assertRaisesRegex(F.FeedError, "pinned 2"):
            e2.app()

    def test_space_folding_and_pin(self):
        feed = [("1722", "In"), ("746", "the  beginning"), ("4160-3588-2316", "God made"),
                ("3588", "the"), ("3772", "heaven")]
        e = self.env(src={GEN: GEN_SRC}, feed={GEN: feed}, dash_pin=0, fold_pin=1)
        rows, _ = run_verse(e.app(), e.src, GEN)
        self.assertEqual(rows[1][1], "the beginning")
        e2 = self.env(src={GEN: GEN_SRC}, feed={GEN: feed}, fold_pin=5)
        with self.assertRaisesRegex(F.FeedError, "pinned 5"):
            e2.app()

    def test_ours_only_kept(self):
        k = ("Gen", 1, 3)
        e = self.env(src={GEN: GEN_SRC, k: "AndG2532"}, feed={GEN: GEN_FEED})
        app = e.app()
        rows, old = run_verse(app, e.src, k)
        self.assertIs(rows, old)
        self.assertEqual(app.tally["ours_only"], 1)


@unittest.skipUnless(F.FEED_PATH.is_file(), "real feed TSV not present (gitignored)")
class DryRunWritesNoDb(unittest.TestCase):
    def test_dry_run_leaves_copy_and_scrape_untouched(self):
        with _tempfile.TemporaryDirectory() as d:
            copy, scrape, out = Path(d) / "copy.db", Path(d) / "scrape.db", Path(d) / "runs"
            con = _sqlite3.connect(copy)
            con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT)")
            con.execute("INSERT INTO verses (book, chapter, verse) VALUES ('Gen', 1, 1)")
            con.execute("CREATE TABLE lexicon (strongs TEXT, kjv_def TEXT, strongs_def TEXT)")
            con.commit(); con.close()
            con = _sqlite3.connect(scrape)
            con.execute("CREATE TABLE bh_words (book TEXT, chapter INT, verse INT, position INT, strongs TEXT,"
                        " english TEXT, italic_words TEXT, smcap_words TEXT, greek_pos INT)")
            con.commit(); con.close()
            before = {p: (hashlib.sha256(p.read_bytes()).hexdigest(), _os.path.getmtime(p)) for p in (copy, scrape)}
            argv = sys.argv
            sys.argv = ["build_words_from_abp.py", "x.db", str(scrape), "--dry-run", str(copy), "--out", str(out)]
            try:
                import io
                from contextlib import redirect_stdout
                buf = io.StringIO()
                with redirect_stdout(buf):
                    B.main()
            finally:
                sys.argv = argv
            after = {p: (hashlib.sha256(p.read_bytes()).hexdigest(), _os.path.getmtime(p)) for p in (copy, scrape)}
            self.assertEqual(before, after)
            self.assertFalse(Path(d, "copy.db.new").exists())
            self.assertIn("transplanted", buf.getvalue())
            self.assertTrue((out / "strict_fail_20261031.tsv").is_file())
            self.assertTrue((out / "eligible_20261031.tsv").is_file())

    def test_empty_copy_path_refused(self):
        argv = sys.argv
        sys.argv = ["build_words_from_abp.py", "--dry-run", ""]
        try:
            with self.assertRaises(SystemExit):
                B.main()
        finally:
            sys.argv = argv


if __name__ == "__main__":
    unittest.main()
