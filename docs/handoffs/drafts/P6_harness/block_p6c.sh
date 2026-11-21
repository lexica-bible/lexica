set +H
L=~/edition_upgrade_runs/p6c_swap_deploy.log
if [ -e "$L" ]; then echo "P6C RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
export TZ=UTC
echo "P6C - the swap, part C: the site back (JP has ENABLED, then RELOADED the web app) and deploy.sh pulls the swap commit (DESIGN 9.213 P6, 9.227, 9.228) - WINDOW END (this paste) $(date -u +%FT%TZ) - PA HEAD before $(git -C ~/bible-db log -1 --format=%h)"
R=~/edition_upgrade_runs
grep -q "^P6B RESULT: DONE" "$R/p6b_swap_window.log" || { echo "P6C RESULT: STOP - P6B did not finish DONE; deploy.sh NOT run (DESIGN 9.227 (3))"; exit 1; }
cd ~/bible-db || { echo "P6C RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
D=$R/p6_swap
bash ~/bible-db/scripts/deploy.sh > "$D/deploy.out" 2>&1; rd=$?
cat "$D/deploy.out"
echo "deploy.sh exit $rd (expect 0) - $(date -u +%FT%TZ)"
s=$(git log -1 --format=%s); echo "PA HEAD after: $(git log -1 --format=%h) - $s"
bad=0
grep -q "    reloaded (API " "$D/deploy.out" && echo "API reload: yes" || { echo "API reload: NO - press the dashboard Reload by hand and tell the ruling chat"; bad=1; }
grep -qx "200 200 200 200 200 " "$D/deploy.out" && echo "worker sweep 5x 200: yes" || { echo "worker sweep 5x 200: NO"; bad=1; }
case "$s" in "edition upgrade: THE SWAP COMMIT"*) echo "HEAD is the swap commit: yes";; *) echo "HEAD is the swap commit: NO"; bad=1;; esac
grep -q '"abp_corrections_active": 375,' scripts/cert_invariants.py && echo "cert pin 375 in the checkout: yes" || { echo "cert pin 375 in the checkout: NO"; bad=1; }
grep -q '^SURFACE_FLOOR = 395014$' scripts/health_check.py && echo "health floor 395014 in the checkout: yes" || { echo "health floor 395014: NO"; bad=1; }
grep -q '^_CACHE_CODE_VER = 49 ' ai.py && echo "_CACHE_CODE_VER 49 in the checkout: yes" || { echo "_CACHE_CODE_VER 49: NO"; bad=1; }
[ -s tests/fixtures/corrections/abp_corrections_active_built_20261121.txt ] && echo "the 375 member file in the checkout: yes" || { echo "the 375 member file: NO"; bad=1; }
[ "$rd" = 0 ] && [ "$bad" = 0 ] || { echo "P6C RESULT: CHECK - lines above; to the ruling chat"; exit 1; }
echo "P6C RESULT: DONE - live is the new edition on the swap commit; P7 (read-only, at least 60 s after the reload) next"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
