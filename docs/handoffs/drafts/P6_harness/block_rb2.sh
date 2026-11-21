set +H
L=~/edition_upgrade_runs/rb2_rollback_deploy.log
if [ -e "$L" ]; then echo "RB2 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
export TZ=UTC
echo "RB2 - ROLLBACK, part 2: the site back (JP has ENABLED, then RELOADED the web app) and deploy.sh pulls the revert of the swap commit (charter 7 'roll both or neither'; DESIGN 9.227 (3)) - WINDOW END (this paste) $(date -u +%FT%TZ) - PA HEAD before $(git -C ~/bible-db log -1 --format=%h)"
R=~/edition_upgrade_runs
D=$R/p6_swap
grep -q "^RB1 RESULT: DONE" "$R/rb1_rollback_window.log" || { echo "RB2 RESULT: STOP - RB1 did not finish DONE; deploy.sh NOT run"; exit 1; }
cd ~/bible-db || { echo "RB2 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
bash ~/bible-db/scripts/deploy.sh > "$D/deploy_rollback.out" 2>&1; rd=$?
cat "$D/deploy_rollback.out"
echo "deploy.sh exit $rd (expect 0) - $(date -u +%FT%TZ)"
s=$(git log -1 --format=%s); echo "PA HEAD after: $(git log -1 --format=%h) - $s"
bad=0
grep -q "    reloaded (API " "$D/deploy_rollback.out" && echo "API reload: yes" || { echo "API reload: NO - press the dashboard Reload by hand and tell the ruling chat"; bad=1; }
grep -qx "200 200 200 200 200 " "$D/deploy_rollback.out" && echo "worker sweep 5x 200: yes" || { echo "worker sweep 5x 200: NO"; bad=1; }
case "$s" in 'Revert "edition upgrade: THE SWAP COMMIT'*) echo "HEAD is the revert of the swap commit: yes";; *) echo "HEAD is the revert of the swap commit: NO"; bad=1;; esac
grep -q '"abp_corrections_active": 374,' scripts/cert_invariants.py && echo "cert pin back to 374: yes" || { echo "cert pin back to 374: NO"; bad=1; }
grep -q '^SURFACE_FLOOR = 395003$' scripts/health_check.py && echo "health floor back to 395003: yes" || { echo "health floor back to 395003: NO"; bad=1; }
[ "$rd" = 0 ] && [ "$bad" = 0 ] || { echo "RB2 RESULT: CHECK - lines above; to the ruling chat"; exit 1; }
echo "RB2 RESULT: DONE - live is the pre-swap file on the pre-swap code; to the ruling chat"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
