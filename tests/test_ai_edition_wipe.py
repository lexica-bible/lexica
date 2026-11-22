"""Locked tests for the Q6 wipe (edition upgrade, DESIGN 9.242): every saved AI answer written
from the old English is dropped by one added salt, "edition:app-20261121", in the fingerprint of
summary / xref / pn / chrono (ai_search_cache, removed by each category's own startup prune,
app.py :449-452) and of the LSJ summaries (lsj / abp_ext summary_json, dropped on their next view,
views_lsj.py :396-398). Search was reset at the swap (_CACHE_CODE_VER 49, DESIGN 9.226 Q2 (a)).

  A  each fingerprint = the old one's parts + exactly that salt (and is not the old one);
  B  each category's prune, run on a temp copy of the table, deletes ITS old rows - every one,
     summary's per-book author suffixes included - keeps rows under the new fingerprint, and
     leaves every other category's rows, search and legacy rows alone (ai.md LANDMINE).

Run:  python tests/test_ai_edition_wipe.py
"""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                       # noqa: E402
from core import ai_fingerprint   # noqa: E402
import views_chrono as VC         # noqa: E402
import views_crossref as VX       # noqa: E402
import views_metav as VM          # noqa: E402
import views_summary as VS        # noqa: E402
import views_lsj as VL            # noqa: E402

SALT = "edition:app-20261121"
OLD = {
    "chrono": ("chrono", VC._SYSTEM, VC._PROMPT_TMPL, VC._MODEL),
    "xref": ("xref", VX._XREF_CURATION_SYSTEM, VX._XREF_SYNTHESIS_SYSTEM, "msg:bsb-fallback-4"),
    "pn": ("pn", VM._PN_SYSTEM, VM._PN_USER_TMPL, VM._PN_USER_TMPL_NOVERSE),
    "summary": ("summary", VS._SUMMARY_SYSTEM, VS._AUTHOR_LINE_TMPL, VS._BOOK_PROMPT_TMPL,
                VS._CHAP_PROMPT_TMPL, VS._CHAP_MODEL),
    "lsj": ("lsj", VL._LSJ_SYNTHESIS_SYSTEM, VL._LSJ_ASK_CTX, VL._LSJ_ASK_GEN),
}
NEW = {"chrono": VC._VER, "xref": VX._XREF_VER, "pn": VM._PN_VER, "summary": VS._SUMMARY_TPL_BASE,
       "lsj": VL._LSJ_SYNTH_VER}


class A_Fingerprints(unittest.TestCase):
    def test_each_is_old_parts_plus_the_salt(self):
        for cat, parts in OLD.items():
            with self.subTest(cat):
                self.assertNotEqual(NEW[cat], ai_fingerprint(*parts))
                self.assertEqual(NEW[cat], ai_fingerprint(*parts, SALT))

    def test_search_not_touched_here(self):
        import ai
        self.assertEqual(ai._CACHE_CODE_VER, 49)


class B_Prunes(unittest.TestCase):
    PRUNES = {"chrono": VC.prune_cache, "xref": VX.prune_cache, "pn": VM.prune_cache,
              "summary": VS.prune_cache}

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.db = str(Path(t.name) / "bible.db")
        c = sqlite3.connect(self.db)
        c.execute("CREATE TABLE ai_search_cache (query TEXT PRIMARY KEY, result_json TEXT, ver_key TEXT,"
                  " created_at REAL)")
        rows = []
        for cat in ("chrono", "xref", "pn"):
            rows += [(f"{cat}-old-1", ai_fingerprint(*OLD[cat])), (f"{cat}-old-2", ai_fingerprint(*OLD[cat])),
                     (f"{cat}-new", NEW[cat])]
        old_base = ai_fingerprint(*OLD["summary"])
        rows += [("summary-old-a", old_base + ":aaaaaaaa"), ("summary-old-b", old_base + ":bbbbbbbb"),
                 ("summary-new", NEW["summary"] + ":aaaaaaaa"),
                 ("search-1", "search:0123456789abcdef"), ("legacy-1", "0123456789abcdef")]
        c.executemany("INSERT INTO ai_search_cache VALUES (?, '{}', ?, 0)", rows)
        c.commit()
        c.close()

    def left(self):
        c = sqlite3.connect(self.db)
        try:
            return sorted(r[0] for r in c.execute("SELECT query FROM ai_search_cache"))
        finally:
            c.close()

    def test_each_prune_deletes_only_its_own_old_rows(self):
        with mock.patch.object(core, "DB", self.db):
            got = {cat: fn() for cat, fn in self.PRUNES.items()}
        self.assertEqual(got, {"chrono": 2, "xref": 2, "pn": 2, "summary": 2})
        self.assertEqual(self.left(), ["chrono-new", "legacy-1", "pn-new", "search-1", "summary-new", "xref-new"])

    def test_one_prune_leaves_the_other_categories(self):
        with mock.patch.object(core, "DB", self.db):
            self.assertEqual(VX.prune_cache(), 2)
        left = self.left()
        self.assertNotIn("xref-old-1", left)
        for q in ("chrono-old-1", "pn-old-1", "summary-old-a", "search-1", "legacy-1"):
            self.assertIn(q, left)

    def test_second_run_deletes_nothing(self):          # every worker runs it at startup
        with mock.patch.object(core, "DB", self.db):
            for fn in self.PRUNES.values():
                fn()
            self.assertEqual([fn() for fn in self.PRUNES.values()], [0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
