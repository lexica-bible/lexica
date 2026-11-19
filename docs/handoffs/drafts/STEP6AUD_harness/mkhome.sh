# STEP6AUD tests: one test home = the base clone (at the test commit) + the clean test copies + the made-up feeds +
# made-up stand-ins for the PA-only files the block reads. Usage: mkhome.sh <home>   (WSL only)
set -euo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
G=~/gate6
H=$1
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs" "$H/db_backups"
cp -a "$G/base" "$H/bible-db"
cp -a "$G/feedhome/LXX-Rahlfs-1935" "$G/feedhome/TAGNT_Mat-Jhn.txt" "$G/feedhome/TAGNT_Act-Rev.txt" "$H/"
cp "$G/dbs/bible_edupg_test_20261101.db" "$G/dbs/bible_edupg_test_built_20261102.db" "$H/bible-db/"
python3 -c 'import datetime; print(datetime.datetime.now().isoformat())' > "$H/db_backups/last_success.txt"
export HOME="$H"
cd "$H/bible-db"
B=$H/bible-db/bible_edupg_test_built_20261102.db; S=$H/bible-db/bible_edupg_test_20261101.db; R=$H/edition_upgrade_runs
# the "built =" guard folder, made the way HEADFIX2's was (eu_step prep on built)
python3 scripts/eu_step.py pre --tag TESTPREP --ref "$(git log -1 --format=%h)" --dir "$R/step4_headfix2_20261116" --db "$B" | tail -1
python3 scripts/eu_step.py prep --tag TESTPREP --built "$B" --dir "$R/step4_headfix2_20261116" --copy words,abp_corrections --save abp_corrections | tail -1
# step-5 eligible file: every verse eligible
python3 - "$S" "$R/step5_eligible_20261101.tsv" <<'PY'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
    f.write("book\tchapter\tverse\teligible\treason\n")
    for b, ch, v in c.execute("SELECT book, chapter, verse FROM verses ORDER BY id"):
        f.write("%s\t%d\t%d\t1\ttest\n" % (b, ch, v))
PY
# STEP4-DELTA2 words_cells.tsv (english members = Rom 1:1, Rom 1:2) and B2's prose list (written = Rom 1:3)
mkdir -p "$R/step4_delta2_20261116/delta"
printf 'book\tchapter\tverse\tposition\tcolumn\ta\tb\tmoved\nRom\t1\t1\t1\tenglish\t%s\t%s\t0\nRom\t1\t2\t1\tenglish\t%s\t%s\t0\nRom\t1\t2\t1\tenglish_head\t%s\t%s\t0\n' \
  "'a'" "'b'" "'a'" "'b'" "'a'" "'b'" > "$R/step4_delta2_20261116/delta/words_cells.tsv"
printf 'book\tchapter\tverse\toutcome\treason\told_len\tnew_len\tchanged\nRom\t1\t3\twritten\ttest\t1\t2\t1\nRom\t1\t4\tkept\ttest\t1\t1\t0\n' > "$R/step5_prose_20261101.tsv"
# the step-4 run-2 log's G2 lines (as check.py prints them, DR :13553-13608) and the delta count line (eu_words_delta.py :247)
{ echo "(made-up stand-in for step4_gate_r2_20261118.log)"; echo "  words.strongs_base           26"
  echo "=== G2 strongs / strongs_base / morph / lemma / is_pn = the (ii) list ==="
  echo "  declared: swap cells 80 + six rows 6 = 86; delta members in these five columns 86 (DESIGN 9.142 (1): 80 + 6 = 86)"
  echo "G2: PASS"; } > "$R/step4_gate_r2_20261118.log"
# PN-star lines (build_words_from_abp.py :2808-2812) at :45 of the stage-B log and in BSTD's build.out
{ for i in $(seq 1 44); do echo "stage-B line $i"; done
  echo "  PN-star pass (lane 2): A 1,505 + B 2,552 written (per DECISION — the sizing plan also prints per SLOT), 3,161 refusals (x 1)"; } > "$R/stageB_build_20261102.log"
mkdir -p "$R/step4_b_standard_20261117"
echo "  PN-star pass (lane 2): A 1,505 + B 2,552 written (per DECISION — the sizing plan also prints per SLOT), 3,161 refusals (x 1)" > "$R/step4_b_standard_20261117/build.out"
# the 10/30 logs: the census run on the clean built (members + its log, as the 10/30 block made them), the phrase-gloss dump on src
python3 scripts/census_count_differs.py "$B" abp_app_html/abp_app_slots.tsv --out "$H/count_differs_members.tsv" > "$H/edition_a_count_differs.log" 2>&1
python3 scripts/audit_phrase_gloss_underdist.py "$S" --dump-all > "$H/edition_d_phrase_gloss_all.txt" 2>&1
{ echo "(made-up stand-in for the 10/30 phrase-gloss log)"; echo "  FLAGGED BEYOND allowlist (gate <= 671):    662"; } > "$H/edition_d_phrase_gloss.log"
cp "$S6/step6aud_check.py" "$R/step6aud_check_20261119.py"
grep "COUNT-DIFFERS" "$H/edition_a_count_differs.log"; wc -l < "$H/count_differs_members.tsv"
echo "home ready: $H (test commit $(git log -1 --format=%h))"
