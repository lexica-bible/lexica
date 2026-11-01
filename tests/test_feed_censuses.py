"""Locked tests for the two feed scanners (DESIGN_q2_build.md §9.35-§9.41):
scripts/census_feed_dash.py and scripts/census_feed_markup.py.

Synthetic cells only — one per shape / class, plus clean controls that must stay quiet
(§9.15: no committed feed text). The frozen census files are checked against their
.sha256 always; a fresh scan of the real feed is compared to them only when the feed
TSV is present (PA, or the local second copy) and skipped otherwise.

Run:  python tests/test_feed_censuses.py
"""
import csv
import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import abp_app_feed as F           # noqa: E402
import census_feed_dash as D       # noqa: E402
import census_feed_markup as M     # noqa: E402
import census_feed_brackets as K   # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "edition_upgrade"
DASH_FILE = FIX / "feed_dash_census_20261031.tsv"
MARKUP_FILE = FIX / "feed_markup_census_20261031.tsv"
GLUE_FILE = FIX / "feed_glue_census_20261031.tsv"
BRACKET_FILE = FIX / "feed_bracket_census_20261031.tsv"
CARVEOUT_FILE = FIX / "correction_carveout_20261031.tsv"
BS = "\\"


class DashShapes(unittest.TestCase):
    def test_each_shape(self):
        self.assertEqual(D.shapes("type -"), {"end_space_hyphen"})
        self.assertEqual(D.shapes("lesser - younger."), {"mid_space_hyphen"})
        self.assertEqual(D.shapes("exalted --"), {"double_hyphen"})
        self.assertEqual(D.shapes("a – b"), {"en_dash"})
        self.assertEqual(D.shapes("a — b"), {"em_dash"})
        self.assertEqual(D.shapes("- and"), {"other_hyphen"})
        self.assertEqual(D.shapes("3chest- plates"), {"other_hyphen"})
        self.assertEqual(D.shapes("me-"), {"other_hyphen"})

    def test_quiet_controls(self):
        for cell in ("four-footed,", "sixty-six", "In", "", "the beginning"):
            self.assertEqual(D.shapes(cell), set(), cell)

    def test_combined(self):
        self.assertEqual(D.shapes("covenant - my covenant -"),
                         {"end_space_hyphen", "mid_space_hyphen"})


class MarkupClasses(unittest.TestCase):
    def test_backslash_codes_named(self):
        self.assertEqual(M.classes("insides" + BS + "Gr livers"), {"backslash:Gr"})
        self.assertEqual(M.classes(BS + "Scap lord"), {"backslash:Scap"})
        self.assertEqual(M.classes(BS + "Engsevenbd 600"), {"backslash:Engsevenbd"})
        self.assertEqual(M.classes("earth" + BS + "dagger" + BS + "cvnote3:10"),
                         {"backslash:dagger", "backslash:cvnote"})

    def test_backslash_other(self):
        self.assertEqual(M.classes("Urim " + BS + "& Thummim"), {"backslash:&"})
        self.assertEqual(M.classes("mhd" + BS + "'enor"), {"backslash:'"})
        self.assertEqual(M.classes(BS), {"backslash:bare"})
        self.assertEqual(M.classes("and" + BS + " "), {"backslash:bare"})

    def test_other_classes(self):
        self.assertEqual(M.classes("2532 kai"), {"strongs_translit"})
        self.assertEqual(M.classes("3588-1161 ta de"), {"strongs_translit"})
        self.assertEqual(M.classes("DownfallTophet"), {"camel_glue"})
        self.assertEqual(M.classes("a tree timber.."), {"double_period"})
        self.assertEqual(M.classes("him‚"), {"non_ascii:U+201A"})
        self.assertEqual(M.classes("θεος"), {"greek_letter"})

    def test_quiet_controls(self):
        for cell in ("[2sea monsters", "1great],", "God made", "it was good.",
                     "of the", "LORD", "Jesus Christ", "", "and 600"):
            self.assertEqual(M.classes(cell), set(), cell)

    def test_strongs_translit_also_fires_on_a_leading_numeral(self):
        # Known breadth of the frozen rule: ANY cell starting with a 3+ digit number and a
        # space fires, a plain numeral too. All 13 real-feed hits were read 2026-10-31 and
        # are Strong's + transliteration; a numeral-led cell would show up as a rescan diff.
        self.assertEqual(M.classes("600 and 66"), {"strongs_translit"})


class BracketShapes(unittest.TestCase):
    def test_each_class(self):
        self.assertEqual(K.shapes("and that] went"), {"close_without_open"})
        # the S9 (f) shape: a digit glued OUTSIDE any open bracket fires both classes
        self.assertEqual(K.shapes("and 1that] went"), {"close_without_open", "digit_outside"})
        self.assertEqual(K.shapes("[1a [1b]"), {"open_while_open"})
        self.assertEqual(K.shapes("[2let 1us"), {"unclosed"})
        self.assertEqual(K.shapes("4dried up"), {"digit_outside"})
        self.assertEqual(K.shapes("[the 2x 1y]"), {"item_without_digit"})
        self.assertEqual(K.shapes("[2x 2y 1z]"), {"duplicate_digit"})
        self.assertEqual(K.shapes("[1x 3y]"), {"digit_gap"})

    def test_quiet_controls(self):
        for t in ("And God said, Let [3bring forth 1the 2earth]", "[2sea monsters 1great],",
                  "[3each 5as 8called 6the 7Lord 1so 2let 4walk]!", "600 and 60 and 6", ""):
            self.assertEqual(K.shapes(t), set(), t)

    def test_control_fires_on_abp_texts(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(K.control(), 0)


class FrozenFiles(unittest.TestCase):
    def test_sidecars_match(self):
        for f in (DASH_FILE, MARKUP_FILE, GLUE_FILE, BRACKET_FILE, CARVEOUT_FILE):
            F.verify_sidecar(f)          # raises FeedError on any mismatch

    def test_glue_verdicts(self):
        with open(GLUE_FILE, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        verdicts = [r["verdict"] for r in rows]
        self.assertEqual(len(rows), 50)
        self.assertEqual((verdicts.count("glued"), verdicts.count("wording"),
                          verdicts.count("unclear")), (19, 30, 1))
        self.assertTrue(set(verdicts) <= {"glued", "wording", "unclear"})

    def test_dash_end_count_pinned(self):
        with open(DASH_FILE, encoding="utf-8", newline="") as fh:
            shapes = [r["shape"] for r in csv.DictReader(fh, delimiter="\t")]
        self.assertEqual(shapes.count("end_space_hyphen"), 4248)


@unittest.skipUnless(F.FEED_PATH.is_file(), "real feed TSV not present (gitignored)")
class RealFeedRescan(unittest.TestCase):
    def rescan(self, mod):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.tsv"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(mod.main(["--out", str(out)]), 0)
            return hashlib.sha256(out.read_bytes()).hexdigest()

    def test_dash_rescan_equals_frozen(self):
        self.assertEqual(self.rescan(D), hashlib.sha256(DASH_FILE.read_bytes()).hexdigest())

    def test_bracket_rescan_equals_frozen(self):
        self.assertEqual(self.rescan(K), hashlib.sha256(BRACKET_FILE.read_bytes()).hexdigest())

    def test_markup_rescan_equals_frozen(self):
        self.assertEqual(self.rescan(M), hashlib.sha256(MARKUP_FILE.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
