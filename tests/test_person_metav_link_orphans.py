"""build_person_metav_link.py: --check-place-orphans (read-only) + --out-dir (ruling 2026-11-07).

  1. clean db: every kind='place' link resolves -> "PLACE-LINK ORPHANS: 0", exit 0
     (a PERSON row with an unknown entity is NOT counted — the check is place-only);
  2. one planted place orphan -> count 1, exit 1 (STOP), the orphan is named;
  3. tables missing -> exit 2;
  4. the check never writes the db (mtime + sha256 unchanged);
  5. --out-dir moves the two leftover lists; with no flag they stay in scripts/ (unchanged).
"""
import hashlib
import importlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "scripts", "build_person_metav_link.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def _mkdb(path, orphan=False, tables=True):
    conn = sqlite3.connect(path)
    if tables:
        conn.execute("CREATE TABLE tipnr_entities (uniq TEXT, head TEXT, bases TEXT, section TEXT)")
        conn.execute("CREATE TABLE tipnr_metav_link (uniq TEXT, kind TEXT, metav_id INTEGER)")
        conn.executemany("INSERT INTO tipnr_entities VALUES (?,?,?,?)", [
            ("Bethel_1", "Bethel", "H1008", "place"), ("Judah_1", "Judah", "H3063", "person"),
        ])
        rows = [("Bethel_1", "place", 11), ("Judah_1", "person", 22),
                ("Nobody_9", "person", 33)]            # person orphan: not this check's business
        if orphan:
            rows.append(("Ghost_1", "place", 44))
        conn.executemany("INSERT INTO tipnr_metav_link VALUES (?,?,?)", rows)
    else:
        conn.execute("CREATE TABLE other (x)")
    conn.commit()
    conn.close()


def _stamp(path):
    with open(path, "rb") as f:
        return os.stat(path).st_mtime_ns, hashlib.sha256(f.read()).hexdigest()


class PlaceOrphanCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "built.db")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self):
        return subprocess.run([sys.executable, SCRIPT, "--bible", self.db, "--check-place-orphans"],
                              capture_output=True, text=True, cwd=self.tmp.name)

    def test_clean_is_zero(self):
        _mkdb(self.db)
        before = _stamp(self.db)
        r = self._run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PLACE-LINK ORPHANS: 0", r.stdout)
        self.assertIn("RESULT: OK", r.stdout)
        self.assertEqual(_stamp(self.db), before, "the read-only check wrote the db")

    def test_orphan_stops(self):
        _mkdb(self.db, orphan=True)
        before = _stamp(self.db)
        r = self._run()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("PLACE-LINK ORPHANS: 1", r.stdout)
        self.assertIn("orphan: Ghost_1", r.stdout)
        self.assertIn("RESULT: STOP", r.stdout)
        self.assertEqual(_stamp(self.db), before, "the read-only check wrote the db")

    def test_missing_tables(self):
        _mkdb(self.db, tables=False)
        r = self._run()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_function_direct(self):
        _mkdb(self.db, orphan=True)
        import build_person_metav_link as bpl
        self.assertEqual(bpl.check_place_orphans(self.db), (1, ["Ghost_1"]))


class OutDir(unittest.TestCase):
    def _load(self, argv):
        with mock.patch.object(sys, "argv", argv):
            import build_person_metav_link as bpl
            return importlib.reload(bpl)

    def test_default_is_scripts(self):
        bpl = self._load(["build_person_metav_link.py"])
        self.assertEqual(bpl.OUT_DIR, os.path.join(ROOT, "scripts"))

    def test_out_dir_flag(self):
        bpl = self._load(["build_person_metav_link.py", "--out-dir", "/tmp/aside"])
        self.assertEqual(bpl.OUT_DIR, "/tmp/aside")


if __name__ == "__main__":
    unittest.main()
