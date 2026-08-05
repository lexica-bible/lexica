"""Red-first controls for apply_cushi_namekeyed.py (reviewer-ruled 2026-08-05).

Two ruled controls:
  1. a NON-Cushi slot carrying H3570 must be REFUSED by the name leg;
  2. a Cushi slot at a MOVED position (any position) must still apply.
Plus: an already-fixed H3569 Cushi slot is not a member (settles to 0).
"""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import apply_cushi_namekeyed as fix


def _mkdb(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE words (verse_id INT, position INT,"
                 " english TEXT, english_head TEXT, strongs_base TEXT)")
    rows = [
        (10, 3, "Cushi", "Cushi", "H3570"),        # clean, frozen position
        (11, 16, "Cushi,", "Cushi", "H3570"),       # moved position (churn row)
        (10, 12, "did obeisance", "obeisance", "H3570"),  # non-name: REFUSE
        (12, 5, "Cushi", "Cushi", "H3569"),         # already right: not a member
        (13, 2, "took", "took", "G2983"),           # unrelated
    ]
    conn.executemany("INSERT INTO words VALUES (?,?,?,?,?)", rows)
    conn.commit()
    return conn


class CushiNameKeyed(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = _mkdb(self.path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.path)

    def test_members_are_exactly_the_cushi_h3570_slots(self):
        members = fix.find_members(self.conn)
        keys = {(m[1], m[2]) for m in members}
        self.assertEqual(keys, {(10, 3), (11, 16)})

    def test_control_non_cushi_h3570_refused(self):
        # ruled control 1: 'obeisance' at H3570 is NOT a member
        members = fix.find_members(self.conn)
        self.assertNotIn((10, 12), {(m[1], m[2]) for m in members})

    def test_control_moved_position_still_applies(self):
        # ruled control 2: position is not consulted — the churn row applies
        members = fix.find_members(self.conn)
        self.assertIn((11, 16), {(m[1], m[2]) for m in members})

    def test_apply_writes_only_members(self):
        members = fix.find_members(self.conn)
        self.conn.executemany(
            "UPDATE words SET strongs_base=? WHERE rowid=?",
            [(fix.RIGHT, m[0]) for m in members])
        self.conn.commit()
        state = dict(((v, p), s) for v, p, s in self.conn.execute(
            "SELECT verse_id, position, strongs_base FROM words"))
        self.assertEqual(state[(10, 3)], "H3569")
        self.assertEqual(state[(11, 16)], "H3569")
        self.assertEqual(state[(10, 12)], "H3570")   # refused slot untouched
        self.assertEqual(state[(13, 2)], "G2983")
        # settles: a second pass finds nothing
        self.assertEqual(fix.find_members(self.conn), [])


if __name__ == "__main__":
    unittest.main()
