# STOP tests on a fresh clean home (h3) with the test block AS WRITTEN (same swaps as T1): each STOPs before any audit runs.
set -uo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
H=/home/jp/gate6/h3
bash "$S6/mkhome.sh" "$H" > /dev/null 2>&1 || { echo "mkhome failed"; exit 1; }
python3 "$S6/mktest.py" "$S6/block.sh" /home/jp/gate6/block_stops.sh "$H" > /dev/null
BF=/home/jp/gate6/block_stops.sh
R=$H/edition_upgrade_runs; U=$R/step6aud_check_20261119.py
clean() { rm -rf "$R/step6_audit_20261119" "$R/step6_audit_20261119.log"; }
run() { echo "=============== $1 ==============="; ( export HOME="$H"; cd "$H"; bash "$BF" ) 2>&1 | grep -vE "^  [a-z0-9_]+: exit" | tail -n "${2:-6}"; ls "$R/step6_audit_20261119" 2>/dev/null | tr '\n' ' '; echo; }
# T4 upload missing
mv "$U" "$U.away"; run "T4 the uploaded check program missing -> STOP after pre, nothing read" 3; mv "$U.away" "$U"; clean
# T5 damaged upload: one line break inside a string (the 11/18 shape)
cp "$U" "$U.good"
python3 - "$U" <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding="utf-8").read()
old = 'print("=== inputs ===")'
assert t.count(old) == 1
open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, 'print("=== in\nputs ===")'))
PY
run "T5 the uploaded check program with one line break added inside a string -> STOP at its sha, no audit run" 3; mv "$U.good" "$U"; clean
# T6 built changed after the guard
cp "$H/bible-db/bible_edupg_test_built_20261102.db" "$H/built.good"
python3 -c "import sqlite3; c=sqlite3.connect('$H/bible-db/bible_edupg_test_built_20261102.db'); c.execute(\"UPDATE words SET english='zzchanged' WHERE rowid=5\"); c.commit()"
run "T6 built changed after the guard was made -> CHECK FAIL, STOP" 4; mv "$H/built.good" "$H/bible-db/bible_edupg_test_built_20261102.db"; clean
# T7 an abp_texts file changed in the checkout (tracked) -> STOP at the git guard
echo "(Gen 99:99) planted" >> "$H/bible-db/abp_texts/abp_ot_texts/abp_genesis.txt"
run "T7 abp_texts changed in the checkout -> STOP (git diff / porcelain)" 2; git -C "$H/bible-db" checkout -q -- abp_texts; clean
# T7b an untracked file added to abp_texts -> STOP (porcelain)
echo "x" > "$H/bible-db/abp_texts/abp_ot_texts/abp_extra.txt"
run "T7b an untracked file in abp_texts -> STOP (porcelain)" 2; rm "$H/bible-db/abp_texts/abp_ot_texts/abp_extra.txt"; clean
# T7c cert_manifest.json edited -> STOP
sed -i 's/"note"/"noteX"/' "$H/bible-db/cert_manifest.json"
run "T7c cert_manifest.json edited -> STOP" 2; git -C "$H/bible-db" checkout -q -- cert_manifest.json; clean
# T7d the count-differs member list one line short -> STOP before any audit
cp "$H/count_differs_members.tsv" "$H/cdm.good"; sed -i '$d' "$H/count_differs_members.tsv"
run "T7d the count-differs member list one verse short -> STOP" 3; mv "$H/cdm.good" "$H/count_differs_members.tsv"; clean
