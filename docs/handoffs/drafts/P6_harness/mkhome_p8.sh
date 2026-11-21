# P8 tests: a test home after the swap - a clone of the REAL master (the swap commit 7bb92e10 in its history) with ONE test commit on
# top that sets restore_surface_fill.py's two pins to the made-up files' shas; the made-up live / src / pre-fill copy (mkdbs_p8.py);
# the frozen snapshot made by the REAL snapshot_surface_fill.py from the made-up live; the report + both .sha256 files.
# The TEST copy of the block: REF = the test commit; XS / XR / XB4 / XSRC / XW / XA = the made-up files' values. Nothing else differs.
# usage: mkhome_p8.sh <home> [plant]   plant: none | srcsame | stale (a fill slot's word changed on live after the freeze)   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
H=$1; PL=${2:-none}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs"
git clone -q --bare ~/gate4/repo "$H/origin.git"
git -C "$H/origin.git" fetch -q /mnt/c/Users/JP/projects/bible-db master:refs/heads/realmaster
git clone -q "$H/origin.git" "$H/bible-db"
cd "$H/bible-db"; git checkout -q -B main origin/realmaster
git merge-base --is-ancestor 7bb92e10 HEAD
export HOME="$H" PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
python3 "$T/mkdbs_p8.py" "$H/bible-db" "$H" "$([ "$PL" = srcsame ] && echo srcsame || echo none)"
FX=tests/fixtures/rebuild_trap; mkdir -p $FX
cp "$H/report.tsv" $FX/restore_report_20261115.tsv
( cd $FX && sha256sum restore_report_20261115.tsv > restore_report_20261115.tsv.sha256 )
cp bible.db "$H/freeze_src.db"
python3 scripts/snapshot_surface_fill.py --src "$H/freeze_src.db" --prefill "$H/abp_surface_prefill_20261115.db" \
  --from-restore $FX/restore_report_20261115.tsv --out $FX/abp_surface_fill_20261115.tsv | tail -2
rm "$H/freeze_src.db"
XS=$(sha256sum < $FX/abp_surface_fill_20261115.tsv | cut -d' ' -f1); XR=$(sha256sum < $FX/restore_report_20261115.tsv | cut -d' ' -f1)
XB4=$(sha256sum < "$H/abp_surface_prefill_20261115.db" | cut -d' ' -f1)
sed -i -e "s/^SNAPSHOT_SHA256 = \"[0-9a-f]*\"/SNAPSHOT_SHA256 = \"$XS\"/" -e "s/^REPORT_SHA256 = \"[0-9a-f]*\"/REPORT_SHA256 = \"$XR\"/" scripts/restore_surface_fill.py
git -c user.email=t@t -c user.name=t commit -q -am "test pins"; REF=$(git log -1 --format=%h)
if [ "$PL" = stale ]; then python3 -c "
import sqlite3,sys
c=sqlite3.connect('bible.db'); c.execute(\"UPDATE words SET english_head='changed' WHERE verse_id=3 AND position=4\"); c.commit(); c.close()"; fi
DG=$(python3 - <<'PY'
import os, sys
sys.path.insert(0, "scripts")
import eu_step as E
c = E.ro("bible.db")
for t in ("words", "abp_surface"):
    n, d = E.digest(c, t)
    print("%s=%d %s" % (t, n, d[:12]))
PY
)
XW=$(sed -n 's/^words=//p' <<< "$DG"); XA=$(sed -n 's/^abp_surface=//p' <<< "$DG")
XSRC=$(sha256sum < "$H/bible-db/bible_edupg_test_20261101.db" | cut -d' ' -f1)
sed -e "s/^REF=.*/REF=$REF/" -e "s/^XSRC=[0-9a-f]*/XSRC=$XSRC/" -e "s/^XS=[0-9a-f]*/XS=$XS/" -e "s/^XR=[0-9a-f]*/XR=$XR/" -e "s/^XB4=[0-9a-f]*/XB4=$XB4/" \
    -e "s/^XW=\"[^\"]*\"/XW=\"$XW\"/" -e "s/^XA=\"[^\"]*\"/XA=\"$XA\"/" "$T/block_p8.sh" > "$H/p8.sh"
echo "home ready: $H (plant $PL; REF $REF; words $XW; abp_surface $XA)"
