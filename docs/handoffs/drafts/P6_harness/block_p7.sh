set +H
L=~/edition_upgrade_runs/p7_after_swap_$(date -u +%Y%m%d).log
if [ -e "$L" ]; then echo "P7 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=d34d6723
export TZ=UTC
export LC_ALL=C
export PYTHONDONTWRITEBYTECODE=1
export GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} + the swap commit - P7 - after the swap: cert_invariants and health_check on live, G5 against the rollback file (DESIGN 9.213 P7 / Q9, 9.222 (5), 9.223) - READ-ONLY: live and the rollback file only read; writes only its run folder and this log; site UP - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "P7 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
LIVE=~/bible-db/bible.db
R=~/edition_upgrade_runs
D=$R/p7_after_swap
U=$R/p7_check_20261121.py                                                  # the check program as JP uploaded it through PA's Files page; outside the repo
XP7=__XP7__                                                                # sha256 of the check program CC wrote and tested; any other file STOPs
CERT=scripts/cert_invariants.py
HC=scripts/health_check.py
WAIT=60                                                                    # seconds after P6C's log was last written (the reload is inside P6C's deploy.sh) - plan P7
WANT="ai.py scripts/audit_phrase_gloss_underdist.py scripts/cert_invariants.py scripts/health_check.py tests/fixtures/corrections/abp_corrections_active_built_20261121.txt tests/fixtures/corrections/abp_corrections_active_built_20261121.txt.sha256 tests/test_surface_fill_restore.py "
# the eight files of the cleared swap commit, each by git blob id (CC, from the cleared working tree = swap_commit_full.patch 003bb52f...83ee, DESIGN 9.231)
PINS="7f112bdddab79d4f2ba861c76504bd4c5d024ff7 .claude/commands/rebuild-words.md
3ffffc60e2034dcf206caca69e91e7c98631ee34 ai.py
c682f995ba13682b981535591cbd99ff0a3c3c95 scripts/audit_phrase_gloss_underdist.py
241b8911b1b2acc9438e5a54c1906760463a4cd0 scripts/cert_invariants.py
ea7b4bd027e7a7559057094fc8b073b977202064 scripts/health_check.py
210267f6515e902ffb6cf58dec73b3b6549a181d tests/fixtures/corrections/abp_corrections_active_built_20261121.txt
6f4ee7b20df2de01dbc82428a5f172b509f61a72 tests/fixtures/corrections/abp_corrections_active_built_20261121.txt.sha256
52dce7c6bd88d7a9cdd31ac8ca18e4d30d4c6566 tests/test_surface_fill_restore.py"
EU() { PYTHONIOENCODING=utf-8 python3 "$@"; }
# run a read up to 3 times, 30 s apart, ONLY while its output says "database is locked" (a site worker writing its cache, as on 10/25); every output printed
try3() { o=$1; shift; for i in 1 2 3; do "$@" > "${o}_$i.out" 2>&1; rx=$?; echo "--- run $i (exit $rx) ---"; cat "${o}_$i.out"; grep -q "database is locked" "${o}_$i.out" || break; [ "$i" -lt 3 ] && { echo "run $i hit 'database is locked'; the same read again in 30 s"; sleep 30; }; done; }
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
pcf() { find ~/bible-db \( -name __pycache__ -type d -o -path '*/__pycache__/*' \) -printf '%M %u %g %s %T@ %p\n' 2>/dev/null | sort | sha256sum | cut -c1-16; }   # DESIGN 9.209
# --- guards: every miss is STOP, nothing read ---
grep -q "^P6C RESULT: DONE" "$R/p6c_swap_deploy.log" 2>/dev/null || { echo "P7 RESULT: STOP - P6C has not finished DONE ($R/p6c_swap_deploy.log); nothing read"; exit 1; }
s=$(git log -1 --format=%s); echo "PA HEAD subject: $s"
a=no; git merge-base --is-ancestor "$REF" HEAD && a=yes
nm=$(git diff --name-only "$REF" HEAD -- scripts tests ai.py | sort | tr '\n' ' ')
us=$(git status --porcelain --untracked-files=no -- scripts tests ai.py); rs=$?; u=$(grep -c . <<< "$us")
c=no; case "$s" in "edition upgrade: THE SWAP COMMIT"*) c=yes;; esac
n=no; [ "$nm" = "$WANT" ] && n=yes
b=yes; while read -r want path; do got=$(git rev-parse "HEAD:$path" 2>/dev/null); [ "$got" = "$want" ] || { b=no; echo "  content differs from the cleared swap commit: $path (HEAD has ${got:-nothing})"; }; done <<< "$PINS"
echo "PA's code: HEAD is the swap commit: $c; $REF is in its history: $a; files changed since $REF in scripts / tests / ai.py = the cleared seven names: $n; all eight cleared files byte-for-byte as cleared (git blob ids): $b; git status exit $rs, uncommitted changes in them: $u (expect yes, yes, yes, yes, 0, 0)"
[ "$n" = yes ] || echo "  changed: $nm"
[ -n "$us" ] && echo "$us"
[ "$c" = yes ] && [ "$a" = yes ] && [ "$n" = yes ] && [ "$b" = yes ] && [ "$rs" = 0 ] && [ "$u" = 0 ] || { echo "P7 RESULT: STOP - PA's code is not the swap commit as cleared; nothing read"; exit 1; }
[ -s "$R/p6_swap/rollback.txt" ] || { echo "P7 RESULT: STOP - $R/p6_swap/rollback.txt is missing; nothing read"; exit 1; }
RB=$(sed -n 1p "$R/p6_swap/rollback.txt"); X0=$(sed -n 2p "$R/p6_swap/rollback.txt")
case "$RB" in "$HOME"/bible-db/bible_pre_edition_upgrade_*.db) ;; *) echo "P7 RESULT: STOP - unexpected rollback name: $RB; nothing read"; exit 1;; esac
grep -Eqx '[0-9a-f]{64}' <<< "$X0" || { echo "P7 RESULT: STOP - rollback.txt line 2 is not a sha256; nothing read"; exit 1; }
[ -s "$RB" ] || { echo "P7 RESULT: STOP - the rollback file is missing or empty: $RB; nothing read"; exit 1; }
[ -s "$LIVE" ] || { echo "P7 RESULT: STOP - bible.db is missing or empty; nothing read - TO THE RULING CHAT NOW"; exit 1; }
for x in -journal -wal -shm; do [ -e "$RB$x" ] && { echo "P7 RESULT: STOP - side file beside the rollback file: $RB$x; nothing read"; exit 1; }; done
[ -s "$U" ] || { echo "P7 RESULT: STOP - the uploaded check program is missing or empty: $U; nothing read"; exit 1; }
k=$(h "$U"); echo "uploaded check program sha256: $k (expect $XP7)"
[ "$k" = "$XP7" ] || { echo "P7 RESULT: STOP - the uploaded check program is not the file CC wrote and tested; nothing read"; exit 1; }
[ -e "$D" ] && { echo "P7 RESULT: STOP - the run folder already exists (an earlier run? it is kept as is): $D; nothing read"; exit 1; }
mkdir -p "$D" && cp "$U" "$D/check.py" || { echo "P7 RESULT: STOP - cannot make the run folder or copy the program into it"; exit 1; }
t6=$(stat -c %Y "$R/p6c_swap_deploy.log"); w=$(( WAIT - ($(date +%s) - t6) ))
echo "P6C's log was last written $(date -u -d "@$t6" +%FT%TZ); waiting ${w} s if above 0 (at least $WAIT s after it)"
[ "$w" -gt 0 ] && sleep "$w"
pc0=$(pcf)
r0=$(h "$RB"); echo "the rollback file $RB sha256 = rollback.txt line 2 (live just before the swap): $([ "$r0" = "$X0" ] && echo yes || echo NO)"
[ "$r0" = "$X0" ] || { echo "P7 RESULT: STOP - the rollback file is not the pre-swap bytes; nothing compared - TO THE RULING CHAT NOW"; exit 1; }
stat -c 'live now: %s bytes, last write %y (printed only; the site is up and writes its cache)' "$LIVE"
for x in -journal -wal -shm; do echo "beside live: bible.db$x $([ -e "$LIVE$x" ] && echo present || echo absent) (printed only)"; done
bad=0; fin=0
# --- 1. cert_invariants on live (read-only; it opens the file mode=ro) ---
echo "=== 1. cert_invariants on live - start $(date -u +%T) (expect 7/7 green; check 4 at the pin 375, spent 1) ==="
try3 "$D/cert" EU "$CERT" "$LIVE"; rc=$rx; ci=$i
grep -qx "CERTIFIED STATE HOLDS (7/7 green)" "$D/cert_$ci.out" && [ "$rc" = 0 ] && echo "cert 7/7 green, exit 0 (run $ci): yes" || { echo "cert 7/7 green, exit 0 (run $ci): NO"; fin=1; }
grep -q "spent by lane-3: 1 (declared 1)" "$D/cert_$ci.out" && echo "cert spent line 1 / 1: yes" || { echo "cert spent line 1 / 1: NO"; fin=1; }
grep -q '"abp_corrections_active": 375,' scripts/cert_invariants.py && echo "the pin read by check 4 is 375: yes" || { echo "the pin read by check 4 is 375: NO"; fin=1; }
# --- 2. health_check on live (reads only; its backup sweep and disk line are the nightly task's, left out) ---
echo "=== 2. health_check on live, --no-backup-check --no-disk-check - start $(date -u +%T) (expect the floor line OK at 395014 and 0 warning(s), 0 error(s)) ==="
try3 "$D/health" EU "$HC" "$LIVE" --no-backup-check --no-disk-check; rh=$rx
grep -qF "[OK  ] abp_surface rows BELOW floor 395014  [fill or a backfill missing?]: 0 " "$D/health_$i.out" && echo "health floor line OK at 395014 (run $i): yes" || { echo "health floor line OK at 395014 (run $i): NO"; fin=1; }
grep -qx "  0 warning(s), 0 error(s)\." "$D/health_$i.out" && [ "$rh" = 0 ] && echo "health 0 warnings, 0 errors (run $i): yes" || { echo "health 0 warnings, 0 errors (run $i): NO"; fin=1; }
# --- 3. G5 and the keys: the rollback file -> live (the program, read once; both files opened read-only) ---
echo "=== 3. G5 and the keys - start $(date -u +%T) ==="
EU -c 'import hashlib, sys
p, x = sys.argv[1], sys.argv[2]
b = open(p, "rb").read()
h = hashlib.sha256(b).hexdigest()
print("check.py sha256 as run: %s (expect %s)" % (h, x), flush=True)
h == x or sys.exit(4)
sys.path[0] == "" and sys.path.pop(0)
sys.argv = [p] + sys.argv[3:]
exec(compile(b, p, "exec"), {"__name__": "__main__"})' "$D/check.py" "$XP7" "LIVE=$LIVE" "RB=$RB" "REPO=$HOME/bible-db" < /dev/null > "$D/check.out" 2>&1; r2=$?
cat "$D/check.out"; echo "check exit $r2 (expect 0; 3 = findings; 2 = a STOP inside the read; 4 = check.py not the pinned bytes) - end $(date -u +%T)"
# --- after: every miss is CHECK ---
r1=$(h "$RB"); echo "the rollback file's sha256 after = before: $([ "$r1" = "$r0" ] && echo yes || echo NO)"; [ "$r1" = "$r0" ] || bad=1
for x in -journal -wal -shm; do [ -e "$RB$x" ] && { echo "CHECK: side file $RB$x"; bad=1; }; done
pc1=$(pcf); echo "the checkout's cache folders and their contents unchanged: $([ "$pc1" = "$pc0" ] && echo yes || echo NO)"; [ "$pc1" = "$pc0" ] || bad=1
us1=$(git status --porcelain --untracked-files=no -- scripts tests ai.py); [ "$us1" = "$us" ] && echo "scripts / tests / ai.py still as committed: yes" || { echo "scripts / tests / ai.py still as committed: NO"; bad=1; }
[ "$r2" = 0 ] || [ "$r2" = 3 ] || { echo "P7 RESULT: STOP - the G5 read did not finish (exit $r2; $D/check.out); the site stays as it is; to the ruling chat as printed"; exit 1; }
[ "$bad" = 0 ] || { echo "P7 RESULT: CHECK - lines above; the site stays as it is; to the ruling chat as printed"; exit 1; }
[ "$fin" = 0 ] && [ "$r2" = 0 ] || { echo "P7 RESULT: FINDINGS - the NO lines and FINDING lines above; the site stays as it is; nothing is restored, removed or re-run before the ruling chat has read this log"; exit 1; }
echo "P7 RESULT: DONE - $(date -u +%FT%TZ) - cert 7/7, the health floor OK with 0 warnings, G5 and the six keys as declared; this log to the ruling chat by cat. Part B (the five verses on the served site) is CC's and JP's, recorded in words"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
