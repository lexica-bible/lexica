# assemble the tests record from the final pass outputs (WSL) -> stdout
set -uo pipefail
G=/home/jp/gate6
echo "# STEP6AUD tests (11/19, CC, WSL test homes ~/gate6/h3-h5; the block run AS WRITTEN with only the constants below swapped)."
echo "# Harness: docs/handoffs/drafts/STEP6AUD_harness/ (setup_base.sh -> mkfeeds.py + mkdbs.py; mkhome.sh; mkplants.py; mktest.py; run.sh; tstops.sh; t8.sh; final.sh)."
echo "# Base clone = ~/gate4/repo at d34d6723 + ONE test-only commit $(git -C $G/base log -1 --format=%h) that re-pins cert_manifest.json over the made-up feeds"
echo "#   ($(git -C $G/base diff --stat d34d6723 HEAD | tail -1)); so REF is swapped to it in every test. scripts/ and tests/ = d34d6723."
echo "# Test copies: the 11/18 made-up pair (~/gate5/home3; 626,309 words / 31,237 verses, rows 'wordN') + lexicon / word_gloss (from"
echo "#   scripts/apfathers/raw/dodson.csv), bdb, lsj, abp_surface (395,003 src / 395,014 built), abp_corrections (built 375 active incl."
echo "#   the Heb 11:24 @7 spent row; src 374), the Psa 39:1 control rows, a Job 3:3 content-other on both, Hab 3:1 sized to the slots sample."
echo "# Made-up feeds: Rahlfs (Gen 1:1-3), TAGNT (Mat / Act 1:1-2), a 1-row bh_scrape.db; the local abp_app_slots.tsv is a 3,480-line"
echo "#   SAMPLE (8 chapters), not PA's 10/24 file. So tier 2, the lint + sizing and the census ran for real on made-up inputs: their"
echo "#   output format is real, their figures mean nothing for PA. Their PA-only failure lines (load failed / NOT found / NOT AUDITED"
echo "#   for a missing source) were tested only on HAND-WRITTEN outputs (T8)."
echo "# check program sha256 $(sha256sum < $G/h4/edition_upgrade_runs/step6aud_check_20261119.py | cut -d' ' -f1)"
for T in T1 T3; do
  echo; echo "=============== $T: the block's swapped constants (diff block.sh -> the test block) ==============="
  cat $G/$T.diff
  [ "$T" = T3 ] && { echo "--- plants (mkplants.py on h5; the guard re-made on the planted built) ---"; cat $G/plants_h5.out; }
  echo "=============== $T: screen output ==============="
  cat $G/$T.out
done
echo; cat $G/T2.out
echo; echo "=============== STOP tests (h3) ==============="; cat $G/TSTOPS.out
echo; echo "=============== T8: the check program alone through the block's launcher, one hand-edited output per case (h4) ==============="
cat $G/T8.out
