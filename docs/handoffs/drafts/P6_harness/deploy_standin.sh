#!/bin/bash
# TEST STAND-IN for scripts/deploy.sh (tests only): the real pull and the two invariant tests; the reload + sweep lines are
# printed as deploy.sh prints them on success - no network, no real site touched.
set -e
cd ~/bible-db
git pull -q
python3 tests/test_strongs_join.py >/dev/null
python3 tests/test_build_invariants.py >/dev/null
echo "    reloaded (API — all workers restarted together)."
echo "==> Worker sweep (5x, all must be 200):"
printf "200 200 200 200 200 "
echo
