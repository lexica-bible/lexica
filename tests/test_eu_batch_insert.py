#!/usr/bin/env python3
"""Tests for scripts/eu_batch_insert.py (edition-upgrade corrections batch; DESIGN 9.68 ff., end check 9.148).
Made-up databases only. Covered: a FIRST batch on a copy with no EU rows inserts and reads INSERTED (the
old behaviour, unchanged); a SECOND batch on a copy already holding EU rows also reads INSERTED (9.148:
the end check counts only what this run adds); a dry run writes nothing; --created sets the date, the
default is the first batch's; a key that already has a row (any status) STOPs; a wrong sha or row count STOPs.
"""
import contextlib
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import eu_batch_insert as E  # noqa: E402

SCHEMA = """CREATE TABLE abp_corrections (
    id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL, verse INTEGER NOT NULL,
    position INTEGER NOT NULL, field TEXT NOT NULL, source_value TEXT, corrected_value TEXT,
    reason TEXT NOT NULL, ledger_ref TEXT, applied_at TEXT NOT NULL CHECK (applied_at IN ('ingest','read')),
    status TEXT NOT NULL DEFAULT 'active', created TEXT NOT NULL)"""
HEADER = "book\tchapter\tverse\tposition\tfield\tsource_value\tcorrected_value\tledger_ref\tgroup\tflags\n"


class Insert(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="eubi_")
        self.db = os.path.join(self.tmp, "copy.db")
        c = sqlite3.connect(self.db)
        c.execute(SCHEMA)
        c.execute("INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, "
                  "corrected_value, reason, ledger_ref, applied_at, status, created) "
                  "VALUES ('Gen',1,1,1,'english','a','b','r','L1','ingest','active','2026-07-01')")
        c.commit()
        c.close()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rows(self, name, *lines):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(HEADER + "".join("\t".join(l) + "\n" for l in lines))
        with open(p, "rb") as f:
            return p, hashlib.sha256(f.read()).hexdigest()

    def go(self, path, h, n, *extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = E.main([self.db, "--rows", path, "--sha256", h, "--expect", str(n)] + list(extra))
        return rc, buf.getvalue()

    def q(self, sql):
        c = sqlite3.connect(self.db)
        try:
            return c.execute(sql).fetchall()
        finally:
            c.close()

    def test_first_batch_inserts_as_before(self):
        p, h = self.rows("b1.tsv", ("Isa", "48", "5", "4", "english", "what whould happen", "what would happen",
                                    "EU-Isa48:5", "typo", ""),
                         ("Isa", "48", "5", "-1", "verses.text", "x whould", "x would", "EU-Isa48:5", "typo", ""))
        rc, out = self.go(p, h, 2, "--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("RESULT: INSERTED - counts as expected", out)
        self.assertIn("EU- rows on the copy: 2 (before 0; this batch adds 2, expected 2)", out)
        self.assertEqual(self.q("SELECT DISTINCT created FROM abp_corrections WHERE ledger_ref LIKE 'EU-%'"),
                         [("2026-11-02",)])

    def test_second_batch_on_a_copy_holding_eu_rows_inserts(self):
        p, h = self.rows("b1.tsv", ("Joh", "19", "18", "10", "english", "one h ere", "one here", "EU-Joh19:18", "typo", ""))
        self.assertEqual(self.go(p, h, 1, "--apply")[0], 0)
        p2, h2 = self.rows("b2.tsv", ("Joh", "19", "18", "10", "english_head", "ere", "here", "EU-Joh19:18", "typo", ""))
        rc, out = self.go(p2, h2, 1, "--apply", "--created", "2026-11-15")
        self.assertEqual(rc, 0, out)
        self.assertIn("EU- rows on the copy: 2 (before 1; this batch adds 1, expected 1)", out)
        self.assertIn("RESULT: INSERTED - counts as expected", out)
        self.assertEqual(self.q("SELECT field, source_value, corrected_value, applied_at, status, created "
                                "FROM abp_corrections WHERE field='english_head'"),
                         [("english_head", "ere", "here", "ingest", "active", "2026-11-15")])

    def test_dry_run_writes_nothing(self):
        p, h = self.rows("b.tsv", ("Joh", "19", "18", "10", "english_head", "ere", "here", "EU-Joh19:18", "typo", ""))
        rc, out = self.go(p, h, 1)
        self.assertEqual(rc, 0, out)
        self.assertIn("DRY RUN - nothing written", out)
        self.assertEqual(self.q("SELECT count(*) FROM abp_corrections"), [(1,)])

    def test_existing_key_of_any_status_stops(self):
        c = sqlite3.connect(self.db)
        c.execute("INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value, "
                  "reason, ledger_ref, applied_at, status, created) VALUES ('Joh',19,18,10,'english_head','x','y','r',"
                  "'L9','ingest','retired','2026-07-01')")
        c.commit()
        c.close()
        p, h = self.rows("b.tsv", ("Joh", "19", "18", "10", "english_head", "ere", "here", "EU-Joh19:18", "typo", ""))
        rc, out = self.go(p, h, 1, "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("already have a row in abp_corrections", out)
        self.assertEqual(self.q("SELECT count(*) FROM abp_corrections"), [(2,)])

    def test_wrong_sha_or_count_stops(self):
        p, h = self.rows("b.tsv", ("Joh", "19", "18", "10", "english_head", "ere", "here", "EU-Joh19:18", "typo", ""))
        rc, out = self.go(p, "0" * 64, 1, "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("!= pinned", out)
        rc, out = self.go(p, h, 2, "--apply")
        self.assertEqual(rc, 1)
        self.assertIn("rows in the file != pinned 2", out)
        self.assertEqual(self.q("SELECT count(*) FROM abp_corrections"), [(1,)])

    def test_the_committed_heads_file_is_its_pin(self):
        p = os.path.join(ROOT, "tests", "fixtures", "edition_upgrade", "eu_batch_rows_heads_20261115.tsv")
        with open(p, "rb") as f:
            got = hashlib.sha256(f.read()).hexdigest()
        with open(p + ".sha256", encoding="utf-8") as f:
            self.assertEqual(f.read().split()[0], got)
        rows = E.load(p)
        self.assertEqual([(r["book"], r["chapter"], r["verse"], r["position"], r["field"], r["source_value"],
                           r["corrected_value"], r["ledger_ref"]) for r in rows],
                         [("Joh", 19, 18, 10, "english_head", "ere", "here", "EU-Joh19:18")])


if __name__ == "__main__":
    unittest.main()
