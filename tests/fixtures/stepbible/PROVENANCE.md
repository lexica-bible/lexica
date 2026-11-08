# Pinned STEPBible brief lexicons (read by scripts/build_word_gloss.py)

Pinned 2026-11-07 (ruling: gloss sources come from fixed files, download only behind `--fetch`).
Byte-exact copies of STEPBible-Data `Lexicons/` at the commits below — the versions in place when the
word_gloss table was built (2026-06-22). Upstream changed both files on 2026-11-02 (`5de0a47f`,
"Licence summary clarified"); a line diff showed only the licence-summary header lines differ — every
data row is identical. Checksums: `*.sha256` here, and pinned in `build_word_gloss.py` (`PINNED`).
Verify on PA: `cd tests/fixtures/stepbible && sha256sum -c TBESG.txt.sha256 TBESH.txt.sha256`.

| File | Upstream file | Commit (date) | sha256 |
|---|---|---|---|
| TBESG.txt | `TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt` | `805360e477f2668119806241fb2eea07544b765e` (2025-04-16) | `312f723d7b8ef263bbdfb0451c9b8057125804dfff390b6f8544cff2a84b57f4` |
| TBESH.txt | `TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt` | `48b7cfbda441adb6445ea565b4ed23dd98dfdf2e` (2026-03-22) | `464dccadd95fd8620dd05fa0d7a4caba58ec3c4d5db3ebf38e43d046ca25b591` |

Source: https://github.com/STEPBible/STEPBible-Data — Tyndale House, Cambridge, CC BY 4.0 (credited in
CREDITS.md, "Tyndale Brief lexicons (TBESG / TBESH)"). Files are unmodified (UTF-8 with BOM, LF).
