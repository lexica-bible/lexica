set +H
L=~/edition_upgrade_runs/pb0_putback_ready.log
if [ -e "$L" ]; then echo "PB0 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=d34d6723
export TZ=UTC
export GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} - PB0 - the put-back's code test, made BEFORE the swap (reviewer N1: PB tests ai.py as well as scripts + tests, and no block before Disable reads ai.py on PA) - READ-ONLY; site UP; writes only this log; to run before P6R is pasted - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "PB0 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
s=$(git log -1 --format=%s); echo "PA HEAD subject: $s"
[ -n "$s" ] || { echo "PB0 RESULT: STOP - git gave no HEAD subject"; exit 1; }
a=no; git merge-base --is-ancestor "$REF" HEAD && a=yes
d=no; git diff --quiet "$REF" HEAD -- scripts tests ai.py && d=yes
us=$(git status --porcelain --untracked-files=no -- scripts tests ai.py); rs=$?; u=$(grep -c . <<< "$us")
echo "PA's code against the pre-swap code $REF: $REF is in HEAD's history: $a; scripts / tests / ai.py same as $REF: $d; git status exit $rs, uncommitted changes in them: $u (expect yes, yes, 0, 0)"
[ -n "$us" ] && echo "$us"
[ "$a" = yes ] && [ "$d" = yes ] && [ "$rs" = 0 ] && [ "$u" = 0 ] || { echo "PB0 RESULT: STOP - PA's scripts / tests / ai.py are not $REF: PB would refuse after a swap; P6R is NOT to be pasted; to the ruling chat"; exit 1; }
echo "PB0 RESULT: DONE - PB's code test passes on PA as it stands; P6R may follow (after P6A DONE and CC's push)"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
