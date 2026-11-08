"""build_word_gloss.py reads PINNED TBESG/TBESH copies (ruling 2026-11-07).

  1. the pinned files' sha256 match both the code's PINNED table and the *.sha256 files;
  2. with no --fetch the default sources ARE the pinned paths (not URLs);
  3. a URL source without --fetch is refused and nothing is downloaded;
  4. a pinned file whose bytes changed is refused (sha mismatch);
  5. the pinned files parse (non-empty Greek number/lemma maps, non-empty Hebrew map).
"""
import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_word_gloss as bwg  # noqa: E402

PIN = os.path.join(ROOT, "tests", "fixtures", "stepbible")


class WordGlossPinned(unittest.TestCase):
    def test_pins_match_files_and_sidecars(self):
        self.assertEqual(len(bwg.PINNED), 2)
        for path, sha in bwg.PINNED.items():
            with open(path, "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), sha, path)
            with open(path + ".sha256", encoding="utf-8") as f:
                self.assertEqual(f.read().split()[0], sha, path + ".sha256")

    def test_defaults_are_pinned_paths(self):
        self.assertFalse(bwg.FETCH)
        self.assertEqual(os.path.normpath(bwg.TBESG), os.path.join(PIN, "TBESG.txt"))
        self.assertEqual(os.path.normpath(bwg.TBESH), os.path.join(PIN, "TBESH.txt"))

    def test_url_without_fetch_refused_no_download(self):
        with mock.patch("urllib.request.urlopen") as op:
            with self.assertRaises(SystemExit):
                bwg._read_source(bwg.DEFAULT_TBESG_URL)
            op.assert_not_called()

    def test_changed_pinned_file_refused(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "TBESG.txt")
            shutil.copyfile(os.path.join(PIN, "TBESG.txt"), p)
            with open(p, "ab") as f:
                f.write(b"\ntampered\n")
            real_sha = bwg.PINNED[os.path.join(PIN, "TBESG.txt")]
            with mock.patch.dict(bwg.PINNED, {os.path.normpath(p): real_sha}):
                with self.assertRaises(SystemExit):
                    bwg._read_source(p)

    def test_pinned_files_parse(self):
        nums, lemmas = bwg.parse_tbesg(bwg.TBESG)
        self.assertGreater(len(nums), 1000)
        self.assertGreater(len(lemmas), 1000)
        self.assertGreater(len(bwg.load_tbesh(bwg.TBESH)), 1000)


if __name__ == "__main__":
    unittest.main()
