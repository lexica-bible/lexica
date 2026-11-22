"""Locked tests for the --app-feed mode of the L9 split lint and its sizing partner
(scripts/lint_split_wrong_slot.py, scripts/size_split_compounds.py; edition upgrade DESIGN
§9.214, §9.239). Hand-built OLD-vs-FEED verses on the build's own transplant (the synthetic
feed of tests/test_app_transplant.py's Env) and a made-up lexicon; no real database.

What is proved:
  A  the recipients come from the COMPOSED rows: a verse where both runs split onto the same
     slot with different words is reported with the FEED word (default mode: the OLD word);
  B  a verse the build keeps on the OLD rows (passdiff) is reported with the OLD recipient;
  C  ownership of a composed cell, all three branches (FEED / OLD restore / neither), read
     the same way by the lint and by the sizer, which are coded apart and must agree;
  D  the words-table check: match, a planted different head, a planted missing row, a
     planted row-count difference - each fires;
  E  main --app-feed end to end on a temp db: clean run prints the RESULT line; the frozen
     merge-pair / edge-split lists not matching the replay = STOP, exit 1;
  F  the default mode is unchanged: it still replays the OLD text only.

Run:  python tests/test_split_lint_app.py
"""
import contextlib
import hashlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import build_words_from_abp as B          # noqa: E402
import lint_split_wrong_slot as L         # noqa: E402
import size_split_compounds as S          # noqa: E402
import test_app_transplant as T           # noqa: E402  (Env: the synthetic feed + frozen files)

LEX = {"4160": {"make", "made", "create", "created"}, "2316": {"god", "deity"}, "3588": {"the"},
       "2532": {"and"}, "1473": {"it", "i"}}
K1, K2, K3 = ("Gen", 1, 1), ("Gen", 1, 2), ("Gen", 1, 3)
SRC = {K1: "God madeG4160 G3588 G2316",      # both runs split onto 2316: OLD 'God', FEED 'Deity'
       K2: "God madeG4160 G3588 G2316",      # the FEED has no compound -> passdiff -> OLD rows kept
       K3: "AndG2532 itG1473"}               # no split anywhere
FEED = {K1: [("4160-3588-2316", "Deity created")],
        K2: [("4160-3588-2316", "created")],
        K3: [("2532", "And"), ("1473", "it")]}


def _verses(src):
    return [(k[0], k[1], k[2], B.parse_abp_line(f"({k[0]} {k[1]}:{k[2]}) {t}")[3]) for k, t in src.items()]


@contextlib.contextmanager
def corpus(src):
    """B.iter_verses yields exactly these verses (the abp_texts stand-in). The real split and
    build_verse_words are put back on exit (the default _iter_built never restores its wrapper)."""
    with mock.patch.object(B, "iter_verses", lambda *a: _verses(src)), \
         mock.patch.object(B, "_abp_sources", lambda: ()), \
         mock.patch.object(B, "_split_compounds", B._split_compounds), \
         mock.patch.object(B, "build_verse_words", B.build_verse_words):
        yield


def lint_app(app, src, keys=None, lex=None, changes=None):
    stash = {}
    lex = lex or LEX
    with corpus(src):
        it = L._iter_built_app({}, lex, None, None, app, None, None, set(keys or src), stash, None, changes)
        counts, totals, affected, recon = L._build_counts_and_stash({}, lex, None, None, it)
    return affected, recon, stash


def sizer_app(app, src, keys=None, lex=None):
    with corpus(src):
        return S.size_app(app, {}, lex or LEX, None, None, None, None, set(keys or src))


class Base(unittest.TestCase):
    def env(self, src=SRC, feed=FEED):
        e = T.Env(src=src, feed=feed)
        self.addCleanup(e.close)
        return e


class A_ComposedRows(Base):
    def test_feed_word_reported_not_old(self):
        e = self.env()
        app = e.app()
        affected, recon, stash = lint_app(app, {K1: SRC[K1]})
        self.assertEqual(app.tally["transplanted"], 1)
        self.assertEqual(affected, [("Gen 1:1", [(0, "deity", "2316")])])
        self.assertEqual((recon["total_recip"], recon["verses_any"]), (1, 1))
        self.assertEqual(stash[K1][0], ("deity", "2316"))
        # the fired positive: the default mode (OLD text only) reports the word live does not carry
        with corpus({K1: SRC[K1]}):
            _c, _t, d_aff, _r = L._build_counts_and_stash({}, LEX, None, None)
        self.assertEqual(d_aff, [("Gen 1:1", [(0, "God", "2316")])])

    def test_no_split_no_recipient(self):
        e = self.env()
        affected, recon, _ = lint_app(e.app(), {K3: SRC[K3]})
        self.assertEqual((affected, recon["total_recip"]), ([], 0))


class B_KeptOld(Base):
    def test_passdiff_keeps_old_recipient(self):
        e = self.env()
        app = e.app()
        affected, recon, stash = lint_app(app, {K2: SRC[K2]})
        self.assertEqual(app.verdict[K2], "passdiff")       # the FEED set was built, then refused
        self.assertEqual(affected, [("Gen 1:2", [(0, "God", "2316")])])
        self.assertEqual(recon["total_recip"], 1)
        self.assertEqual(stash[K2][0], ("God", "2316"))

    def test_verse_not_in_db_is_skipped(self):        # run() :2764-2767
        e = self.env()
        affected, recon, stash = lint_app(e.app(), SRC, keys={K3})
        self.assertEqual((affected, list(stash)), ([], [K3]))


class FakeApp:
    """apply() builds a FEED set through B.build_verse_words (the second call, as the real
    apply) and returns crafted composed rows: cell at position 0 from FEED, OLD, or neither."""
    def __init__(self, feed_line, mode):
        self.feed_words = B.parse_abp_line(feed_line)[3]
        self.mode = mode

    def apply(self, key, raw_words, corrs, old_rows, bh_rows, lex, ren=None, names=None):
        feed_rows = B.build_verse_words(self.feed_words, bh_rows, lex)
        out = [list(f) for f in feed_rows]
        o0 = next(o for o in old_rows if o[0] == 0)
        if self.mode == "old":
            out[0][1], out[0][2] = o0[1], o0[2]
        elif self.mode == "neither":
            out[0][1], out[0][2] = "Godhead", "godhead"
        return [tuple(r) for r in out]


class C_Ownership(Base):
    SRC1 = {K1: "God madeG4160 G2316"}
    FEED1 = "(Gen 1:1) Deity madeG4160 G2316"

    def both(self, mode, src=None, feed=None):
        src, feed = src or self.SRC1, feed or self.FEED1
        affected, recon, _ = lint_app(FakeApp(feed, mode), src)
        moved, verses, _samples, n_amb = sizer_app(FakeApp(feed, mode), src)
        self.assertEqual((recon["total_recip"], recon["verses_any"]), (moved, verses))
        self.assertEqual(n_amb, 0)
        return affected, moved

    def test_feed_owner(self):
        self.assertEqual(self.both("feed"), ([("Gen 1:1", [(0, "deity", "2316")])], 1))

    def test_old_owner_merge_restore_or_edge_blank(self):
        # a merge-pair restore, and an edge split's blank row (its piece IS the old English with
        # the old head, build :2211), both equal the OLD cell -> OLD's
        self.assertEqual(self.both("old"), ([("Gen 1:1", [(0, "God", "2316")])], 1))

    def test_neither_owner(self):
        # a cell neither run made (in the real build: an edge split's neighbour left with a new rest)
        self.assertEqual(self.both("neither"), ([], 0))

    def test_repeated_word_credits_the_filled_slot(self):
        # independent review finding 1: the count-beyond-before capture credited the source's own
        # 'God' at position 3; the filled slot is position 0. Lint and sizer must name the same slot.
        src = {K1: "God madeG4160 G2316 andG2532 GodG2316"}
        feed = "(Gen 1:1) God madeG4160 G2316 andG2532 GodG2316"
        affected, moved = self.both("feed", src, feed)
        self.assertEqual((affected, moved), ([("Gen 1:1", [(0, "God", "2316")])], 1))
        _m, _v, samples, _a = sizer_app(FakeApp(feed, "feed"), src)
        self.assertEqual(samples[0][1], "*God<2316> | made<4160> | and<2532> | God<2316>")
        with corpus(src):          # the default capture still credits position 3 (unchanged, harmless there)
            d_aff = L._build_counts_and_stash({}, LEX, None, None)[2]
        self.assertEqual(d_aff, [("Gen 1:1", [(3, "God", "2316")])])

    def test_planted_ambiguous_split_counted_by_both(self):
        # a stand-in split: two G3588 slots, one with 'the', one empty; afterwards both changed,
        # positions swapped -> the pairing is not certain: the lint skips + counts, the sizer counts
        def fake(rows, lexicon, carry=False):
            a, b = rows[0], rows[1]
            rows[0] = (1, "of the", "the") + a[3:]
            rows[1] = (0, "the", "the") + b[3:]
            rows.sort(key=lambda r: r[0])
        src = {K1: "theG3588 G3588"}
        line = "(Gen 1:1) theG3588 G3588"
        with mock.patch.object(B, "_split_compounds", fake):
            amb = []
            stash = {}
            with corpus(src):
                it = L._iter_built_app({}, LEX, None, None, FakeApp(line, "feed"), None, None, set(src), stash, amb)
                list(it)
            _m, _v, _s, n_amb = sizer_app(FakeApp(line, "feed"), src)
        self.assertEqual(amb, [("Gen 1:1", 1), ("Gen 1:1", 1)])     # OLD run and FEED run
        self.assertEqual(n_amb, 2)

    def test_lint_and_sizer_agree_on_the_real_transplant(self):
        e = self.env()
        _a, recon, _ = lint_app(e.app(), SRC)
        moved, verses, samples, _amb = sizer_app(self.env().app(), SRC)
        self.assertEqual((recon["total_recip"], recon["verses_any"]), (moved, verses))
        self.assertEqual((moved, verses), (2, 2))
        self.assertEqual(samples[0], ("Gen 1:1", "*Deity<2316> | created<4160>"))

    def test_owners_unit(self):
        old = {"rows": [(0, "God", "God", "2316", "2316")], "recips": [], "fn": [], "filled": set()}
        feed = {"rows": [(0, "Deity", "deity", "2316", "2316")], "recips": [], "fn": [], "filled": set()}
        olds = [(0, "God", "God", "2316", "2316")]
        self.assertIs(L._owners([old, feed], olds, olds)[0], old)          # rows IS old_rows
        self.assertIs(L._owners([old, feed], [feed["rows"][0]], olds)[0], feed)
        self.assertIs(L._owners([old, feed], [(0, "God", "God", "2316", "2316")], olds)[0], old)
        self.assertIsNone(L._owners([old, feed], [(0, "x", "x", "2316", "2316")], olds)[0])
        with self.assertRaises(RuntimeError):
            L._owners([old], [feed["rows"][0]], olds)


class C2_FilledSlots(unittest.TestCase):
    """The split permutes positions and sorts its rows (build :623-627): a filled slot is
    followed by its Greek side, never its list index (the first draft keyed on the index and
    credited the verb's slot - caught by C's sizer test and the sample line)."""
    def split(self, line):
        rows = []
        real = B._split_compounds

        def grab(r, lexicon, carry=False):
            rows.append(list(r))
            real(r, lexicon, carry)
            rows.append(list(r))
        with mock.patch.object(B, "_split_compounds", grab):
            B.build_verse_words(B.parse_abp_line(f"(Gen 1:1) {line}")[3], [], LEX)
        return rows

    def test_real_split_sorts_and_god_slot_is_filled(self):
        before, after = self.split("God madeG4160 G3588 G2316")
        self.assertEqual([r[4] for r in before], ["4160", "3588", "2316"])
        self.assertEqual([r[4] for r in after], ["2316", "3588", "4160"])     # the list was re-sorted
        self.assertEqual(L._filled(before, after), ([0], 0))                  # position 0 = the 2316 row

    def test_no_split_nothing_filled(self):
        before, after = self.split("AndG2532 itG1473")
        self.assertEqual(L._filled(before, after), ([], 0))

    def test_planted_ambiguous_group_counted_not_guessed(self):
        # two changed rows share one Greek side, one had English before and one did not
        g = ("3588", "3588", 0, "", "", None, None, None, None, None, None, None, None)
        before = [(0, "the", "the") + g[3:], (1, None, None) + g[3:]]
        after = [(1, "the", "the") + g[3:], (0, "of the", "the") + g[3:]]
        self.assertEqual(L._filled(before, after), ([], 1))


class D_WordsTable(unittest.TestCase):
    AFF = [("Gen 1:1", [(0, "deity", "2316")])]
    STASH = {K1: {0: ("deity", "2316"), 1: (None, "3588"), 2: ("created", "4160")}}

    def test_match(self):
        live = {K1: {0: ("deity", "G2316"), 1: (None, "G3588"), 2: ("created", "G4160")}}
        self.assertEqual(L._vs_words(self.AFF, self.STASH, live), (1, [], 0))

    def test_planted_head_differs(self):
        live = {K1: {0: ("god", "G2316"), 1: (None, "G3588"), 2: ("created", "G4160")}}
        m, d, rc = L._vs_words(self.AFF, self.STASH, live)
        self.assertEqual((m, rc), (0, 0))
        self.assertEqual(d, [("Gen 1:1", 0, "deity", "2316", "deity", "G2316", "god", "G2316")])

    def test_planted_bare_base_differs(self):          # the strongs_base invariant: G-prefixed
        live = {K1: {0: ("deity", "2316"), 1: (None, "G3588"), 2: ("created", "G4160")}}
        self.assertEqual(len(L._vs_words(self.AFF, self.STASH, live)[1]), 1)

    def test_planted_missing_row_and_rowcount(self):
        live = {K1: {1: (None, "G3588"), 2: ("created", "G4160")}}
        m, d, rc = L._vs_words(self.AFF, self.STASH, live)
        self.assertEqual((m, rc, d[0][6:]), (0, 1, ("", "(no row)")))

    def test_load_words(self):
        with tempfile.TemporaryDirectory() as t:
            db = Path(t) / "w.db"
            c = sqlite3.connect(db)
            c.executescript("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);"
                            "CREATE TABLE words(verse_id INT, position INT, english_head TEXT, strongs_base TEXT);"
                            "INSERT INTO verses VALUES(7,'Gen',1,1);"
                            "INSERT INTO words VALUES(7,0,'deity','G2316'),(7,1,NULL,'G3588');")
            c.commit()
            self.assertEqual(dict(L._load_words(c)), {K1: {0: ("deity", "G2316"), 1: (None, "G3588")}})
            c.close()


def _frozen(d, name, header):
    p = Path(d) / name
    p.write_text("\t".join(header) + "\n", encoding="utf-8", newline="\n")
    Path(str(p) + ".sha256").write_text(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + name + "\n")
    return p


class E_MainAppFeed(Base):
    def run_main(self, live_heads, frozen_ok=True, mod=L, prog="lint", pre_files=()):
        e = self.env()
        app = e.app()
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        d = Path(t.name)
        db = d / "bible.db"
        c = sqlite3.connect(db)
        c.executescript("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);"
                        "CREATE TABLE words(verse_id INT, position INT, english_head TEXT, strongs_base TEXT);"
                        "CREATE TABLE lexicon(strongs TEXT, kjv_def TEXT, strongs_def TEXT);"
                        "CREATE TABLE word_gloss(strongs TEXT, gloss TEXT);")
        c.executemany("INSERT INTO lexicon VALUES(?,?,?)", [("G" + k, " ".join(sorted(v)), "") for k, v in LEX.items()])
        for i, k in enumerate(SRC, 1):
            c.execute("INSERT INTO verses VALUES(?,?,?,?)", (i, *k))
        for k, cells in live_heads.items():
            vid = list(SRC).index(k) + 1
            c.executemany("INSERT INTO words VALUES(?,?,?,?)", [(vid, p, h, sb) for p, (h, sb) in cells.items()])
        c.commit()
        c.close()
        if frozen_ok:
            mp = _frozen(d, "mp.tsv", B.MERGE_PAIR_HEADER)
            ep = _frozen(d, "ep.tsv", B.EDGE_SPLIT_HEADER)
            real = B.AppTransplant.check_merge_pairs
            app.check_merge_pairs = lambda mode: real(app, mode, frozen=mp, edge_frozen=ep)
        out, cwd = io.StringIO(), os.getcwd()
        argv = [prog, str(db), str(d / "scrape.db"), "--app-feed"]
        for f in pre_files:
            (d / f).write_text("an earlier run's file\n", encoding="utf-8")
        try:
            os.chdir(d)
            with corpus(SRC), mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(B, "AppTransplant", lambda *a, **k: app), \
                 mock.patch.object(B, "abp_source_texts", lambda *a: e.src), \
                 mock.patch.object(B, "load_bh_verse_index", lambda c: {}), \
                 mock.patch.object(B, "build_attestation_map", lambda *a, **k: None), \
                 mock.patch.object(B, "load_name_roster", lambda: None), \
                 mock.patch.object(B, "RahlfsLXX", None), mock.patch.object(B, "TAGNTSource", None), \
                 contextlib.redirect_stdout(out):
                try:
                    mod.main()
                    code = 0
                except SystemExit as x:
                    code = x.code
        finally:
            os.chdir(cwd)
        return code, out.getvalue(), d

    LIVE = {K1: {0: ("deity", "G2316"), 1: (None, "G3588"), 2: ("created", "G4160")},
            K2: {0: ("God", "G2316"), 1: (None, "G3588"), 2: ("made", "G4160")},
            K3: {0: ("And", "G2532"), 1: ("it", "G1473")}}

    def test_clean(self):
        code, out, d = self.run_main(self.LIVE)
        self.assertEqual(code, 0, out)
        self.assertIn("merge-pair list: MATCHES", out)
        self.assertIn("L9 --app-feed RESULT: recipients 2 in 2 verses; content 2; RAW FLAGS 0; RESIDUE 0; "
                      "vs words: match 2, DIFFER 0; ambiguous 0; changed after split 0, emptied 0", out)
        self.assertIn("AMBIGUOUS filled-slot pairings: 0 in 0 split runs", out)
        self.assertIn("CHANGED after the split by a later pass (head or Strong's): 0; EMPTIED: 0", out)
        self.assertIn(f"output folder: {d}", out)
        self.assertTrue((d / "split_wrong_slot_vs_words.tsv").is_file())
        self.assertEqual((d / "split_recipients_changed.tsv").read_text(encoding="utf-8").splitlines(),
                         ["ref\tposition\tclass\tsplit_english\tsplit_head\tsplit_base\tcomposed_english\t"
                          "composed_head\tcomposed_base"])

    def test_earlier_output_in_folder_stops_before_anything(self):     # §9.240 (5)
        code, out, d = self.run_main(self.LIVE, pre_files=("split_recipients_changed.tsv",))
        self.assertEqual(code, 1)
        self.assertIn("STOP: output file(s) already in this folder, not overwritten: "
                      "['split_recipients_changed.tsv']", out)
        self.assertNotIn("words table:", out)
        self.assertEqual((d / "split_recipients_changed.tsv").read_text(encoding="utf-8"),
                         "an earlier run's file\n")

    def test_sizer_earlier_output_stops(self):
        code, out, d = self.run_main(self.LIVE, mod=S, prog="sizer", pre_files=("split_compounds_samples.tsv",))
        self.assertEqual(code, 1)
        self.assertIn("STOP: split_compounds_samples.tsv already in this folder, not overwritten", out)
        self.assertNotIn("lexicon entries", out)

    def test_planted_live_differs(self):
        live = dict(self.LIVE)
        live[K1] = {0: ("god", "G2316"), 1: (None, "G3588"), 2: ("created", "G4160")}
        code, out, d = self.run_main(live)
        self.assertIn("vs words: match 1, DIFFER 1", out)
        self.assertIn("Gen 1:1\t0\tdeity\t2316\tdeity\tG2316\tgod\tG2316",
                      (d / "split_wrong_slot_vs_words.tsv").read_text(encoding="utf-8"))

    def test_frozen_lists_not_matching_stops(self):   # the real frozen files: this replay is not that build
        code, out, _d = self.run_main(self.LIVE, frozen_ok=False)
        self.assertEqual(code, 1)
        self.assertIn("STOP: the replay is not the build's transplant", out)
        self.assertNotIn("RESULT", out)

    def test_sizer_main_same_figures(self):
        code, out, d = self.run_main(self.LIVE, mod=S, prog="sizer")
        self.assertEqual(code, 0, out)             # main returns normally
        self.assertIn("recipient slots filled by split: 2\n", out)
        self.assertIn("verses affected:                 2\n", out)
        self.assertIn("AMBIGUOUS Greek-side groups:     0 ", out)
        self.assertIn("merge-pair list: MATCHES", out)
        self.assertEqual((d / "split_compounds_samples.tsv").read_text(encoding="utf-8").splitlines()[1:],
                         ["Gen 1:1\t*Deity<2316> | created<4160>", "Gen 1:2\t*God<2316> | made<4160>"])

    def test_sizer_frozen_lists_not_matching_stops(self):
        code, out, _d = self.run_main(self.LIVE, frozen_ok=False, mod=S, prog="sizer")
        self.assertEqual(code, 1)
        self.assertIn("STOP: the replay is not the build's transplant", out)


class G_JudgedOnComposed(Base):
    """§9.240 (1): passes after the split (:1982-1999) never move a position but can change a
    filled slot's Strong's number or head, or empty it. Each recipient is judged on the composed
    cell, and every one whose split-time (head, base) differs, or that is emptied, is listed."""
    SRC1 = {K1: "God madeG4160 G2316"}
    FEED1 = "(Gen 1:1) God madeG4160 G2316"

    def test_real_pass_g1473_retag_on_a_filled_slot(self):
        # the REAL _g1473_gloss_retag (:1528-1551): the split puts 'he' on the ἐγώ slot, then the
        # retag re-numbers that slot to αὐτός 846 - a function word, so listed, not judged
        lex = {"2036": {"say", "said"}, "1473": {"i", "he", "me"}}
        src = {K1: "he saidG2036 G1473"}
        line = "(Gen 1:1) he saidG2036 G1473"
        changes = []
        affected, recon, _ = lint_app(FakeApp(line, "feed"), src, lex=lex, changes=changes)
        self.assertEqual((affected, recon["total_recip"]), ([], 1))
        self.assertEqual(changes, [("Gen 1:1", 0, "changed", "he", None, "1473", "he", None, "846")])
        self.assertEqual(sizer_app(FakeApp(line, "feed"), src, lex=lex)[:2], (1, 1))

    def test_planted_base_change_judged_on_composed(self):
        # a stand-in for _fix_backwards_pairing (:714-717): swaps the filled slot's Strong's to 2962
        def swap(rows, lex):
            for i, r in enumerate(rows):
                if r[4] == "2316":
                    rows[i] = r[:3] + ("2962", "2962") + r[5:]
        changes = []
        with mock.patch.object(B, "_fix_backwards_pairing", swap):
            affected, recon, _ = lint_app(FakeApp(self.FEED1, "feed"), self.SRC1, changes=changes)
            moved = sizer_app(FakeApp(self.FEED1, "feed"), self.SRC1)[0]
        self.assertEqual(affected, [("Gen 1:1", [(0, "God", "2962")])])          # live's pair, judged
        self.assertEqual(changes, [("Gen 1:1", 0, "changed", "God", "God", "2316", "God", "God", "2962")])
        self.assertEqual((recon["total_recip"], moved), (1, 1))
        # the judgement follows the composed pair: 2962 never renders 'god' -> FLAG; 2316 would pass
        counts = defaultdict(Counter, {"2962": Counter(lord=20), "2316": Counter(god=20)})
        totals = Counter({"2962": 20, "2316": 20})
        self.assertEqual(L._flag_recips(affected[0][1], counts, totals, "Gen 1:1"),
                         [("Gen 1:1", 0, "god", "2962")])
        self.assertEqual(L._flag_recips([(0, "God", "2316")], counts, totals, "Gen 1:1"), [])

    def test_planted_emptied_slot(self):
        # a stand-in for _funcword_noun_relocate (:1723): the filled slot is emptied
        def empty(rows, lex):
            for i, r in enumerate(rows):
                if r[4] == "2316":
                    rows[i] = (r[0], None, None) + r[3:]
        changes = []
        with mock.patch.object(B, "_funcword_noun_relocate", empty):
            affected, recon, _ = lint_app(FakeApp(self.FEED1, "feed"), self.SRC1, changes=changes)
            moved = sizer_app(FakeApp(self.FEED1, "feed"), self.SRC1)[0]
        self.assertEqual(affected, [])
        self.assertEqual(changes, [("Gen 1:1", 0, "emptied", "God", "God", "2316", None, None, "2316")])
        self.assertEqual((recon["total_recip"], moved), (1, 1))     # still a slot the split filled

    def test_unchanged_recipient_not_listed(self):
        changes = []
        lint_app(FakeApp(self.FEED1, "feed"), self.SRC1, changes=changes)
        self.assertEqual(changes, [])


class F_DefaultUnchanged(unittest.TestCase):
    def test_default_replays_old_text_only(self):
        with corpus(SRC):
            counts, totals, affected, recon = L._build_counts_and_stash({}, LEX, None, None)
        self.assertEqual(affected, [("Gen 1:1", [(0, "God", "2316")]), ("Gen 1:2", [(0, "God", "2316")])])
        self.assertEqual((recon["total_recip"], recon["verses_any"]), (2, 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
