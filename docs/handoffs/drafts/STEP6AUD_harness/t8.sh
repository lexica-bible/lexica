# T8: the check program alone, through the block's own launcher lines (cut from the test block), on a COPY of the clean
# run folder with ONE output hand-edited per case. Shows the branches the made-up feeds cannot reach (PA-only failure lines).
# usage: t8.sh <home> <test block>
set -uo pipefail
H=$1; BLK=$2
export HOME=$H
cd "$H/bible-db"
SRC=$H/edition_upgrade_runs/step6_audit_20261119
# the launcher + its argument lines, exactly as the block has them (from "EU -c" through "> \"$D/check.out\"")
L1=$(grep -n "^EU -c 'import hashlib, sys" "$BLK" | cut -d: -f1)
L2=$(grep -n '> "$D/check.out" 2>&1; r2=$?' "$BLK" | cut -d: -f1)
# the constants block (every assignment line between "set +H" and the A() helper), so the launcher sees the same values
eval "$(sed -n '/^REF=/,/^EU() /p' "$BLK" | grep -E '^[A-Z][A-Z0-9_]*=' )"
EU() { PYTHONIOENCODING=utf-8 python3 "$@"; }
B=$H/bible-db/bible_edupg_test_built_20261102.db; S=$H/bible-db/bible_edupg_test_20261101.db; R=$H/edition_upgrade_runs
WC=$R/step4_delta2_20261116/delta/words_cells.tsv; PRO=$R/step5_prose_20261101.tsv; CDM=$H/count_differs_members.tsv
G4L=$R/step4_gate_r2_20261118.log; PGL=$H/edition_d_phrase_gloss.log; PGA=$H/edition_d_phrase_gloss_all.txt
CDL=$H/edition_a_count_differs.log; BSB=$R/stageB_build_20261102.log; BSO=$R/step4_b_standard_20261117/build.out
LAUNCH=$(sed -n "${L1},${L2}p" "$BLK")
case_() {   # case_ <name> <python edit of the copied folder $D>
  D=$H/t8_$1; rm -rf "$D"; cp -a "$SRC" "$D"; rm -f "$D/check.out"
  python3 -c "$2" "$D"
  eval "$LAUNCH"
  echo "=============== T8 $1: check exit $r2 ==============="
  grep -E "^(STOP|FINDINGS|  FINDING|A[0-9]|C[0-9]|R): |^  FINDING|^STOP" "$D/check.out"
}
case_ tier2_source_missing 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"a9_tier2_built.out"; t=p.read_text(encoding="utf-8"); t=t.replace("rahlfs=yes  tagnt=2 file(s)","rahlfs=yes  tagnt=1 file(s)",1); t+="  !! TAGNT load failed: [Errno 2] (hand-written)\n\n┌─ NOT AUDITED (no reference source / scope) ────\n│   Rev     12000 words   (no --tagnt)\n└────\n"; p.write_text(t,encoding="utf-8")'
case_ lint_rahlfs_not_found 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"c2_lint_src.out"; t=p.read_text(encoding="utf-8"); p.write_text(t.replace("Rahlfs: loaded","Rahlfs: NOT found — OT input will differ from production",1),encoding="utf-8")'
case_ sizing_scope_differs 'import sys,pathlib,re; p=pathlib.Path(sys.argv[1])/"c2_size_built.out"; t=p.read_text(encoding="utf-8"); p.write_text(re.sub(r"(recipient slots filled by split: )([\d,]+)", lambda m: m.group(1)+"{:,}".format(int(m.group(2).replace(",",""))+1), t, 1),encoding="utf-8")'
case_ phrase_control_missed 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"c4_phrase_src.out"; t=p.read_text(encoding="utf-8"); p.write_text(t.replace("CONTROL Psa 39:1: FIRED","CONTROL Psa 39:1: MISSED",1),encoding="utf-8")'
case_ cmdline_other_copy 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"a3_cross_built.out"; L=p.read_text(encoding="utf-8").split("\n"); L[0]=L[0].replace("bible_edupg_test_built_20261102.db","bible_edupg_test_20261101.db"); p.write_text("\n".join(L),encoding="utf-8")'
case_ cert_second_red 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"c1_cert_built.out"; t=p.read_text(encoding="utf-8"); t=t.replace("  [OK  ] 6 backup freshness","  [FAIL] 6 backup freshness\n         - last clean backup was 30h ago (>25h) (hand-written)",1).replace("1 CHECK(S) FAILED (6/7 green)","2 CHECK(S) FAILED (5/7 green)"); p.write_text(t,encoding="utf-8")'
case_ cert_check5_red 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"c1_cert_built.out"; t=p.read_text(encoding="utf-8"); t=t.replace("  [OK  ] 5 feed manifest","  [FAIL] 5 feed manifest\n         - cert_manifest verify FAILED: ERROR: expected 66 ABP files, found 67 (hand-written)",1).replace("1 CHECK(S) FAILED (6/7 green)","2 CHECK(S) FAILED (5/7 green)"); p.write_text(t,encoding="utf-8")'
case_ census_member_extra 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"cd_src.tsv"; p.write_text(p.read_text(encoding="utf-8")+"Rev\t22\t21\t22\t1\t2\t1\t0\t1\tsame-words\n",encoding="utf-8")'
case_ g2_log_missing 'import os; os.rename(os.path.expanduser("~/edition_upgrade_runs/step4_gate_r2_20261118.log"), os.path.expanduser("~/edition_upgrade_runs/step4_gate_r2_20261118.log.away"))'
mv "$R/step4_gate_r2_20261118.log.away" "$R/step4_gate_r2_20261118.log"
# the block constant XJOBSRC set empty (the restated src condition, GAP 1 option b) on the clean outputs, where the made-up src
# DOES carry Job 3:3 -> C3 FINDING on src; the empty value is accepted as an argument
XJOBSRC=""; case_ xjobsrc_empty 'pass'; XJOBSRC="Job 3:3"
