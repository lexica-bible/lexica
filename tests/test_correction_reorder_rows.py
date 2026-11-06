"""Reorder-metadata correction rows (bracket_id / greek_pos) in build_abp_corrections.ENTRIES must
make their verse read like its prose through the v2 gate's own reader-order port — and the verse
must still be a hit without them (a fix that cannot be seen failing proves nothing).
Rows are the verse as stored on live / the 11/2 built copy (CHECK 4, 11/5)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_abp_corrections as C  # noqa: E402
from audit_reassembly_diff import diff_verse_v2  # noqa: E402

# Joh 14:26 — (position, english, bracket_id, greek_pos)
JOH1426 = [(0, "the", 4, 2), (1, "But", 4, 1), (2, "the", None, None), (3, "comforter,", None, None),
           (4, "spirit", 1, 2), (5, None, 1, None), (6, "holy,", 1, 1), (7, "whom", None, None),
           (8, "will send", 2, 3), (9, "the", 2, 1), (10, "father", 2, 2), (11, "in", None, None),
           (12, None, None, None), (13, "my", None, None), (14, "name,", None, None),
           (15, "that one", None, None), (16, "you", 3, 2), (17, "will teach", 3, 1),
           (18, "all things,", None, None), (19, "and", None, None), (20, "will remind", None, None),
           (21, "you", None, None), (22, "all things", None, None), (23, "which", None, None),
           (24, "I said", None, None), (25, "to you.", None, None)]
JOH1426_TEXT = ("But the comforter, the holy spirit, whom the father will send in my name, that one will "
                "teach you all things, and will remind you all things which I said to you.")


def _apply(rows, book, ch, vs):
    """Apply the ENTRIES digit rows for one verse exactly as apply_abp_corrections would:
    only when the cell holds source_value (None here)."""
    out = {p: [e, b, g] for p, e, b, g in rows}
    for (bk, c, v, pos, field, src, cor, _r, _ref) in C.ENTRIES:
        if (bk, c, v) != (book, ch, vs) or field not in ("bracket_id", "greek_pos"):
            continue
        i = 1 if field == "bracket_id" else 2
        cell = out[pos][i]
        assert (cell is None and src is None) or str(cell) == src, (pos, field, cell, src)
        out[pos][i] = int(cor)
    return [dict(position=p, english=e, bracket_id=b, greek_pos=g) for p, (e, b, g) in sorted(out.items())]


class ReorderRows(unittest.TestCase):
    def test_joh1426_rows_exist_with_the_ruled_shape(self):
        rows = [e for e in C.ENTRIES if e[:3] == ("Joh", 14, 26)]
        self.assertEqual([(e[3], e[4], e[5], e[6], e[8]) for e in rows],
                         [(3, "bracket_id", None, "4", "S-joh14:26"), (3, "greek_pos", None, "3", "S-joh14:26")])

    def test_joh1426_without_the_rows_is_a_word_order_hit(self):
        words = [dict(position=p, english=e, bracket_id=b, greek_pos=g) for p, e, b, g in JOH1426]
        d = diff_verse_v2(words, JOH1426_TEXT)
        self.assertIsNotNone(d)
        self.assertEqual(d["klass"], "word-order")

    def test_joh1426_with_the_rows_reads_clean(self):
        self.assertIsNone(diff_verse_v2(_apply(JOH1426, "Joh", 14, 26), JOH1426_TEXT))


if __name__ == "__main__":
    unittest.main()
