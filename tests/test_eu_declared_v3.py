"""Locked test for tests/fixtures/edition_upgrade/declared_deltas.json v3 (DESIGN §9.100 v3
figures, §9.101 G5): the committed file is exactly what scripts/eu_declared_v3.py builds from
the two committed, sha-pinned list files, so its 160 pn_binding rows and 58 gate_b rows are
generated, never typed.

  1. regenerate -> byte-identical to the committed v3
  2. both list files match their .sha256 files and the generator's pins; 160 = ADDED 70 +
     REMOVED 90, 58 distinct header rows
  3. one changed byte in either list file -> the generator STOPs (exit 2), nothing written

Run:  python tests/test_eu_declared_v3.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import eu_declared_v3 as gen

FIX = os.path.join(ROOT, "tests", "fixtures", "edition_upgrade")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class TestDeclaredV3(unittest.TestCase):
    def test_committed_v3_is_the_generated_file(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "v3.json")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "eu_declared_v3.py"), out],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, "rb") as a, open(os.path.join(FIX, "declared_deltas.json"), "rb") as b:
            self.assertEqual(a.read(), b.read(), "declared_deltas.json differs from the generator's output")

    def test_list_files_pinned_and_counted(self):
        for name, pinned in (("pn_binding_delta_20261107.tsv", gen.DELTA_SHA),
                             ("identity_delta_20261107.tsv", gen.IDENT_SHA)):
            p = os.path.join(FIX, name)
            with open(p + ".sha256", encoding="utf-8") as fh:
                self.assertEqual(fh.read().split()[0], pinned, name)
            self.assertEqual(sha(p), pinned, name)
        with open(os.path.join(FIX, "pn_binding_delta_20261107.tsv"), encoding="utf-8") as fh:
            kinds = [ln.split("\t")[0] for ln in fh.read().splitlines()[1:]]
        self.assertEqual((len(kinds), kinds.count("ADDED"), kinds.count("REMOVED")), (160, 70, 90))
        d = gen.build()
        rows = d["gate_b"]["changed_rows"]
        self.assertEqual(len(rows), 58)
        self.assertEqual(len({(r["book"], r["chapter"], r["verse"], r["position"]) for r in rows}), 58)
        self.assertIn({"book": "Jos", "chapter": 5, "verse": 15, "position": 27, "name": "joshua"}, rows)
        self.assertEqual(d["gate_b"]["pins"], {"pinned ruled loss": 0, "glued cure (blanked)": 0,
                                                "glued cure (replaced)": 0, "glued kept as-is": 29})
        self.assertEqual(d["pn_binding"], {"delta_file": gen.DELTA, "sha256": gen.DELTA_SHA})

    def test_changed_byte_stops_the_generator(self):
        for name in ("pn_binding_delta_20261107.tsv", "identity_delta_20261107.tsv"):
            tmp = tempfile.mkdtemp()
            fx = os.path.join(tmp, "tests", "fixtures", "edition_upgrade")
            os.makedirs(fx)
            for n in ("pn_binding_delta_20261107.tsv", "identity_delta_20261107.tsv"):
                shutil.copy(os.path.join(FIX, n), fx)
            p = os.path.join(fx, name)
            with open(p, "rb") as fh:
                raw = bytearray(fh.read())
            raw[-2] = ord("X") if raw[-2] != ord("X") else ord("Y")
            with open(p, "wb") as fh:
                fh.write(bytes(raw))
            old = gen.ROOT
            gen.ROOT = tmp
            try:
                with self.assertRaises(SystemExit) as cm:
                    gen.build()
                self.assertEqual(cm.exception.code, 2, name)
            finally:
                gen.ROOT = old


if __name__ == "__main__":
    unittest.main()
