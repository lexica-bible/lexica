# P7 tests: a test home in the state P6C DONE leaves, made by hand: a clone whose HEAD is a test swap commit (the cleared patch
# applied on d34d6723), P6C's log with its DONE line, p6_swap/rollback.txt, and the made-up pair of files (mkdbs_p7.py).
# The TEST copy of the program differs from p7_check.py in ONE line: the three digests of (1) are the made-up file's own.
# The TEST copy of the block: __XP7__ filled, CERT / HC pointed at the stand-in (p7_standin.py), WAIT shortened.
# usage: mkhome_p7.sh <home> [plant] [wait seconds]   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
PATCH=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/SWAP_COMMIT/swap_commit_full.patch
H=$1; PL=${2:-none}; W=${3:-2}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs/p6_swap" "$H/standin"
git clone -q --bare ~/gate4/repo "$H/origin.git"
git clone -q "$H/origin.git" "$H/work"
( cd "$H/work" && git checkout -q d34d6723 && git switch -q -c master-test && git apply "$PATCH" && git add -A \
  && git -c user.email=t@t -c user.name=t commit -q -m "edition upgrade: THE SWAP COMMIT - test copy" \
  && git push -q origin master-test:refs/heads/swaptest \
  && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m "docs only on top" && git push -q origin master-test:refs/heads/ontop )
git clone -q "$H/origin.git" "$H/bible-db"
( cd "$H/bible-db" && git checkout -q -B main origin/swaptest )
cd "$H/bible-db"
export HOME="$H" PYTHONDONTWRITEBYTECODE=1
R=$H/edition_upgrade_runs
RB=$H/bible-db/bible_pre_edition_upgrade_20261122.db
BL=$(python3 "$T/mkdbs_p7.py" "$H/bible-db" "$(basename "$RB")" "$PL")
printf '%s\n%s\n' "$RB" "$(sha256sum < "$RB" | cut -d' ' -f1)" > "$R/p6_swap/rollback.txt"
echo "P6C RESULT: DONE - live is the new edition on the swap commit; P7 (read-only, at least 60 s after the reload) next" > "$R/p6c_swap_deploy.log"
BL="$BL" python3 - "$T/p7_check.py" "$R/p7_check_20261121.py" <<'PY'
import os, sys
src = open(sys.argv[1], encoding="utf-8", newline="").read().split("\n")
hit = [i for i, l in enumerate(src) if l.startswith("BUILT = {")]
assert len(hit) == 1
src[hit[0]] = os.environ["BL"]
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write("\n".join(src))
PY
XP7=$(sha256sum < "$R/p7_check_20261121.py" | cut -d' ' -f1)
cp "$T/p7_standin.py" "$H/standin/cert.py"; cp "$T/p7_standin.py" "$H/standin/health.py"
sed -e "s/__XP7__/$XP7/" -e "s|^CERT=.*|CERT=$H/standin/cert.py|" -e "s|^HC=.*|HC=$H/standin/health.py|" \
    -e "s/^WAIT=60 /WAIT=$W /" "$T/block_p7.sh" > "$H/p7.sh"
echo "home ready: $H (plant $PL)"
