"""Locked test for tests/fixtures/edition_upgrade/declared_deltas.json (gate 2, v4 = DESIGN §9.100
figures + §9.101 G5 + §9.102 G6): the committed file is exactly what scripts/eu_declared_gate2.py
builds from the three committed, sha-pinned files, so its 160 pn_binding rows, 58 gate_b rows and
34 shape exceptions are generated, never typed.

  1. regenerate -> byte-identical to the committed file
  2. all three files match their .sha256 files and the generator's pins; 160 = ADDED 70 +
     REMOVED 90, 58 distinct header rows, 34 exceptions = 33 + 1, every one of them in the 58
  3. one changed byte in any of the three files -> the generator STOPs (exit 2), nothing written
  4. an exception row that is not one of the 58 -> STOP

Run:  python tests/test_eu_declared_gate2.py
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
import eu_declared_gate2 as gen

FIX = os.path.join(ROOT, "tests", "fixtures", "edition_upgrade")
FILES = (("pn_binding_delta_20261107.tsv", gen.DELTA_SHA),
         ("identity_delta_20261107.tsv", gen.IDENT_SHA),
         ("gate2_shape_exceptions_20261107.tsv", gen.EXC_SHA))


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def copy_fixtures():
    tmp = tempfile.mkdtemp()
    fx = os.path.join(tmp, "tests", "fixtures", "edition_upgrade")
    os.makedirs(fx)
    for n, _s in FILES:
        shutil.copy(os.path.join(FIX, n), fx)
    return tmp, fx


class TestDeclaredGate2(unittest.TestCase):
    def test_committed_file_is_the_generated_file(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "v4.json")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "eu_declared_gate2.py"), out],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, "rb") as a, open(os.path.join(FIX, "declared_deltas.json"), "rb") as b:
            self.assertEqual(a.read(), b.read(), "declared_deltas.json differs from the generator's output")

    def test_files_pinned_and_counted(self):
        for name, pinned in FILES:
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
        self.assertEqual(d["gate_b"]["shape_exceptions"], {"file": gen.EXC, "sha256": gen.EXC_SHA})
        with open(os.path.join(FIX, "gate2_shape_exceptions_20261107.tsv"), encoding="utf-8") as fh:
            exc = fh.read().splitlines()[2:]
        notes = [ln.split("\t")[8] for ln in exc]
        self.assertEqual(len(exc), 34)
        self.assertEqual(sum(gen.OUTSIDE in n for n in notes), 33)
        self.assertEqual(sum(gen.PEOPLE in n for n in notes), 1)
        self.assertTrue(any(ln.startswith("Gen 38:1\t18\t") for ln in exc))

    def test_changed_byte_stops_the_generator(self):
        for name, _s in FILES:
            tmp, fx = copy_fixtures()
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

    def test_exception_outside_the_58_stops(self):
        tmp, fx = copy_fixtures()
        p = os.path.join(fx, "gate2_shape_exceptions_20261107.tsv")
        with open(p, encoding="utf-8") as fh:
            lines = fh.read().splitlines(True)
        lines[2] = lines[2].replace("1Ch 1:48\t2\t", "1Ch 1:48\t3\t", 1)     # a position not in the 58
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(lines))
        old_root, old_sha = gen.ROOT, gen.EXC_SHA
        gen.ROOT, gen.EXC_SHA = tmp, sha(p)
        try:
            with self.assertRaises(SystemExit) as cm:
                gen.build()
            self.assertEqual(cm.exception.code, 2)
        finally:
            gen.ROOT, gen.EXC_SHA = old_root, old_sha


if __name__ == "__main__":
    unittest.main()
