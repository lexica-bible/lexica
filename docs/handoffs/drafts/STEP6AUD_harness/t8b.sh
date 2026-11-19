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
# 9.198 (b) pass direction: XJOBSRC="" and src's reassembly output with its one content-other member line removed -> C3 PASS
XJOBSRC=""; case_ xjobsrc_empty_src_none 'import sys,pathlib; p=pathlib.Path(sys.argv[1])/"c3_v2diff_src.out"; t=p.read_text(encoding="utf-8"); L=[l for l in t.split("\n") if not l.lstrip().startswith("[content-other] Job 3:3")]; assert len(L)==len(t.split("\n"))-1; p.write_text("\n".join(L),encoding="utf-8")'
