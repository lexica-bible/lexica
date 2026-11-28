set +H
L=~/edition_upgrade_runs/split_check_1128_$(date -u +%Y%m%d).log
if [ -e "$L" ]; then echo "SPLITCHECK RESULT: STOP - log already exists (already ran? kept as is): $L"; else
( set -uo pipefail
REF=feb84d69
export TZ=UTC LC_ALL=C PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} - SPLITCHECK - rebuild-words 1a on a fresh copy of live after the split double rows write (DESIGN 9.288 (4), 9.289) - WRITES: the three pinned inputs placed (fixtures + the pre-fill home), a fresh copy of live in the run folder (sqlite backup; live opened read-only) REMOVED on PASS only, the run folder, this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "SPLITCHECK RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
LIVE=~/bible-db/bible.db
FX=tests/fixtures/rebuild_trap
SNAP=$FX/abp_surface_fill_20261127.tsv
REP=$FX/restore_report_20261127.tsv
PF=~/abp_surface_prefill_20261127.db
AM=tests/fixtures/surface_amend/abp_surface_amend_split_20261127.tsv
OLD=$FX/abp_surface_fill_20261126.tsv
SRC_SNAP=~/edition_upgrade_runs/split_refreeze_20261127/abp_surface_fill_20261127.tsv
SRC_REP=~/edition_upgrade_runs/split_proof_20261127/restore_dry.tsv
SRC_PF=~/edition_upgrade_runs/split_proof_20261127/builder.db
D=~/edition_upgrade_runs/split_check_1128
LC=~/edition_upgrade_runs/split_check_1128/live_copy.db
XS=a0777ea9a85fe0b6b5b28a40edd012af1cbe753d650c869899cb9283baf142f0   # the 11/27 frozen file = SNAPSHOT_SHA256 (9.286)
XR=a15bd77e3d1481fb40cc68a2fb4cc9e1ae6ee67511b21ed533f14d5148e12d2f   # the copy-proof report = REPORT_SHA256 (9.284)
XAM=98bfb3508555c664a560cb085c70dab91508df30313f4c8c6c4e37c4ed247b41  # the 2-row amendment file = AMEND_SHA256
XPF=c739a168a067e290f341ea84c58cf606b1f2393d0e4ed245cdebb2560b7b2ec7  # the copy-proof builder table (391,142)
XRS=daa9983cedb63fc317801b06a91525c2159a0ab09c67d70cd2431e52214a4f21   # restore_surface_fill.py at REF (holds the pins)
XHOME_MAX=8300000                                                     # KB: STOP before the copy above this
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
ck() { python3 scripts/snapshot_surface_fill.py --check --src "$LC" --prefill "$PF" --from-restore "$REP" "$@"; }
# --- gates: every miss is STOP; nothing written but the log ---
git merge-base --is-ancestor "$REF" HEAD && git diff --quiet "$REF" HEAD -- scripts tests static/src/00b-two-ending.jsx && [ -z "$(git status --porcelain --untracked-files=no -- scripts tests static)" ] || { echo "SPLITCHECK RESULT: STOP - PA's scripts / tests / two-ending list are not $REF (run deploy.sh); nothing done"; exit 1; }
echo "repo guards: $REF in HEAD's history, scripts / tests / 00b-two-ending.jsx = $REF, nothing uncommitted there: yes"
t=$(date -u +%H%M); if [ "$((10#$t))" -ge 1130 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLITCHECK RESULT: STOP - too near the 13:30 UTC nightly (11:30-14:30); nothing done"; exit 1; fi
[ -e "$D" ] && { echo "SPLITCHECK RESULT: STOP - the run folder already exists (kept as is): $D; nothing done"; exit 1; }
k=$(h scripts/restore_surface_fill.py); [ "$k" = "$XRS" ] || { echo "SPLITCHECK RESULT: STOP - restore_surface_fill.py is not the pinned file ($k); nothing done"; exit 1; }
grep -qx "SURFACE_FLOOR = 394553" scripts/health_check.py || { echo "SPLITCHECK RESULT: STOP - the health floor is not 394553; nothing done"; exit 1; }
for x in "$SRC_SNAP:$XS" "$SRC_SNAP.sha256:" "$SRC_REP:$XR" "$SRC_PF:$XPF" "$AM:$XAM" "$AM.sha256:" "$OLD:"; do
  f=${x%%:*}; want=${x##*:}
  [ -s "$f" ] || { echo "SPLITCHECK RESULT: STOP - missing or empty: $f; nothing done"; exit 1; }
  if [ -n "$want" ]; then k=$(h "$f"); [ "$k" = "$want" ] || { echo "SPLITCHECK RESULT: STOP - $f is not the pinned file ($k); nothing done"; exit 1; }; fi
done
[ "$(cut -d' ' -f1 "$SRC_SNAP.sha256")" = "$XS" ] && [ "$(cut -d' ' -f1 "$AM.sha256")" = "$XAM" ] || { echo "SPLITCHECK RESULT: STOP - a .sha256 beside a source file is not its pin; nothing done"; exit 1; }
echo "sources: the 11/27 frozen file (+ .sha256), the copy-proof report, the copy-proof builder table, the amendment file (+ .sha256): as pinned; the 11/26 file present"
# --- place the three pinned inputs (fixed paths; an existing target must already be the pinned file) ---
echo "=== (place) the frozen file, the report and the pre-fill table ==="
place() {  # $1 source, $2 target, $3 pin
  if [ -e "$2" ]; then k=$(h "$2"); [ "$k" = "$3" ] && { echo "  $2: already placed, = the pin"; return 0; }; echo "  $2: EXISTS and is not the pin ($k)"; return 1; fi
  cp -p -- "$1" "$2" && k=$(h "$2") && [ "$k" = "$3" ] && echo "  $2: placed, = the pin" || { echo "  $2: the copy is not the pin"; return 1; }
}
place "$SRC_SNAP" "$SNAP" "$XS" && place "$SRC_SNAP.sha256" "$SNAP.sha256" "$(h "$SRC_SNAP.sha256")" && place "$SRC_REP" "$REP" "$XR" && place "$SRC_PF" "$PF" "$XPF" \
  || { echo "SPLITCHECK RESULT: STOP - a placement failed (lines above); live untouched"; exit 1; }
if [ -e "$REP.sha256" ]; then [ "$(cut -d' ' -f1 "$REP.sha256")" = "$XR" ] || { echo "SPLITCHECK RESULT: STOP - $REP.sha256 exists and is not $XR"; exit 1; }; echo "  $REP.sha256: already there, = the pin"
else printf '%s  %s\n' "$XR" "$(basename "$REP")" > "$REP.sha256" && echo "  $REP.sha256: written, $(cat "$REP.sha256")"; fi
dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before the copy: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB)"
[ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "SPLITCHECK RESULT: STOP - home is above the bound (or du gave nothing); nothing copied"; exit 1; }
fx0=$(ls -l --time-style=+%s "$FX" tests/fixtures/surface_amend | sha256sum | cut -d' ' -f1)
mkdir "$D" || { echo "SPLITCHECK RESULT: STOP - cannot make the run folder $D"; exit 1; }
# --- the fresh copy (live opened read-only by sqlite's backup) ---
echo "=== (copy) sqlite backup of live into the run folder - start $(date -u +%FT%TZ) ==="
python3 - "$LIVE" "$LC" > "$D/copy.out" 2>&1 <<'PY'
import os, sqlite3, sys
sys.path[0] == "" and sys.path.pop(0)
live, dst = sys.argv[1], sys.argv[2]
s = sqlite3.connect("file:%s?mode=ro" % live, uri=True, timeout=60)
print("live journal mode (read): %s" % s.execute("PRAGMA journal_mode").fetchone()[0])
d = sqlite3.connect(dst)
s.backup(d)
d.execute("PRAGMA journal_mode=DELETE")
d.close()
s.close()
c = sqlite3.connect("file:%s?mode=ro" % dst, uri=True)
print("copy quick_check: %s" % c.execute("PRAGMA quick_check").fetchone()[0])
print("copy abp_surface: %d" % c.execute("SELECT count(*) FROM abp_surface").fetchone()[0])
c.close()
print("copy: %d bytes" % os.path.getsize(dst))
PY
rc=$?; cat "$D/copy.out"; echo "copy exit $rc (expect 0) - end $(date -u +%FT%TZ)"
[ "$rc" = 0 ] && grep -qx "live journal mode (read): delete" "$D/copy.out" && grep -qx "copy quick_check: ok" "$D/copy.out" \
  && grep -qx "copy abp_surface: 394553" "$D/copy.out" || { echo "SPLITCHECK RESULT: STOP - the copy is not right (lines above; anything made is in $D)"; exit 1; }
FL=""; INFO=""
# --- 1. the rebuild-words 1a command, on the copy: must read SNAPSHOT CURRENT ---
echo "=== 1. --check with --amend (rebuild-words 1a, the 11/27 pins) ==="
ck --amend "$AM" --out "$SNAP" > "$D/check.out" 2>&1; r=$?
cat "$D/check.out"; echo "check exit $r (expect 0)"
chk() { case "$(cat "$D/check.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
echo "--- vs the declared figures (DESIGN 9.286):"
chk "frozen file = its .sha256 and the pin" "PASS — checksum file matches, = the pin in restore_surface_fill.py" pin
chk "report = its .sha256" "restore report sha256 $XR = its .sha256" report-file
chk "report = the pin" "restore report = the pin in restore_surface_fill.py" report-pin
chk "amendment file = its .sha256" "amendment file sha256 $XAM = its .sha256" amend-file
chk "amendment file = the pin" "amendment file = the pin in restore_surface_fill.py" amend-pin
chk "G0 3,952 = 3,412 + 539 + 1" "PASS — 3,952 = 3,412 insert + 539 update + 1 remove = the restore report + the amendment file" g0
chk "re-derived = the frozen file byte for byte" "PASS — 3,952 rows, identical bytes" bytes
chk "rows 3,952" "rows                    3,952 | 3,952" rows
chk "inserts / updates 3,412 / 539" "inserts / updates       3,412 / 539 | 3,412 / 539" split
chk "removes 1" "removes                 1 | 1" removes
chk "sha256 pin | file" "sha256                  $XS | $XS" sha
chk "SNAPSHOT CURRENT" "RESULT: SNAPSHOT CURRENT" current
[ "$r" = 0 ] || FL="$FL exit"
# --- 2. control: without --amend the check must STOP (the amendment file is pinned) ---
echo "=== 2. control: --check without --amend - must STOP ==="
ck --out "$SNAP" > "$D/check_noamend.out" 2>&1; rc1=$?
grep -E '^STOPPED|^RESULT' "$D/check_noamend.out" | cut -c1-300; echo "control exit $rc1 (expect 1)"
[ "$rc1" = 1 ] && grep -q -- "--check needs --amend" "$D/check_noamend.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_noamend.out")" = 0 ] || FL="$FL control-noamend"
# --- 3. control: the 11/26 file is no longer the pinned one - must read STALE ---
echo "=== 3. control: --check on the 11/26 frozen file - must read STALE ==="
ck --amend "$AM" --out "$OLD" > "$D/check_old.out" 2>&1; rc2=$?
grep -E '^STOPPED|^RESULT' "$D/check_old.out" | cut -c1-300; echo "control exit $rc2 (expect 1)"
[ "$rc2" = 1 ] && grep -q "STALE SNAPSHOT" "$D/check_old.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_old.out")" = 0 ] || FL="$FL control-old"
# --- 4. the health floor on the copy ---
echo "=== 4. health floor on the copy (394,553 since DESIGN 9.288) ==="
python3 scripts/health_check.py "$LC" --no-backup-check --no-disk-check > "$D/health.out" 2>&1
hl=$(grep "abp_surface rows BELOW floor" "$D/health.out"); echo "$hl"
case "$hl" in *"[OK  ] abp_surface rows BELOW floor 394553"*": 0 "*) echo "  floor line OK, shortfall 0: yes";; *) echo "  floor line OK, shortfall 0: NO"; FL="$FL floor";; esac
# --- 5. stored data re-derived on the copy (DESIGN 9.289 (b)); information: a difference is a follow-up, not a STOP ---
echo "=== 5a. two-ending adjective lists re-derived on the copy (rebuild-words step 10), against static/src/00b-two-ending.jsx ==="
python3 scripts/build_two_ending.py "$LC" > "$D/two_ending.out" 2>&1; r5=$?; echo "build_two_ending exit $r5 (expect 0)"
grep -E "^// (classes|soften)" "$D/two_ending.out"
sed -n '/^\/\/ AUTO-GENERATED/,$p' "$D/two_ending.out" | tr -d '\r' > "$D/two_ending.jsx"
tr -d '\r' < static/src/00b-two-ending.jsx > "$D/two_ending_repo.jsx"
if [ "$r5" = 0 ] && [ -s "$D/two_ending.jsx" ] && cmp -s "$D/two_ending.jsx" "$D/two_ending_repo.jsx"; then echo "  re-derived = the repo's list, byte for byte: yes"
else echo "  re-derived = the repo's list: NO - the difference:"; diff "$D/two_ending_repo.jsx" "$D/two_ending.jsx" | head -n 40; INFO="$INFO two-ending"; fi
echo "=== 5b. dotted_lexicon keys re-derived on the copy (rebuild-words 12a --diff, read-only) ==="
python3 scripts/build_dotted_lexicon.py "$LC" --diff > "$D/dotted_diff.out" 2>&1; r6=$?; echo "build_dotted_lexicon --diff exit $r6 (expect 0)"
grep -E "^\[diff vs" "$D/dotted_diff.out"
grep -qE "^\[diff vs .* \+0 added  -0 removed" "$D/dotted_diff.out" && [ "$r6" = 0 ] && echo "  keys unchanged (+0 / -0): yes" || { echo "  keys unchanged: NO (dotted_diff.out kept)"; INFO="$INFO dotted"; }
# --- nothing else written ---
fx1=$(ls -l --time-style=+%s "$FX" tests/fixtures/surface_amend | sha256sum | cut -d' ' -f1)
echo "fixture folders listing after the placement = after the checks: $([ "$fx1" = "$fx0" ] && echo yes || echo NO)"; [ "$fx1" = "$fx0" ] || FL="$FL fixtures-changed"
for x in -journal -wal -shm; do [ -e "$LC$x" ] && { echo "side file beside the copy: $LC$x"; FL="$FL copy-side-file"; }; done
if [ -n "$FL" ]; then
  echo "the copy is KEPT: $LC ($(stat -c %s "$LC") bytes); home in use: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
  echo "SPLITCHECK RESULT: CHECK -$FL${INFO:+ (information:$INFO)} (lines above; outputs and the copy in $D) - nothing on live changed; to the ruling chat as printed"; exit 1
fi
rm -- ~/edition_upgrade_runs/split_check_1128/live_copy.db; rr=$?
if [ "$rr" = 0 ] && [ -e ~/edition_upgrade_runs/split_check_1128/live_copy.db ]; then rr=1; fi
[ "$rr" = 0 ] && echo "the copy removed: yes" || { echo "SPLITCHECK RESULT: CHECK - passed but the copy could not be removed; to the ruling chat"; exit 1; }
echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before the copy $dk0 KB)"
echo "SPLITCHECK RESULT: PASS - $(date -u +%FT%TZ) - SNAPSHOT CURRENT on a fresh copy of live (3,952 rows = 3,412 + 539 + 1, byte for byte; frozen file, report and amendment file = their pins); without --amend it STOPS; the 11/26 file reads STALE; floor 394,553 OK; the copy removed.${INFO:+ INFORMATION, a follow-up:$INFO differs (lines above).}"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
